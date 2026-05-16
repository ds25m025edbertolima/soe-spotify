import logging
import sys

from pyspark.sql import SparkSession

from .config import (
    SPARK_MASTER,
    SPARK_APP_NAME,
    SPARK_LOG_LEVEL,
    SPARK_DRIVER_JAVA_OPTIONS,
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


def create_spark_session() -> SparkSession:
    """Create and configure Spark session."""
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


def run_etl_pipeline(
    load_to_database: bool = True,
) -> None:
    """Run complete ETL pipeline: raw → processed → analytics → database."""
    spark = create_spark_session()

    try:
        logger.info("\n" + "=" * 60)
        logger.info("STARTING SOE-SPOTIFY ETL PIPELINE")
        logger.info("=" * 60 + "\n")

        # RAW STAGE: Load CSVs → Raw Parquet
        raw_stage = RawStage(spark)
        raw_tracks, raw_artists, raw_albums, raw_audio, raw_lyrics = (
            raw_stage.run()
        )

        # PROCESSED STAGE: Clean → Processed Parquet
        processed_stage = ProcessedStage(spark)
        (
            processed_tracks,
            processed_artists,
            processed_albums,
            processed_features,
        ) = processed_stage.run(
            raw_tracks, raw_artists, raw_albums, raw_audio, raw_lyrics
        )

        # ANALYTICS STAGE: Engineer Features → Analytics Parquet
        analytics_stage = AnalyticsStage(spark)
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
            logger.info("\nSyncing to PostgreSQL...")
            db_loader = DatabaseLoader()
            db_loader.run(
                analytics_artists,
                analytics_albums,
                analytics_tracks,
                analytics_genres,
                analytics_features,
            )

        logger.info("\n" + "=" * 60)
        logger.info("ETL PIPELINE COMPLETED SUCCESSFULLY!")
        logger.info("=" * 60 + "\n")

    except Exception as e:
        logger.error(f"\nETL PIPELINE FAILED: {e}", exc_info=True)
        sys.exit(1)

    finally:
        spark.stop()
        logger.info("Spark session stopped")


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
