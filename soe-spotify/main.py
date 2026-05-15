import logging
import sys
from typing import Optional

from soe_spotify.etl import SpotifyETL
from soe_spotify.firebase_loader import FirebaseLoader

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def run_etl_pipeline(
    load_to_firebase: bool = True,
    skip_delete: bool = False,
) -> None:
    etl = SpotifyETL()
    loader = None

    try:
        logger.info("Starting ETL pipeline...")

        tracks, artists, albums = etl.run_full_etl()

        if load_to_firebase:
            logger.info("Initializing Firebase loader...")
            loader = FirebaseLoader()

            if not skip_delete:
                logger.info("Clearing existing Firestore collections...")
                loader.delete_collection("tracks")
                loader.delete_collection("artists")
                loader.delete_collection("albums")

            logger.info("Loading data to Firestore...")
            loader.load_tracks(tracks)
            loader.load_artists(artists)
            loader.load_albums(albums)

            logger.info("Verifying loaded data...")
            loader.verify_collection("tracks")
            loader.verify_collection("artists")
            loader.verify_collection("albums")

        logger.info("ETL pipeline completed successfully!")

    except Exception as e:
        logger.error(f"ETL pipeline failed: {e}", exc_info=True)
        sys.exit(1)

    finally:
        etl.stop()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Run Spotify ETL pipeline with Spark and Firebase"
    )
    parser.add_argument(
        "--no-firebase",
        action="store_true",
        help="Skip loading to Firebase (for testing)",
    )
    parser.add_argument(
        "--skip-delete",
        action="store_true",
        help="Skip deleting existing Firestore collections",
    )

    args = parser.parse_args()

    run_etl_pipeline(
        load_to_firebase=not args.no_firebase,
        skip_delete=args.skip_delete,
    )
