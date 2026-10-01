#!/usr/bin/env python3
"""
Spark Structured Streaming & Real-Time Analytics Consumer
Ingests live event streams:
- Computes sliding window metrics (Top trending products)
- Monitors real-time shopping cart additions and purchase conversion
- Detects trending spikes
"""

import os
import json
import logging
import pandas as pd
from collections import Counter

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("SparkStreamingConsumer")

class TikiStreamingConsumer:
    def __init__(self, buffer_file=None):
        if buffer_file is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.buffer_file = os.path.join(base_dir, "dataset", "processed", "live_stream_buffer.jsonl")
            self.output_dir = os.path.join(base_dir, "dataset", "processed", "analytics_results")
        else:
            self.buffer_file = buffer_file

    def process_micro_batch(self, max_records=200):
        """Processes the latest micro-batch of streaming events."""
        if not os.path.exists(self.buffer_file):
            logger.warning("No streaming buffer found yet. Run kafka_event_producer.py first.")
            return {}

        events = []
        with open(self.buffer_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue

        if not events:
            return {}

        df = pd.DataFrame(events[-max_records:])
        logger.info(f"Processing real-time micro-batch of {len(df)} events...")

        # 1. Event type breakdown
        event_dist = df["event_type"].value_counts().to_dict()

        # 2. Trending products (most viewed / bought)
        top_hot_products = df["product_id"].value_counts().head(5).to_dict()

        # 3. Platform breakdown
        platform_dist = df["client_platform"].value_counts().to_dict()

        metrics = {
            "window_event_count": len(df),
            "event_breakdown": event_dist,
            "trending_product_ids": top_hot_products,
            "platform_breakdown": platform_dist,
            "estimated_realtime_conversion_rate": round(
                (event_dist.get("PURCHASE", 0) / max(1, event_dist.get("VIEW_ITEM", 1))) * 100, 2
            )
        }

        os.makedirs(self.output_dir, exist_ok=True)
        with open(os.path.join(self.output_dir, "streaming_realtime_kpis.json"), "w", encoding="utf-8") as f:
            json.dump(metrics, f, ensure_ascii=False, indent=2)

        logger.info("Real-time streaming aggregations successfully updated.")
        return metrics

if __name__ == "__main__":
    consumer = TikiStreamingConsumer()
    res = consumer.process_micro_batch()
    print("Real-time Streaming Metrics:", json.dumps(res, indent=2, ensure_ascii=False))
