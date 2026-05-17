import pandas as pd
from pathlib import Path
import sys

project_root = Path.cwd()
sys.path.insert(0, str(project_root))
from soeSpotify import config

df_artists = pd.read_parquet(config.PROCESSED_ARTISTS)
df_albums = pd.read_parquet(config.PROCESSED_ALBUMS)
df_tracks = pd.read_parquet(config.PROCESSED_TRACKS)
df_features = pd.read_parquet(config.PROCESSED_TRACK_FEATURES)

print(f"Processed Tracks: {len(df_tracks)}")

# Clean
df_tracks["artists_id"] = df_tracks["artists_id"].str.extract(r"'(.*?)'")[0]

# Filter
valid_artist_ids = df_artists["artist_id"].unique()
valid_album_ids = df_albums["album_id"].unique()

df_tracks_filtered = df_tracks[
    (df_tracks["artists_id"].isin(valid_artist_ids)) & 
    (df_tracks["album_id"].isin(valid_album_ids))
].copy()

print(f"Filtered Tracks: {len(df_tracks_filtered)}")

# Merge features
df = df_tracks_filtered.merge(df_features, on="track_id", how="left")
print(f"After merge features: {len(df)}")

# Merge artists
artists_cols = df_artists.copy()
artists_cols = artists_cols.rename(
    columns={c: f"artist_{c}" for c in df_artists.columns}
)
df = df.merge(
    artists_cols,
    left_on="artists_id",
    right_on="artist_artist_id",
    how="left",
)
print(f"After merge artists: {len(df)}")

# Merge albums
albums_cols = df_albums.copy()
albums_cols = albums_cols.rename(
    columns={c: f"album_{c}" for c in df_albums.columns}
)
df = df.merge(
    albums_cols,
    left_on="album_id",
    right_on="album_album_id",
    how="left",
)
print(f"After merge albums: {len(df)}")

# Select columns
final_cols = [
    "track_id", "track_name", "popularity", "duration_ms", "explicit",
    "preview_url", "uri", "album_id", "album_album_name", "album_album_type",
    "album_release_date", "artists_id", "artist_artist_name",
    "artist_artist_popularity", "artist_followers", "artist_genres",
]
df_final = df[[c for c in final_cols if c in df.columns]].copy()
print(f"Final Tracks: {len(df_final)}")
