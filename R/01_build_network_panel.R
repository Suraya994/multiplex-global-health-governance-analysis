required_packages <- c("dplyr", "tidyr", "readr", "igraph", "zoo")

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
library(igraph)
library(zoo)

panel <- read_csv("analysis_panel_100countries_2004_2024.csv", show_col_types = FALSE)

vars_network <- c(
  "SH.XPD.CHEX.GD.ZS",
  "SH.MED.PHYS.ZS",
  "SH.MED.NUMW.P3",
  "SH.MED.BEDS.ZS",
  "IT.NET.USER.ZS",
  "NY.GDP.PCAP.PP.KD"
)

outcome_vars <- c(
  "SP.DYN.LE00.IN"
)

panel_clean <- panel %>%
  arrange(iso3c, year) %>%
  group_by(iso3c) %>%
  mutate(across(all_of(vars_network), ~ na.approx(.x, x = year, na.rm = FALSE))) %>%
  mutate(across(all_of(vars_network), ~ na.locf(.x, na.rm = FALSE))) %>%
  mutate(across(all_of(vars_network), ~ na.locf(.x, fromLast = TRUE, na.rm = FALSE))) %>%
  ungroup()

build_year_network <- function(df_year, k = 5) {
  yr <- unique(df_year$year)
  X <- df_year %>%
    select(all_of(vars_network)) %>%
    mutate(across(everything(), ~ as.numeric(scale(.x)))) %>%
    as.matrix()

  rownames(X) <- df_year$iso3c
  X[is.na(X)] <- 0

  dist_mat <- as.matrix(dist(X, method = "euclidean"))
  sim_mat <- 1 / (1 + dist_mat)
  diag(sim_mat) <- 0

  adj <- matrix(0, nrow = nrow(sim_mat), ncol = ncol(sim_mat), dimnames = dimnames(sim_mat))
  for (i in seq_len(nrow(sim_mat))) {
    nn <- order(sim_mat[i, ], decreasing = TRUE)[seq_len(min(k, nrow(sim_mat) - 1))]
    adj[i, nn] <- sim_mat[i, nn]
  }
  adj <- pmax(adj, t(adj))
  g <- graph_from_adjacency_matrix(adj, mode = "undirected", weighted = TRUE, diag = FALSE)

  tibble(
    iso3c = names(V(g)),
    year = yr,
    degree = degree(g, normalized = TRUE),
    strength = strength(g, weights = E(g)$weight),
    eigen = eigen_centrality(g, weights = E(g)$weight)$vector,
    betweenness = betweenness(g, weights = 1 / E(g)$weight, normalized = TRUE),
    closeness = closeness(g, weights = 1 / E(g)$weight, normalized = TRUE),
    local_clustering = transitivity(g, type = "local", isolates = "zero"),
    network_density = edge_density(g),
    network_clustering = transitivity(g, type = "average"),
    network_components = components(g)$no
  )
}

network_panel <- panel_clean %>%
  group_split(year) %>%
  lapply(build_year_network, k = 5) %>%
  bind_rows()

analysis_panel_io <- panel_clean %>%
  left_join(network_panel, by = c("iso3c", "year")) %>%
  group_by(iso3c) %>%
  arrange(year, .by_group = TRUE) %>%
  mutate(
    life_expectancy = SP.DYN.LE00.IN,
    health_spending = SH.XPD.CHEX.GD.ZS,
    physicians = SH.MED.PHYS.ZS,
    nurses = SH.MED.NUMW.P3,
    hospital_beds = SH.MED.BEDS.ZS,
    internet = IT.NET.USER.ZS,
    gdp_pc_ppp = NY.GDP.PCAP.PP.KD,
    population = SP.POP.TOTL,
    l_life_expectancy = lag(life_expectancy, 1),
    l_degree = lag(degree, 1),
    l_strength = lag(strength, 1),
    l_eigen = lag(eigen, 1),
    l_network_density = lag(network_density, 1),
    l_network_clustering = lag(network_clustering, 1)
  ) %>%
  ungroup()

write_csv(network_panel, "io_network_metrics_100countries_2004_2024.csv")
write_csv(analysis_panel_io, "io_analysis_panel_100countries_2004_2024.csv")

message("DONE")
