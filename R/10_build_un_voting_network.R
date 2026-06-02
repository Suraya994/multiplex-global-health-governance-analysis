required_packages <- c("dplyr", "tidyr", "readr", "igraph", "purrr")

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
library(purrr)

template <- read_delim(
  "global_health_100_country_template.csv",
  delim = ";",
  show_col_types = FALSE,
  trim_ws = TRUE
) %>%
  mutate(iso3c = toupper(iso3c)) %>%
  filter(tolower(include_flag) == "yes", !is.na(iso3c), iso3c != "")

votes <- read_csv("un_ga_voting_100countries_2004_2024.csv", show_col_types = FALSE) %>%
  filter(!is.na(vote_numeric), iso3c %in% template$iso3c)

countries <- sort(template$iso3c)

pairwise_year <- function(y) {
  wide <- votes %>%
    filter(year == y) %>%
    select(iso3c, resolution_id, vote_numeric) %>%
    distinct() %>%
    pivot_wider(names_from = resolution_id, values_from = vote_numeric) %>%
    right_join(tibble(iso3c = countries), by = "iso3c") %>%
    arrange(iso3c)

  X <- as.matrix(wide %>% select(-iso3c))
  rownames(X) <- wide$iso3c
  pairs <- combn(wide$iso3c, 2, simplify = FALSE)

  map_dfr(pairs, function(p) {
    a <- X[p[1], ]
    b <- X[p[2], ]
    ok <- !is.na(a) & !is.na(b)
    common_votes <- sum(ok)
    agreement <- if (common_votes > 0) mean(a[ok] == b[ok]) else NA_real_
    cosine <- if (common_votes > 0 && sqrt(sum(a[ok]^2)) > 0 && sqrt(sum(b[ok]^2)) > 0) {
      sum(a[ok] * b[ok]) / (sqrt(sum(a[ok]^2)) * sqrt(sum(b[ok]^2)))
    } else {
      NA_real_
    }
    tibble(
      year = y,
      iso_o = p[1],
      iso_d = p[2],
      common_votes = common_votes,
      un_voting_agreement = agreement,
      un_voting_cosine = cosine
    )
  })
}

edges_all <- map_dfr(sort(unique(votes$year)), pairwise_year)

network_year <- function(y, k = 10, min_common_votes = 5) {
  ey <- edges_all %>%
    filter(year == y, common_votes >= min_common_votes, !is.na(un_voting_agreement))

  adj <- matrix(0, nrow = length(countries), ncol = length(countries), dimnames = list(countries, countries))
  for (cty in countries) {
    top_edges <- ey %>%
      filter(iso_o == cty | iso_d == cty) %>%
      mutate(peer = if_else(iso_o == cty, iso_d, iso_o)) %>%
      arrange(desc(un_voting_agreement), desc(common_votes)) %>%
      slice_head(n = k)
    for (i in seq_len(nrow(top_edges))) {
      peer <- top_edges$peer[i]
      w <- top_edges$un_voting_agreement[i]
      adj[cty, peer] <- max(adj[cty, peer], w, na.rm = TRUE)
      adj[peer, cty] <- max(adj[peer, cty], w, na.rm = TRUE)
    }
  }

  g <- graph_from_adjacency_matrix(adj, mode = "undirected", weighted = TRUE, diag = FALSE)

  tibble(
    iso3c = names(V(g)),
    year = y,
    un_degree = degree(g, normalized = TRUE),
    un_strength = strength(g, weights = E(g)$weight),
    un_eigen = eigen_centrality(g, weights = E(g)$weight)$vector,
    un_betweenness = betweenness(g, weights = 1 / E(g)$weight, normalized = TRUE),
    un_closeness = closeness(g, weights = 1 / E(g)$weight, normalized = TRUE),
    un_local_clustering = transitivity(g, type = "local", isolates = "zero"),
    un_network_density = edge_density(g),
    un_network_clustering = transitivity(g, type = "average"),
    un_network_components = components(g)$no
  )
}

metrics <- map_dfr(sort(unique(votes$year)), network_year) %>%
  left_join(template, by = "iso3c")

write_csv(edges_all, "un_ga_voting_similarity_edges_100countries_2004_2024.csv")
write_csv(metrics, "un_ga_voting_network_metrics_100countries_2004_2024.csv")

message("DONE")
