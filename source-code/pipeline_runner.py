#!/usr/bin/env python3
"""
Master Big Data Pipeline Orchestrator
Executes all end-to-end steps:
1. Data Cleaning & Feature Engineering (ETL)
2. Parquet Data Lake Export
3. Category & Pricing Market Analytics
4. Vietnamese NLP Sentiment & Aspect Mining
5. ALS Collaborative Filtering Model Training
6. Customer RFM Segmentation
7. Streaming Clickstream Simulation & Real-time Aggregation
"""

import sys
import os
import time
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("PipelineRunner")

# Setup sys.path
sys_path = os.path.dirname(os.path.abspath(__file__))
if sys_path not in sys.path:
    sys.path.insert(0, sys_path)

from etl_spark.data_cleaning_job import TikiDataCleaner
from etl_spark.parquet_export_job import ParquetExportJob
from analytics_ml.category_pricing_analysis import TikiPricingAnalytics
from analytics_ml.sentiment_nlp_spark import VietnameseReviewNLP
from analytics_ml.recommendation_als import TikiRecommender
from analytics_ml.customer_rfm_clustering import CustomerRFMAnalyzer
from streaming.kafka_event_producer import TikiKafkaProducer
from streaming.spark_streaming_consumer import TikiStreamingConsumer

def run_full_pipeline():
    logger.info("=" * 70)
    logger.info("🚀 BẮT ĐẦU CHẠY TOÀN BỘ PIPELINE BIG DATA HỆ THỐNG TIKI")
    logger.info("=" * 70)
    start_time = time.time()

    # Step 1: Data Cleaning (Spark ETL)
    logger.info("[BƯỚC 1/7] Thực thi Batch ETL Data Cleaning & Schema Validation...")
    cleaner = TikiDataCleaner()
    cleaner.run()

    # Step 2: Parquet Partitioned Export
    logger.info("[BƯỚC 2/7] Chuyển đổi dữ liệu sang Parquet Snappy phân vùng Data Lake...")
    parquet_job = ParquetExportJob()
    parquet_job.run()

    # Step 3: Category & Pricing Analytics
    logger.info("[BƯỚC 3/7] Phân tích thị phần danh mục, biến động giá và xếp hạng seller...")
    pricing = TikiPricingAnalytics()
    pricing.run_analytics()

    # Step 4: NLP Sentiment Analysis
    logger.info("[BƯỚC 4/7] Khai phá cảm xúc NLP và phân tích khía cạnh (Giao hàng, đóng gói, chất lượng)...")
    nlp = VietnameseReviewNLP()
    nlp.run_pipeline()

    # Step 5: ALS Recommendation Model
    logger.info("[BƯỚC 5/7] Huấn luyện mô hình Gợi ý sản phẩm Spark MLlib ALS...")
    rec = TikiRecommender()
    rec.train_als_model()

    # Step 6: Customer RFM Segmentation
    logger.info("[BƯỚC 6/7] Phân cụm khách hàng theo mô hình RFM & K-Means...")
    rfm = CustomerRFMAnalyzer()
    rfm.run_rfm_segmentation()

    # Step 7: Real-time Streaming Simulation
    logger.info("[BƯỚC 7/7] Giả lập luồng sự kiện Clickstream Kafka và tính toán micro-batch...")
    producer = TikiKafkaProducer()
    producer.stream_events(max_events=60, delay_seconds=0.01)
    consumer = TikiStreamingConsumer()
    consumer.process_micro_batch()

    elapsed = time.time() - start_time
    logger.info("=" * 70)
    logger.info(f"✅ TOÀN BỘ PIPELINE HOÀN THÀNH THÀNH CÔNG TRONG {elapsed:.2f} GIÂY!")
    logger.info("=" * 70)

if __name__ == "__main__":
    run_full_pipeline()
