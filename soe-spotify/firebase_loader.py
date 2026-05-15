import logging
from typing import Any, Generator

import firebase_admin
from firebase_admin import credentials, firestore
from pyspark.sql import DataFrame

from soe_spotify.config import (
    FIREBASE_CREDENTIALS,
    FIREBASE_STORAGE_BUCKET,
    FIRESTORE_BATCH_SIZE,
    COLLECTION_TRACKS,
    COLLECTION_ARTISTS,
    COLLECTION_ALBUMS,
)

logger = logging.getLogger(__name__)


class FirebaseLoader:
    def __init__(self) -> None:
        self._initialize_firebase()
        self.db = firestore.client()

    def _initialize_firebase(self) -> None:
        if not firebase_admin._apps:
            cred = credentials.Certificate(str(FIREBASE_CREDENTIALS))
            firebase_admin.initialize_app(
                cred, {"storageBucket": FIREBASE_STORAGE_BUCKET}
            )
            logger.info("Firebase initialized")
        else:
            logger.info("Firebase already initialized")

    def _batch_rows(
        self, rows: list[dict[str, Any]], batch_size: int
    ) -> Generator[list[dict[str, Any]], None, None]:
        for i in range(0, len(rows), batch_size):
            yield rows[i : i + batch_size]

    def _clean_row(self, row: dict[str, Any]) -> dict[str, Any]:
        cleaned = {}
        for key, value in row.items():
            if value is None or (isinstance(value, float) and value != value):
                cleaned[key] = None
            elif isinstance(value, (int, float, str, bool)):
                cleaned[key] = value
            else:
                cleaned[key] = str(value)
        return cleaned

    def load_dataframe(
        self,
        df: DataFrame,
        collection: str,
        document_id_col: str = "track_id",
    ) -> None:
        rows = df.toJSON().map(lambda x: eval(x)).collect()

        total_rows = len(rows)
        logger.info(f"Loading {total_rows} documents to '{collection}' collection")

        for batch_num, batch in enumerate(
            self._batch_rows(rows, FIRESTORE_BATCH_SIZE), 1
        ):
            batch_ref = self.db.batch()
            for row in batch:
                row = self._clean_row(row)
                doc_id = str(row.pop(document_id_col, None))
                if doc_id and doc_id != "None":
                    doc_ref = self.db.collection(collection).document(doc_id)
                    batch_ref.set(doc_ref, row)

            batch_ref.commit()
            logger.info(
                f"Batch {batch_num} committed "
                f"({min(batch_num * FIRESTORE_BATCH_SIZE, total_rows)}/{total_rows})"
            )

    def load_tracks(self, df: DataFrame) -> None:
        self.load_dataframe(df, COLLECTION_TRACKS, "track_id")
        logger.info(f"Loaded tracks to '{COLLECTION_TRACKS}' collection")

    def load_artists(self, df: DataFrame) -> None:
        self.load_dataframe(df, COLLECTION_ARTISTS, "artist_id")
        logger.info(f"Loaded artists to '{COLLECTION_ARTISTS}' collection")

    def load_albums(self, df: DataFrame) -> None:
        self.load_dataframe(df, COLLECTION_ALBUMS, "album_id")
        logger.info(f"Loaded albums to '{COLLECTION_ALBUMS}' collection")

    def verify_collection(self, collection: str) -> tuple[int, int]:
        docs = self.db.collection(collection).limit(1).stream()
        count = 0
        for _ in self.db.collection(collection).stream():
            count += 1
        logger.info(f"Collection '{collection}' contains {count} documents")
        return count

    def delete_collection(self, collection: str, batch_size: int = 100) -> None:
        docs = self.db.collection(collection).limit(batch_size).stream()
        deleted = 0

        for doc in docs:
            doc.reference.delete()
            deleted += 1

        if deleted >= batch_size:
            return self.delete_collection(collection, batch_size)

        logger.info(f"Deleted {deleted} documents from '{collection}'")
