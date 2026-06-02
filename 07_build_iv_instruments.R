required_packages <- c("dplyr", "tidyr", "readr", "igraph")

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

panel <- read_csv("io_analysis_panel_100countries_2004_2024.csv", show_col_types = FALSE)
gravity <- read_csv("iv_gravity_cepii_100countries.csv", show_col_types = FALSE)

countries <- sort(unique(panel$iso3c))
years <- sort(unique(panel$year))

exog_edges <- gravity %>%
  mutate(
    geographic_weight = 1 / (1 + log_dist),
    affinity_weight = geographic_weight *
      (1 + 0.25 * coalesce(contig, 0)) *
      (1 + 0.25 * coalesce(common_language, 0)) *
      (1 + 0.35 * coalesce(historical_tie, 0))
  ) %>%
  group_by(iso_o) %>%
  mutate(rank_affinity = rank(-affinity_weight, ties.method = "first")) %>%
  ungroup()

top_k_edges <- exog_edges %>%
  filter(rank_affinity <= 10) %>%
  select(iso_o, iso_d, affinity_weight)

adj <- matrix(0, nrow = length(countries), ncol = length(countries), dimnames = list(countries, countries))
for (i in seq_len(nrow(top_k_edges))) {
  o <- top_k_edges$iso_o[i]
  d <- top_k_edges$iso_d[i]
  w <- top_k_edges$affinity_weight[i]
  adj[o, d] <- max(adj[o, d], w)
  adj[d, o] <- max(adj[d, o], w)
}

g_exog <- graph_from_adjacency_matrix(adj, mode = "undirected", weighted = TRUE, diag = FALSE)

exogenous_centrality <- tibble(
  iso3c = names(V(g_exog)),
  iv_geo_degree = degree(g_exog, normalized = TRUE),
  iv_geo_strength = strength(g_exog, weights = E(g_exog)$weight),
  iv_geo_eigen = eigen_centrality(g_exog, weights = E(g_exog)$weight)$vector,
  iv_geo_betweenness = betweenness(g_exog, weights = 1 / E(g_exog)$weight, normalized = TRUE)
)

regional_diffusion <- panel %>%
  select(iso3c, year, eigen, degree, strength, global_group, region) %>%
  left_join(gravity, by = c("iso3c" = "iso_o"), relationship = "many-to-many") %>%
  left_join(
    panel %>% select(iso_d = iso3c, year, peer_eigen = eigen, peer_degree = degree, peer_strength = strength),
    by = c("iso_d", "year")
  ) %>%
  group_by(iso3c, year) %>%
  summarise(
    iv_distance_weighted_peer_eigen = weighted.mean(peer_eigen, w = 1 / (1 + log_dist), na.rm = TRUE),
    iv_language_peer_eigen = mean(peer_eigen[common_language == 1], na.rm = TRUE),
    iv_historical_peer_eigen = mean(peer_eigen[historical_tie == 1], na.rm = TRUE),
    iv_contiguous_peer_eigen = mean(peer_eigen[contig == 1], na.rm = TRUE),
    .groups = "drop"
  ) %>%
  mutate(across(starts_with("iv_"), ~ ifelse(is.nan(.x), NA_real_, .x)))

panel_iv <- panel %>%
  left_join(exogenous_centrality, by = "iso3c") %>%
  left_join(regional_diffusion, by = c("iso3c", "year")) %>%
  group_by(iso3c) %>%
  arrange(year, .by_group = TRUE) %>%
  mutate(across(starts_with("iv_"), ~ lag(.x, 1), .names = "l_{.col}")) %>%
  ungroup()

write_csv(exogenous_centrality, "iv_exogenous_network_centrality.csv")
write_csv(regional_diffusion, "iv_temporal_diffusion_instruments.csv")
write_csv(panel_iv, "io_analysis_panel_with_iv_100countries_2004_2024.csv")

message("DONE")
