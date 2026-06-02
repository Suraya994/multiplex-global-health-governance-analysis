required_packages <- c("dplyr", "readr", "fixest", "modelsummary")

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
library(fixest)
setFixest_notes(FALSE)
library(modelsummary)

df <- read_csv("io_analysis_panel_100countries_2004_2024.csv", show_col_types = FALSE) %>%
  mutate(
    log_gdp_pc = log(gdp_pc_ppp),
    log_population = log(population),
    north = ifelse(global_group == "Global North", 1, 0),
    south = ifelse(global_group == "Global South", 1, 0),
    health_spending_lag = dplyr::lag(health_spending),
    internet_lag = dplyr::lag(internet)
  ) %>%
  group_by(iso3c) %>%
  arrange(year, .by_group = TRUE) %>%
  mutate(
    l_health_spending = lag(health_spending, 1),
    l_internet = lag(internet, 1),
    l_log_gdp_pc = lag(log_gdp_pc, 1),
    l_hospital_beds = lag(hospital_beds, 1),
    l_physicians = lag(physicians, 1)
  ) %>%
  ungroup()

m_centrality_capacity <- feols(
  eigen ~ l_health_spending + l_physicians + l_hospital_beds + l_log_gdp_pc + l_internet |
    iso3c + year,
  data = df,
  cluster = ~ iso3c
)

m_diffusion <- feols(
  life_expectancy ~ l_eigen + l_health_spending + l_log_gdp_pc + l_internet + l_hospital_beds |
    iso3c + year,
  data = df,
  cluster = ~ iso3c
)

m_stratification <- feols(
  eigen ~ south * l_log_gdp_pc + l_health_spending + l_internet |
    iso3c + year,
  data = df,
  cluster = ~ iso3c
)

models <- list(
  "Centrality as capacity mechanism" = m_centrality_capacity,
  "Network diffusion and outcome" = m_diffusion,
  "North-South stratification" = m_stratification
)

modelsummary(models, output = "io_mechanism_models.html")
capture.output(summary(m_centrality_capacity), summary(m_diffusion), summary(m_stratification), file = "io_mechanism_models.txt")

message("DONE")
