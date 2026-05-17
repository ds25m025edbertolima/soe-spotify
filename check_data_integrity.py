import pandas as pd
from pathlib import Path
import sys

project_root = Path.cwd()
sys.path.insert(0, str(project_root))
from soeSpotify import config

print("Checking Processed Data...")
df_artists = pd.read_parquet(config.PROCESSED_ARTISTS)
df_albums = pd.read_parquet(config.PROCESSED_ALBUMS)
df_tracks = pd.read_parquet(config.PROCESSED_TRACKS)

print(f"Processed Artists: {len(df_artists)}")
print(f"Processed Albums:  {len(df_albums)}")
print(f"Processed Tracks:  {len(df_tracks)}")

print("\nID Column Names:")
print(f"Artists: {df_artists.columns.tolist()}")
print(f"Albums:  {df_albums.columns.tolist()}")
print(f"Tracks:  {df_tracks.columns.tolist()}")

valid_artist_ids = set(df_artists["artist_id"])
valid_album_ids = set(df_albums["album_id"])

tracks_with_valid_artist = df_tracks["artists_id"].isin(valid_artist_ids).sum()
tracks_with_valid_album = df_tracks["album_id"].isin(valid_album_ids).sum()
tracks_with_both = ((df_tracks["artists_id"].isin(valid_artist_ids)) & (df_tracks["album_id"].isin(valid_album_ids))).sum()

print(f"\nTracks with valid artist: {tracks_with_valid_artist}")
print(f"Tracks with valid album:  {tracks_with_valid_album}")
print(f"Tracks with both:         {tracks_with_both}")

# Check first few tracks artists_id vs artist_id
print("\nSample Track Artists IDs:")
print(df_tracks["artists_id"].head().tolist())
print("\nSample Artist IDs:")
print(df_artists["artist_id"].head().tolist())
