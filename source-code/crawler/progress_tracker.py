#!/usr/bin/env python3
"""
Progress Tracker for Tiki Crawler.
Saves crawl state to disk so the crawler can resume after interruption.
Tracks: which categories/products have been crawled, total counts, timing.
"""

import os
import json
import logging
from datetime import datetime

try:
    from .config import PROGRESS_FILE, RAW_DATA_DIR
except ImportError:
    from config import PROGRESS_FILE, RAW_DATA_DIR

logger = logging.getLogger("ProgressTracker")


class ProgressTracker:
    """
    Tracks crawling progress and supports resume-from-crash.
    
    Progress state is saved as JSON:
    {
        "started_at": "2026-10-01 12:00:00",
        "last_updated": "2026-10-01 12:30:00",
        "phase": "products",  # current phase: categories, products, reviews, details
        "products": {
            "completed_categories": [1789, 1815],
            "current_category_id": 1882,
            "current_page": 5,
            "total_crawled": 350
        },
        "reviews": {
            "completed_product_ids": [123, 456, ...],
            "current_product_id": 789,
            "total_crawled": 1200
        },
        "details": {
            "completed_product_ids": [123, 456, ...],
            "total_crawled": 100
        },
        "stats": {
            "total_products": 350,
            "total_reviews": 1200,
            "total_details": 100,
            "total_errors": 5,
            "total_api_requests": 1500
        }
    }
    """

    def __init__(self, progress_file=None):
        self.progress_file = progress_file or PROGRESS_FILE
        os.makedirs(os.path.dirname(self.progress_file), exist_ok=True)
        self.state = self._load()

    def _load(self):
        """Load existing progress or create fresh state."""
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, "r", encoding="utf-8") as f:
                    state = json.load(f)
                logger.info(f"📂 Resumed from progress file: {self.progress_file}")
                logger.info(
                    f"   Products: {state.get('stats', {}).get('total_products', 0)}, "
                    f"Reviews: {state.get('stats', {}).get('total_reviews', 0)}, "
                    f"Details: {state.get('stats', {}).get('total_details', 0)}"
                )
                return state
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Corrupted progress file, starting fresh: {e}")

        return self._fresh_state()

    def _fresh_state(self):
        """Create a fresh progress state."""
        return {
            "started_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "phase": "categories",
            "products": {
                "completed_categories": [],
                "current_category_id": None,
                "current_page": 0,
                "total_crawled": 0,
            },
            "reviews": {
                "completed_product_ids": [],
                "current_product_id": None,
                "total_crawled": 0,
            },
            "details": {
                "completed_product_ids": [],
                "total_crawled": 0,
            },
            "stats": {
                "total_products": 0,
                "total_reviews": 0,
                "total_details": 0,
                "total_errors": 0,
                "total_api_requests": 0,
            },
        }

    def save(self):
        """Persist current state to disk."""
        self.state["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(self.progress_file, "w", encoding="utf-8") as f:
                json.dump(self.state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save progress: {e}")

    def reset(self):
        """Reset all progress (start fresh crawl)."""
        self.state = self._fresh_state()
        self.save()
        logger.info("🔄 Progress reset — starting fresh crawl")

    # ===================== Products =====================

    def is_category_done(self, category_id):
        """Check if a category has been fully crawled."""
        return category_id in self.state["products"]["completed_categories"]

    def get_resume_page(self, category_id):
        """Get the page to resume from for a category."""
        if self.state["products"]["current_category_id"] == category_id:
            return self.state["products"]["current_page"]
        return 1  # start from page 1

    def update_product_progress(self, category_id, page, batch_count):
        """Update product crawling progress after a page is done."""
        self.state["products"]["current_category_id"] = category_id
        self.state["products"]["current_page"] = page
        self.state["products"]["total_crawled"] += batch_count
        self.state["stats"]["total_products"] += batch_count
        self.save()

    def mark_category_done(self, category_id):
        """Mark a category as fully crawled."""
        if category_id not in self.state["products"]["completed_categories"]:
            self.state["products"]["completed_categories"].append(category_id)
        self.state["products"]["current_category_id"] = None
        self.state["products"]["current_page"] = 0
        self.save()

    # ===================== Reviews =====================

    def is_product_reviews_done(self, product_id):
        """Check if reviews for a product have been fully crawled."""
        return product_id in self.state["reviews"]["completed_product_ids"]

    def update_review_progress(self, product_id, batch_count):
        """Update review crawling progress."""
        self.state["reviews"]["current_product_id"] = product_id
        self.state["reviews"]["total_crawled"] += batch_count
        self.state["stats"]["total_reviews"] += batch_count

    def mark_product_reviews_done(self, product_id):
        """Mark reviews for a product as fully crawled."""
        if product_id not in self.state["reviews"]["completed_product_ids"]:
            self.state["reviews"]["completed_product_ids"].append(product_id)
        self.state["reviews"]["current_product_id"] = None
        # Save periodically (every 50 products to avoid too many disk writes)
        if len(self.state["reviews"]["completed_product_ids"]) % 50 == 0:
            self.save()

    # ===================== Product Details =====================

    def is_product_detail_done(self, product_id):
        """Check if product detail has been scraped."""
        return product_id in self.state["details"]["completed_product_ids"]

    def update_detail_progress(self, product_id):
        """Update detail scraping progress."""
        if product_id not in self.state["details"]["completed_product_ids"]:
            self.state["details"]["completed_product_ids"].append(product_id)
        self.state["details"]["total_crawled"] += 1
        self.state["stats"]["total_details"] += 1
        if self.state["details"]["total_crawled"] % 50 == 0:
            self.save()

    # ===================== Stats =====================

    def increment_errors(self, count=1):
        """Increment error counter."""
        self.state["stats"]["total_errors"] += count

    def increment_requests(self, count=1):
        """Increment API request counter."""
        self.state["stats"]["total_api_requests"] += count

    def set_phase(self, phase):
        """Set current crawl phase."""
        self.state["phase"] = phase
        self.save()
        logger.info(f"📍 Phase changed to: {phase}")

    def get_summary(self):
        """Get a human-readable summary of progress."""
        s = self.state["stats"]
        started = self.state.get("started_at", "N/A")
        updated = self.state.get("last_updated", "N/A")
        return (
            f"\n{'='*60}\n"
            f"📊 CRAWL PROGRESS SUMMARY\n"
            f"{'='*60}\n"
            f"  Started:       {started}\n"
            f"  Last Updated:  {updated}\n"
            f"  Current Phase: {self.state.get('phase', 'N/A')}\n"
            f"  ────────────────────────────────────────\n"
            f"  📦 Products:    {s['total_products']:,}\n"
            f"  ⭐ Reviews:     {s['total_reviews']:,}\n"
            f"  📝 Details:     {s['total_details']:,}\n"
            f"  ❌ Errors:      {s['total_errors']:,}\n"
            f"  🌐 API Calls:   {s['total_api_requests']:,}\n"
            f"  Categories done: {len(self.state['products']['completed_categories'])}/10\n"
            f"{'='*60}\n"
        )
