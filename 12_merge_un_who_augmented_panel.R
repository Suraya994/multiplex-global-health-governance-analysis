required_packages <- c("dplyr", "readr", "tidyr")

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
library(tidyr)

panel <- read_csv("io_analysis_panel_100countries_2004_2024.csv", show_col_types = FALSE)

who <- read_csv("who_governance_panel_100countries_2004_2024.csv", show_col_types = FALSE) %>%
  select(-any_of(c("country_name_wdi", "global_group", "region")))

un_metrics <- read_csv("un_ga_voting_network_metrics_100countries_2004_2024.csv", show_col_types = FALSE) %>%
  select(-any_of(c("country_name_wdi", "global_group", "region", "country_name_standard", "who_name_override", "wgi_name_override", "include_flag")))

un_summary <- read_csv("un_ga_voting_country_year_summary_100countries.csv", show_col_types = FALSE) %>%
  select(iso3c, year, starts_with("un_votes"), starts_with("un_"))

augmented <- panel %>%
  left_join(who, by = c("iso3c", "year")) %>%
  left_join(un_metrics, by = c("iso3c", "year")) %>%
  left_join(un_summary, by = c("iso3c", "year")) %>%
  group_by(iso3c) %>%
  arrange(year, .by_group = TRUE) %>%
  mutate(
    l_un_eigen = lag(un_eigen, 1),
    l_un_degree = lag(un_degree, 1),
    l_un_strength = lag(un_strength, 1),
    l_UHC_INDEX_REPORTED = lag(UHC_INDEX_REPORTED, 1),
    l_SDGIHR2021 = lag(SDGIHR2021, 1),
    l_GHED_EXTCHE_SHA2011 = lag(GHED_EXTCHE_SHA2011, 1)
  ) %>%
  ungroup()

missingness <- augmented %>%
  summarise(across(everything(), ~ sum(is.na(.x)))) %>%
  pivot_longer(everything(), names_to = "variable", values_to = "missing") %>%
  mutate(
    n_total = nrow(augmented),
    missing_ratio = missing / n_total
  ) %>%
  arrange(desc(missing_ratio), variable)

write_csv(augmented, "bm_who_augmented_panel_100countries_2004_2024.csv")
write_csv(missingness, "bm_who_augmented_panel_missingness.csv")

message("DONE")
