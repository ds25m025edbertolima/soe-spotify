import logging
from pathlib import Path

from pyspark.sql import SparkSession, DataFrame

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

    def __init__(self, spark: SparkSession) -> None:
        self.spark = spark
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Create output directories if they don't exist."""
        DATA_RAW_PARQUET.mkdir(parents=True, exist_ok=True)
        logger.info(f"Raw parquet directory ready: {DATA_RAW_PARQUET}")

    def load_and_save_tracks(self) -> DataFrame:
        """Load tracks CSV and save to raw parquet."""
        logger.info(f"Loading tracks from {CSV_TRACKS}")
        df = self.spark.read.csv(str(CSV_TRACKS), header=True, inferSchema=True)
        count = df.count()
        logger.info(f"Loaded {count} tracks")

        logger.info(f"Saving to {RAW_TRACKS}")
        df.write.mode("overwrite").parquet(str(RAW_TRACKS))
        logger.info(f"Saved {count} tracks to raw stage")
        return df

    def load_and_save_artists(self) -> DataFrame:
        """Load artists CSV and save to raw parquet."""
        logger.info(f"Loading artists from {CSV_ARTISTS}")
        df = self.spark.read.csv(str(CSV_ARTISTS), header=True, inferSchema=True)
        count = df.count()
        logger.info(f"Loaded {count} artists")

        logger.info(f"Saving to {RAW_ARTISTS}")
        df.write.mode("overwrite").parquet(str(RAW_ARTISTS))
        logger.info(f"Saved {count} artists to raw stage")
        return df

    def load_and_save_albums(self) -> DataFrame:
        """Load albums CSV and save to raw parquet."""
        logger.info(f"Loading albums from {CSV_ALBUMS}")
        df = self.spark.read.csv(str(CSV_ALBUMS), header=True, inferSchema=True)
        count = df.count()
        logger.info(f"Loaded {count} albums")

        logger.info(f"Saving to {RAW_ALBUMS}")
        df.write.mode("overwrite").parquet(str(RAW_ALBUMS))
        logger.info(f"Saved {count} albums to raw stage")
        return df

    def load_and_save_audio_features(self) -> DataFrame:
        """Load audio features CSV and save to raw parquet."""
        logger.info(f"Loading audio features from {CSV_AUDIO_FEATURES}")
        df = self.spark.read.csv(
            str(CSV_AUDIO_FEATURES), header=True, inferSchema=True
        )
        count = df.count()
        logger.info(f"Loaded {count} audio feature records")

        logger.info(f"Saving to {RAW_AUDIO_FEATURES}")
        df.write.mode("overwrite").parquet(str(RAW_AUDIO_FEATURES))
        logger.info(f"Saved {count} audio features to raw stage")
        return df

    def load_and_save_lyrics_features(self) -> DataFrame:
        """Load lyrics features CSV and save to raw parquet."""
        logger.info(f"Loading lyrics features from {CSV_LYRICS_FEATURES}")
        df = self.spark.read.csv(
            str(CSV_LYRICS_FEATURES), header=True, inferSchema=True
        )
        count = df.count()
        logger.info(f"Loaded {count} lyrics feature records")

        logger.info(f"Saving to {RAW_LYRICS_FEATURES}")
        df.write.mode("overwrite").parquet(str(RAW_LYRICS_FEATURES))
        logger.info(f"Saved {count} lyrics features to raw stage")
        return df

    def run(self) -> tuple[DataFrame, DataFrame, DataFrame, DataFrame, DataFrame]:
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
