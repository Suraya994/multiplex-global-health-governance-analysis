required_packages <- c("dplyr", "readr", "plm", "lmtest", "sandwich")

local_lib <- file.path(getwd(), "r_libs")
if (!dir.exists(local_lib)) dir.create(local_lib, recursive = TRUE)
.libPaths(c(local_lib, .libPaths()))

for (pkg in required_packages) {
  if (!requireNamespace(pkg, quietly = TRUE)) {
    install.packages(pkg, repos = "https://cloud.r-project.org")
  }
}

library(dplyr)
library(readr)
library(plm)
library(lmtest)
library(sandwich)

df <- read_csv("io_analysis_panel_100countries_2004_2024.csv", show_col_types = FALSE) %>%
  filter(!is.na(life_expectancy)) %>%
  mutate(
    log_gdp_pc = log(gdp_pc_ppp),
    log_population = log(population)
  )

pdf("io_system_gmm_results.pdf", width = 8.5, height = 11)

model_sys_gmm_degree <- pgmm(
  life_expectancy ~ lag(life_expectancy, 1) + lag(degree, 1) + health_spending +
    log_gdp_pc + log_population + internet |
    lag(life_expectancy, 2:4) + lag(degree, 2:4),
  data = df,
  index = c("iso3c", "year"),
  effect = "twoways",
  model = "twosteps",
  transformation = "ld"
)

model_sys_gmm_eigen <- pgmm(
  life_expectancy ~ lag(life_expectancy, 1) + lag(eigen, 1) + health_spending +
    log_gdp_pc + log_population + internet |
    lag(life_expectancy, 2:4) + lag(eigen, 2:4),
  data = df,
  index = c("iso3c", "year"),
  effect = "twoways",
  model = "twosteps",
  transformation = "ld"
)

print(summary(model_sys_gmm_degree, robust = TRUE))
print(mtest(model_sys_gmm_degree, order = 1))
print(mtest(model_sys_gmm_degree, order = 2))
print(sargan(model_sys_gmm_degree))

print(summary(model_sys_gmm_eigen, robust = TRUE))
print(mtest(model_sys_gmm_eigen, order = 1))
print(mtest(model_sys_gmm_eigen, order = 2))
print(sargan(model_sys_gmm_eigen))

dev.off()

capture.output(
  summary(model_sys_gmm_degree, robust = TRUE),
  mtest(model_sys_gmm_degree, order = 1),
  mtest(model_sys_gmm_degree, order = 2),
  sargan(model_sys_gmm_degree),
  file = "io_system_gmm_degree_results.txt"
)

capture.output(
  summary(model_sys_gmm_eigen, robust = TRUE),
  mtest(model_sys_gmm_eigen, order = 1),
  mtest(model_sys_gmm_eigen, order = 2),
  sargan(model_sys_gmm_eigen),
  file = "io_system_gmm_eigen_results.txt"
)

message("DONE")
