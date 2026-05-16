# GEMINI.md - soe-spotify Project Instructions

This document provides foundational context, architectural patterns, and development workflows for the **soe-spotify** music recommendation study case.

## Project Overview

**soe-spotify** is a data engineering and machine learning study case focused on building a music recommendation system. It processes Spotify datasets (tracks, artists, albums, audio features, and lyrics) through a structured ETL pipeline to create analytical views and feature matrices for recommendation models.

### Core Technologies
- **Language:** Python 3.14+
- **Data Processing:** Pandas, PyArrow (Parquet storage)
- **Database:** PostgreSQL 16 (running in Docker)
- **Orchestration:** Simple Python-based 3-stage pipeline (Raw → Processed → Analytics)
- **Tooling:** Ruff (linting/formatting), MkDocs (documentation), Makefile

## Architecture & Data Flow

The project follows a **three-stage ETL pipeline** architecture:

1.  **RAW Stage:** Loads source CSV files and converts them to immutable Parquet files with minimal transformation.
2.  **PROCESSED Stage:** Cleans, validates, deduplicates, and handles null values.
3.  **ANALYTICS Stage:** Joins entities (Track-Artist-Album), denormalizes data, creates genre mappings, and builds feature matrices.
4.  **Database Sync (Optional):** Syncs final analytical tables to a PostgreSQL `home` schema and creates SQL views for analysis.

### Directory Structure (CCDS Based)
- `soeSpotify/`: Main source code package.
    - `stages/`: Implementation of Raw, Processed, and Analytics stages.
    - `main.py`: CLI entry point.
    - `database.py`: PostgreSQL loading and view creation.
    - `config.py`: Centralized configuration (paths, DB URLs).
- `data/`: Local data storage organized by stage (`raw`, `processed`, `analytics`).
- `notebooks/`: Jupyter notebooks for EDA and experimentation.
- `docs/`: Project documentation (MkDocs).
- `scripts/`: Infrastructure scripts (e.g., `setup_db.sh`).

## Development Workflows

### Environment Setup
```powershell
make create_environment    # Create virtualenv
make requirements          # Install dependencies
```

### Running the Pipeline
```powershell
# Option 1: Full pipeline (requires PostgreSQL in Docker)
make db-setup              # Start Docker DB
python -m soeSpotify.main

# Option 2: Parquet only (no database)
make etl-no-db             # or python -m soeSpotify.main --no-database
```

### Code Quality & Standards
- **Linting & Formatting:** Use Ruff. Always run `make format` before committing.
- **Line Length:** 99 characters (configured in `pyproject.toml`).
- **Type Hints:** Full type annotations are required (Python 3.14+ syntax).
- **Import Order:** Standard Lib → Third Party → First Party (`soeSpotify`).

## Key Project Guidelines

- **Package Naming:** Use `soeSpotify` as the primary package identifier.
- **Data Integrity:** Primary keys (e.g., `track_id`, `artist_id`) must be validated and deduplicated in the `PROCESSED` stage.
- **Configuration:** Always reference paths and constants from `soeSpotify.config`. Do not hardcode strings.
- **Reproducibility:** All data transformations should be implemented in the `stages` module, not just in notebooks. Notebooks are for exploration; production logic belongs in the source package.
- **Secrets:** Never commit `.env` or service account keys. Use `.env.example` as a template.

## External Integrations

### Firebase
The project includes configuration for Firebase/Firestore (`.firebaserc`, `firestore.rules`, `storage.rules`). 
- **Purpose:** Backend infrastructure for application-facing features.
- **Security:** Do not commit service account keys (`*-adminsdk-*.json`).
- **Management:** Use the Firebase CLI for rules deployment.

### PostgreSQL
- **Role:** Analytical database for structured querying and dashboarding.
- **Deployment:** Managed via Docker (see `scripts/setup_db.sh`).
- **Views:** Managed by `soeSpotify/database.py`.

## Important Files
- `QUICKSTART.md`: Rapid onboarding for running the pipeline.
- `DATA_ARCHITECTURE.md`: Detailed schema and SQL view definitions.
- `pyproject.toml`: Project metadata and tool configurations (Ruff, Flit).
- `Makefile`: Convenience commands for the development lifecycle.
- `CLAUDE.md`: Specific instructions for Claude Code (similar purpose to this file).
