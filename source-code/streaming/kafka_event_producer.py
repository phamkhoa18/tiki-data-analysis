#!/usr/bin/env python3
"""
Real-time Clickstream & Order Event Simulator (Kafka Producer)
Simulates continuous user activity events on Tiki:
- view_item
- add_to_cart
- checkout_success
- search_query
Streams events to Kafka topic 'tiki_live_events' or local stream log buffer.
"""

import os
import time
import json
import random
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("KafkaEventProducer")

EVENT_TYPES = ["VIEW_ITEM", "VIEW_ITEM", "VIEW_ITEM", "ADD_TO_CART", "PURCHASE", "SEARCH"]

class TikiKafkaProducer:
    def __init__(self, topic="tiki_live_events", bootstrap_servers="localhost:9092", buffer_file=None):
        self.topic = topic
        self.bootstrap_servers = bootstrap_servers
        self.kafka_producer = None
        
        # Try initializing kafka-python if broker is running
        try:
            from kafka import KafkaProducer
            self.kafka_producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode("utf-8")
            )
            logger.info(f"Connected to Kafka broker at {bootstrap_servers}")
        except Exception:
            logger.info("Kafka broker not detected. Running in File Streaming Buffer mode for Spark Streaming.")

        if buffer_file is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.buffer_file = os.path.join(base_dir, "dataset", "processed", "live_stream_buffer.jsonl")
        else:
            self.buffer_file = buffer_file

    def generate_single_event(self):
        event_type = random.choice(EVENT_TYPES)
        cat_id = random.choice([1789, 1815, 1882, 8322, 1520, 915, 1883])
        prod_id = random.randint(100001, 101500)
        user_id = random.randint(1001, 2500)
        
        event = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            "event_id": f"EVT-{int(time.time()*1000)}-{random.randint(100,999)}",
            "event_type": event_type,
            "customer_id": user_id,
            "product_id": prod_id,
            "category_id": cat_id,
            "client_platform": random.choice(["iOS_App", "Android_App", "Desktop_Web", "Mobile_Web"]),
            "session_id": f"sess_{user_id}_{random.randint(10, 99)}"
        }
        return event

    def stream_events(self, max_events=100, delay_seconds=0.1):
        """Simulates continuous event streaming."""
        logger.info(f"Starting event stream simulation (Target: {max_events} events)...")
        os.makedirs(os.path.dirname(self.buffer_file), exist_ok=True)
        
        with open(self.buffer_file, "a", encoding="utf-8") as f:
            for i in range(1, max_events + 1):
                event = self.generate_single_event()
                
                # Send to Kafka if available
                if self.kafka_producer:
                    self.kafka_producer.send(self.topic, event)
                
                # Always append to stream buffer for Spark consumption
                f.write(json.dumps(event, ensure_ascii=False) + "\n")
                f.flush()

                if i % 20 == 0:
                    logger.info(f"Emitted {i}/{max_events} events: {event['event_type']} on Product #{event['product_id']}")
                time.sleep(delay_seconds)

        logger.info(f"Finished generating {max_events} events into {self.buffer_file}")

if __name__ == "__main__":
    producer = TikiKafkaProducer()
    producer.stream_events(max_events=50, delay_seconds=0.05)
