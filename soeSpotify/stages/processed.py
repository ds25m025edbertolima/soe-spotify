import logging

import pandas as pd
import numpy as np

from ..config import (
    RAW_TRACKS,
    RAW_ARTISTS,
    RAW_ALBUMS,
    RAW_AUDIO_FEATURES,
    RAW_LYRICS_FEATURES,
    PROCESSED_TRACKS,
    PROCESSED_ARTISTS,
    PROCESSED_ALBUMS,
    PROCESSED_TRACK_FEATURES,
    DATA_PROCESSED,
)

logger = logging.getLogger(__name__)


class ProcessedStage:
    """Clean, validate, and deduplicate raw data."""

    def __init__(self) -> None:
        DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
        logger.info(f"Processed stage directory ready: {DATA_PROCESSED}")

    @staticmethod
    def _clean_nulls_and_nans(df: pd.DataFrame) -> pd.DataFrame:
        """Replace NaN with None for consistent null handling."""
        # Replace NaN with None in numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            df[col] = df[col].replace({np.nan: None})
        return df

    def process_artists(self, raw_artists: pd.DataFrame) -> pd.DataFrame:
        """Clean and validate artists data."""
        logger.info("Processing artists...")

        df = raw_artists.rename(
            columns={
                "id": "artist_id",
                "name": "artist_name",
                "artist_popularity": "artist_popularity",
                "followers": "followers",
                "genres": "genres",
                "type": "type",
            }
        ).copy()

        # Keep only needed columns
        df = df[["artist_id", "artist_name", "artist_popularity", "followers",
                 "genres", "type"]]

        # Remove nulls in primary key
        df = df.dropna(subset=["artist_id"])
        logger.info(f"Removed null artist_ids, {len(df)} artists remaining")

        # Remove duplicates
        df = df.drop_duplicates(subset=["artist_id"])
        logger.info(f"Removed duplicates, {len(df)} unique artists")

        # Clean nulls/NaNs
        df = self._clean_nulls_and_nans(df)

        return df

    def process_albums(self, raw_albums: pd.DataFrame) -> pd.DataFrame:
        """Clean and validate albums data."""
        logger.info("Processing albums...")

        df = raw_albums.rename(
            columns={
                "id": "album_id",
                "name": "album_name",
                "album_type": "album_type",
                "artist_id": "artist_id",
                "release_date": "release_date",
                "release_date_precision": "release_date_precision",
                "total_tracks": "total_tracks",
                "uri": "uri",
            }
        ).copy()

        # Keep only needed columns
        df = df[["album_id", "album_name", "album_type", "artist_id",
                 "release_date", "release_date_precision", "total_tracks", "uri"]]

        # Remove nulls in primary key
        df = df.dropna(subset=["album_id"])
        logger.info(f"Removed null album_ids, {len(df)} albums remaining")

        # Remove duplicates
        df = df.drop_duplicates(subset=["album_id"])
        logger.info(f"Removed duplicates, {len(df)} unique albums")

        # Clean nulls/NaNs
        df = self._clean_nulls_and_nans(df)

        return df

    def process_tracks(self, raw_tracks: pd.DataFrame) -> pd.DataFrame:
        """Clean and validate tracks data."""
        logger.info("Processing tracks...")

        df = raw_tracks.rename(
            columns={
                "id": "track_id",
                "name": "track_name",
                "album_id": "album_id",
                "artists_id": "artists_id",
                "popularity": "popularity",
                "duration_ms": "duration_ms",
                "explicit": "explicit",
                "country": "country",
                "playlist": "playlist",
                "uri": "uri",
                "preview_url": "preview_url",
                "analysis_url": "analysis_url",
                "href": "href",
                "track_href": "track_href",
                "available_markets": "available_markets",
            }
        ).copy()

        # Keep track metadata + Spotify audio features
        cols = [
            "track_id", "track_name", "album_id", "artists_id", "popularity",
            "duration_ms", "explicit", "country", "playlist", "uri",
            "preview_url", "analysis_url", "href", "track_href",
            "available_markets",
            # Spotify audio features (high-level)
            "acousticness", "danceability", "energy", "instrumentalness",
            "key", "liveness", "loudness", "mode", "speechiness", "tempo",
            "time_signature", "valence",
        ]
        df = df[[c for c in cols if c in df.columns]]

        # Remove nulls in primary key
        df = df.dropna(subset=["track_id"])
        logger.info(f"Removed null track_ids, {len(df)} tracks remaining")

        # Remove duplicates
        df = df.drop_duplicates(subset=["track_id"])
        logger.info(f"Removed duplicates, {len(df)} unique tracks")

        # Clean nulls/NaNs
        df = self._clean_nulls_and_nans(df)

        return df

    def process_track_features(
        self,
        raw_audio: pd.DataFrame,
        raw_lyrics: pd.DataFrame,
    ) -> pd.DataFrame:
        """Combine and validate audio + lyrics features."""
        logger.info("Processing track features...")

        # Clean audio features
        audio = raw_audio.copy()
        # Drop unnamed/index columns
        audio = audio.loc[:, ~audio.columns.str.contains("^Unnamed")]
        audio = audio.dropna(subset=["track_id"])
        audio = self._clean_nulls_and_nans(audio)

        # Clean lyrics features
        lyrics = raw_lyrics[[
            "track_id", "mean_syllables_word", "mean_words_sentence",
            "n_sentences", "n_words", "sentence_similarity", "vocabulary_wealth"
        ]].copy()
        lyrics = lyrics.dropna(subset=["track_id"])
        lyrics = self._clean_nulls_and_nans(lyrics)

        # Join audio + lyrics on track_id
        df = audio.merge(lyrics, on="track_id", how="left")
        df = df.fillna(0)

        logger.info(f"Combined features for {len(df)} tracks")

        return df

    def run(
        self,
        raw_tracks: pd.DataFrame,
        raw_artists: pd.DataFrame,
        raw_albums: pd.DataFrame,
        raw_audio: pd.DataFrame,
        raw_lyrics: pd.DataFrame,
    ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Process all raw data and save to processed stage."""
        logger.info("=" * 60)
        logger.info("PROCESSED STAGE: Cleaning & Validating Data")
        logger.info("=" * 60)

        artists = self.process_artists(raw_artists)
        logger.info(f"Saving {len(artists)} artists")
        artists.to_parquet(PROCESSED_ARTISTS, engine="pyarrow", index=False)

        albums = self.process_albums(raw_albums)
        logger.info(f"Saving {len(albums)} albums")
        albums.to_parquet(PROCESSED_ALBUMS, engine="pyarrow", index=False)

        tracks = self.process_tracks(raw_tracks)
        logger.info(f"Saving {len(tracks)} tracks")
        tracks.to_parquet(PROCESSED_TRACKS, engine="pyarrow", index=False)

        track_features = self.process_track_features(raw_audio, raw_lyrics)
        logger.info(f"Saving {len(track_features)} track features")
        track_features.to_parquet(
            PROCESSED_TRACK_FEATURES, engine="pyarrow", index=False
        )

        logger.info("Processed stage completed successfully")
        return tracks, artists, albums, track_features
