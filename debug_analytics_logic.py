import pandas as pd
from pathlib import Path
import sys

project_root = Path.cwd()
sys.path.insert(0, str(project_root))
from soeSpotify import config

print("Diagnosing Analytics Stage logic...")
df_artists = pd.read_parquet(config.PROCESSED_ARTISTS)
df_albums = pd.read_parquet(config.PROCESSED_ALBUMS)
df_tracks = pd.read_parquet(config.PROCESSED_TRACKS)

print(f"Initial Tracks: {len(df_tracks)}")

# Clean artists_id
df_tracks["artists_id_cleaned"] = df_tracks["artists_id"].str.extract(r"'(.*?)'")[0]

print("\nSample mapping:")
for i in range(5):
    orig = df_tracks["artists_id"].iloc[i]
    cleaned = df_tracks["artists_id_cleaned"].iloc[i]
    print(f"  {orig} -> {cleaned}")

valid_artist_ids = set(df_artists["artist_id"])
matches_artist = df_tracks["artists_id_cleaned"].isin(valid_artist_ids).sum()
print(f"\nMatches with valid artists: {matches_artist}")

valid_album_ids = set(df_albums["album_id"])
matches_album = df_tracks["album_id"].isin(valid_album_ids).sum()
print(f"Matches with valid albums:  {matches_album}")

matches_both = ((df_tracks["artists_id_cleaned"].isin(valid_artist_ids)) & (df_tracks["album_id"].isin(valid_album_ids))).sum()
print(f"Matches with BOTH:          {matches_both}")

if matches == 0 and matches_v2 == 0:
    print("\nERROR: Still no matches!")
    print("\nSample Artist IDs (from Artists table):")
    print(df_artists["artist_id"].head().tolist())
