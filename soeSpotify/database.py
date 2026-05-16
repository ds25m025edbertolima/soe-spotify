import logging

from sqlalchemy import create_engine, text
from pyspark.sql import DataFrame

from .config import DATABASE_URL, DB_BATCH_SIZE

logger = logging.getLogger(__name__)


class DatabaseLoader:
    """Load analytics parquet data to PostgreSQL and create views."""

    def __init__(self, database_url: str = DATABASE_URL) -> None:
        self.engine = create_engine(
            database_url,
            echo=False,
            future=True,
            pool_pre_ping=True,
        )
        logger.info("Database connection established")

    def load_dataframe_to_postgres(
        self,
        df: DataFrame,
        table_name: str,
    ) -> None:
        """Load Spark DataFrame to PostgreSQL table."""
        logger.info(f"Loading {df.count()} rows to {table_name}")

        # Convert to Pandas and write to PostgreSQL
        pdf = df.toPandas()
        pdf.to_sql(
            table_name,
            self.engine,
            if_exists="replace",
            index=False,
            method="multi",
            chunksize=DB_BATCH_SIZE,
        )
        logger.info(f"Loaded {len(pdf)} rows to {table_name}")

    def create_base_views(self) -> None:
        """Create base views on analytics tables."""
        logger.info("Creating base views...")

        views_sql = """
        -- Base views reference analytics tables
        CREATE OR REPLACE VIEW home.artists AS
        SELECT * FROM artists;

        CREATE OR REPLACE VIEW home.albums AS
        SELECT * FROM albums;

        CREATE OR REPLACE VIEW home.tracks AS
        SELECT * FROM tracks;

        CREATE OR REPLACE VIEW home.genres AS
        SELECT * FROM genres;

        CREATE OR REPLACE VIEW home.track_features AS
        SELECT * FROM track_features;
        """

        with self.engine.connect() as conn:
            for statement in views_sql.split(";"):
                if statement.strip():
                    conn.execute(text(statement))
            conn.commit()

        logger.info("Base views created")

    def create_analysis_views(self) -> None:
        """Create analysis views."""
        logger.info("Creating analysis views...")

        views_sql = """
        -- V_1_1: Total Artists
        CREATE OR REPLACE VIEW home.v_1_1_total_artists AS
        SELECT COUNT(*) as total_artists
        FROM home.artists;

        -- V_1_2: Artists by Popularity
        CREATE OR REPLACE VIEW home.v_1_2_artists_popularity AS
        SELECT artist_name,
               artist_popularity,
               followers
        FROM home.artists
        ORDER BY artist_popularity DESC;

        -- V_1_3: Artists by Followers
        CREATE OR REPLACE VIEW home.v_1_3_artists_followers AS
        SELECT artist_name,
               followers,
               artist_popularity
        FROM home.artists
        ORDER BY followers DESC;

        -- V_1_4: Artist Summary
        CREATE OR REPLACE VIEW home.v_1_4_artist_summary AS
        SELECT artist_name,
               artist_popularity,
               followers
        FROM home.artists;

        -- V_1_5: Artist-Album Relationships
        CREATE OR REPLACE VIEW home.v_1_5_artist_albums AS
        SELECT ar.artist_id,
               ar.artist_name,
               ar.followers as artist_followers,
               ar.artist_popularity,
               ab.album_id,
               ab.album_name,
               ab.release_date,
               ab.total_tracks,
               ab.album_type
        FROM home.artists ar
        LEFT JOIN home.albums ab ON ar.artist_id = ab.artist_id;

        -- V_1_6: Artist-Genre Relationships
        CREATE OR REPLACE VIEW home.v_1_6_artist_genres AS
        SELECT ar.artist_name,
               ar.followers,
               ar.artist_popularity,
               ge.genre
        FROM home.artists ar
        JOIN home.genres ge ON ar.artist_id = ge.artist_id;

        -- V_3_1: Track Features Full
        CREATE OR REPLACE VIEW home.v_3_1_track_features_full AS
        SELECT tr.track_id,
               tr.artist_name,
               tr.album_name,
               tr.track_name,
               tr.track_popularity,
               tf.danceability,
               tf.energy,
               tf.loudness,
               tf.speechiness,
               tf.acousticness,
               tf.instrumentalness,
               tf.liveness,
               tf.valence,
               tf.tempo,
               tf.duration_ms,
               tf.time_signature,
               tf.key,
               tf.mode
        FROM home.tracks tr
        LEFT JOIN home.track_features tf ON tr.track_id = tf.track_id;

        -- V_1_7: Artist-Track Analysis
        CREATE OR REPLACE VIEW home.v_1_7_artist_tracks AS
        SELECT ar.artist_name,
               ar.followers,
               ar.artist_popularity,
               tf.track_id,
               tf.track_name,
               tf.track_popularity,
               tf.danceability,
               tf.energy,
               tf.tempo,
               tf.valence
        FROM home.artists ar
        LEFT JOIN home.v_3_1_track_features_full tf
          ON ar.artist_id = tf.artist_id;

        -- V_2_1: Album-Track Analysis
        CREATE OR REPLACE VIEW home.v_2_1_album_tracks AS
        SELECT ab.album_name,
               ab.release_date,
               ab.total_tracks,
               ab.album_type,
               ar.artist_name,
               tr.track_id,
               tr.track_name,
               tr.track_popularity,
               tf.danceability,
               tf.energy,
               tf.tempo,
               tf.valence
        FROM home.albums ab
        LEFT JOIN home.artists ar ON ab.artist_id = ar.artist_id
        LEFT JOIN home.tracks tr ON ab.album_id = tr.album_id
        LEFT JOIN home.track_features tf ON tr.track_id = tf.track_id;
        """

        with self.engine.connect() as conn:
            for statement in views_sql.split(";"):
                if statement.strip():
                    conn.execute(text(statement))
            conn.commit()

        logger.info("Analysis views created")

    def run(
        self,
        artists: DataFrame,
        albums: DataFrame,
        tracks: DataFrame,
        genres: DataFrame,
        features: DataFrame,
    ) -> None:
        """Load all analytics data and create views."""
        logger.info("=" * 60)
        logger.info("DATABASE SYNC: Loading Analytics → PostgreSQL")
        logger.info("=" * 60)

        self.load_dataframe_to_postgres(artists, "artists")
        self.load_dataframe_to_postgres(albums, "albums")
        self.load_dataframe_to_postgres(tracks, "tracks")
        self.load_dataframe_to_postgres(genres, "genres")
        self.load_dataframe_to_postgres(features, "track_features")

        self.create_base_views()
        self.create_analysis_views()

        logger.info("Database sync completed successfully")
