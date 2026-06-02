# Integration Without Equalization

**Visible and Structural Hierarchies in Multiplex Global Health Governance**

This repository contains the replication package for a 100-country empirical
analysis of multiplex global health governance between 2004 and 2024. The
pipeline combines World Development Indicators, network centrality measures,
UN General Assembly voting data, WHO governance indicators, instrumental
variables, dynamic panel models, placebo checks, and temporal network models.

The central empirical question is whether greater integration into global health
governance networks produces equalization, or whether participation expands while
structural hierarchy remains durable.

## Repository Structure

```text
.
├── R/              # Main R analysis pipeline
├── scripts/        # Auxiliary Python scripts for publication-grade figures
├── data/           # 100-country processed panels and network data
├── results/        # Model outputs, diagnostics, and audit reports
├── figures/        # Publication figures
├── manuscript/     # Manuscript materials and release notes
├── docs/           # Reproducibility notes
├── README.md
├── requirements.txt
├── requirements-python.txt
├── AUTHORS.md
├── .gitignore
├── LICENSE
└── CITATION.cff
```

## Authorship And License

This repository is authored and maintained by **Suraya Bazarova**.

Code and documentation are released under the MIT License. The license grants
reuse rights while preserving Suraya Bazarova's copyright and authorship notice.
Data-source terms should be checked separately before public archival release.

## Environment

Install the R packages listed in `requirements.txt`, or run:

```r
source("R/00_setup.R")
```

The split-figure utility is written in Python. Its dependencies are listed in
`requirements-python.txt`.

## Pipeline Order

Run the scripts in this order when rebuilding the full analysis:

```text
0.  R/00_setup.R
1.  R/run_wdi_100_country_panel.R
2.  R/01_build_network_panel.R
3.  R/02_system_gmm.R
4.  R/03_mechanism_models.R
5.  R/04_placebo_falsification.R
6.  R/05_temporal_network_models_skeleton.R
7.  R/06_fetch_iv_gravity_data.R
8.  R/07_build_iv_instruments.R
9.  R/08_iv_models.R
10. R/09_fetch_un_ga_voting_data.R
11. R/10_build_un_voting_network.R
12. R/11_fetch_who_governance_indicators.R
13. R/12_merge_un_who_augmented_panel.R
```

To run the full pipeline from the repository root:

```bash
Rscript R/run_pipeline.R
```

The included processed panels allow readers to inspect and reproduce the reported
model stages without rebuilding every upstream data pull.

## Core Data Files

The main processed datasets are:

```text
data/wdi_panel_100countries_2004_2024_long.csv
data/io_network_metrics_100countries_2004_2024.csv
data/io_analysis_panel_100countries_2004_2024.csv
data/io_analysis_panel_with_iv_100countries_2004_2024.csv
data/iv_gravity_cepii_100countries.csv
```

Panel dimensions:

```text
100 countries x 21 years = 2,100 country-year observations
```

## Main Outputs

Key result files are stored in `results/`:

```text
io_system_gmm_degree_results.txt
io_system_gmm_eigen_results.txt
io_temporal_ergm_results.txt
io_iv_models_results.txt
io_placebo_falsification_results.txt
```

Publication figures are stored in `figures/`.

The public manuscript version is stored in `manuscript/`.

## Publication Figure Panels

The auxiliary split-figure script exports each dashboard panel as a standalone
PNG and vector PDF:

```bash
python scripts/publication_figure_panels.py \
  --data-dir data \
  --output-dir split_figures \
  --seed 42 \
  --n-jobs 1
```

For a quick smoke test:

```bash
python scripts/publication_figure_panels.py \
  --data-dir data \
  --output-dir split_figures_test \
  --n-boot 20 \
  --perm-repeats 2 \
  --dpi 120 \
  --n-jobs 1
```

## Reproducibility Notes

- The repository is organized as a replication package rather than a software
  library.
- Data files are processed research panels. When rebuilding from raw external
  sources, users may need current access to World Bank, UN, WHO, and CEPII data
  endpoints.
- Local package caches, environment-specific files, and machine-specific working
  artifacts are intentionally excluded from this public repository.
- Before public archival release, verify that each included
  dataset is legally shareable under its source terms.

## Public Release Scope

This public repository includes the reproducible analysis infrastructure,
processed 100-country panels, model outputs, and figure-generation code. Internal
drafts, private working notes, and non-public correspondence are intentionally
excluded.

## Article

**Integration Without Equalization: Visible and Structural Hierarchies in
Multiplex Global Health Governance**

Author: Suraya Bazarova
