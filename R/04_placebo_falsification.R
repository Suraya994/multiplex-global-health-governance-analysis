required_packages <- c("dplyr", "readr", "igraph", "fixest", "purrr")

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
library(igraph)
library(fixest)
setFixest_notes(FALSE)
library(purrr)

set.seed(20240504)

df <- read_csv("io_analysis_panel_100countries_2004_2024.csv", show_col_types = FALSE) %>%
  mutate(
    log_gdp_pc = log(gdp_pc_ppp),
    log_population = log(population)
  )

base_model <- feols(
  life_expectancy ~ l_eigen + health_spending + log_gdp_pc + internet |
    iso3c + year,
  data = df,
  cluster = ~ iso3c
)

shuffle_once <- function(iter) {
  placebo <- df %>%
    group_by(year) %>%
    mutate(placebo_eigen = sample(eigen, size = n(), replace = FALSE)) %>%
    ungroup() %>%
    group_by(iso3c) %>%
    arrange(year, .by_group = TRUE) %>%
    mutate(l_placebo_eigen = lag(placebo_eigen, 1)) %>%
    ungroup()

  m <- feols(
    life_expectancy ~ l_placebo_eigen + health_spending + log_gdp_pc + internet |
      iso3c + year,
    data = placebo,
    cluster = ~ iso3c
  )

  tibble(
    iteration = iter,
    placebo_beta = coef(m)["l_placebo_eigen"]
  )
}

placebo_results <- map_dfr(1:200, shuffle_once)

actual_beta <- coef(base_model)["l_eigen"]
p_empirical <- mean(abs(placebo_results$placebo_beta) >= abs(actual_beta), na.rm = TRUE)

summary_tbl <- tibble(
  actual_beta = actual_beta,
  placebo_mean = mean(placebo_results$placebo_beta, na.rm = TRUE),
  placebo_sd = sd(placebo_results$placebo_beta, na.rm = TRUE),
  empirical_p = p_empirical
)

write_csv(placebo_results, "io_placebo_shuffled_network_results.csv")
write_csv(summary_tbl, "io_placebo_shuffled_network_summary.csv")

capture.output(
  summary(base_model),
  summary_tbl,
  file = "io_placebo_falsification_results.txt"
)

message("DONE")
