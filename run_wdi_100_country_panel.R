required_packages <- c("dplyr", "tidyr", "readr", "jsonlite")

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

options(timeout = 30)

template <- read_delim(
  "global_health_100_country_template.csv",
  delim = ";",
  show_col_types = FALSE,
  trim_ws = TRUE
) %>%
  mutate(
    include_flag = tolower(include_flag),
    iso3c = toupper(iso3c)
  ) %>%
  filter(include_flag == "yes", !is.na(iso3c), iso3c != "")

countries <- unique(template$iso3c)
years <- 2004:2024

indicators <- c(
  "SH.XPD.CHEX.GD.ZS",
  "SH.MED.PHYS.ZS",
  "SH.MED.NUMW.P3",
  "SH.MED.BEDS.ZS",
  "SP.DYN.LE00.IN",
  "NY.GDP.PCAP.PP.KD",
  "SP.POP.TOTL",
  "SE.ADT.LITR.ZS",
  "IT.NET.USER.ZS",
  "GB.XPD.RSDV.GD.ZS"
)

country_chunks <- split(countries, ceiling(seq_along(countries) / 20))

download_indicator_chunk <- function(indicator_code, chunk, chunk_id, max_tries = 3) {
  country_part <- paste(chunk, collapse = ";")
  url <- paste0(
    "http://api.worldbank.org/v2/country/", country_part,
    "/indicator/", indicator_code,
    "?format=json&date=2004:2024&per_page=20000"
  )

  for (attempt in seq_len(max_tries)) {
    message("Downloading ", indicator_code, " | chunk ", chunk_id, " | attempt ", attempt)
    tmp <- tempfile(fileext = ".json")
    status <- tryCatch(
      system2(
        "curl",
        args = c("-L", "--silent", "--show-error", "--max-time", "30", shQuote(url), "-o", shQuote(tmp))
      ),
      error = function(e) 1
    )

    response <- tryCatch(
      {
        if (!identical(status, 0L) || !file.exists(tmp) || file.info(tmp)$size == 0) {
          stop("download failed")
        }
        fromJSON(tmp)
      },
      error = function(e) e
    )

    if (!inherits(response, "error") && length(response) >= 2 && !is.null(response[[2]]) && nrow(response[[2]]) > 0) {
      return(
        as_tibble(response[[2]]) %>%
          transmute(
            iso3c = countryiso3code,
            country = country$value,
            year = as.integer(date),
            indicator = indicator_code,
            value = as.numeric(value)
          )
      )
    }

    Sys.sleep(1.5 * attempt)
  }

  expand_grid(
    iso3c = chunk,
    year = years
  ) %>%
    mutate(
      country = NA_character_,
      indicator = indicator_code,
      value = NA_real_
    )
}

panel_long_raw <- bind_rows(lapply(indicators, function(indicator_code) {
  bind_rows(Map(
    function(chunk, chunk_id) download_indicator_chunk(indicator_code, chunk, chunk_id),
    country_chunks,
    seq_along(country_chunks)
  ))
}))

panel_long_raw <- expand_grid(
  iso3c = countries,
  year = years,
  indicator = indicators
) %>%
  left_join(panel_long_raw, by = c("iso3c", "year", "indicator")) %>%
  mutate(country = coalesce(country, iso3c))

panel_wide <- panel_long_raw %>%
  select(iso3c, country, year, indicator, value) %>%
  pivot_wider(names_from = indicator, values_from = value) %>%
  mutate(iso3c = toupper(iso3c)) %>%
  left_join(template, by = "iso3c")

panel_long <- panel_wide %>%
  pivot_longer(
    cols = all_of(indicators),
    names_to = "indicator",
    values_to = "value"
  )

missing_by_indicator <- panel_long %>%
  group_by(indicator) %>%
  summarise(
    n_total = n(),
    missing = sum(is.na(value)),
    non_missing = sum(!is.na(value)),
    missing_ratio = missing / n_total,
    .groups = "drop"
  ) %>%
  arrange(desc(missing_ratio))

missing_by_country <- panel_long %>%
  group_by(iso3c, country, country_name_wdi, global_group, region) %>%
  summarise(
    n_total = n(),
    missing = sum(is.na(value)),
    missing_ratio = missing / n_total,
    .groups = "drop"
  ) %>%
  arrange(desc(missing_ratio), iso3c)

write_csv(panel_long, "wdi_panel_100countries_2004_2024_long.csv")
write_csv(panel_wide, "analysis_panel_100countries_2004_2024.csv")
write_csv(missing_by_indicator, "missingness_check_100countries.csv")
write_csv(missing_by_country, "missingness_check_100countries_by_country.csv")

message("DONE")
