# Rebuild the multiplex global health governance analysis pipeline.
#
# This script assumes it is run from the repository root:
#   Rscript R/run_pipeline.R

pipeline_steps <- c(
  "R/run_wdi_100_country_panel.R",
  "R/01_build_network_panel.R",
  "R/02_system_gmm.R",
  "R/03_mechanism_models.R",
  "R/04_placebo_falsification.R",
  "R/05_temporal_network_models_skeleton.R",
  "R/06_fetch_iv_gravity_data.R",
  "R/07_build_iv_instruments.R",
  "R/08_iv_models.R",
  "R/09_fetch_un_ga_voting_data.R",
  "R/10_build_un_voting_network.R",
  "R/11_fetch_who_governance_indicators.R",
  "R/12_merge_un_who_augmented_panel.R"
)

source("R/00_setup.R")

for (step in pipeline_steps) {
  message("\n", strrep("=", 72))
  message("Running: ", step)
  message(strrep("=", 72))
  source(step)
}

message("\nPipeline complete.")
