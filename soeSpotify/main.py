import logging
import sys
from typing import Optional

from .etl import SpotifyETL
from .database import DatabaseLoader

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def run_etl_pipeline(
    load_to_database: bool = True,
    skip_delete: bool = False,
) -> None:
    etl = SpotifyETL()
    loader = None

    try:
        logger.info("Starting ETL pipeline...")

        tracks, artists, albums = etl.run_full_etl()

        if load_to_database:
            logger.info("Initializing database loader...")
            loader = DatabaseLoader()

            if not skip_delete:
                logger.info("Clearing existing database tables...")
                loader.clear_table("tracks")
                loader.clear_table("artists")
                loader.clear_table("albums")

            logger.info("Loading data to database...")
            loader.load_artists(artists)
            loader.load_albums(albums)
            loader.load_tracks(tracks)

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
        description="Run Spotify ETL pipeline with Spark and PostgreSQL"
    )
    parser.add_argument(
        "--no-database",
        action="store_true",
        help="Skip loading to database (for testing)",
    )
    parser.add_argument(
        "--skip-delete",
        action="store_true",
        help="Skip deleting existing database tables",
    )

    args = parser.parse_args()

    run_etl_pipeline(
        load_to_database=not args.no_database,
        skip_delete=args.skip_delete,
    )
