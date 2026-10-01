#!/usr/bin/env python3
"""
Tiki API Crawler & Ingestion Module
Crawls product catalog and customer reviews from Tiki's public REST APIs:
- Product Listing Endpoint: https://tiki.vn/api/v2/products
- Product Reviews Endpoint: https://tiki.vn/api/v2/reviews
"""

import os
import json
import csv
import logging
import argparse
import requests
from datetime import datetime

try:
    from .rate_limiter import PoliteRateLimiter
except ImportError:
    from rate_limiter import PoliteRateLimiter

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("TikiCrawler")

class TikiAPICrawler:
    def __init__(self, output_dir=None):
        self.rate_limiter = PoliteRateLimiter()
        self.session = requests.Session()
        if output_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.output_dir = os.path.join(base_dir, "dataset", "raw")
        else:
            self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def fetch_products_by_category(self, category_id=1789, limit=40, max_pages=3):
        """Fetches products for a specific category ID."""
        url = "https://tiki.vn/api/v2/products"
        collected = []

        for page in range(1, max_pages + 1):
            params = {
                "limit": limit,
                "category": category_id,
                "page": page,
                "sort": "top_seller"
            }
            self.rate_limiter.wait()
            try:
                logger.info(f"Crawling category {category_id} | Page {page}/{max_pages}...")
                resp = self.session.get(url, params=params, headers=self.rate_limiter.get_headers(), timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    items = data.get("data", [])
                    if not items:
                        logger.warning(f"No more products found on page {page}.")
                        break
                    
                    for it in items:
                        product = {
                            "id": it.get("id"),
                            "sku": it.get("sku", f"TK-{it.get('id')}"),
                            "name": it.get("name"),
                            "price": it.get("price"),
                            "original_price": it.get("original_price", it.get("price")),
                            "discount_rate": it.get("discount_rate", 0),
                            "rating_average": it.get("rating_average", 0.0),
                            "review_count": it.get("review_count", 0),
                            "quantity_sold": it.get("all_time_quantity_sold", it.get("quantity_sold", {}).get("value", 0)),
                            "category_id": category_id,
                            "category_name": it.get("primary_category_name", "Thiết Bị Số"),
                            "brand_name": it.get("brand_name", "Khác"),
                            "seller_id": it.get("seller_id", 1),
                            "seller_name": it.get("seller_name", "Tiki Trading"),
                            "is_official_seller": it.get("is_official_seller", True),
                            "is_tiki_now": "tikinow" in str(it.get("badges", [])).lower(),
                            "inventory_status": it.get("inventory_status", "available"),
                            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        collected.append(product)
                else:
                    logger.warning(f"Failed with status code: {resp.status_code}")
                    break
            except Exception as e:
                logger.error(f"Error fetching page {page}: {e}")
                break

        logger.info(f"Successfully collected {len(collected)} products for category {category_id}.")
        return collected

    def fetch_reviews_for_product(self, product_id, limit=20, max_pages=2):
        """Fetches customer reviews for a single product."""
        url = "https://tiki.vn/api/v2/reviews"
        reviews = []

        for page in range(1, max_pages + 1):
            params = {
                "product_id": product_id,
                "sort": "score|desc",
                "page": page,
                "limit": limit,
                "include": "comments,contribute_info"
            }
            self.rate_limiter.wait()
            try:
                resp = self.session.get(url, params=params, headers=self.rate_limiter.get_headers(), timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    items = data.get("data", [])
                    if not items:
                        break
                    for r in items:
                        rating = r.get("rating", 5)
                        sentiment = "POSITIVE" if rating >= 4 else ("NEUTRAL" if rating == 3 else "NEGATIVE")
                        review = {
                            "review_id": r.get("id"),
                            "product_id": product_id,
                            "product_name": r.get("product_name", f"Product #{product_id}"),
                            "category_id": 1789,
                            "customer_id": r.get("customer_id", 0),
                            "customer_name": r.get("created_by", {}).get("full_name", "Ẩn danh"),
                            "rating": rating,
                            "sentiment": sentiment,
                            "title": r.get("title", ""),
                            "content": r.get("content", ""),
                            "thank_count": r.get("thank_count", 0),
                            "delivery_rating": rating,
                            "quality_rating": rating,
                            "is_buyer": True,
                            "created_at": datetime.fromtimestamp(r.get("created_at", datetime.now().timestamp())).strftime("%Y-%m-%d %H:%M:%S") if r.get("created_at") else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        reviews.append(review)
                else:
                    break
            except Exception as e:
                logger.error(f"Error fetching reviews for {product_id}: {e}")
                break

        return reviews

    def save_to_csv(self, data, filename):
        if not data:
            logger.warning(f"No data to save for {filename}")
            return
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        logger.info(f"Saved {len(data)} records to {filepath}")

def main():
    parser = argparse.ArgumentParser(description="Tiki API Data Ingestion")
    parser.add_argument("--category", type=int, default=1789, help="Category ID (default: 1789 - Phones & Tablets)")
    parser.add_argument("--pages", type=int, default=2, help="Number of pages to crawl")
    args = parser.parse_args()

    crawler = TikiAPICrawler()
    prods = crawler.fetch_products_by_category(category_id=args.category, max_pages=args.pages)
    if prods:
        crawler.save_to_csv(prods, f"crawled_category_{args.category}.csv")

if __name__ == "__main__":
    main()
