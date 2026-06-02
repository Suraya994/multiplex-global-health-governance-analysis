# Scripts

This folder contains auxiliary scripts that support journal-ready output
generation.

## Split Figures

Generate standalone PNG and vector PDF panels from the 100-country datasets:

```bash
python scripts/split_figures_journal.py \
  --data-dir data \
  --output-dir split_figures \
  --seed 42 \
  --n-jobs 1
```

For a quick smoke test, reduce bootstrap and permutation settings:

```bash
python scripts/split_figures_journal.py \
  --data-dir data \
  --output-dir split_figures_test \
  --n-boot 20 \
  --perm-repeats 2 \
  --dpi 120 \
  --n-jobs 1
```
