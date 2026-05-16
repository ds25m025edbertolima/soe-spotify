import logging

import pandas as pd
from sqlalchemy import create_engine, text

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
        df: pd.DataFrame,
        table_name: str,
    ) -> None:
        """Load Pandas DataFrame to PostgreSQL table using append."""
        logger.info(f"Loading {len(df)} rows to {table_name}")

        # Write Pandas DataFrame to PostgreSQL
        df.to_sql(
            table_name,
            self.engine,
            if_exists="append",
            index=False,
            method="multi",
            chunksize=DB_BATCH_SIZE,
        )
        logger.info(f"Loaded {len(df)} rows to {table_name}")

    def truncate_tables(self) -> None:
        """Truncate all analytics tables in correct order."""
        logger.info("Truncating tables...")
        tables = ["genres", "track_features", "tracks", "albums", "artists"]
        with self.engine.connect() as conn:
            for table in tables:
                conn.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
            conn.commit()
        logger.info("Tables truncated")

    def create_schema(self) -> None:
        """Create home schema if it doesn't exist."""
        logger.info("Creating schema 'home'...")
        with self.engine.connect() as conn:
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS home"))
            conn.commit()
        logger.info("Schema 'home' ready")

    def create_base_views(self) -> None:
        """Create base views on analytics tables with explicit public schema reference."""
        logger.info("Creating base views...")

        views_sql = """
        -- Base views reference analytics tables in public schema
        CREATE OR REPLACE VIEW home.artists AS SELECT * FROM public.artists;
        CREATE OR REPLACE VIEW home.albums AS SELECT * FROM public.albums;
        CREATE OR REPLACE VIEW home.tracks AS SELECT * FROM public.tracks;
        CREATE OR REPLACE VIEW home.genres AS SELECT * FROM public.genres;
        CREATE OR REPLACE VIEW home.track_features AS SELECT * FROM public.track_features;
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
        SELECT COUNT(*) as total_artists FROM home.artists;

        -- V_1_2: Artists by Popularity
        CREATE OR REPLACE VIEW home.v_1_2_artists_popularity AS
        SELECT artist_name, artist_popularity, followers FROM home.artists
        ORDER BY artist_popularity DESC;

        -- V_1_3: Artists by Followers
        CREATE OR REPLACE VIEW home.v_1_3_artists_followers AS
        SELECT artist_name, followers, artist_popularity FROM home.artists
        ORDER BY followers DESC;

        -- V_1_4: Artist Summary
        CREATE OR REPLACE VIEW home.v_1_4_artist_summary AS
        SELECT artist_name, artist_popularity, followers FROM home.artists;

        -- V_1_5: Artist-Album Relationships
        CREATE OR REPLACE VIEW home.v_1_5_artist_albums AS
        SELECT ar.artist_id, ar.artist_name, ar.followers as artist_followers,
               ar.artist_popularity, ab.album_id, ab.album_name, ab.release_date,
               ab.total_tracks, ab.album_type
        FROM home.artists ar
        LEFT JOIN home.albums ab ON ar.artist_id = ab.artist_id;

        -- V_1_6: Artist-Genre Relationships
        CREATE OR REPLACE VIEW home.v_1_6_artist_genres AS
        SELECT ar.artist_name, ar.followers, ar.artist_popularity, ge.genre
        FROM home.artists ar
        JOIN home.genres ge ON ar.artist_id = ge.artist_id;

        -- V_3_1: Track Features Full
        CREATE OR REPLACE VIEW home.v_3_1_track_features_full AS
        SELECT tr.track_id, tr.artist_name, tr.album_name, tr.track_name,
               tr.track_popularity, tf.danceability, tf.energy, tf.loudness,
               tf.speechiness, tf.acousticness, tf.instrumentalness, tf.liveness,
               tf.valence, tf.tempo, tr.duration_ms, tf.time_signature, tf.key, tf.mode
        FROM home.tracks tr
        LEFT JOIN home.track_features tf ON tr.track_id = tf.track_id;

        -- V_1_7: Artist-Track Analysis
        CREATE OR REPLACE VIEW home.v_1_7_artist_tracks AS
        SELECT ar.artist_name, ar.followers, ar.artist_popularity, tr.track_id,
               tr.track_name, tr.track_popularity, tf.danceability, tf.energy,
               tf.tempo, tf.valence
        FROM home.artists ar
        LEFT JOIN home.tracks tr ON ar.artist_id = tr.artists_id
        LEFT JOIN home.track_features tf ON tr.track_id = tf.track_id;

        -- V_2_1: Album-Track Analysis
        CREATE OR REPLACE VIEW home.v_2_1_album_tracks AS
        SELECT ab.album_name, ab.release_date, ab.total_tracks, ab.album_type,
               ar.artist_name, tr.track_id, tr.track_name, tr.track_popularity,
               tf.danceability, tf.energy, tf.tempo, tf.valence
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
        artists: pd.DataFrame,
        albums: pd.DataFrame,
        tracks: pd.DataFrame,
        genres: pd.DataFrame,
        features: pd.DataFrame,
    ) -> None:
        """Load all analytics data and create views."""
        logger.info("=" * 60)
        logger.info("DATABASE SYNC: Loading Analytics → PostgreSQL")
        logger.info("=" * 60)

        # 1. Truncate existing data (preserving table structures/PKs/FKs)
        try:
            self.truncate_tables()
        except Exception as e:
            logger.warning(f"Truncate failed (tables might not exist yet): {e}")
            logger.info("Creating schema and views first...")

        # 2. Ensure schema and views exist (in case they were dropped)
        self.create_schema()
        self.create_base_views()
        self.create_analysis_views()

        # 3. Load data using append
        self.load_dataframe_to_postgres(artists, "artists")
        self.load_dataframe_to_postgres(albums, "albums")
        self.load_dataframe_to_postgres(tracks, "tracks")
        self.load_dataframe_to_postgres(genres, "genres")
        self.load_dataframe_to_postgres(features, "track_features")

        logger.info("Database sync completed successfully")
