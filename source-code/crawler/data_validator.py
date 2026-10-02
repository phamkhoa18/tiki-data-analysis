#!/usr/bin/env python3
"""
Data Validator & Cleaner for Tiki Crawler.
Validates, cleans, and normalizes crawled data right after collection.
- Type validation (int, float, str, bool)
- Null/empty handling with sensible defaults
- Duplicate removal by primary key
- UTF-8 encoding normalization
- Datetime format standardization
"""

import re
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("DataValidator")


class DataValidator:
    """Validates and cleans crawled Tiki data in-memory."""

    def __init__(self):
        self.stats = {
            "products_cleaned": 0,
            "reviews_cleaned": 0,
            "duplicates_removed": 0,
            "nulls_filled": 0,
            "encoding_fixed": 0,
        }

    # ================================================================
    # Product Validation
    # ================================================================

    def validate_products(self, products):
        """Validate and clean a list of product dicts."""
        logger.info(f"🔍 Validating {len(products)} products...")

        seen_ids = set()
        cleaned = []

        for p in products:
            pid = self._safe_int(p.get("product_id"))
            if not pid:
                continue
            if pid in seen_ids:
                self.stats["duplicates_removed"] += 1
                continue
            seen_ids.add(pid)

            cleaned_product = {
                "product_id": pid,
                "sku": self._safe_str(p.get("sku", "")),
                "name": self._clean_text(p.get("name", "")),
                "url_key": self._safe_str(p.get("url_key", "")),
                "url_path": self._safe_str(p.get("url_path", "")),
                "price": self._safe_int(p.get("price", 0)),
                "original_price": self._safe_int(p.get("original_price", 0)),
                "discount": self._safe_int(p.get("discount", 0)),
                "discount_rate": self._safe_int(p.get("discount_rate", 0)),
                "rating_average": self._safe_float(p.get("rating_average", 0)),
                "review_count": self._safe_int(p.get("review_count", 0)),
                "quantity_sold": self._safe_int(p.get("quantity_sold", 0)),
                "category_id": self._safe_int(p.get("category_id", 0)),
                "category_name": self._clean_text(p.get("category_name", "")),
                "brand_id": self._safe_int(p.get("brand_id", 0)),
                "brand_name": self._clean_text(p.get("brand_name", "Không rõ")),
                "seller_id": self._safe_int(p.get("seller_id", 0)),
                "seller_name": self._clean_text(p.get("seller_name", "")),
                "seller_product_id": self._safe_int(p.get("seller_product_id", 0)),
                "is_official_store": self._safe_bool(p.get("is_official_store", False)),
                "is_authentic": self._safe_bool(p.get("is_authentic", False)),
                "is_tiki_now": self._safe_bool(p.get("is_tiki_now", False)),
                "is_freeship_xtra": self._safe_bool(p.get("is_freeship_xtra", False)),
                "origin": self._clean_text(p.get("origin", "")),
                "thumbnail_url": self._safe_str(p.get("thumbnail_url", "")),
                "inventory_status": self._safe_str(p.get("inventory_status", "available")),
                "crawled_at": self._safe_datetime(p.get("crawled_at", "")),
                "data_source": self._safe_str(p.get("data_source", "tiki_api")),
            }

            # Fix: original_price should be >= price
            if cleaned_product["original_price"] < cleaned_product["price"]:
                cleaned_product["original_price"] = cleaned_product["price"]

            # Fix: discount_rate should match price difference
            if cleaned_product["original_price"] > 0 and cleaned_product["discount_rate"] == 0:
                diff = cleaned_product["original_price"] - cleaned_product["price"]
                if diff > 0:
                    cleaned_product["discount_rate"] = round(diff / cleaned_product["original_price"] * 100)
                    cleaned_product["discount"] = diff

            cleaned.append(cleaned_product)
            self.stats["products_cleaned"] += 1

        logger.info(
            f"  ✅ Products: {len(cleaned)} valid, "
            f"{self.stats['duplicates_removed']} dupes removed"
        )
        return cleaned

    # ================================================================
    # Review Validation
    # ================================================================

    def validate_reviews(self, reviews):
        """Validate and clean a list of review dicts."""
        logger.info(f"🔍 Validating {len(reviews)} reviews...")

        seen_ids = set()
        cleaned = []

        for r in reviews:
            rid = self._safe_int(r.get("review_id"))
            if not rid:
                continue
            if rid in seen_ids:
                self.stats["duplicates_removed"] += 1
                continue
            seen_ids.add(rid)

            rating = self._safe_int(r.get("rating", 0))
            rating = max(1, min(5, rating)) if rating > 0 else 0

            # Recalculate sentiment from rating
            if rating >= 4:
                sentiment = "POSITIVE"
            elif rating == 3:
                sentiment = "NEUTRAL"
            elif rating >= 1:
                sentiment = "NEGATIVE"
            else:
                sentiment = "UNKNOWN"

            cleaned_review = {
                "review_id": rid,
                "product_id": self._safe_int(r.get("product_id", 0)),
                "customer_id": self._safe_int(r.get("customer_id", 0)),
                "customer_name": self._clean_text(r.get("customer_name", "Ẩn danh")),
                "rating": rating,
                "title": self._clean_text(r.get("title", "")),
                "content": self._clean_text(r.get("content", "")),
                "thank_count": self._safe_int(r.get("thank_count", 0)),
                "is_purchased": self._safe_bool(r.get("is_purchased", False)),
                "has_images": self._safe_bool(r.get("has_images", False)),
                "images": self._safe_json_str(r.get("images", "[]")),
                "seller_id": self._safe_int(r.get("seller_id", 0)),
                "seller_name": self._clean_text(r.get("seller_name", "")),
                "product_attributes": self._safe_json_str(r.get("product_attributes", "[]")),
                "vote_agree": self._safe_json_str(r.get("vote_agree", "[]")),
                "vote_disagree": self._safe_json_str(r.get("vote_disagree", "[]")),
                "usage_duration": self._safe_str(r.get("usage_duration", "")),
                "sentiment": sentiment,
                "created_at": self._safe_datetime(r.get("created_at", "")),
                "crawled_at": self._safe_datetime(r.get("crawled_at", "")),
            }
            cleaned.append(cleaned_review)
            self.stats["reviews_cleaned"] += 1

        logger.info(
            f"  ✅ Reviews: {len(cleaned)} valid, "
            f"{self.stats['duplicates_removed']} dupes removed"
        )
        return cleaned

    # ================================================================
    # Type Conversion Helpers
    # ================================================================

    def _safe_int(self, value, default=0):
        """Convert value to int safely."""
        if value is None:
            self.stats["nulls_filled"] += 1
            return default
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    def _safe_float(self, value, default=0.0):
        """Convert value to float safely."""
        if value is None:
            self.stats["nulls_filled"] += 1
            return default
        try:
            return round(float(value), 2)
        except (ValueError, TypeError):
            return default

    def _safe_bool(self, value, default=False):
        """Convert value to bool safely."""
        if value is None:
            return default
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ("true", "1", "yes")
        return bool(value)

    def _safe_str(self, value, default=""):
        """Convert value to string safely."""
        if value is None:
            self.stats["nulls_filled"] += 1
            return default
        return str(value).strip()

    def _safe_json_str(self, value, default="[]"):
        """Ensure value is a valid JSON string."""
        if not value:
            return default
        if isinstance(value, (list, dict)):
            return json.dumps(value, ensure_ascii=False)
        if isinstance(value, str):
            try:
                json.loads(value)
                return value
            except json.JSONDecodeError:
                return default
        return default

    def _clean_text(self, text, max_length=5000):
        """Clean and normalize text content."""
        if not text:
            return ""
        text = str(text).strip()
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove null bytes
        text = text.replace('\x00', '')
        # Truncate if too long
        if len(text) > max_length:
            text = text[:max_length]
        self.stats["encoding_fixed"] += 1
        return text

    def _safe_datetime(self, value, default=""):
        """Validate and normalize datetime string."""
        if not value:
            return default
        try:
            # Try parsing common formats
            for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"]:
                try:
                    dt = datetime.strptime(str(value), fmt)
                    return dt.strftime("%Y-%m-%d %H:%M:%S")
                except ValueError:
                    continue
            return str(value)
        except Exception:
            return default

    def get_stats(self):
        """Return validation statistics."""
        return self.stats
