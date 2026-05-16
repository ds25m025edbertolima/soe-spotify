import logging

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import col, collect_list, explode

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

    def __init__(self, spark: SparkSession) -> None:
        self.spark = spark
        DATA_ANALYTICS.mkdir(parents=True, exist_ok=True)
        logger.info(f"Analytics stage directory ready: {DATA_ANALYTICS}")

    def build_analytics_artists(self, artists: DataFrame) -> DataFrame:
        """Create business-ready artists table."""
        logger.info("Building analytics artists table...")

        df = artists.select(
            col("artist_id"),
            col("artist_name"),
            col("artist_popularity"),
            col("followers"),
            col("type"),
            col("genres"),
        )

        return df

    def build_analytics_albums(
        self, albums: DataFrame, artists: DataFrame
    ) -> DataFrame:
        """Create denormalized albums table with artist info."""
        logger.info("Building analytics albums table...")

        # Select and rename artist columns to avoid conflicts
        artists_cols = {c: f"artist_{c}" for c in artists.columns}
        artists_renamed = artists.select(
            [col(c).alias(artists_cols[c]) for c in artists.columns]
        )

        # Join albums with artists
        df = (
            albums.join(
                artists_renamed,
                albums["artist_id"] == artists_renamed["artist_artist_id"],
                "left",
            )
            .select(
                col("album_id"),
                col("album_name"),
                col("album_type"),
                col("release_date"),
                col("total_tracks"),
                col("uri"),
                col("artist_id"),
                col("artist_artist_name").alias("artist_name"),
                col("artist_followers"),
                col("artist_artist_popularity").alias("artist_popularity"),
            )
        )

        return df

    def build_analytics_tracks(
        self,
        tracks: DataFrame,
        artists: DataFrame,
        albums: DataFrame,
        features: DataFrame,
    ) -> DataFrame:
        """Create denormalized tracks table with full context."""
        logger.info("Building analytics tracks table...")

        # Join tracks with features
        df = tracks.join(features, "track_id", "left")

        # Rename artist columns to avoid conflicts
        artists_renamed = artists.select(
            [col(c).alias(f"artist_{c}") for c in artists.columns]
        )
        df = df.join(
            artists_renamed,
            df["artists_id"] == artists_renamed["artist_artist_id"],
            "left",
        )

        # Rename album columns
        albums_renamed = albums.select(
            [col(c).alias(f"album_{c}") for c in albums.columns]
        )
        df = df.join(
            albums_renamed,
            df["album_id"] == albums_renamed["album_album_id"],
            "left",
        )

        # Select final columns
        df = df.select(
            col("track_id"),
            col("track_name"),
            col("popularity").alias("track_popularity"),
            col("duration_ms"),
            col("explicit"),
            col("preview_url"),
            col("uri"),
            col("album_id"),
            col("album_album_name").alias("album_name"),
            col("album_album_type"),
            col("album_release_date"),
            col("artists_id"),
            col("artist_artist_name").alias("artist_name"),
            col("artist_artist_popularity"),
            col("artist_followers"),
            col("artist_genres"),
            # Audio features
            col("acousticness"),
            col("danceability"),
            col("energy"),
            col("instrumentalness"),
            col("key"),
            col("liveness"),
            col("loudness"),
            col("mode"),
            col("speechiness"),
            col("tempo"),
            col("time_signature"),
            col("valence"),
            # Lyrics features
            col("mean_syllables_word"),
            col("mean_words_sentence"),
            col("n_sentences"),
            col("n_words"),
            col("sentence_similarity"),
            col("vocabulary_wealth"),
        )

        return df

    def build_analytics_genres(self, artists: DataFrame) -> DataFrame:
        """Create genres mapping table (artist_id → genre)."""
        logger.info("Building analytics genres table...")

        # Explode genres array into individual rows
        df = (
            artists.select(
                col("artist_id"),
                col("artist_name"),
                col("genres"),
            )
            .filter(col("genres").isNotNull())
            .select(
                col("artist_id"),
                col("artist_name"),
                explode(col("genres")).alias("genre"),
            )
        )

        logger.info(f"Created {df.count()} genre mappings")

        return df

    def build_analytics_track_features(self, tracks: DataFrame) -> DataFrame:
        """Create feature matrix for ML models."""
        logger.info("Building analytics track features table...")

        # Select feature columns
        feature_cols = [
            "track_id",
            "artist_name",
            "album_name",
            "acousticness",
            "danceability",
            "energy",
            "instrumentalness",
            "key",
            "liveness",
            "loudness",
            "mode",
            "speechiness",
            "tempo",
            "time_signature",
            "valence",
            "track_popularity",
            "duration_ms",
            "mean_syllables_word",
            "mean_words_sentence",
            "n_sentences",
            "n_words",
            "sentence_similarity",
            "vocabulary_wealth",
        ]

        df = tracks.select([col(c) for c in feature_cols if c in tracks.columns])

        return df

    def run(
        self,
        tracks: DataFrame,
        artists: DataFrame,
        albums: DataFrame,
        features: DataFrame,
    ) -> tuple[DataFrame, DataFrame, DataFrame, DataFrame, DataFrame]:
        """Build all analytics tables."""
        logger.info("=" * 60)
        logger.info("ANALYTICS STAGE: Feature Engineering & Denormalization")
        logger.info("=" * 60)

        analytics_artists = self.build_analytics_artists(artists)
        logger.info(f"Saving {analytics_artists.count()} analytics artists")
        analytics_artists.write.mode("overwrite").parquet(
            str(ANALYTICS_ARTISTS)
        )

        analytics_albums = self.build_analytics_albums(albums, artists)
        logger.info(f"Saving {analytics_albums.count()} analytics albums")
        analytics_albums.write.mode("overwrite").parquet(str(ANALYTICS_ALBUMS))

        analytics_tracks = self.build_analytics_tracks(
            tracks, artists, albums, features
        )
        logger.info(f"Saving {analytics_tracks.count()} analytics tracks")
        analytics_tracks.write.mode("overwrite").parquet(str(ANALYTICS_TRACKS))

        analytics_genres = self.build_analytics_genres(artists)
        logger.info(f"Saving {analytics_genres.count()} analytics genres")
        analytics_genres.write.mode("overwrite").parquet(str(ANALYTICS_GENRES))

        analytics_features = self.build_analytics_track_features(analytics_tracks)
        logger.info(f"Saving {analytics_features.count()} feature records")
        analytics_features.write.mode("overwrite").parquet(
            str(ANALYTICS_TRACK_FEATURES)
        )

        logger.info("Analytics stage completed successfully")
        return (
            analytics_tracks,
            analytics_artists,
            analytics_albums,
            analytics_genres,
            analytics_features,
        )
