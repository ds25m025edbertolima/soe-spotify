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

# Firebase configuration
FIREBASE_CREDENTIALS = PROJECT_ROOT / (
    "fhtw-soe-firebase-adminsdk-fbsvc-5a77ac938f.json"
)
FIREBASE_STORAGE_BUCKET = "soe-music-recommender.appspot.com"

# Firestore collections
COLLECTION_TRACKS = "tracks"
COLLECTION_ARTISTS = "artists"
COLLECTION_ALBUMS = "albums"

# Spark configuration
SPARK_MASTER = "local[*]"
SPARK_APP_NAME = "soe-spotify-etl"
SPARK_LOG_LEVEL = "WARN"

# ETL batch size for Firestore writes
FIRESTORE_BATCH_SIZE = 500
