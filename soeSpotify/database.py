import logging
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from pyspark.sql import DataFrame

from .config import DATABASE_URL, DB_BATCH_SIZE

logger = logging.getLogger(__name__)


class DatabaseLoader:
    def __init__(self, database_url: str = DATABASE_URL) -> None:
        self.engine = create_engine(
            database_url, echo=False, future=True, pool_pre_ping=True
        )
        self.Session = sessionmaker(bind=self.engine)
        self._initialize_database()
        logger.info("Database initialized")

    def _initialize_database(self) -> None:
        with self.engine.connect() as conn:
            conn.execute(
                text("""
                    CREATE TABLE IF NOT EXISTS artists (
                        artist_id TEXT PRIMARY KEY,
                        artist_name TEXT NOT NULL,
                        popularity INTEGER,
                        followers INTEGER,
                        genres TEXT,
                        type TEXT
                    )
                """)
            )
            conn.execute(
                text("""
                    CREATE TABLE IF NOT EXISTS albums (
                        album_id TEXT PRIMARY KEY,
                        album_name TEXT NOT NULL,
                        album_type TEXT,
                        artist_id TEXT,
                        release_date TEXT,
                        release_date_precision TEXT,
                        total_tracks INTEGER,
                        uri TEXT
                    )
                """)
            )
            conn.execute(
                text("""
                    CREATE TABLE IF NOT EXISTS tracks (
                        track_id TEXT PRIMARY KEY,
                        track_name TEXT NOT NULL,
                        album_id TEXT,
                        artists_id TEXT,
                        popularity INTEGER,
                        duration_ms INTEGER,
                        explicit BOOLEAN,
                        country TEXT,
                        playlist TEXT,
                        acousticness FLOAT,
                        danceability FLOAT,
                        energy FLOAT,
                        instrumentalness FLOAT,
                        key INTEGER,
                        liveness FLOAT,
                        loudness FLOAT,
                        mode INTEGER,
                        speechiness FLOAT,
                        tempo FLOAT,
                        time_signature INTEGER,
                        valence FLOAT,
                        uri TEXT,
                        preview_url TEXT,
                        analysis_url TEXT,
                        href TEXT,
                        track_href TEXT,
                        available_markets TEXT,
                        mean_syllables_word FLOAT,
                        mean_words_sentence FLOAT,
                        n_sentences INTEGER,
                        n_words INTEGER,
                        sentence_similarity FLOAT,
                        vocabulary_wealth FLOAT
                    )
                """)
            )
            conn.commit()
            logger.info("Database tables created/verified")

    def _clean_row(self, row: dict[str, Any]) -> dict[str, Any]:
        cleaned = {}
        for key, value in row.items():
            if value is None or (isinstance(value, float) and value != value):
                cleaned[key] = None
            else:
                cleaned[key] = value
        return cleaned

    def load_dataframe(
        self,
        df: DataFrame,
        table_name: str,
    ) -> None:
        logger.info(f"Loading data to '{table_name}' table")

        rows_processed = 0
        batch_rows = []

        for row in df.toLocalIterator():
            row_dict = row.asDict()
            batch_rows.append(self._clean_row(row_dict))

            if len(batch_rows) >= DB_BATCH_SIZE:
                rows_processed += self._commit_batch(batch_rows, table_name)
                batch_rows = []

        if batch_rows:
            rows_processed += self._commit_batch(batch_rows, table_name)

        logger.info(
            f"Loaded {rows_processed} rows to '{table_name}' table"
        )

    def _commit_batch(
        self, batch_rows: list[dict[str, Any]], table_name: str
    ) -> int:
        try:
            with self.engine.connect() as conn:
                for row in batch_rows:
                    placeholders = ", ".join([f":{k}" for k in row.keys()])
                    columns = ", ".join(row.keys())
                    query = f"""
                        INSERT INTO {table_name} ({columns})
                        VALUES ({placeholders})
                        ON CONFLICT (
                            {self._get_primary_key(table_name)}
                        ) DO UPDATE SET
                        {self._get_update_clause(row)}
                    """
                    conn.execute(text(query), row)
                conn.commit()
            logger.info(f"Batch committed ({len(batch_rows)} rows)")
            return len(batch_rows)
        except Exception as e:
            logger.error(f"Error committing batch to '{table_name}': {e}")
            raise

    def _get_primary_key(self, table_name: str) -> str:
        pk_map = {
            "tracks": "track_id",
            "artists": "artist_id",
            "albums": "album_id",
        }
        return pk_map.get(table_name, "id")

    def _get_update_clause(self, row: dict[str, Any]) -> str:
        pk = self._get_primary_key("tracks")
        cols = [k for k in row.keys() if k != pk]
        return ", ".join([f"{col} = EXCLUDED.{col}" for col in cols])

    def load_tracks(self, df: DataFrame) -> None:
        self.load_dataframe(df, "tracks")
        logger.info("Tracks loaded successfully")

    def load_artists(self, df: DataFrame) -> None:
        self.load_dataframe(df, "artists")
        logger.info("Artists loaded successfully")

    def load_albums(self, df: DataFrame) -> None:
        self.load_dataframe(df, "albums")
        logger.info("Albums loaded successfully")

    def verify_collection(self, table_name: str) -> int:
        with self.engine.connect() as conn:
            result = conn.execute(
                text(f"SELECT COUNT(*) as count FROM {table_name}")
            )
            count = result.fetchone()[0]
        logger.info(f"Table '{table_name}' contains {count} rows")
        return count

    def clear_table(self, table_name: str) -> None:
        with self.engine.connect() as conn:
            conn.execute(text(f"TRUNCATE TABLE {table_name} RESTART IDENTITY"))
            conn.commit()
        logger.info(f"Table '{table_name}' cleared")
