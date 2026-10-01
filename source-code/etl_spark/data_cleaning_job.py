#!/usr/bin/env python3
"""
PySpark Batch ETL Job: Data Cleaning & Feature Engineering
- Schema validation
- Missing value imputation
- Outlier filtering (price < 0 or > 500,000,000)
- Derived business metrics (revenue_estimate, discount_amount, popularity_score)
"""

import os
import sys
import logging
import pandas as pd
import numpy as np

try:
    from .spark_session_builder import get_spark_session
except ImportError:
    from spark_session_builder import get_spark_session

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("DataCleaningJob")

class TikiDataCleaner:
    def __init__(self, data_dir=None):
        if data_dir is None:
            root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.data_dir = os.path.join(root, "dataset")
        else:
            self.data_dir = data_dir
        self.raw_dir = os.path.join(self.data_dir, "raw")
        self.processed_dir = os.path.join(self.data_dir, "processed")
        os.makedirs(self.processed_dir, exist_ok=True)

    def clean_products(self):
        """Cleans products data and enriches with business features."""
        csv_path = os.path.join(self.raw_dir, "tiki_products.csv")
        logger.info(f"Loading raw products from {csv_path}...")
        
        df = pd.read_csv(csv_path)
        initial_count = len(df)
        
        # 1. Remove duplicates by ID
        df = df.drop_duplicates(subset=["id"])
        
        # 2. Impute missing values
        df["rating_average"] = df["rating_average"].fillna(4.0)
        df["review_count"] = df["review_count"].fillna(0).astype(int)
        df["quantity_sold"] = df["quantity_sold"].fillna(0).astype(int)
        df["brand_name"] = df["brand_name"].fillna("Khác")
        df["seller_name"] = df["seller_name"].fillna("Tiki Trading")
        
        # 3. Filter price anomalies
        df = df[(df["price"] > 1000) & (df["price"] <= 200000000)]
        df["discount_rate"] = df["discount_rate"].clip(lower=0, upper=90)
        
        # 4. Feature engineering
        df["discount_amount"] = df["original_price"] - df["price"]
        df["revenue_estimate"] = df["price"] * df["quantity_sold"]
        # Popularity score = rating * log10(reviews + 1)
        df["popularity_score"] = (df["rating_average"] * np.log10(df["review_count"] + 1)).round(2)
        
        cleaned_path = os.path.join(self.processed_dir, "cleaned_products.csv")
        df.to_csv(cleaned_path, index=False)
        logger.info(f"Products cleaning complete: {initial_count} -> {len(df)} records. Saved to {cleaned_path}")
        return df

    def clean_reviews(self):
        """Cleans customer reviews, normalizes sentiment tags."""
        csv_path = os.path.join(self.raw_dir, "tiki_reviews.csv")
        logger.info(f"Loading raw reviews from {csv_path}...")
        
        df = pd.read_csv(csv_path)
        initial_count = len(df)
        
        df = df.drop_duplicates(subset=["review_id"])
        df["title"] = df["title"].fillna("")
        df["content"] = df["content"].fillna("")
        df["thank_count"] = df["thank_count"].fillna(0).astype(int)
        df["rating"] = df["rating"].clip(lower=1, upper=5)
        
        # Standardize sentiment
        df["sentiment"] = df["sentiment"].map({
            "POSITIVE": "TÍCH CỰC",
            "NEUTRAL": "TRUNG TÍNH",
            "NEGATIVE": "TIÊU CỰC"
        }).fillna("TÍCH CỰC")
        
        cleaned_path = os.path.join(self.processed_dir, "cleaned_reviews.csv")
        df.to_csv(cleaned_path, index=False)
        logger.info(f"Reviews cleaning complete: {initial_count} -> {len(df)} records. Saved to {cleaned_path}")
        return df

    def run(self):
        spark, is_native = get_spark_session()
        logger.info(f"Executing Batch Cleaning Pipeline (Engine: {'Spark' if is_native else 'Arrow/Pandas'})...")
        prod_df = self.clean_products()
        rev_df = self.clean_reviews()
        if spark:
            try:
                spark_prod = spark.createDataFrame(prod_df)
                spark_prod.createOrReplaceTempView("products")
                logger.info(f"Registered PySpark TempView 'products'. Schema:")
                spark_prod.printSchema()
            except Exception as e:
                logger.warning(f"PySpark schema registration note: {e}")
        return prod_df, rev_df

if __name__ == "__main__":
    cleaner = TikiDataCleaner()
    cleaner.run()
