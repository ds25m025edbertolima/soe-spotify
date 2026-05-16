# Data Architecture: Processing Stages

This project uses a **three-stage data pipeline** with Spark and Supabase PostgreSQL.

## Processing Stages

```
CSV Source Files (data/raw/)
    ↓
[RAW STAGE] Spark loads CSV → Parquet (unmodified)
    ↓ data/raw/*.parquet
[PROCESSED STAGE] Clean, validate, deduplicate
    ↓ data/processed/*.parquet
[ANALYTICS STAGE] Feature engineering, denormalization
    ↓ data/analytics/*.parquet
Supabase PostgreSQL Views (SQL Analytics & Queries)
```

---

## Layer Definitions

### RAW STAGE (`data/raw/*.parquet`)
**Unmodified data as extracted from CSV source**
- Load CSV with minimal transformation
- Schema inference from data
- Store in Parquet for efficiency
- Read-only - source of truth

Files:
- `raw_tracks.parquet`
- `raw_artists.parquet`
- `raw_albums.parquet`
- `raw_audio_features.parquet`
- `raw_lyrics_features.parquet`

### PROCESSED STAGE (`data/processed/*.parquet`)
**Cleaned, validated, deduplicated data**
- Data quality checks & corrections
- Type validation & casting
- Handle missing values (nulls, NaNs)
- Remove duplicates
- Remove invalid IDs

Files:
- `processed_tracks.parquet`
- `processed_artists.parquet`
- `processed_albums.parquet`
- `processed_track_features.parquet` (audio + lyrics combined)

### ANALYTICS STAGE (`data/analytics/*.parquet`)
**Business-ready, denormalized tables**
- Join artist/album relationships
- Combine audio + lyrics features
- Create genre mappings
- Denormalize for query efficiency
- Create feature matrix for ML

Files:
- `analytics_artists.parquet`
- `analytics_albums.parquet`
- `analytics_tracks.parquet`
- `analytics_genres.parquet`
- `analytics_track_features.parquet`
- `analytics_recommendation_matrix.parquet`

---

## PostgreSQL Views (Supabase)

### Base Views (Analytics Layer)
```sql
-- Base tables reference analytics parquet files
CREATE VIEW home.artists AS
SELECT * FROM analytics_layer.artists;

CREATE VIEW home.albums AS
SELECT * FROM analytics_layer.albums;

CREATE VIEW home.tracks AS
SELECT * FROM analytics_layer.tracks;

CREATE VIEW home.genres AS
SELECT * FROM analytics_layer.genres;

CREATE VIEW home.track_features AS
SELECT * FROM analytics_layer.track_features;
```

### Analysis Views

**V_1_1: Total Artist Count**
```sql
CREATE VIEW home.v_1_1_total_artists AS
SELECT COUNT(*) as total_artists
FROM home.artists;
```

**V_1_2: Artists by Popularity**
```sql
CREATE VIEW home.v_1_2_artists_popularity AS
SELECT artist_name,
       artist_popularity,
       followers
FROM home.artists
ORDER BY artist_popularity DESC;
```

**V_1_3: Artists by Followers**
```sql
CREATE VIEW home.v_1_3_artists_followers AS
SELECT artist_name,
       followers,
       artist_popularity
FROM home.artists
ORDER BY followers DESC;
```

**V_1_4: Artist Summary**
```sql
CREATE VIEW home.v_1_4_artist_summary AS
SELECT artist_name,
       artist_popularity,
       followers
FROM home.artists;
```

**V_1_5: Artist-Album Relationships**
```sql
CREATE VIEW home.v_1_5_artist_albums AS
SELECT ar.artist_name,
       ar.artist_id,
       ar.followers as artist_followers,
       ar.artist_popularity,
       ab.album_id,
       ab.album_name,
       ab.release_date,
       ab.total_tracks,
       ab.album_type
FROM home.artists ar
LEFT JOIN home.albums ab ON ar.artist_id = ab.artist_id;
```

**V_1_6: Artist-Genre Relationships**
```sql
CREATE VIEW home.v_1_6_artist_genres AS
SELECT ar.artist_name,
       ar.followers,
       ar.artist_popularity,
       ge.genre
FROM home.artists ar
JOIN home.genres ge ON ar.artist_id = ge.artist_id;
```

**V_3_1: Track Features Full**
```sql
CREATE VIEW home.v_3_1_track_features_full AS
SELECT tr.track_id,
       tr.artist_id,
       tr.album_id,
       tr.track_name,
       tr.track_popularity,
       tf.danceability,
       tf.energy,
       tf.loudness,
       tf.speechiness,
       tf.acousticness,
       tf.instrumentalness,
       tf.liveness,
       tf.valence,
       tf.tempo,
       tf.duration_ms,
       tf.time_signature,
       tf.key,
       tf.mode
FROM home.tracks tr
LEFT JOIN home.track_features tf ON tr.track_id = tf.track_id;
```

**V_1_7: Artist-Track Analysis**
```sql
CREATE VIEW home.v_1_7_artist_tracks AS
SELECT ar.artist_name,
       ar.followers,
       ar.artist_popularity,
       tf.track_id,
       tf.track_name,
       tf.track_popularity,
       tf.danceability,
       tf.energy,
       tf.tempo,
       tf.valence
FROM home.artists ar
LEFT JOIN home.v_3_1_track_features_full tf 
  ON ar.artist_id = tf.artist_id;
```

**V_2_1: Album-Track Analysis**
```sql
CREATE VIEW home.v_2_1_album_tracks AS
SELECT ab.album_name,
       ab.release_date,
       ab.total_tracks,
       ab.album_type,
       ar.artist_name,
       tr.track_id,
       tr.track_name,
       tr.track_popularity,
       tf.danceability,
       tf.energy,
       tf.tempo,
       tf.valence
FROM home.albums ab
LEFT JOIN home.artists ar ON ab.artist_id = ar.artist_id
LEFT JOIN home.tracks tr ON ab.album_id = tr.album_id
LEFT JOIN home.track_features tf ON tr.track_id = tf.track_id;
```

---

## Data Flow

### Spark Pipeline

```python
# RAW STAGE: Load CSV → Parquet (unmodified)
raw_tracks = spark.read.csv("data/raw/.../spotify_tracks.csv", header=True)
raw_tracks.write.mode("overwrite").parquet("data/raw/raw_tracks.parquet")

# PROCESSED STAGE: Clean & validate
processed_tracks = raw_tracks.filter(col("track_id").isNotNull())
processed_tracks = cleaned_and_validated(processed_tracks)
processed_tracks.write.mode("overwrite").parquet("data/processed/processed_tracks.parquet")

# ANALYTICS STAGE: Engineer features & denormalize
analytics_tracks = processed_tracks.join(processed_artists, "artist_id")
analytics_tracks = analytics_tracks.join(processed_albums, "album_id")
analytics_tracks.write.mode("overwrite").parquet("data/analytics/analytics_tracks.parquet")
```

### PostgreSQL Integration

```python
# Copy analytics parquet to PostgreSQL
analytics_df = spark.read.parquet("data/analytics/analytics_tracks.parquet")
analytics_df.write \
  .jdbc(database_url, "analytics_tracks", mode="overwrite", properties=db_props)

# Create PostgreSQL views on top
sql("CREATE VIEW home.tracks AS SELECT * FROM analytics_tracks")
```

---

## Module Responsibilities

### `soeSpotify/stages/raw.py`
- Load CSV files from `data/raw/<source>/`
- Write to `data/raw/*.parquet`
- Minimal transformation, schema inference

### `soeSpotify/stages/processed.py`
- Read raw parquet
- Validate data quality
- Clean types, handle nulls/NaNs
- Remove duplicates
- Write to `data/processed/*.parquet`

### `soeSpotify/stages/analytics.py`
- Read processed parquet
- Join relationships (artist → album → track)
- Combine features (audio + lyrics)
- Create genre mappings
- Denormalize for queries
- Write to `data/analytics/*.parquet`

### `soeSpotify/database.py`
- Load analytics parquet → PostgreSQL tables
- Create SQL views (home.artists, home.tracks, etc.)
- Create analysis views (v_1_1, v_1_2, etc.)

### `soeSpotify/main.py`
- Orchestrate: raw → processed → analytics
- Trigger database sync
- Logging and error handling

---

## Directory Structure

```
soe-spotify/
├── data/
│   ├── raw/                    ← Source CSVs + raw parquet
│   │   ├── Data Sources/       (spotify_tracks.csv, etc.)
│   │   ├── Features Extracted/
│   │   └── *.parquet           (raw stage output)
│   ├── processed/              ← Cleaned parquet
│   │   └── *.parquet
│   └── analytics/              ← Business-ready parquet
│       └── *.parquet
│
├── soeSpotify/
│   ├── __init__.py
│   ├── config.py               (paths, constants)
│   ├── main.py                 (orchestration)
│   ├── database.py             (PostgreSQL integration)
│   ├── stages/
│   │   ├── __init__.py
│   │   ├── raw.py              (CSV → raw parquet)
│   │   ├── processed.py        (raw → processed)
│   │   └── analytics.py        (processed → analytics)
│   └── features/
│       ├── __init__.py
│       ├── engineering.py      (feature creation)
│       └── validation.py       (data quality checks)
```

---

## Benefits

✓ **Immutability:** Raw stage is never modified  
✓ **Auditability:** Each stage is a checkpoint  
✓ **Reproducibility:** Full pipeline from source CSVs  
✓ **Performance:** Parquet is columnar and compressed  
✓ **Flexibility:** SQL analytics via PostgreSQL views  
✓ **Scalability:** Spark handles large datasets  
✓ **Data Quality:** Processed stage has validation rules  
