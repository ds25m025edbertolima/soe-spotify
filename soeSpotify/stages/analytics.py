import logging

import pandas as pd

from ..config import (
    PROCESSED_TRACKS,
    PROCESSED_ARTISTS,
    PROCESSED_ALBUMS,
    PROCESSED_TRACK_FEATURES,
    ANALYTICS_TRACKS,
    ANALYTICS_ARTISTS,
    ANALYTICS_ALBUMS,
    ANALYTICS_GENRES,
    ANALYTICS_TRACK_FEATURES,
    DATA_ANALYTICS,
)

logger = logging.getLogger(__name__)


class AnalyticsStage:
    """Feature engineering, denormalization, and business-ready tables."""

    def __init__(self) -> None:
        DATA_ANALYTICS.mkdir(parents=True, exist_ok=True)
        logger.info(f"Analytics stage directory ready: {DATA_ANALYTICS}")

    def build_analytics_artists(self, artists: pd.DataFrame) -> pd.DataFrame:
        """Create business-ready artists table."""
        logger.info("Building analytics artists table...")

        df = artists[[
            "artist_id", "artist_name", "artist_popularity", "followers", "type",
            "genres"
        ]].copy()
        
        # Ensure correct types
        df["artist_popularity"] = df["artist_popularity"].fillna(0).astype("int64")
        df["followers"] = df["followers"].fillna(0).astype("int64")

        return df

    def build_analytics_albums(
        self, albums: pd.DataFrame, artists: pd.DataFrame
    ) -> pd.DataFrame:
        """Create denormalized albums table with artist info."""
        logger.info("Building analytics albums table...")

        # FILTER: Only keep albums that reference an existing artist (Foreign Key constraint)
        valid_artist_ids = artists["artist_id"].unique()
        df_albums = albums[albums["artist_id"].isin(valid_artist_ids)].copy()
        
        logger.info(f"Filtered albums: {len(df_albums)}/{len(albums)} reference valid artists")

        # Prepare artist columns with prefix to avoid conflicts
        artists_cols = artists.copy()
        artists_cols = artists_cols.rename(
            columns={c: f"artist_{c}" for c in artists.columns}
        )

        # Join albums with artists
        df = df_albums.merge(
            artists_cols,
            left_on="artist_id",
            right_on="artist_artist_id",
            how="left",
        )

        # Select and rename final columns
        df = df[[
            "album_id", "album_name", "album_type", "release_date", "total_tracks",
            "uri", "artist_id", "artist_artist_name", "artist_followers",
            "artist_artist_popularity"
        ]].copy()

        df = df.rename(
            columns={
                "artist_artist_name": "artist_name",
                "artist_artist_popularity": "artist_popularity",
            }
        )
        
        # Ensure correct types for database sync
        df["total_tracks"] = df["total_tracks"].fillna(0).astype("int64")
        df["artist_followers"] = df["artist_followers"].fillna(0).astype("int64")
        df["artist_popularity"] = df["artist_popularity"].fillna(0).astype("int64")

        return df

    def build_analytics_tracks(
        self,
        tracks: pd.DataFrame,
        artists: pd.DataFrame,
        albums: pd.DataFrame,
        features: pd.DataFrame,
    ) -> pd.DataFrame:
        """Create denormalized tracks table with full context."""
        logger.info("Building analytics tracks table...")

        # Create a copy to avoid side effects on the input dataframe
        df_base = tracks.copy()

        # CLEAN: artists_id is often "['ID']", extract the first one safely
        # Only extract if it looks like a string representation of a list
        is_list_format = df_base["artists_id"].str.contains(r"\[", na=False)
        if is_list_format.any():
            df_base.loc[is_list_format, "artists_id"] = df_base.loc[is_list_format, "artists_id"].str.extract(r"'(.*?)'")[0]

        # FILTER: Only keep tracks that reference valid artists AND valid albums
        valid_artist_ids = artists["artist_id"].unique()
        valid_album_ids = albums["album_id"].unique()
        
        df_tracks_filtered = df_base[
            (df_base["artists_id"].isin(valid_artist_ids)) & 
            (df_base["album_id"].isin(valid_album_ids))
        ].copy()
        
        logger.info(f"Filtered tracks: {len(df_tracks_filtered)}/{len(tracks)} have valid references")

        # Join tracks with features
        df = df_tracks_filtered.merge(features, on="track_id", how="left")

        # Join with artists
        artists_cols = artists.copy()
        artists_cols = artists_cols.rename(
            columns={c: f"artist_{c}" for c in artists.columns}
        )
        df = df.merge(
            artists_cols,
            left_on="artists_id",
            right_on="artist_artist_id",
            how="left",
        )

        # Join with albums
        albums_cols = albums.copy()
        albums_cols = albums_cols.rename(
            columns={c: f"album_{c}" for c in albums.columns}
        )
        df = df.merge(
            albums_cols,
            left_on="album_id",
            right_on="album_album_id",
            how="left",
        )

        # Select final columns
        final_cols = [
            "track_id", "track_name", "popularity", "duration_ms",
            "preview_url", "uri", "album_id", "album_album_name", "album_album_type",
            "album_release_date", "artists_id", "artist_artist_name",
            "artist_artist_popularity", "artist_followers", "artist_genres",
            # Audio features
            "acousticness", "danceability", "energy", "instrumentalness", "key",
            "liveness", "loudness", "mode", "speechiness", "tempo",
            "time_signature", "valence",
            # Lyrics features
            "mean_syllables_word", "mean_words_sentence", "n_sentences", "n_words",
            "sentence_similarity", "vocabulary_wealth",
        ]

        df = df[[c for c in final_cols if c in df.columns]].copy()

        # Rename for clarity
        df = df.rename(
            columns={
                "popularity": "track_popularity",
                "album_album_name": "album_name",
                "album_album_type": "album_type",
                "album_release_date": "release_date",
                "artist_artist_name": "artist_name",
                "artist_artist_popularity": "artist_popularity",
                "artist_genres": "genres",
            }
        )
        
        # Ensure correct types
        df["track_popularity"] = df["track_popularity"].fillna(0).astype("int64")
        df["duration_ms"] = df["duration_ms"].fillna(0).astype("int64")
        df["artist_popularity"] = df["artist_popularity"].fillna(0).astype("int64")
        df["artist_followers"] = df["artist_followers"].fillna(0).astype("int64")
        
        # Audio feature integers
        for col in ["key", "mode", "time_signature"]:
            if col in df.columns:
                df[col] = df[col].fillna(0).astype("int64")

        return df

    def build_analytics_genres(self, artists: pd.DataFrame) -> pd.DataFrame:
        """Create genres mapping table (artist_id → genre)."""
        logger.info("Building analytics genres table...")

        # Explode genres array into individual rows
        genres_list = []

        for _, row in artists.iterrows():
            artist_id = row["artist_id"]
            artist_name = row["artist_name"]
            genres = row["genres"]

            if isinstance(genres, str):
                # Handle string representation of list
                if genres.startswith("[") and genres.endswith("]"):
                    import ast
                    try:
                        genre_list = ast.literal_eval(genres)
                    except (ValueError, SyntaxError):
                        genre_list = [genres]
                else:
                    genre_list = [genres]
            elif isinstance(genres, list):
                genre_list = genres
            else:
                continue

            for genre in genre_list:
                if genre:  # Skip empty genres
                    genres_list.append({
                        "artist_id": artist_id,
                        "artist_name": artist_name,
                        "genre": genre,
                    })

        df = pd.DataFrame(genres_list)
        
        # FILTER: Only keep genres for valid artists
        valid_artist_ids = artists["artist_id"].unique()
        df = df[df["artist_id"].isin(valid_artist_ids)].copy()

        logger.info(f"Created {len(df)} genre mappings")

        return df

    def build_analytics_track_features(
        self, tracks: pd.DataFrame, features: pd.DataFrame
    ) -> pd.DataFrame:
        """Create feature table with audio + lyrics features for database."""
        logger.info("Building analytics track features table...")

        # Get high-level Spotify audio features from processed tracks
        spotify_features = [
            "track_id", "acousticness", "danceability", "energy",
            "instrumentalness", "key", "liveness", "loudness", "mode",
            "speechiness", "tempo", "time_signature", "valence",
        ]
        audio_cols = [c for c in spotify_features if c in tracks.columns]

        # Get lyrics features from the features dataframe
        lyrics_features = [
            "mean_syllables_word", "mean_words_sentence", "n_sentences",
            "n_words", "sentence_similarity", "vocabulary_wealth",
        ]
        lyrics_cols = [c for c in lyrics_features if c in features.columns]

        # Start with high-level audio features from tracks
        df_audio = tracks[audio_cols].copy()
        df_audio = df_audio.drop_duplicates(subset=["track_id"])

        # Merge with lyrics features
        if lyrics_cols:
            df_lyrics = features[["track_id"] + lyrics_cols].copy()
            df_lyrics = df_lyrics.drop_duplicates(subset=["track_id"])
            df = df_audio.merge(df_lyrics, on="track_id", how="left")
        else:
            df = df_audio

        df = df.fillna(0)
        
        # FILTER: Only keep features for valid tracks (Foreign Key constraint)
        valid_track_ids = tracks["track_id"].unique()
        df = df[df["track_id"].isin(valid_track_ids)].copy()
        
        # Ensure correct types for audio feature integers
        for col in ["key", "mode", "time_signature"]:
            if col in df.columns:
                df[col] = df[col].fillna(0).astype("int64")

        logger.info(f"Analytics features: {len(df)} rows, {len(df.columns)} columns")

        return df

    def run(
        self,
        tracks: pd.DataFrame,
        artists: pd.DataFrame,
        albums: pd.DataFrame,
        features: pd.DataFrame,
    ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Build all analytics tables."""
        logger.info("=" * 60)
        logger.info("ANALYTICS STAGE: Feature Engineering & Denormalization")
        logger.info("=" * 60)

        analytics_artists = self.build_analytics_artists(artists)
        logger.info(f"Saving {len(analytics_artists)} analytics artists")
        analytics_artists.to_parquet(
            ANALYTICS_ARTISTS, engine="pyarrow", index=False
        )

        analytics_albums = self.build_analytics_albums(albums, analytics_artists)
        logger.info(f"Saving {len(analytics_albums)} analytics albums")
        analytics_albums.to_parquet(ANALYTICS_ALBUMS, engine="pyarrow", index=False)

        analytics_tracks = self.build_analytics_tracks(
            tracks, analytics_artists, analytics_albums, features
        )
        logger.info(f"Saving {len(analytics_tracks)} analytics tracks")
        analytics_tracks.to_parquet(ANALYTICS_TRACKS, engine="pyarrow", index=False)

        analytics_genres = self.build_analytics_genres(analytics_artists)
        logger.info(f"Saving {len(analytics_genres)} analytics genres")
        analytics_genres.to_parquet(ANALYTICS_GENRES, engine="pyarrow", index=False)

        analytics_features = self.build_analytics_track_features(
            analytics_tracks, features
        )
        logger.info(f"Saving {len(analytics_features)} feature records")
        analytics_features.to_parquet(
            ANALYTICS_TRACK_FEATURES, engine="pyarrow", index=False
        )

        logger.info("Analytics stage completed successfully")
        return (
            analytics_tracks,
            analytics_artists,
            analytics_albums,
            analytics_genres,
            analytics_features,
        )
