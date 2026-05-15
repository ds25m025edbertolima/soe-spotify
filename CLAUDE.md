# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**soe-spotify** is a music recommendation study case built on the Cookiecutter Data Science (CCDS) template. It recommends songs users are most likely to want to hear next based on previously played/selected songs. The project integrates Firebase/Firestore for backend infrastructure.

**Python Version:** 3.14+

## Development Environment

### Initial Setup

```bash
make create_environment    # Create virtualenv (Windows: mkvirtualenv.bat)
make requirements          # Install dependencies
```

### Common Commands

**Dependency Management:**
- `make requirements` — Install/update Python dependencies from requirements.txt
- Add new dependencies to requirements.txt, then run `make requirements`

**Code Quality:**
- `make lint` — Check code with ruff (format and linting)
- `make format` — Auto-format and fix code with ruff
- `make clean` — Remove compiled .pyc files and __pycache__ directories

**Jupyter & Documentation:**
- `jupyter lab` — Start JupyterLab (from notebooks/ directory)
- `mkdocs serve` — Preview documentation locally (docs/ uses mkdocs)

## Code Style & Tooling

**Formatting:** Ruff (99-character line limit, not 100)
- Configuration in `pyproject.toml` under `[tool.ruff]`
- Import sorting enabled with isort plugin
- Always run `make format` before committing

**Type Hints:** Full type annotations required (Python 3.14+ syntax supported)

**Import Order:**
1. Standard library
2. Third-party packages
3. Local imports (from soe_spotify)
4. Use `soe_spotify` as first-party package identifier

## Project Structure

```
soe-spotify/
├── __init__.py           # Package initialization
├── config.py             # Configuration and constants
├── dataset.py            # Data loading/generation
├── features.py           # Feature engineering
├── plots.py              # Visualization code
└── modeling/
    ├── train.py          # Model training logic
    └── predict.py        # Model inference

data/
├── raw/                  # Original immutable data
├── interim/              # Intermediate transformations
└── processed/            # Final datasets for modeling

notebooks/               # Jupyter notebooks for exploration
models/                  # Trained model artifacts
reports/                 # Generated analysis outputs
```

## Architecture Patterns

### Module Organization

The project follows CCDS conventions with clear separation:
- **dataset.py** — Data acquisition and loading from external sources
- **features.py** — Feature engineering and transformation pipeline
- **modeling/ — Model training/inference logic
- **config.py** — Centralized configuration (paths, hyperparameters, constants)
- **plots.py** — Visualization utilities for reports and notebooks

### Working with Data

Expect heavy use of pandas, numpy, and scikit-learn for data manipulation and ML. Code should:
- Keep data processing pipelines in `features.py`
- Store dataset references and paths in `config.py`
- Use `data/raw/` → `data/interim/` → `data/processed/` workflow
- Document data assumptions and transformations in docstrings

### Dependencies

Key packages (from requirements.txt):
- **Data Science:** pandas, numpy, scikit-learn, pyspark
- **Visualization:** matplotlib, seaborn, yellowbrick
- **ML:** scikit-learn (sklearn), pyspark
- **Notebooks:** jupyterlab, notebook, ipython
- **Firebase:** Firebase integration for backend (firebaserc, firestore rules present)
- **Docs:** mkdocs

## Firebase Integration

The project has Firebase/Firestore configured:
- `.firebaserc` — Firebase project configuration
- `firestore.rules` — Firestore security rules
- `firestore.indexes.json` — Custom indexes
- `storage.rules` — Cloud Storage rules
- `firebase.json` — Firebase project metadata

Do not commit the service account key (`*-adminsdk-*.json`). Add to `.gitignore` if not already present.

## Notebook Conventions

Naming convention: `{number}-{initials}-{description}.ipynb`
- Example: `1.0-jqp-initial-data-exploration.ipynb`
- Use sequential numbers for notebook ordering
- Keep notebooks in notebooks/ directory
- Use for exploration only; move production code to soe_spotify/ module
