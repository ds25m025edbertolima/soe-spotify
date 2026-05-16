import os
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw" / "SpotGenTrack"
DATA_INTERIM = PROJECT_ROOT / "data" / "interim"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"

# CSV paths
CSV_ALBUMS = DATA_RAW / "Data Sources" / "spotify_albums.csv"
CSV_ARTISTS = DATA_RAW / "Data Sources" / "spotify_artists.csv"
CSV_TRACKS = DATA_RAW / "Data Sources" / "spotify_tracks.csv"
CSV_AUDIO_FEATURES = DATA_RAW / "Features Extracted" / (
    "low_level_audio_features.csv"
)
CSV_LYRICS_FEATURES = DATA_RAW / "Features Extracted" / "lyrics_features.csv"

# Supabase/PostgreSQL configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/soe_spotify"
)

# Database tables
TABLE_TRACKS = "tracks"
TABLE_ARTISTS = "artists"
TABLE_ALBUMS = "albums"

# Spark configuration
SPARK_MASTER = "local[*]"
SPARK_APP_NAME = "soe-spotify-etl"
SPARK_LOG_LEVEL = "WARN"

# JVM options for Java compatibility
SPARK_DRIVER_JAVA_OPTIONS = (
    "--add-opens=java.base/jdk.internal.ref=ALL-UNNAMED "
    "--add-opens=java.base/sun.nio.ch=ALL-UNNAMED "
    "--add-opens=java.base/sun.security.action=ALL-UNNAMED"
)

# ETL batch size for database writes
DB_BATCH_SIZE = 1000
