import os
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_ROOT = PROJECT_ROOT / "data"

# Raw data sources (CSV files - immutable)
DATA_RAW = DATA_ROOT / "raw"
DATA_RAW_SOURCES = DATA_RAW / "SpotGenTrack" / "Data Sources"
DATA_RAW_FEATURES = DATA_RAW / "SpotGenTrack" / "Features Extracted"

CSV_ALBUMS = DATA_RAW_SOURCES / "spotify_albums.csv"
CSV_ARTISTS = DATA_RAW_SOURCES / "spotify_artists.csv"
CSV_TRACKS = DATA_RAW_SOURCES / "spotify_tracks.csv"
CSV_AUDIO_FEATURES = DATA_RAW_FEATURES / "low_level_audio_features.csv"
CSV_LYRICS_FEATURES = DATA_RAW_FEATURES / "lyrics_features.csv"

# Processing stages (Parquet storage)
DATA_RAW_PARQUET = DATA_RAW / "parquet"
DATA_PROCESSED = DATA_ROOT / "processed"
DATA_ANALYTICS = DATA_ROOT / "analytics"

# Raw stage parquet files
RAW_TRACKS = DATA_RAW_PARQUET / "raw_tracks.parquet"
RAW_ARTISTS = DATA_RAW_PARQUET / "raw_artists.parquet"
RAW_ALBUMS = DATA_RAW_PARQUET / "raw_albums.parquet"
RAW_AUDIO_FEATURES = DATA_RAW_PARQUET / "raw_audio_features.parquet"
RAW_LYRICS_FEATURES = DATA_RAW_PARQUET / "raw_lyrics_features.parquet"

# Processed stage parquet files
PROCESSED_TRACKS = DATA_PROCESSED / "processed_tracks.parquet"
PROCESSED_ARTISTS = DATA_PROCESSED / "processed_artists.parquet"
PROCESSED_ALBUMS = DATA_PROCESSED / "processed_albums.parquet"
PROCESSED_TRACK_FEATURES = DATA_PROCESSED / "processed_track_features.parquet"

# Analytics stage parquet files
ANALYTICS_TRACKS = DATA_ANALYTICS / "analytics_tracks.parquet"
ANALYTICS_ARTISTS = DATA_ANALYTICS / "analytics_artists.parquet"
ANALYTICS_ALBUMS = DATA_ANALYTICS / "analytics_albums.parquet"
ANALYTICS_GENRES = DATA_ANALYTICS / "analytics_genres.parquet"
ANALYTICS_TRACK_FEATURES = DATA_ANALYTICS / "analytics_track_features.parquet"

# Supabase/PostgreSQL configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/soe_spotify"
)

# ETL batch size for database writes
DB_BATCH_SIZE = 1000
