#!/usr/bin/env python3
"""
Parquet Export & Partitioning Job
Converts cleaned datasets to Apache Parquet format partitioned by category_id.
Enables columnar compression (Snappy) and high-speed predicate pushdown queries.
"""

import os
import sys
import logging
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ParquetExportJob")

class ParquetExportJob:
    def __init__(self, data_dir=None):
        if data_dir is None:
            root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.data_dir = os.path.join(root, "dataset")
        else:
            self.data_dir = data_dir
        self.processed_dir = os.path.join(self.data_dir, "processed")

    def export_products_to_parquet(self):
        cleaned_csv = os.path.join(self.processed_dir, "cleaned_products.csv")
        if not os.path.exists(cleaned_csv):
            logger.error("cleaned_products.csv not found! Run data_cleaning_job.py first.")
            return

        df = pd.read_csv(cleaned_csv)
        parquet_dir = os.path.join(self.processed_dir, "parquet_products")
        os.makedirs(parquet_dir, exist_ok=True)
        
        # Partition by category_id
        df.to_parquet(
            parquet_dir,
            engine="pyarrow",
            compression="snappy",
            partition_cols=["category_id"],
            index=False
        )
        logger.info(f"Exported products to partitioned Parquet at: {parquet_dir}")

    def export_reviews_to_parquet(self):
        cleaned_csv = os.path.join(self.processed_dir, "cleaned_reviews.csv")
        if not os.path.exists(cleaned_csv):
            logger.error("cleaned_reviews.csv not found! Run data_cleaning_job.py first.")
            return

        df = pd.read_csv(cleaned_csv)
        parquet_dir = os.path.join(self.processed_dir, "parquet_reviews")
        os.makedirs(parquet_dir, exist_ok=True)

        df.to_parquet(
            parquet_dir,
            engine="pyarrow",
            compression="snappy",
            partition_cols=["category_id"],
            index=False
        )
        logger.info(f"Exported reviews to partitioned Parquet at: {parquet_dir}")

    def run(self):
        logger.info("Starting Parquet Export & Lakehouse Storage Pipeline...")
        self.export_products_to_parquet()
        self.export_reviews_to_parquet()
        logger.info("Parquet storage generation completed successfully.")

if __name__ == "__main__":
    job = ParquetExportJob()
    job.run()
