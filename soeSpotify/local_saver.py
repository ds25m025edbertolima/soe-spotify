import logging
from pathlib import Path

from pyspark.sql import DataFrame

from .config import DATA_PROCESSED

logger = logging.getLogger(__name__)


class LocalSaver:
    def __init__(self, output_dir: Path | str = DATA_PROCESSED) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"LocalSaver initialized with output dir: {self.output_dir}")

    def save_dataframe(
        self, df: DataFrame, name: str, format: str = "csv"
    ) -> Path:
        output_path = self.output_dir / f"{name}.{format}"
        logger.info(f"Saving {name} to {output_path} ({format})")

        pandas_df = df.toPandas()
        row_count = len(pandas_df)
        col_count = len(pandas_df.columns)

        if format == "csv":
            pandas_df.to_csv(output_path, index=False)
        elif format == "parquet":
            pandas_df.to_parquet(output_path, index=False)
        else:
            raise ValueError(f"Unsupported format: {format}")

        logger.info(f"Saved {name}: {row_count} rows, {col_count} columns")
        return output_path

    def save_tracks(self, df: DataFrame) -> Path:
        return self.save_dataframe(df, "tracks")

    def save_artists(self, df: DataFrame) -> Path:
        return self.save_dataframe(df, "artists")

    def save_albums(self, df: DataFrame) -> Path:
        return self.save_dataframe(df, "albums")

    def save_enriched_tracks(self, df: DataFrame) -> Path:
        return self.save_dataframe(df, "enriched_tracks")
