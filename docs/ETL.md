# ETL Pipeline Documentation

## Overview

The ETL (Extract, Transform, Load) pipeline processes Spotify music data using Apache Spark and loads it into Firebase Firestore for use in the recommendation engine.

### Data Flow

```
CSV Files (Raw Data)
    ↓
PySpark Transformation
    ↓ (joins, cleaning, feature enrichment)
Firestore Collections
    ↓
Ready for ML/Recommendations
```

## Architecture

### Components

1. **etl.py** — Spark-based ETL engine
   - Loads CSV data from multiple sources
   - Applies transformations (rename, filter, type conversion)
   - Joins tables (tracks + audio features + lyrics + metadata)
   - Returns enriched DataFrames

2. **firebase_loader.py** — Firestore integration
   - Converts Spark DataFrames to Firestore documents
   - Handles batch writes (efficient, respects Firestore limits)
   - Provides collection verification and cleanup

3. **config.py** — Centralized configuration
   - File paths
   - Firebase credentials and collections
   - Spark settings
   - Batch sizes

4. **main.py** — Pipeline orchestration
   - Runs full ETL workflow
   - Manages error handling and cleanup
   - CLI interface with options

## Data Transformations

### Tracks Table (101,939 documents)

**Columns:**
- Metadata: `track_id`, `track_name`, `album_id`, `artists_id`, `popularity`, `uri`
- Audio Features: `acousticness`, `danceability`, `energy`, `instrumentalness`, `key`, 
  `liveness`, `loudness`, `mode`, `speechiness`, `tempo`, `time_signature`, `valence`
- Technical: `duration_ms`, `explicit`, `country`, `playlist`, `preview_url`, `analysis_url`
- Inherited Audio Features: 200+ low-level audio features (Chroma, Tonnetz, ZCR, spectral)
- Inherited Lyrics Features: `mean_syllables_word`, `mean_words_sentence`, `n_sentences`, 
  `n_words`, `sentence_similarity`, `vocabulary_wealth`

**Processing:**
- Removes rows with missing `track_id`
- Joins with audio features (left join, fills NaN with 0)
- Joins with lyrics features (left join)
- Joins with artist metadata
- Joins with album metadata

### Artists Table (documents per unique artist)

**Columns:**
- `artist_id`, `artist_name`, `popularity`, `followers`, `genres`, `type`

**Processing:**
- Removes rows with missing `artist_id`
- Renames for clarity

### Albums Table (documents per unique album)

**Columns:**
- `album_id`, `album_name`, `album_type`, `artist_id`, `release_date`, 
  `release_date_precision`, `total_tracks`, `uri`

**Processing:**
- Removes rows with missing `album_id`

## Usage

### Installation

```bash
make requirements
```

This installs:
- Apache Spark (pyspark)
- Firebase Admin SDK (firebase-admin)
- Data science libraries (pandas, numpy, scikit-learn)

### Running the Pipeline

**Full ETL (load to Firebase):**
```bash
make etl
```

**Dry-run (Spark processing without Firebase):**
```bash
make etl-dry-run
```

**Append mode (don't delete existing Firestore data):**
```bash
make etl-append
```

**Programmatic usage:**
```python
from soe_spotify.etl import SpotifyETL
from soe_spotify.firebase_loader import FirebaseLoader

# Extract and transform
etl = SpotifyETL()
tracks, artists, albums = etl.run_full_etl()

# Load to Firebase
loader = FirebaseLoader()
loader.load_tracks(tracks)
loader.load_artists(artists)
loader.load_albums(albums)

# Verify
loader.verify_collection("tracks")

etl.stop()
```

## Performance Notes

- **Data Volume:** ~102k tracks, ~200+ audio features per track
- **Processing:** Spark handles distributed processing (local[*] by default)
- **Firestore Writes:** Batched at 500 documents per commit
- **Typical Runtime:** 5-10 minutes (includes Firebase writes)

## Firebase Structure

### Collections

```
firestore/
├── tracks/
│   ├── {track_id_1}
│   │   ├── track_name: "Song Name"
│   │   ├── popularity: 75
│   │   ├── danceability: 0.45
│   │   ├── ... (200+ audio features)
│   │   └── artist_name: "Artist Name"
│   └── {track_id_2}
│       └── ...
├── artists/
│   ├── {artist_id_1}
│   │   ├── artist_name: "Name"
│   │   ├── popularity: 82
│   │   ├── followers: "12000000"
│   │   └── genres: "pop, electronic"
│   └── ...
└── albums/
    ├── {album_id_1}
    │   ├── album_name: "Album Title"
    │   ├── release_date: "2023-01-15"
    │   └── artist_id: "abc123"
    └── ...
```

## Troubleshooting

**Firebase credentials not found:**
```
FileNotFoundError: fhtw-soe-firebase-adminsdk-fbsvc-5a77ac938f.json
```
Solution: Ensure the Firebase service account key is in the project root.

**Firestore quota exceeded:**
```
google.cloud.exceptions.ResourceExhausted
```
Solution: Use `--skip-delete` to append instead of replacing data, or wait for quota reset.

**CSV not found:**
```
FileNotFoundError: data/raw/SpotGenTrack/...
```
Solution: Ensure CSV files are in `data/raw/SpotGenTrack/` with correct subdirectories:
- `Data Sources/` (albums, artists, tracks CSVs)
- `Features Extracted/` (audio and lyrics features CSVs)

## Next Steps

After loading to Firestore:
1. Use the `predict.py` module to build recommendations
2. Create indices for frequently queried fields
3. Set up scheduled ETL runs with Cloud Scheduler
4. Monitor Firestore usage and costs
