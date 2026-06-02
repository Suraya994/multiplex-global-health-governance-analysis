required_packages <- c("dplyr", "readr", "countrycode", "haven", "archive", "stringr", "readxl")

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
library(countrycode)
library(haven)
library(archive)
library(stringr)
library(readxl)

template <- read_delim(
  "global_health_100_country_template.csv",
  delim = ";",
  show_col_types = FALSE,
  trim_ws = TRUE
) %>%
  mutate(iso3c = toupper(iso3c)) %>%
  filter(tolower(include_flag) == "yes", !is.na(iso3c), iso3c != "")

dir.create("external_iv_data", showWarnings = FALSE)

urls <- c(
  "http://www.cepii.fr/distance/dist_cepii.zip",
  "https://www.cepii.fr/distance/dist_cepii.zip"
)

zip_path <- file.path("external_iv_data", "dist_cepii.zip")

existing_files <- list.files("external_iv_data", recursive = TRUE, full.names = TRUE)
has_existing_cepii <- any(str_detect(tolower(existing_files), "dist_cepii.*\\.(dta|csv|xls|xlsx)$|dist.*\\.(dta|csv|xls|xlsx)$"))

downloaded <- has_existing_cepii
if (!downloaded) {
  for (u in urls) {
    status <- tryCatch(
      system2("curl", c("-L", "--silent", "--show-error", "--max-time", "120", shQuote(u), "-o", shQuote(zip_path))),
      error = function(e) 1
    )
    if (identical(status, 0L) && file.exists(zip_path) && file.info(zip_path)$size > 1000) {
      downloaded <- TRUE
      break
    }
  }
}

if (!downloaded) {
  stop("CEPII distance archive could not be downloaded.")
}

if (file.exists(zip_path)) {
  archive_extract(zip_path, dir = "external_iv_data")
}

files <- list.files("external_iv_data", recursive = TRUE, full.names = TRUE)
dta_file <- files[str_detect(tolower(files), "dist_cepii.*\\.dta$|dist.*\\.dta$")][1]
csv_file <- files[str_detect(tolower(files), "dist_cepii.*\\.csv$|dist.*\\.csv$")][1]
xls_file <- files[str_detect(tolower(files), "dist_cepii.*\\.xls$|dist.*\\.xls$")][1]
xlsx_file <- files[str_detect(tolower(files), "dist_cepii.*\\.xlsx$|dist.*\\.xlsx$")][1]

if (!is.na(dta_file)) {
  gravity <- read_dta(dta_file)
} else if (!is.na(csv_file)) {
  gravity <- read_csv(csv_file, show_col_types = FALSE)
} else if (!is.na(xlsx_file)) {
  gravity <- read_excel(xlsx_file)
} else if (!is.na(xls_file)) {
  gravity <- read_excel(xls_file)
} else {
  stop("No readable CEPII distance data file found in archive.")
}

gravity <- gravity %>%
  rename_with(tolower)

get_col <- function(data, nm) {
  if (nm %in% names(data)) {
    as.character(data[[nm]])
  } else {
    rep(NA_character_, nrow(data))
  }
}

iso_o_raw <- get_col(gravity, "iso_o")
iso_d_raw <- get_col(gravity, "iso_d")
country_o_raw <- get_col(gravity, "country_o")
country_d_raw <- get_col(gravity, "country_d")

gravity <- gravity %>%
  mutate(
    iso_o = coalesce(
      iso_o_raw,
      countrycode(country_o_raw, "country.name", "iso3c", warn = FALSE)
    ),
    iso_d = coalesce(
      iso_d_raw,
      countrycode(country_d_raw, "country.name", "iso3c", warn = FALSE)
    )
  )

keep <- template$iso3c

gravity_100 <- gravity %>%
  filter(iso_o %in% keep, iso_d %in% keep, iso_o != iso_d) %>%
  transmute(
    iso_o,
    iso_d,
    dist = as.numeric(.data$dist),
    distw = suppressWarnings(as.numeric(.data$distw)),
    contig = suppressWarnings(as.integer(.data$contig)),
    comlang_off = suppressWarnings(as.integer(.data$comlang_off)),
    comlang_ethno = suppressWarnings(as.integer(.data$comlang_ethno)),
    colony = suppressWarnings(as.integer(.data$colony)),
    comcol = suppressWarnings(as.integer(.data$comcol)),
    curcol = suppressWarnings(as.integer(.data$curcol)),
    col45 = suppressWarnings(as.integer(.data$col45)),
    smctry = suppressWarnings(as.integer(.data$smctry))
  ) %>%
  mutate(
    log_dist = log(dist),
    historical_tie = ifelse(coalesce(colony, 0) == 1 | coalesce(comcol, 0) == 1 | coalesce(curcol, 0) == 1 | coalesce(col45, 0) == 1 | coalesce(smctry, 0) == 1, 1, 0),
    common_language = ifelse(coalesce(comlang_off, 0) == 1 | coalesce(comlang_ethno, 0) == 1, 1, 0)
  )

write_csv(gravity_100, "iv_gravity_cepii_100countries.csv")

message("DONE")
