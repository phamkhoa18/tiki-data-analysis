#!/usr/bin/env python3
"""
Tiki API Crawler — Production-Grade Data Collector
Crawls REAL product catalog and customer reviews from Tiki's public REST APIs.

Data Sources:
  - Source #1 (API): https://tiki.vn/api/v2/products  → Product listings
  - Source #1 (API): https://tiki.vn/api/v2/reviews   → Customer reviews

Features:
  - Crawls 10 categories with full pagination
  - Extracts rich product data (price, brand, seller, badges, images, etc.)
  - Crawls reviews for products with review_count > 0
  - Deduplicates products across categories
  - Resume-from-crash support via progress tracker
  - Polite rate limiting with exponential backoff
  - Saves to CSV + JSON + JSONL formats
"""

import os
import json
import csv
import time
import random
import logging
from datetime import datetime

try:
    from curl_cffi import requests
    CURL_CFFI_AVAILABLE = True
except ImportError:
    import requests
    CURL_CFFI_AVAILABLE = False

try:
    from .config import (
        TIKI_PRODUCTS_API, TIKI_REVIEWS_API,
        CATEGORIES, PRODUCTS_PER_PAGE, MAX_PRODUCT_PAGES,
        PRODUCT_SORT, REVIEWS_PER_PAGE, MAX_REVIEW_PAGES,
        MIN_REVIEW_COUNT, REVIEW_SORT, RAW_DATA_DIR,
        PRODUCTS_CSV, PRODUCTS_JSON,
        REVIEWS_CSV, REVIEWS_JSON,
        CATEGORIES_CSV, CATEGORIES_JSON,
        SELLERS_CSV, SELLERS_JSON,
        FLUSH_BUFFER_SIZE, LOG_FORMAT, LOG_DATE_FORMAT,
    )
    from .rate_limiter import PoliteRateLimiter
    from .progress_tracker import ProgressTracker
except ImportError:
    from config import (
        TIKI_PRODUCTS_API, TIKI_REVIEWS_API,
        CATEGORIES, PRODUCTS_PER_PAGE, MAX_PRODUCT_PAGES,
        PRODUCT_SORT, REVIEWS_PER_PAGE, MAX_REVIEW_PAGES,
        MIN_REVIEW_COUNT, REVIEW_SORT, RAW_DATA_DIR,
        PRODUCTS_CSV, PRODUCTS_JSON,
        REVIEWS_CSV, REVIEWS_JSON,
        CATEGORIES_CSV, CATEGORIES_JSON,
        SELLERS_CSV, SELLERS_JSON,
        FLUSH_BUFFER_SIZE, LOG_FORMAT, LOG_DATE_FORMAT,
    )
    from rate_limiter import PoliteRateLimiter
    from progress_tracker import ProgressTracker

logging.basicConfig(level=logging.INFO, format=LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
logger = logging.getLogger("TikiCrawler")


# ============================================================
# Schema field definitions
# ============================================================

PRODUCT_FIELDS = [
    "product_id", "sku", "name", "url_key", "url_path",
    "price", "original_price", "discount", "discount_rate",
    "rating_average", "review_count", "quantity_sold",
    "category_id", "category_name",
    "brand_id", "brand_name",
    "seller_id", "seller_name", "seller_product_id",
    "is_official_store", "is_authentic", "is_tiki_now",
    "is_freeship_xtra", "origin",
    "thumbnail_url", "inventory_status",
    "crawled_at", "data_source",
]

REVIEW_FIELDS = [
    "review_id", "product_id",
    "customer_id", "customer_name",
    "rating", "title", "content",
    "thank_count", "is_purchased", "has_images", "images",
    "seller_id", "seller_name",
    "product_attributes", "vote_agree", "vote_disagree",
    "usage_duration", "sentiment",
    "created_at", "crawled_at",
]

CATEGORY_FIELDS = [
    "category_id", "category_name", "parent_id", "level",
    "url_slug", "total_products", "crawled_at",
]

SELLER_FIELDS = [
    "seller_id", "seller_name", "is_official_store",
    "total_products", "avg_rating", "total_reviews",
]


class TikiAPICrawler:
    """Production-grade Tiki API crawler with full pagination and resume support."""

    def __init__(self, output_dir=None, fresh=False):
        self.rate_limiter = PoliteRateLimiter()
        self.session = self._create_session()
        self.output_dir = output_dir or RAW_DATA_DIR
        os.makedirs(self.output_dir, exist_ok=True)

        self.progress = ProgressTracker()
        if fresh:
            self.progress.reset()

        # In-memory collections
        self.all_products = []
        self.all_reviews = []
        self.all_categories = []
        self.seen_product_ids = set()
        self.seen_review_ids = set()

        # Load existing data if resuming
        self._load_existing_data()

    def _load_existing_data(self):
        """Load existing crawled data for deduplication when resuming."""
        products_path = os.path.join(self.output_dir, PRODUCTS_CSV)
        reviews_path = os.path.join(self.output_dir, REVIEWS_CSV)

        if os.path.exists(products_path):
            try:
                with open(products_path, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        pid = int(row.get("product_id", 0))
                        if pid:
                            self.seen_product_ids.add(pid)
                            self.all_products.append(row)
                logger.info(f"📂 Loaded {len(self.seen_product_ids)} existing products for dedup")
            except Exception as e:
                logger.warning(f"Could not load existing products: {e}")

        if os.path.exists(reviews_path):
            try:
                with open(reviews_path, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        rid = int(row.get("review_id", 0))
                        if rid:
                            self.seen_review_ids.add(rid)
                            self.all_reviews.append(row)
                logger.info(f"📂 Loaded {len(self.seen_review_ids)} existing reviews for dedup")
            except Exception as e:
                logger.warning(f"Could not load existing reviews: {e}")

    def _create_session(self):
        """Create an HTTP session, using curl_cffi browser impersonation if available."""
        if CURL_CFFI_AVAILABLE:
            return requests.Session(impersonate="safari17_0")
        return requests.Session()

    # ================================================================
    # Phase 1: Crawl Categories
    # ================================================================

    def crawl_categories(self):
        """Fetch category metadata including total product counts from API."""
        logger.info("=" * 60)
        logger.info("📋 PHASE 1: Crawling Categories")
        logger.info("=" * 60)

        self.progress.set_phase("categories")
        categories_data = []
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for cat in CATEGORIES:
            cat_id = cat["id"]
            # Quick API call to get total product count
            params = {"limit": 1, "category": cat_id, "page": 1}
            resp = self.rate_limiter.request_with_retry(
                self.session, "GET", TIKI_PRODUCTS_API, params=params
            )
            total_products = 0
            if resp:
                try:
                    data = resp.json()
                    paging = data.get("paging", {})
                    total_products = paging.get("total", 0)
                    if not total_products:
                        total_text = str(paging.get("total_text", "0"))
                        total_products = int(total_text.replace("+", "").replace(",", ""))
                except Exception as e:
                    logger.warning(f"  ⚠️ Could not parse category {cat_id} count: {e}")
                    total_products = 0

            cat_row = {
                "category_id": cat_id,
                "category_name": cat["name"],
                "parent_id": 0,
                "level": 1,
                "url_slug": cat["slug"],
                "total_products": total_products,
                "crawled_at": now,
            }
            categories_data.append(cat_row)
            logger.info(f"  ✅ {cat['name']} (ID: {cat_id}) — {total_products:,} products")

        self.all_categories = categories_data
        self._save_csv(categories_data, CATEGORIES_CSV, CATEGORY_FIELDS)
        self._save_json(categories_data, CATEGORIES_JSON)
        logger.info(f"📋 Saved {len(categories_data)} categories\n")
        return categories_data

    # ================================================================
    # Phase 2: Crawl Products
    # ================================================================

    def crawl_products(self, max_pages_per_cat=None):
        """Crawl products across all categories with full pagination."""
        logger.info("=" * 60)
        logger.info("📦 PHASE 2: Crawling Products")
        logger.info("=" * 60)

        self.progress.set_phase("products")
        max_pages = max_pages_per_cat or MAX_PRODUCT_PAGES
        total_new = 0

        for cat_idx, cat in enumerate(CATEGORIES):
            cat_id = cat["id"]
            cat_name = cat["name"]

            # Delay between categories to avoid rate limiting
            if cat_idx > 0:
                delay = random.uniform(2.0, 4.0)
                logger.info(f"  ⏳ Cooling down {delay:.1f}s between categories...")
                time.sleep(delay)

            # Skip completed categories
            if self.progress.is_category_done(cat_id):
                logger.info(f"  ⏭️  Skipping {cat_name} (already done)")
                continue

            logger.info(f"\n🏷️  Category: {cat_name} (ID: {cat_id})")
            start_page = self.progress.get_resume_page(cat_id)
            cat_count = 0
            empty_pages = 0
            json_retries = 0  # Track JSON parse failures for retry

            page = start_page
            while page <= max_pages:
                params = {
                    "limit": PRODUCTS_PER_PAGE,
                    "category": cat_id,
                    "page": page,
                    "sort": PRODUCT_SORT,
                }

                resp = self.rate_limiter.request_with_retry(
                    self.session, "GET", TIKI_PRODUCTS_API, params=params
                )

                if not resp:
                    logger.warning(f"  ❌ Failed page {page} — stopping category")
                    self.progress.increment_errors()
                    break

                try:
                    data = resp.json()
                    items = data.get("data", [])
                    json_retries = 0  # Reset on success
                except Exception as e:
                    json_retries += 1
                    resp_preview = resp.text[:200] if resp else "(no response)"
                    logger.warning(
                        f"  ⚠️ Invalid JSON on page {page} (attempt {json_retries}/3): "
                        f"{resp_preview}..."
                    )
                    if json_retries < 3:
                        # Reset session to get new cookies (Tiki anti-bot)
                        try:
                            self.session.close()
                        except Exception:
                            pass
                        self.session = self._create_session()
                        wait_time = 5 * json_retries  # 5s, 10s backoff
                        logger.info(f"  ⏳ Session reset. Waiting {wait_time}s before retry...")
                        time.sleep(wait_time)
                        continue  # Retry SAME page (while loop doesn't auto-increment)
                    else:
                        logger.error(f"  ❌ Failed after 3 JSON retries — skipping category")
                        self.progress.increment_errors()
                        break

                if not items:
                    empty_pages += 1
                    if empty_pages >= 2:
                        logger.info(f"  📭 No more products after page {page}")
                        break
                    page += 1
                    continue

                empty_pages = 0
                batch = []
                for item in items:
                    product = self._parse_product(item, cat_id, cat_name)
                    if product and product["product_id"] not in self.seen_product_ids:
                        self.seen_product_ids.add(product["product_id"])
                        batch.append(product)

                if batch:
                    self.all_products.extend(batch)
                    cat_count += len(batch)
                    total_new += len(batch)

                self.progress.update_product_progress(cat_id, page, len(batch))
                logger.info(
                    f"  📄 Page {page}: +{len(batch)} products "
                    f"(cat total: {cat_count}, overall: {len(self.all_products)})"
                )

                # Check if we've reached the last page
                paging = data.get("paging", {})
                last_page = paging.get("last_page", max_pages)
                if page >= last_page:
                    logger.info(f"  📭 Reached last page ({last_page})")
                    break

                page += 1  # Move to next page

            self.progress.mark_category_done(cat_id)
            logger.info(f"  ✅ {cat_name}: {cat_count} new products crawled")

            # Flush to disk after each category
            self._save_csv(self.all_products, PRODUCTS_CSV, PRODUCT_FIELDS)
            self._save_json(self.all_products, PRODUCTS_JSON)

        logger.info(f"\n📦 TOTAL: {len(self.all_products)} products ({total_new} new)\n")
        return self.all_products

    def _parse_product(self, item, category_id, category_name):
        """Parse a single product from the API response into our standardized schema."""
        try:
            # Handle quantity_sold which can be dict or int
            qty_sold = item.get("quantity_sold", 0)
            if isinstance(qty_sold, dict):
                qty_sold = qty_sold.get("value", 0)
            elif qty_sold is None:
                qty_sold = 0

            # Handle all_time_quantity_sold from visible_impression_info
            vis_info = item.get("visible_impression_info", {})
            amplitude = vis_info.get("amplitude", {})
            all_time_sold = amplitude.get("all_time_quantity_sold", qty_sold)
            final_sold = max(int(qty_sold), int(all_time_sold)) if all_time_sold else int(qty_sold)

            # Detect TikiNOW
            is_tiki_now = item.get("is_tikinow_delivery", False)

            # Detect freeship
            is_freeship = False
            if vis_info:
                is_freeship = amplitude.get("is_freeship_xtra", False)
            if not is_freeship:
                is_freeship = item.get("freeship_campaign", "") != ""

            return {
                "product_id": item.get("id"),
                "sku": item.get("sku", ""),
                "name": item.get("name", ""),
                "url_key": item.get("url_key", ""),
                "url_path": item.get("url_path", ""),
                "price": item.get("price", 0),
                "original_price": item.get("original_price", item.get("price", 0)),
                "discount": item.get("discount", 0),
                "discount_rate": item.get("discount_rate", 0),
                "rating_average": item.get("rating_average", 0),
                "review_count": item.get("review_count", 0),
                "quantity_sold": final_sold,
                "category_id": category_id,
                "category_name": item.get("primary_category_name", category_name),
                "brand_id": item.get("brand_id", 0),
                "brand_name": item.get("brand_name", "Không rõ"),
                "seller_id": item.get("seller_id", 0),
                "seller_name": item.get("seller_name", ""),
                "seller_product_id": item.get("seller_product_id", 0),
                "is_official_store": item.get("is_from_official_store", False),
                "is_authentic": bool(item.get("is_authentic", 0)),
                "is_tiki_now": is_tiki_now,
                "is_freeship_xtra": is_freeship,
                "origin": item.get("origin", ""),
                "thumbnail_url": item.get("thumbnail_url", ""),
                "inventory_status": "available" if item.get("availability", 0) == 1 else "unavailable",
                "crawled_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "data_source": "tiki_api",
            }
        except Exception as e:
            logger.error(f"Error parsing product {item.get('id', '?')}: {e}")
            return None

    # ================================================================
    # Phase 3: Crawl Reviews
    # ================================================================

    def crawl_reviews(self, max_pages_per_product=None):
        """Crawl reviews for all products that have review_count > 0."""
        logger.info("=" * 60)
        logger.info("⭐ PHASE 3: Crawling Reviews")
        logger.info("=" * 60)

        self.progress.set_phase("reviews")
        max_pages = max_pages_per_product or MAX_REVIEW_PAGES

        # Filter products that have reviews, sorted by review_count (highest first)
        products_with_reviews = [
            p for p in self.all_products
            if int(p.get("review_count", 0)) >= MIN_REVIEW_COUNT
        ]
        products_with_reviews.sort(key=lambda x: int(x.get("review_count", 0)), reverse=True)

        logger.info(f"🎯 {len(products_with_reviews)} products have reviews (min {MIN_REVIEW_COUNT})")
        total_new = 0

        for idx, product in enumerate(products_with_reviews, 1):
            pid = int(product["product_id"])

            # Skip already crawled
            if self.progress.is_product_reviews_done(pid):
                continue

            review_count = int(product.get("review_count", 0))
            product_name = product.get("name", "")[:50]

            logger.info(
                f"  [{idx}/{len(products_with_reviews)}] "
                f"Product {pid}: \"{product_name}...\" ({review_count} reviews)"
            )

            prod_reviews = []
            for page in range(1, max_pages + 1):
                params = {
                    "product_id": pid,
                    "sort": REVIEW_SORT,
                    "page": page,
                    "limit": REVIEWS_PER_PAGE,
                    "include": "comments,contribute_info",
                }

                resp = self.rate_limiter.request_with_retry(
                    self.session, "GET", TIKI_REVIEWS_API, params=params
                )

                if not resp:
                    self.progress.increment_errors()
                    break

                try:
                    data = resp.json()
                    items = data.get("data", [])
                except (json.JSONDecodeError, KeyError):
                    self.progress.increment_errors()
                    break

                if not items:
                    break

                for r in items:
                    review = self._parse_review(r, pid)
                    if review and review["review_id"] not in self.seen_review_ids:
                        self.seen_review_ids.add(review["review_id"])
                        prod_reviews.append(review)

                # Check pagination
                paging = data.get("paging", {})
                if page >= paging.get("last_page", 1):
                    break

            if prod_reviews:
                self.all_reviews.extend(prod_reviews)
                total_new += len(prod_reviews)
                self.progress.update_review_progress(pid, len(prod_reviews))
                logger.info(f"    ✅ +{len(prod_reviews)} reviews (total: {len(self.all_reviews)})")

            self.progress.mark_product_reviews_done(pid)

            # Periodic flush
            if idx % 100 == 0:
                self._save_csv(self.all_reviews, REVIEWS_CSV, REVIEW_FIELDS)
                self._save_json(self.all_reviews, REVIEWS_JSON)
                logger.info(f"  💾 Flushed {len(self.all_reviews)} reviews to disk")

        # Final save
        self._save_csv(self.all_reviews, REVIEWS_CSV, REVIEW_FIELDS)
        self._save_json(self.all_reviews, REVIEWS_JSON)
        logger.info(f"\n⭐ TOTAL: {len(self.all_reviews)} reviews ({total_new} new)\n")
        return self.all_reviews

    def _parse_review(self, r, product_id):
        """Parse a single review from the API response into our standardized schema."""
        try:
            review_id = r.get("id")
            if not review_id:
                return None

            rating = r.get("rating", 0)
            if rating >= 4:
                sentiment = "POSITIVE"
            elif rating == 3:
                sentiment = "NEUTRAL"
            else:
                sentiment = "NEGATIVE"

            # Customer info
            created_by = r.get("created_by", {})
            customer_name = created_by.get("full_name", created_by.get("name", "Ẩn danh"))
            customer_id = created_by.get("id", r.get("customer_id", 0))
            is_purchased = created_by.get("purchased", False)

            # Images
            images = r.get("images", [])
            image_urls = []
            if images:
                for img in images:
                    if isinstance(img, dict):
                        image_urls.append(img.get("full_path", img.get("url", "")))
                    elif isinstance(img, str):
                        image_urls.append(img)

            # Seller info
            seller = r.get("seller", {})

            # Vote attributes
            vote_attrs = r.get("vote_attributes", {})
            vote_agree = vote_attrs.get("agree", [])
            vote_disagree = vote_attrs.get("disagree", [])

            # Usage duration from timeline
            timeline = r.get("timeline", {})
            usage_duration = timeline.get("content", "")

            # Product attributes (color, size, variant)
            product_attrs = r.get("product_attributes", [])

            # Created at timestamp
            created_ts = r.get("created_at", 0)
            if isinstance(created_ts, (int, float)) and created_ts > 0:
                created_at = datetime.fromtimestamp(created_ts).strftime("%Y-%m-%d %H:%M:%S")
            else:
                created_at = ""

            return {
                "review_id": review_id,
                "product_id": product_id,
                "customer_id": customer_id,
                "customer_name": customer_name,
                "rating": rating,
                "title": r.get("title", ""),
                "content": r.get("content", ""),
                "thank_count": r.get("thank_count", 0),
                "is_purchased": is_purchased,
                "has_images": len(image_urls) > 0,
                "images": json.dumps(image_urls, ensure_ascii=False) if image_urls else "[]",
                "seller_id": seller.get("id", 0),
                "seller_name": seller.get("name", ""),
                "product_attributes": json.dumps(product_attrs, ensure_ascii=False) if product_attrs else "[]",
                "vote_agree": json.dumps(vote_agree, ensure_ascii=False) if vote_agree else "[]",
                "vote_disagree": json.dumps(vote_disagree, ensure_ascii=False) if vote_disagree else "[]",
                "usage_duration": usage_duration,
                "sentiment": sentiment,
                "created_at": created_at,
                "crawled_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        except Exception as e:
            logger.error(f"Error parsing review {r.get('id', '?')}: {e}")
            return None

    # ================================================================
    # Extract Sellers
    # ================================================================

    def extract_sellers(self):
        """Extract unique sellers from crawled products and compute aggregated stats."""
        logger.info("=" * 60)
        logger.info("🏪 Extracting Sellers")
        logger.info("=" * 60)

        sellers_map = {}
        for p in self.all_products:
            sid = p.get("seller_id", 0)
            if not sid:
                continue
            sid = int(sid)

            if sid not in sellers_map:
                sellers_map[sid] = {
                    "seller_id": sid,
                    "seller_name": p.get("seller_name", ""),
                    "is_official_store": p.get("is_official_store", False),
                    "total_products": 0,
                    "sum_rating": 0.0,
                    "total_reviews": 0,
                }

            sellers_map[sid]["total_products"] += 1
            sellers_map[sid]["sum_rating"] += float(p.get("rating_average", 0))
            sellers_map[sid]["total_reviews"] += int(p.get("review_count", 0))

        sellers = []
        for s in sellers_map.values():
            avg_rating = round(s["sum_rating"] / s["total_products"], 2) if s["total_products"] > 0 else 0
            sellers.append({
                "seller_id": s["seller_id"],
                "seller_name": s["seller_name"],
                "is_official_store": s["is_official_store"],
                "total_products": s["total_products"],
                "avg_rating": avg_rating,
                "total_reviews": s["total_reviews"],
            })

        sellers.sort(key=lambda x: x["total_products"], reverse=True)

        self._save_csv(sellers, SELLERS_CSV, SELLER_FIELDS)
        self._save_json(sellers, SELLERS_JSON)
        logger.info(f"🏪 Extracted {len(sellers)} unique sellers\n")
        return sellers

    # ================================================================
    # I/O Helpers
    # ================================================================

    def _save_csv(self, data, filename, fieldnames):
        """Save data to CSV with proper UTF-8 encoding."""
        if not data:
            return
        filepath = os.path.join(self.output_dir, filename)
        try:
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
                writer.writeheader()
                writer.writerows(data)
        except Exception as e:
            logger.error(f"Failed to save CSV {filename}: {e}")

    def _save_json(self, data, filename):
        """Save data to JSON with proper UTF-8 encoding."""
        if not data:
            return
        filepath = os.path.join(self.output_dir, filename)
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save JSON {filename}: {e}")

    def get_products_for_detail_scraping(self, max_count=None):
        """Get list of products sorted by popularity for detail scraping (Source #2)."""
        sorted_products = sorted(
            self.all_products,
            key=lambda x: (int(x.get("review_count", 0)), int(x.get("quantity_sold", 0))),
            reverse=True,
        )
        if max_count:
            sorted_products = sorted_products[:max_count]
        return sorted_products


# ================================================================
# CLI Entry Point
# ================================================================

def main():
    """Run the full Tiki API crawler pipeline."""
    import argparse

    parser = argparse.ArgumentParser(description="🕷️ Tiki API Crawler — Full Pipeline")
    parser.add_argument("--fresh", action="store_true", help="Start fresh crawl (ignore progress)")
    parser.add_argument("--max-pages", type=int, default=MAX_PRODUCT_PAGES, help="Max pages per category")
    parser.add_argument("--max-review-pages", type=int, default=MAX_REVIEW_PAGES, help="Max review pages per product")
    parser.add_argument("--skip-reviews", action="store_true", help="Skip crawling reviews")
    parser.add_argument("--category", type=int, default=None, help="Crawl only this category ID")
    args = parser.parse_args()

    crawler = TikiAPICrawler(fresh=args.fresh)

    # Phase 1: Categories
    crawler.crawl_categories()

    # Phase 2: Products
    crawler.crawl_products(max_pages_per_cat=args.max_pages)

    # Phase 3: Reviews
    if not args.skip_reviews:
        crawler.crawl_reviews(max_pages_per_product=args.max_review_pages)

    # Extract Sellers
    crawler.extract_sellers()

    # Summary
    logger.info(crawler.progress.get_summary())
    logger.info("🏁 Crawl complete!")


if __name__ == "__main__":
    main()
