# Project Structure Audit

Comparing current structure with CCDS template expectations.

## Summary
- **Status:** ⚠️ MOSTLY COMPLIANT with issues
- **Missing:** 3 files, 4 modules
- **Extra/Unexpected:** 5 items (can be cleaned up)

---

## Expected vs. Actual

### Root Level Files

| Expected | Status | Notes |
|----------|--------|-------|
| LICENSE | ✓ Present | - |
| Makefile | ✓ Present | Updated for PostgreSQL |
| README.md | ✓ Present | - |
| pyproject.toml | ✓ Present | Configured for soeSpotify |
| requirements.txt | ✓ Present | Firebase removed, PostgreSQL added |
| setup.cfg | ✗ **MISSING** | Flake8 config (not critical, use ruff instead) |
| .env.example | ✓ Present | Added for database setup |

### Root Level Directories

| Expected | Status | Details |
|----------|--------|---------|
| data/ | ✓ Present | ✓ external ✓ interim ✓ processed ✓ raw |
| docs/ | ✓ Present | Contains mkdocs config + DATABASE_SETUP.md |
| models/ | ✓ Present | Empty (ready for trained models) |
| notebooks/ | ✓ Present | Has EDA.ipynb + 2 untitled notebooks |
| references/ | ✓ Present | Empty (ready for data dictionaries) |
| reports/ | ✓ Present | ✓ figures subdirectory |
| scripts/ | ✓ Present | NEW - Database setup scripts |

### soeSpotify Module Structure

| Expected | Status | Notes |
|----------|--------|-------|
| `__init__.py` | ✓ Present | - |
| `config.py` | ✓ Present | Stores paths, DB config, constants |
| `dataset.py` | ✗ **MISSING** | Scripts to download/generate data |
| `features.py` | ✗ **MISSING** | Feature engineering pipeline |
| `plots.py` | ✗ **MISSING** | Visualization utilities |
| `modeling/` | ✗ **MISSING** | Directory with train.py, predict.py |
| `etl.py` | ✓ Present | ETL/transformation logic (Spark) |
| `database.py` | ✓ Present | NEW - Database loader (PostgreSQL) |
| `main.py` | ✓ Present | ETL pipeline orchestration |
| `local_saver.py` | ✓ Present | Save DataFrames locally (CSV/Parquet) |

---

## Unexpected/Extra Items

1. **`.agents/` directory** — Claude Code skill references (safe to ignore)
2. **`public/` directory** — Firebase hosting files (consider removing)
3. **`dataconnect/` directory** — Firebase Data Connect config (consider removing)
4. **`Untitled.ipynb`, `Untitled1.ipynb`** — Temporary notebooks (should delete)
5. **`fhtw-soe-ad96b7577ca1.json`** — Firebase service account file (⚠️ SHOULD HAVE BEEN DELETED, CHECK .gitignore)
6. **`skills-lock.json`** — Claude Code artifacts (safe to ignore)
7. **`CLAUDE.md`** — Project instructions (custom, helpful to keep)

---

## Recommendations

### Priority 1: Clean Up
```bash
# Remove temporary notebooks
rm Untitled.ipynb Untitled1.ipynb

# Verify Firebase credentials NOT in git
git status fhtw-soe-ad96b7577ca1.json
# Should show as untracked or in gitignore
```

### Priority 2: Create Missing Modules

The following modules are expected but not yet implemented:

1. **`soeSpotify/dataset.py`** — Data loading/generation
   ```python
   # Should contain functions to:
   # - Load CSV files from data/raw/
   # - Download data from external sources if needed
   # - Initialize Spark DataFrames
   ```

2. **`soeSpotify/features.py`** — Feature engineering
   ```python
   # Should contain classes/functions for:
   # - Creating derived features from raw data
   # - Scaling/normalizing features
   # - Handling missing values
   # - Audio feature engineering
   ```

3. **`soeSpotify/plots.py`** — Visualization utilities
   ```python
   # Should contain functions for:
   # - Distribution plots of features
   # - Correlation heatmaps
   # - Model evaluation plots
   # - Genre/artist analysis visualizations
   ```

4. **`soeSpotify/modeling/`** — Model training & inference
   ```
   soeSpotify/modeling/
   ├── __init__.py
   ├── train.py      # Model training logic
   └── predict.py    # Model inference/recommendation
   ```

### Priority 3: Optional Cleanup
```bash
# Remove Firebase/Google Cloud artifacts
rm -rf dataconnect/
rm -rf public/

# Keep .agents/ only if using Claude Code skills
```

---

## Current vs. Expected Coverage

### ✓ Complete
- Data management (raw, interim, processed)
- Documentation structure (docs/)
- Model storage (models/)
- Notebook organization (notebooks/)
- Project configuration
- Database integration

### ⚠️ Partially Complete
- Module organization (missing features.py, plots.py, modeling/)
- Data loading (dataset.py in ETL only)

### ✗ Not Started
- Feature engineering as separate module
- Visualization utilities
- Model training & inference logic

---

## How to Proceed

1. **Short term:** Clean up temporary files and Firebase artifacts
2. **Medium term:** Implement `dataset.py` to extract data loading from `etl.py`
3. **Long term:** Add `features.py`, `plots.py`, and `modeling/` as you develop ML features
