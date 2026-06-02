# Project setup for the multiplex global health governance replication package.
#
# Run once before rebuilding the empirical pipeline:
#   source("R/00_setup.R")

required_packages <- c(
  "dplyr",
  "tidyr",
  "readr",
  "jsonlite",
  "igraph",
  "zoo",
  "plm",
  "lmtest",
  "sandwich",
  "modelsummary",
  "fixest",
  "network",
  "networkDynamic",
  "tergm",
  "btergm",
  "statnet",
  "ggplot2",
  "ggrepel",
  "patchwork",
  "readxl",
  "janitor"
)

install_missing <- function(packages) {
  missing <- packages[!vapply(packages, requireNamespace, logical(1), quietly = TRUE)]

  if (length(missing) == 0) {
    message("All required R packages are already installed.")
    return(invisible(NULL))
  }

  message("Installing missing R packages: ", paste(missing, collapse = ", "))
  install.packages(missing, repos = "https://cloud.r-project.org")
}

install_missing(required_packages)

message("R setup complete.")
