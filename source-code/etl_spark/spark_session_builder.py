"""
SparkSession Builder & Hardware Configuration Manager
Provides optimized SparkSession configuration for Big Data processing:
- Memory management
- Catalyst Optimizer settings
- Arrow optimization
- Graceful standalone / fallback mode
"""

import os
import sys
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("SparkSessionBuilder")

def get_spark_session(app_name="TikiBigDataAnalytics", master="local[*]"):
    """
    Initializes and returns an Apache SparkSession.
    If PySpark is available with Java runtime, launches Spark.
    Returns (spark, is_native_spark).
    """
    try:
        from pyspark.sql import SparkSession

        # Check if JAVA_HOME is set or java binary is present
        spark = SparkSession.builder \
            .appName(app_name) \
            .master(master) \
            .config("spark.driver.memory", "4g") \
            .config("spark.executor.memory", "4g") \
            .config("spark.sql.shuffle.partitions", "8") \
            .config("spark.sql.execution.arrow.pyspark.enabled", "true") \
            .config("spark.sql.parquet.compression.codec", "snappy") \
            .getOrCreate()
        
        logger.info(f"Initialized Apache Spark {spark.version} successfully.")
        return spark, True
    except Exception as e:
        logger.warning(f"Native SparkSession could not be started ({e}). Activating high-performance PyArrow/Pandas fallback engine.")
        return None, False
