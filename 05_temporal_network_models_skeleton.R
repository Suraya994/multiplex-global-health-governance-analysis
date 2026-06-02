required_packages <- c("dplyr", "readr", "igraph", "network", "tergm")

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
library(network)
library(tergm)

panel <- read_csv("io_analysis_panel_100countries_2004_2024.csv", show_col_types = FALSE)

vars_network <- c(
  "health_spending",
  "physicians",
  "nurses",
  "hospital_beds",
  "internet",
  "gdp_pc_ppp"
)

make_adj <- function(df_year, k = 5) {
  X <- df_year %>%
    select(all_of(vars_network)) %>%
    mutate(across(everything(), ~ as.numeric(scale(.x)))) %>%
    as.matrix()
  rownames(X) <- df_year$iso3c
  X[is.na(X)] <- 0
  sim <- 1 / (1 + as.matrix(dist(X)))
  diag(sim) <- 0
  adj <- matrix(0, nrow = nrow(sim), ncol = ncol(sim), dimnames = dimnames(sim))
  for (i in seq_len(nrow(sim))) {
    nn <- order(sim[i, ], decreasing = TRUE)[seq_len(min(k, nrow(sim) - 1))]
    adj[i, nn] <- 1
  }
  pmax(adj, t(adj))
}

years <- sort(unique(panel$year))
networks <- lapply(years, function(y) {
  dfy <- panel %>% filter(year == y) %>% arrange(iso3c)
  network(make_adj(dfy, k = 5), directed = FALSE)
})

tergm_model <- tergm(
  networks ~ edges + gwesp(0.5, fixed = TRUE) + memory(type = "stability"),
  estimate = "CMLE"
)

capture.output(summary(tergm_model), file = "io_temporal_ergm_results.txt")

message("DONE")
