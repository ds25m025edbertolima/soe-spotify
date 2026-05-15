# ETL Pipeline Quick Start

## What Was Built

A complete ETL pipeline that:
- **Extracts** Spotify data from 5 CSV files (albums, artists, tracks, audio features, lyrics)
- **Transforms** data using Apache Spark (joins, cleanups, enrichment)
- **Loads** 102k+ tracks with 200+ audio features into Firebase Firestore

## Run the Pipeline

```bash
# Full run (extract, transform, load to Firebase)
make etl

# Test without Firebase (just Spark processing)
make etl-dry-run

# Append to existing data (don't delete Firestore collections)
make etl-append
```

## File Structure

```
soe-spotify/
├── config.py              # Configuration, paths, Firebase settings
├── etl.py                 # Spark-based ETL engine
├── firebase_loader.py     # Firebase/Firestore integration
├── main.py                # Orchestration script (entry point)
└── __init__.py            # Package exports

scripts/
└── verify_setup.py        # Verify CSV files, Firebase, dependencies

docs/
├── ETL.md                 # Full documentation
└── QUICKSTART_ETL.md      # This file
```

## Pipeline Architecture

```
Input CSV Files
  ├── spotify_tracks.csv (101,939 rows)
  ├── spotify_artists.csv
  ├── spotify_albums.csv
  ├── low_level_audio_features.csv (209 columns)
  └── lyrics_features.csv
         ↓
    SpotifyETL (Spark)
         ↓
  Transform & Join
  ├── Load tracks → transform → select relevant columns
  ├── Load artists → rename, filter nulls
  ├── Load albums → rename, filter nulls
  ├── Load audio features → keep all 200+ features
  ├── Load lyrics features → transform
  └── Join all: tracks ← audio ← lyrics
         ↓
  Enhanced DataFrames
     ↓
  FirebaseLoader (Batch writes)
     ↓
  Firestore Collections
  ├── tracks/{track_id} - 101,939 documents
  ├── artists/{artist_id}
  └── albums/{album_id}
```

## Data in Firestore

### Tracks (101,939 documents)
Each track contains:
- Metadata: `track_id`, `track_name`, `popularity`, `duration_ms`
- Audio Features (14): `acousticness`, `danceability`, `energy`, `instrumentalness`, 
  `key`, `liveness`, `loudness`, `mode`, `speechiness`, `tempo`, `time_signature`, 
  `valence`
- Low-level Features (200+): Chroma, Tonnetz, ZCR, spectral features, etc.
- Lyrics Features (7): `mean_syllables_word`, `n_words`, `vocabulary_wealth`, etc.
- Artist Info: `artist_id`, `artist_name`, `artist_popularity`
- Album Info: `album_id`, `album_name`, `release_date`

### Artists & Albums
Denormalized reference data for relationship queries.

## Code Examples

### Run Programmatically
```python
from soe_spotify.etl import SpotifyETL
from soe_spotify.firebase_loader import FirebaseLoader

# Extract & transform with Spark
etl = SpotifyETL()
tracks, artists, albums = etl.run_full_etl()

# Load to Firebase
loader = FirebaseLoader()
loader.load_tracks(tracks)
loader.verify_collection("tracks")  # Should show 101,939 docs

etl.stop()
```

### Query in Firestore
```python
import firebase_admin
from firebase_admin import firestore

db = firestore.client()

# Get a track with its audio features
doc = db.collection("tracks").document("track_id_here").get()
track = doc.to_dict()
print(track["track_name"], track["danceability"])

# Query tracks by popularity
popular = (
    db.collection("tracks")
    .where("popularity", ">=", 80)
    .limit(10)
    .stream()
)
for doc in popular:
    print(doc.to_dict()["track_name"])
```

## Performance

- **Input:** 102k tracks, 5 CSV files
- **Processing:** ~5-10 minutes (includes Firestore writes)
- **Storage:** ~500MB in Firestore
- **Batch Size:** 500 documents per Firestore commit

## Troubleshooting

**Verify everything is set up:**
```bash
python scripts/verify_setup.py
```

**Firebase error: "Credentials not found"**
- Ensure `fhtw-soe-firebase-adminsdk-fbsvc-5a77ac938f.json` exists in project root
- Check file permissions

**CSV files not found:**
- Verify CSV files are in: `data/raw/SpotGenTrack/Data Sources/`
- Verify features are in: `data/raw/SpotGenTrack/Features Extracted/`

**Firestore quota exceeded:**
- Use `make etl-append --skip-delete` to not delete existing collections
- Or wait for quota reset (typically daily)

## Next Steps

1. Run the ETL pipeline:
   ```bash
   make etl
   ```

2. Verify data in Firestore:
   ```bash
   python scripts/verify_setup.py  # Shows success
   ```

3. Query your data in `predict.py` or notebooks

4. Build recommendation models using the audio features

## Tips

- Use `make etl-dry-run` first to test without Firebase costs
- Monitor Firestore usage in Google Cloud Console
- Create indices for frequently queried fields (see `firestore.indexes.json`)
- Consider caching track features in memory for recommendation queries
