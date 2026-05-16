# Quick Start Guide

## Overview

This project uses a **three-stage data pipeline** (Pandas + PyArrow) to process Spotify data:

```
CSV Files → RAW Stage → PROCESSED Stage → ANALYTICS Stage → PostgreSQL
```

## Installation

```powershell
# Install dependencies
pip install -r requirements.txt
```

## Run Pipeline

### Option 1: Parquet Only (No Database)

Fastest - just creates parquet files:

```powershell
python -m soeSpotify.main --no-database
```

Output:
- `data/raw/parquet/` - Raw unmodified data
- `data/processed/` - Cleaned & validated data
- `data/analytics/` - Business-ready tables

### Option 2: Full Pipeline with PostgreSQL

Syncs analytics tables to PostgreSQL and creates SQL views:

```powershell
# 1. Start PostgreSQL (Docker)
docker run --name soe-spotify-db `
  -e POSTGRES_PASSWORD=postgres `
  -e POSTGRES_DB=soe_spotify `
  -p 5432:5432 `
  -d postgres:16

# 2. Create .env file
Copy-Item .env.example .env
# Edit .env if using non-local PostgreSQL

# 3. Run full pipeline
pip install -r requirements.txt
python -m soeSpotify.main
```

## Data Output

### Parquet Files

**Raw Stage** (data/raw/parquet/)
- `raw_tracks.parquet` - 101,939 tracks
- `raw_artists.parquet` - 56,129 artists
- `raw_albums.parquet` - 75,511 albums
- `raw_audio_features.parquet` - Audio features
- `raw_lyrics_features.parquet` - Lyrics features

**Processed Stage** (data/processed/)
- Cleaned, deduplicated, validated data

**Analytics Stage** (data/analytics/)
- `analytics_tracks.parquet` - Denormalized tracks with artist/album info
- `analytics_artists.parquet` - Artist metadata
- `analytics_albums.parquet` - Album metadata with artist details
- `analytics_genres.parquet` - Genre mappings (87,202 entries)
- `analytics_track_features.parquet` - Feature matrix for ML

### PostgreSQL Views

Once synced to PostgreSQL:

```sql
-- Base views
SELECT * FROM home.artists;
SELECT * FROM home.tracks;
SELECT * FROM home.albums;
SELECT * FROM home.genres;
SELECT * FROM home.track_features;

-- Analysis views
SELECT * FROM home.v_1_1_total_artists;
SELECT * FROM home.v_1_2_artists_popularity;
SELECT * FROM home.v_1_5_artist_albums;
SELECT * FROM home.v_3_1_track_features_full;
SELECT * FROM home.v_2_1_album_tracks;
```

## Pipeline Details

### Raw Stage
- Loads CSV files with Pandas
- Minimal transformation (schema inference)
- Stores in Parquet for efficiency

### Processed Stage
- Data validation & cleaning
- Null/NaN handling
- Deduplication by primary key
- Type corrections

### Analytics Stage
- Join artist/album/track relationships
- Combine audio + lyrics features
- Create genre mappings
- Denormalize for query efficiency
- Build feature matrix for ML

## Performance

On Windows (101K tracks, 56K artists):
- **Raw Stage:** ~20 seconds
- **Processed Stage:** ~3 seconds
- **Analytics Stage:** ~3 seconds
- **Total:** ~26 seconds (no database)

No Spark/Hadoop/Java needed - pure Python!

## Next Steps

1. **Explore data:**
   ```python
   import pandas as pd
   df = pd.read_parquet("data/analytics/analytics_tracks.parquet")
   df.head()
   ```

2. **Build recommendations:**
   - Use feature matrix from `analytics_track_features.parquet`
   - Train ML model on audio/lyrics features
   - Implement similarity/matching logic

3. **Query in PostgreSQL:**
   ```sql
   SELECT track_name, danceability, energy, valence
   FROM home.v_3_1_track_features_full
   WHERE energy > 0.8 AND danceability > 0.7;
   ```

## Documentation

- **DATA_ARCHITECTURE.md** - Full architecture and SQL view definitions
- **DATABASE_SETUP.md** - PostgreSQL/Supabase setup guide
- **docs/QUICKSTART_ETL.md** - Detailed ETL documentation

## Troubleshooting

**Permission denied when writing parquet:**
```powershell
# Clean up locked files
rm -recurse -force data/raw/parquet, data/processed, data/analytics
mkdir -p data/raw/parquet, data/processed, data/analytics
python -m soeSpotify.main --no-database
```

**PostgreSQL connection fails:**
```powershell
# Check PostgreSQL is running
docker ps | grep soe-spotify-db

# Verify .env has correct DATABASE_URL
Get-Content .env
```

**ModuleNotFoundError:**
```powershell
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```
