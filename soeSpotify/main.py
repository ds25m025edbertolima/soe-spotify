# Sets up logging.
# Imports all ETL stages.
# Defines a function called run_etl_pipeline().
# Runs raw data loading.
# Runs data cleaning/processing.
# Runs analytics table creation.
# Loads results into PostgreSQL.

import logging
import sys

from .config import (
    PROCESSED_TRACKS,
    PROCESSED_ARTISTS,
    PROCESSED_ALBUMS,
    PROCESSED_TRACK_FEATURES,
)
from .stages.raw import RawStage
from .stages.processed import ProcessedStage
from .stages.analytics import AnalyticsStage
from .database import DatabaseLoader

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def run_etl_pipeline(
    load_to_database: bool = True,
) -> None:
    """Run complete ETL pipeline: raw → processed → analytics → database."""
    try:
        logger.info("\n" + "=" * 60)
        logger.info("STARTING SOE-SPOTIFY ETL PIPELINE")
        logger.info("=" * 60 + "\n")

        # RAW STAGE: Load CSVs → Raw Parquet
        logger.info("Step 1/4: RAW STAGE")
        raw_stage = RawStage()
        raw_tracks, raw_artists, raw_albums, raw_audio, raw_lyrics = raw_stage.run()

        # PROCESSED STAGE: Clean → Processed Parquet
        logger.info("\nStep 2/4: PROCESSED STAGE")
        processed_stage = ProcessedStage()
        (
            processed_tracks,
            processed_artists,
            processed_albums,
            processed_features,
        ) = processed_stage.run(
            raw_tracks, raw_artists, raw_albums, raw_audio, raw_lyrics
        )

        # ANALYTICS STAGE: Engineer Features → Analytics Parquet
        logger.info("\nStep 3/4: ANALYTICS STAGE")
        analytics_stage = AnalyticsStage()
        (
            analytics_tracks,
            analytics_artists,
            analytics_albums,
            analytics_genres,
            analytics_features,
        ) = analytics_stage.run(
            processed_tracks,
            processed_artists,
            processed_albums,
            processed_features,
        )

        # DATABASE STAGE: Load to PostgreSQL & Create Views
        if load_to_database:
            logger.info("\nStep 4/4: DATABASE SYNC")
            db_loader = DatabaseLoader()
            db_loader.run(
                analytics_artists,
                analytics_albums,
                analytics_tracks,
                analytics_genres,
                analytics_features,
            )
        else:
            logger.info(
                "\nStep 4/4: SKIPPED (--no-database flag set)"
            )

        logger.info("\n" + "=" * 60)
        logger.info("ETL PIPELINE COMPLETED SUCCESSFULLY!")
        logger.info("=" * 60 + "\n")

    except Exception as e:
        logger.error(f"\nETL PIPELINE FAILED: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Run SOE-Spotify ETL: Raw → Processed → Analytics"
    )
    parser.add_argument(
        "--no-database",
        action="store_true",
        help="Skip loading to PostgreSQL database",
    )

    args = parser.parse_args()

    run_etl_pipeline(
        load_to_database=not args.no_database,
    )
