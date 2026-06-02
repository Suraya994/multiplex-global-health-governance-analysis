required_packages <- c("data.table", "dplyr", "readr", "stringr", "lubridate")

local_lib <- file.path(getwd(), "r_libs")
if (!dir.exists(local_lib)) dir.create(local_lib, recursive = TRUE)
.libPaths(c(local_lib, .libPaths()))

for (pkg in required_packages) {
  if (!requireNamespace(pkg, quietly = TRUE)) {
    install.packages(pkg, repos = "https://cloud.r-project.org")
  }
}

library(data.table)
library(dplyr)
library(readr)
library(stringr)
library(lubridate)

template <- read_delim(
  "global_health_100_country_template.csv",
  delim = ";",
  show_col_types = FALSE,
  trim_ws = TRUE
) %>%
  mutate(iso3c = toupper(iso3c)) %>%
  filter(tolower(include_flag) == "yes", !is.na(iso3c), iso3c != "")

dir.create("external_un_who_data", showWarnings = FALSE)

url <- "https://digitallibrary.un.org/record/4060887/files/2026_02_06_ga_voting.csv?download=1"
raw_path <- file.path("external_un_who_data", "2026_02_06_ga_voting.csv")

if (!file.exists(raw_path) || file.info(raw_path)$size < 1000000) {
  status <- system2(
    "curl",
    c("-L", "--fail", "--show-error", "--connect-timeout", "30", "--max-time", "1800", shQuote(url), "-o", shQuote(raw_path))
  )
  if (!identical(status, 0L)) stop("UN General Assembly voting data could not be downloaded.")
}

keep_cols <- c(
  "undl_id", "ms_code", "ms_name", "ms_vote", "date", "session", "resolution",
  "draft", "committee_report", "meeting", "title", "agenda_title", "subjects",
  "vote_note", "total_yes", "total_no", "total_abstentions", "total_non_voting",
  "total_ms", "undl_link"
)

raw <- fread(raw_path, select = keep_cols, showProgress = TRUE)

votes_100 <- raw %>%
  as_tibble() %>%
  mutate(
    iso3c = toupper(ms_code),
    vote_date = as.Date(date),
    year = year(vote_date),
    vote_clean = toupper(str_trim(ms_vote)),
    vote_numeric = case_when(
      vote_clean %in% c("Y", "YES") ~ 1,
      vote_clean %in% c("N", "NO") ~ -1,
      vote_clean %in% c("A", "ABSTAIN", "ABSTENTION") ~ 0,
      TRUE ~ NA_real_
    ),
    vote_yes = if_else(vote_clean %in% c("Y", "YES"), 1, 0, missing = NA_real_),
    resolution_id = paste0(undl_id, "_", resolution)
  ) %>%
  filter(year >= 2004, year <= 2024, iso3c %in% template$iso3c) %>%
  left_join(template, by = "iso3c")

country_year <- votes_100 %>%
  group_by(iso3c, country_name_wdi, global_group, region, year) %>%
  summarise(
    un_votes_total = n(),
    un_votes_yes = sum(vote_clean %in% c("Y", "YES"), na.rm = TRUE),
    un_votes_no = sum(vote_clean %in% c("N", "NO"), na.rm = TRUE),
    un_votes_abstain = sum(vote_clean %in% c("A", "ABSTAIN", "ABSTENTION"), na.rm = TRUE),
    un_yes_share = un_votes_yes / un_votes_total,
    un_no_share = un_votes_no / un_votes_total,
    un_abstain_share = un_votes_abstain / un_votes_total,
    .groups = "drop"
  )

resolution_summary <- votes_100 %>%
  distinct(undl_id, resolution, year, vote_date, session, title, agenda_title, subjects, total_yes, total_no, total_abstentions, total_non_voting, total_ms, undl_link) %>%
  arrange(year, resolution)

write_csv(votes_100, "un_ga_voting_100countries_2004_2024.csv")
write_csv(country_year, "un_ga_voting_country_year_summary_100countries.csv")
write_csv(resolution_summary, "un_ga_voting_resolution_summary_2004_2024.csv")

message("DONE")
