# Starts a Spark session.
# Loads Spotify CSV files.
# Selects and renames useful columns.
# Removes rows without important IDs.
# Joins tracks with audio features and lyrics features.
# Joins tracks with artist and album information.
# Returns final enriched track data, artists data, and albums data.

import logging
from typing import Optional

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import (
    col,
    split,
    trim,
    when,
    isnan,
    isnull,
    coalesce,
    collect_list,
    struct,
)

from .config import (
    SPARK_MASTER,
    SPARK_APP_NAME,
    SPARK_LOG_LEVEL,
    SPARK_DRIVER_JAVA_OPTIONS,
    CSV_ALBUMS,
    CSV_ARTISTS,
    CSV_TRACKS,
    CSV_AUDIO_FEATURES,
    CSV_LYRICS_FEATURES,
)

logger = logging.getLogger(__name__)


class SpotifyETL:
    def __init__(self) -> None:
        self.spark = self._create_spark_session()

    def _create_spark_session(self) -> SparkSession:
        spark = (
            SparkSession.builder.master(SPARK_MASTER)
            .appName(SPARK_APP_NAME)
            .config("spark.sql.legacy.timeParserPolicy", "LEGACY")
            .config("spark.driver.extraJavaOptions", SPARK_DRIVER_JAVA_OPTIONS)
            .config("spark.executor.extraJavaOptions", SPARK_DRIVER_JAVA_OPTIONS)
            .getOrCreate()
        )
        spark.sparkContext.setLogLevel(SPARK_LOG_LEVEL)
        logger.info("Spark session created")
        return spark

    def load_tracks(self) -> DataFrame:
        df = self.spark.read.csv(str(CSV_TRACKS), header=True, inferSchema=True)
        logger.info(f"Loaded tracks: {df.count()} rows")
        return df

    def load_artists(self) -> DataFrame:
        df = self.spark.read.csv(str(CSV_ARTISTS), header=True, inferSchema=True)
        logger.info(f"Loaded artists: {df.count()} rows")
        return df

    def load_albums(self) -> DataFrame:
        df = self.spark.read.csv(str(CSV_ALBUMS), header=True, inferSchema=True)
        logger.info(f"Loaded albums: {df.count()} rows")
        return df

    def load_audio_features(self) -> DataFrame:
        df = self.spark.read.csv(
            str(CSV_AUDIO_FEATURES), header=True, inferSchema=True
        )
        logger.info(f"Loaded audio features: {df.count()} rows, {len(df.columns)} "
                    "columns")
        return df

    def load_lyrics_features(self) -> DataFrame:
        df = self.spark.read.csv(
            str(CSV_LYRICS_FEATURES), header=True, inferSchema=True
        )
        logger.info(f"Loaded lyrics features: {df.count()} rows")
        return df

    def transform_artists(self, df: DataFrame) -> DataFrame:
        df = df.select(
            col("id").alias("artist_id"),
            col("name").alias("artist_name"),
            col("artist_popularity").alias("popularity"),
            col("followers"),
            col("genres"),
            col("type"),
        )
        df = df.filter(col("artist_id").isNotNull())
        logger.info("Transformed artists")
        return df

    def transform_albums(self, df: DataFrame) -> DataFrame:
        df = df.select(
            col("id").alias("album_id"),
            col("name").alias("album_name"),
            col("album_type"),
            col("artist_id"),
            col("release_date"),
            col("release_date_precision"),
            col("total_tracks"),
            col("uri"),
        )
        df = df.filter(col("album_id").isNotNull())
        logger.info("Transformed albums")
        return df

    def transform_tracks(self, df: DataFrame) -> DataFrame:
        # Define columns to select with their aliases
        cols_specs = [
            ("id", "track_id"),
            ("name", "track_name"),
            ("album_id", None),
            ("artists_id", None),
            ("popularity", None),
            ("duration_ms", None),
            ("explicit", None),
            ("country", None),
            ("playlist", None),
            ("acousticness", None),
            ("danceability", None),
            ("energy", None),
            ("instrumentalness", None),
            ("key", None),
            ("liveness", None),
            ("loudness", None),
            ("mode", None),
            ("speechiness", None),
            ("tempo", None),
            ("time_signature", None),
            ("valence", None),
            ("uri", None),
            ("preview_url", None),
            ("analysis_url", None),
            ("href", None),
            ("track_href", None),
            ("available_markets", None),
        ]

        # Select only columns that exist, applying casts and aliases
        selections = []
        for source, alias in cols_specs:
            if source in df.columns:
                c = col(source)
                if source == "explicit":
                    c = c.cast("boolean")
                if alias:
                    c = c.alias(alias)
                selections.append(c)

        df = df.select(*selections)
        df = df.filter(col("track_id").isNotNull())
        logger.info("Transformed tracks")
        return df

    def transform_audio_features(self, df: DataFrame) -> DataFrame:
        df = df.select(
            col("track_id"),
            *[col(c) for c in df.columns if c != "track_id" and c != "Unnamed: 0"],
        )
        df = df.filter(col("track_id").isNotNull())
        logger.info("Transformed audio features")
        return df

    def transform_lyrics_features(self, df: DataFrame) -> DataFrame:
        df = df.select(
            col("track_id"),
            col("mean_syllables_word"),
            col("mean_words_sentence"),
            col("n_sentences"),
            col("n_words"),
            col("sentence_similarity"),
            col("vocabulary_wealth"),
        )
        df = df.filter(col("track_id").isNotNull())
        logger.info("Transformed lyrics features")
        return df

    def join_track_features(
        self, tracks: DataFrame, audio: DataFrame, lyrics: DataFrame
    ) -> DataFrame:
        # Drop popularity from audio if it exists to avoid conflict with track
        # popularity
        audio_cols = [c for c in audio.columns if c != "popularity"]
        audio = audio.select(*audio_cols)

        df = (
            tracks.join(audio, "track_id", "left")
            .join(lyrics, "track_id", "left")
            .fillna(0)
        )
        logger.info(f"Joined track features: {df.count()} rows")
        return df

    def join_with_artists(
        self, tracks: DataFrame, artists: DataFrame
    ) -> DataFrame:
        # Rename all artist columns to avoid conflicts with track columns
        artist_cols = {c: f"artist_{c}" for c in artists.columns}
        artists_renamed = artists.select(
            [col(c).alias(artist_cols[c]) for c in artists.columns]
        )
        df = tracks.join(
            artists_renamed,
            tracks["artists_id"] == artists_renamed["artist_artist_id"],
            "left",
        )
        logger.info(f"Joined with artists: {df.count()} rows")
        return df

    def join_with_albums(
        self, tracks: DataFrame, albums: DataFrame
    ) -> DataFrame:
        # Rename all album columns except album_id to avoid conflicts
        album_cols = {c: f"album_{c}" for c in albums.columns if c != "album_id"}
        renames = [(c, album_cols[c]) if c in album_cols else c for c in albums.columns]
        albums_renamed = albums.select(
            [col(c).alias(album_cols.get(c, c)) for c in albums.columns]
        )
        df = tracks.join(albums_renamed, "album_id", "left")
        logger.info(f"Joined with albums: {df.count()} rows")
        return df

    def run_full_etl(self) -> tuple[DataFrame, DataFrame, DataFrame]:
        artists = self.load_artists()
        artists = self.transform_artists(artists)

        albums = self.load_albums()
        albums = self.transform_albums(albums)

        tracks = self.load_tracks()
        tracks = self.transform_tracks(tracks)

        audio = self.load_audio_features()
        audio = self.transform_audio_features(audio)

        lyrics = self.load_lyrics_features()
        lyrics = self.transform_lyrics_features(lyrics)

        enriched_tracks = self.join_track_features(tracks, audio, lyrics)
        enriched_tracks = self.join_with_artists(enriched_tracks, artists)
        enriched_tracks = self.join_with_albums(enriched_tracks, albums)

        logger.info("ETL pipeline completed successfully")
        return enriched_tracks, artists, albums

    def stop(self) -> None:
        self.spark.stop()
        logger.info("Spark session stopped")
