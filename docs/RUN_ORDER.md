# Run Order

The analysis is organized as a staged empirical pipeline. Run scripts from the
repository root in the following order:

```r
source("R/run_wdi_100_country_panel.R")
source("R/01_build_network_panel.R")
source("R/02_system_gmm.R")
source("R/03_mechanism_models.R")
source("R/04_placebo_falsification.R")
source("R/05_temporal_network_models_skeleton.R")
source("R/06_fetch_iv_gravity_data.R")
source("R/07_build_iv_instruments.R")
source("R/08_iv_models.R")
source("R/09_fetch_un_ga_voting_data.R")
source("R/10_build_un_voting_network.R")
source("R/11_fetch_who_governance_indicators.R")
source("R/12_merge_un_who_augmented_panel.R")
```

Some upstream scripts call external data services. The processed `data/` folder
is included so readers can inspect the final empirical panels even when external
services change.
