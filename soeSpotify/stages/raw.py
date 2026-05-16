import logging
from pathlib import Path

import pandas as pd

from ..config import (
    CSV_ALBUMS,
    CSV_ARTISTS,
    CSV_TRACKS,
    CSV_AUDIO_FEATURES,
    CSV_LYRICS_FEATURES,
    RAW_TRACKS,
    RAW_ARTISTS,
    RAW_ALBUMS,
    RAW_AUDIO_FEATURES,
    RAW_LYRICS_FEATURES,
    DATA_RAW_PARQUET,
)

logger = logging.getLogger(__name__)


class RawStage:
    """Load CSV files and write unmodified to raw parquet stage."""

    def __init__(self) -> None:
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Create output directories if they don't exist."""
        DATA_RAW_PARQUET.mkdir(parents=True, exist_ok=True)
        logger.info(f"Raw parquet directory ready: {DATA_RAW_PARQUET}")

    def load_and_save_tracks(self) -> pd.DataFrame:
        """Load tracks CSV and save to raw parquet."""
        logger.info(f"Loading tracks from {CSV_TRACKS}")
        df = pd.read_csv(CSV_TRACKS)
        count = len(df)
        logger.info(f"Loaded {count} tracks")

        logger.info(f"Saving to {RAW_TRACKS}")
        df.to_parquet(RAW_TRACKS, engine="pyarrow", index=False)
        logger.info(f"Saved {count} tracks to raw stage")
        return df

    def load_and_save_artists(self) -> pd.DataFrame:
        """Load artists CSV and save to raw parquet."""
        logger.info(f"Loading artists from {CSV_ARTISTS}")
        df = pd.read_csv(CSV_ARTISTS)
        count = len(df)
        logger.info(f"Loaded {count} artists")

        logger.info(f"Saving to {RAW_ARTISTS}")
        df.to_parquet(RAW_ARTISTS, engine="pyarrow", index=False)
        logger.info(f"Saved {count} artists to raw stage")
        return df

    def load_and_save_albums(self) -> pd.DataFrame:
        """Load albums CSV and save to raw parquet."""
        logger.info(f"Loading albums from {CSV_ALBUMS}")
        df = pd.read_csv(CSV_ALBUMS)
        count = len(df)
        logger.info(f"Loaded {count} albums")

        logger.info(f"Saving to {RAW_ALBUMS}")
        df.to_parquet(RAW_ALBUMS, engine="pyarrow", index=False)
        logger.info(f"Saved {count} albums to raw stage")
        return df

    def load_and_save_audio_features(self) -> pd.DataFrame:
        """Load audio features CSV and save to raw parquet."""
        logger.info(f"Loading audio features from {CSV_AUDIO_FEATURES}")
        df = pd.read_csv(CSV_AUDIO_FEATURES)
        count = len(df)
        logger.info(f"Loaded {count} audio feature records")

        logger.info(f"Saving to {RAW_AUDIO_FEATURES}")
        df.to_parquet(RAW_AUDIO_FEATURES, engine="pyarrow", index=False)
        logger.info(f"Saved {count} audio features to raw stage")
        return df

    def load_and_save_lyrics_features(self) -> pd.DataFrame:
        """Load lyrics features CSV and save to raw parquet."""
        logger.info(f"Loading lyrics features from {CSV_LYRICS_FEATURES}")
        df = pd.read_csv(CSV_LYRICS_FEATURES)
        count = len(df)
        logger.info(f"Loaded {count} lyrics feature records")

        logger.info(f"Saving to {RAW_LYRICS_FEATURES}")
        df.to_parquet(RAW_LYRICS_FEATURES, engine="pyarrow", index=False)
        logger.info(f"Saved {count} lyrics features to raw stage")
        return df

    def run(
        self,
    ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Load all raw data and save to parquet stage."""
        logger.info("=" * 60)
        logger.info("RAW STAGE: Loading CSV files → Raw Parquet")
        logger.info("=" * 60)

        tracks = self.load_and_save_tracks()
        artists = self.load_and_save_artists()
        albums = self.load_and_save_albums()
        audio_features = self.load_and_save_audio_features()
        lyrics_features = self.load_and_save_lyrics_features()

        logger.info("Raw stage completed successfully")
        return tracks, artists, albums, audio_features, lyrics_features
