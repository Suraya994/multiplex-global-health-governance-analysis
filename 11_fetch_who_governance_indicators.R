required_packages <- c("dplyr", "tidyr", "readr", "jsonlite", "purrr", "stringr")

local_lib <- file.path(getwd(), "r_libs")
if (!dir.exists(local_lib)) dir.create(local_lib, recursive = TRUE)
.libPaths(c(local_lib, .libPaths()))

for (pkg in required_packages) {
  if (!requireNamespace(pkg, quietly = TRUE)) {
    install.packages(pkg, repos = "https://cloud.r-project.org")
  }
}

library(dplyr)
library(tidyr)
library(readr)
library(jsonlite)
library(purrr)
library(stringr)

template <- read_delim(
  "global_health_100_country_template.csv",
  delim = ";",
  show_col_types = FALSE,
  trim_ws = TRUE
) %>%
  mutate(iso3c = toupper(iso3c)) %>%
  filter(tolower(include_flag) == "yes", !is.na(iso3c), iso3c != "")

dir.create("external_un_who_data", showWarnings = FALSE)

indicators <- tibble::tribble(
  ~indicator_code, ~indicator_label,
  "UHC_INDEX_REPORTED", "UHC service coverage index",
  "UHC_AVAILABILITY_SCORE", "Primary data availability for UHC service coverage index",
  "UHC_SCI_CAPACITY", "UHC service coverage sub-index on service capacity and access",
  "UHC_SCI_INFECT", "UHC service coverage sub-index on infectious diseases",
  "UHC_SCI_RMNCH", "UHC service coverage sub-index on reproductive, maternal, newborn and child health",
  "UHC_SCI_NCD", "UHC service coverage sub-index on noncommunicable diseases",
  "SDGIHR", "Average of 13 International Health Regulations core capacity scores",
  "SDGIHR2018", "IHR SPAR first edition average core capacity score",
  "SDGIHR2021", "IHR SPAR second edition average core capacity score",
  "UHC_IHR", "Compliance with international health regulations",
  "GHED_EXTCHE_SHA2011", "External health expenditure as percentage of current health expenditure",
  "GHED_EXT_pc_PPP_SHA2011", "External health expenditure per capita in PPP international dollars"
)

fetch_odata_all <- function(url) {
  out <- list()
  next_url <- url
  i <- 1
  while (!is.null(next_url) && !is.na(next_url) && nzchar(next_url)) {
    x <- tryCatch(
      fromJSON(next_url, flatten = TRUE),
      error = function(e) NULL
    )
    if (is.null(x)) break
    if (!is.null(x$value) && is.data.frame(x$value) && NROW(x$value) > 0) {
      out[[i]] <- as_tibble(x$value)
    }
    next_url <- x[["@odata.nextLink"]]
    i <- i + 1
    Sys.sleep(0.2)
  }
  bind_rows(out)
}

fetch_indicator <- function(code) {
  filter_txt <- URLencode("SpatialDimType eq 'COUNTRY'", reserved = TRUE)
  url <- paste0("https://ghoapi.azureedge.net/api/", code, "?$filter=", filter_txt)
  message("Downloading WHO GHO ", code)
  df <- fetch_odata_all(url)
  if (nrow(df) == 0) {
    warning("No WHO GHO rows returned for ", code)
    return(tibble(indicator_code = code))
  }
  df %>% mutate(indicator_code = code)
}

who_raw <- map_dfr(indicators$indicator_code, fetch_indicator)

write_csv(who_raw, file.path("external_un_who_data", "who_gho_selected_indicators_raw.csv"))

who_long <- who_raw %>%
  mutate(
    SpatialDim = if ("SpatialDim" %in% names(.)) SpatialDim else NA_character_,
    TimeDim = if ("TimeDim" %in% names(.)) TimeDim else NA_integer_,
    NumericValue = if ("NumericValue" %in% names(.)) NumericValue else NA_real_,
    Value = if ("Value" %in% names(.)) Value else NA_character_,
    ParentLocation = if ("ParentLocation" %in% names(.)) ParentLocation else NA_character_,
    ParentLocationCode = if ("ParentLocationCode" %in% names(.)) ParentLocationCode else NA_character_
  ) %>%
  transmute(
    iso3c = recode(toupper(SpatialDim), ROM = "ROU"),
    year = as.integer(TimeDim),
    indicator_code,
    value = suppressWarnings(as.numeric(NumericValue)),
    value_text = as.character(Value),
    parent_location = ParentLocation,
    parent_location_code = ParentLocationCode
  ) %>%
  filter(year >= 2004, year <= 2024, iso3c %in% template$iso3c) %>%
  left_join(indicators, by = "indicator_code") %>%
  left_join(template, by = "iso3c") %>%
  arrange(iso3c, year, indicator_code)

who_wide <- who_long %>%
  select(iso3c, country_name_wdi, global_group, region, year, indicator_code, value) %>%
  pivot_wider(names_from = indicator_code, values_from = value)

missingness <- expand_grid(
  iso3c = template$iso3c,
  year = 2004:2024,
  indicator_code = indicators$indicator_code
) %>%
  left_join(who_long %>% select(iso3c, year, indicator_code, value), by = c("iso3c", "year", "indicator_code")) %>%
  group_by(indicator_code) %>%
  summarise(
    n_total = n(),
    missing = sum(is.na(value)),
    non_missing = sum(!is.na(value)),
    missing_ratio = missing / n_total,
    .groups = "drop"
  ) %>%
  left_join(indicators, by = "indicator_code") %>%
  arrange(desc(missing_ratio))

write_csv(who_long, "who_governance_indicators_100countries_2004_2024_long.csv")
write_csv(who_wide, "who_governance_panel_100countries_2004_2024.csv")
write_csv(missingness, "who_governance_missingness_100countries.csv")

message("DONE")
