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

df <- read_csv("io_analysis_panel_with_iv_100countries_2004_2024.csv", show_col_types = FALSE) %>%
  mutate(
    log_gdp_pc = log(gdp_pc_ppp),
    log_population = log(population)
  )

iv_model_eigen_diffusion <- feols(
  life_expectancy ~ health_spending + log_gdp_pc + log_population + internet |
    iso3c + year |
    l_eigen ~ l_iv_distance_weighted_peer_eigen,
  data = df,
  cluster = ~ iso3c
)

iv_model_eigen_language <- feols(
  life_expectancy ~ health_spending + log_gdp_pc + log_population + internet |
    iso3c + year |
    l_eigen ~ l_iv_language_peer_eigen,
  data = df,
  cluster = ~ iso3c
)

iv_model_eigen_historical <- feols(
  life_expectancy ~ health_spending + log_gdp_pc + log_population + internet |
    iso3c + year |
    l_eigen ~ l_iv_historical_peer_eigen,
  data = df,
  cluster = ~ iso3c
)

iv_model_eigen_contiguous <- feols(
  life_expectancy ~ health_spending + log_gdp_pc + log_population + internet |
    iso3c + year |
    l_eigen ~ l_iv_contiguous_peer_eigen,
  data = df,
  cluster = ~ iso3c
)

models <- list(
  "IV: distance-weighted peer eigen" = iv_model_eigen_diffusion,
  "IV: common-language peer eigen" = iv_model_eigen_language,
  "IV: historical-tie peer eigen" = iv_model_eigen_historical,
  "IV: contiguous-neighbor peer eigen" = iv_model_eigen_contiguous
)

modelsummary(models, output = "io_iv_models.html")
capture.output(
  summary(iv_model_eigen_diffusion, stage = 1:2),
  fitstat(iv_model_eigen_diffusion, ~ ivf1 + ivwald1 + wh),
  summary(iv_model_eigen_language, stage = 1:2),
  fitstat(iv_model_eigen_language, ~ ivf1 + ivwald1 + wh),
  summary(iv_model_eigen_historical, stage = 1:2),
  fitstat(iv_model_eigen_historical, ~ ivf1 + ivwald1 + wh),
  summary(iv_model_eigen_contiguous, stage = 1:2),
  fitstat(iv_model_eigen_contiguous, ~ ivf1 + ivwald1 + wh),
  file = "io_iv_models_results.txt"
)

message("DONE")
