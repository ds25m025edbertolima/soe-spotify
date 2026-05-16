import logging

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import col, isnan, isnull, when

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

    def __init__(self, spark: SparkSession) -> None:
        self.spark = spark
        DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
        logger.info(f"Processed stage directory ready: {DATA_PROCESSED}")

    def _clean_nulls_and_nans(self, df: DataFrame) -> DataFrame:
        """Replace NaN with None for consistent null handling."""
        return df.select(
            [
                when(isnan(col(c)), None).otherwise(col(c)).alias(c)
                if c in [t[0] for t in df.dtypes if t[1].startswith("double")]
                else col(c)
                for c in df.columns
            ]
        )

    def process_artists(self, raw_artists: DataFrame) -> DataFrame:
        """Clean and validate artists data."""
        logger.info("Processing artists...")

        df = raw_artists.select(
            col("id").alias("artist_id"),
            col("name").alias("artist_name"),
            col("artist_popularity").alias("artist_popularity"),
            col("followers"),
            col("genres"),
            col("type"),
        )

        # Remove nulls in primary key
        df = df.filter(col("artist_id").isNotNull())
        logger.info(f"Removed null artist_ids, {df.count()} artists remaining")

        # Remove duplicates
        df = df.dropDuplicates(["artist_id"])
        logger.info(f"Removed duplicates, {df.count()} unique artists")

        # Clean nulls/NaNs
        df = self._clean_nulls_and_nans(df)

        return df

    def process_albums(self, raw_albums: DataFrame) -> DataFrame:
        """Clean and validate albums data."""
        logger.info("Processing albums...")

        df = raw_albums.select(
            col("id").alias("album_id"),
            col("name").alias("album_name"),
            col("album_type"),
            col("artist_id"),
            col("release_date"),
            col("release_date_precision"),
            col("total_tracks"),
            col("uri"),
        )

        # Remove nulls in primary key
        df = df.filter(col("album_id").isNotNull())
        logger.info(f"Removed null album_ids, {df.count()} albums remaining")

        # Remove duplicates
        df = df.dropDuplicates(["album_id"])
        logger.info(f"Removed duplicates, {df.count()} unique albums")

        # Clean nulls/NaNs
        df = self._clean_nulls_and_nans(df)

        return df

    def process_tracks(self, raw_tracks: DataFrame) -> DataFrame:
        """Clean and validate tracks data."""
        logger.info("Processing tracks...")

        df = raw_tracks.select(
            col("id").alias("track_id"),
            col("name").alias("track_name"),
            col("album_id"),
            col("artists_id"),
            col("popularity"),
            col("duration_ms"),
            col("explicit"),
            col("country"),
            col("playlist"),
            col("uri"),
            col("preview_url"),
            col("analysis_url"),
            col("href"),
            col("track_href"),
            col("available_markets"),
        )

        # Remove nulls in primary key
        df = df.filter(col("track_id").isNotNull())
        logger.info(f"Removed null track_ids, {df.count()} tracks remaining")

        # Remove duplicates
        df = df.dropDuplicates(["track_id"])
        logger.info(f"Removed duplicates, {df.count()} unique tracks")

        # Clean nulls/NaNs
        df = self._clean_nulls_and_nans(df)

        return df

    def process_track_features(
        self,
        raw_audio: DataFrame,
        raw_lyrics: DataFrame,
    ) -> DataFrame:
        """Combine and validate audio + lyrics features."""
        logger.info("Processing track features...")

        # Clean audio features
        audio = raw_audio.select(
            col("track_id"),
            *[
                col(c)
                for c in raw_audio.columns
                if c not in ["track_id", "Unnamed: 0"]
            ],
        )
        audio = audio.filter(col("track_id").isNotNull())
        audio = self._clean_nulls_and_nans(audio)

        # Clean lyrics features
        lyrics = raw_lyrics.select(
            col("track_id"),
            col("mean_syllables_word"),
            col("mean_words_sentence"),
            col("n_sentences"),
            col("n_words"),
            col("sentence_similarity"),
            col("vocabulary_wealth"),
        )
        lyrics = lyrics.filter(col("track_id").isNotNull())
        lyrics = self._clean_nulls_and_nans(lyrics)

        # Join audio + lyrics on track_id
        df = audio.join(lyrics, "track_id", "left")
        df = df.fillna(0)

        logger.info(f"Combined features for {df.count()} tracks")

        return df

    def run(
        self,
        raw_tracks: DataFrame,
        raw_artists: DataFrame,
        raw_albums: DataFrame,
        raw_audio: DataFrame,
        raw_lyrics: DataFrame,
    ) -> tuple[DataFrame, DataFrame, DataFrame, DataFrame]:
        """Process all raw data and save to processed stage."""
        logger.info("=" * 60)
        logger.info("PROCESSED STAGE: Cleaning & Validating Data")
        logger.info("=" * 60)

        artists = self.process_artists(raw_artists)
        logger.info(f"Saving {artists.count()} artists")
        artists.write.mode("overwrite").parquet(str(PROCESSED_ARTISTS))

        albums = self.process_albums(raw_albums)
        logger.info(f"Saving {albums.count()} albums")
        albums.write.mode("overwrite").parquet(str(PROCESSED_ALBUMS))

        tracks = self.process_tracks(raw_tracks)
        logger.info(f"Saving {tracks.count()} tracks")
        tracks.write.mode("overwrite").parquet(str(PROCESSED_TRACKS))

        track_features = self.process_track_features(raw_audio, raw_lyrics)
        logger.info(f"Saving {track_features.count()} track features")
        track_features.write.mode("overwrite").parquet(
            str(PROCESSED_TRACK_FEATURES)
        )

        logger.info("Processed stage completed successfully")
        return tracks, artists, albums, track_features
