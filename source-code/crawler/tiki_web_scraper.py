#!/usr/bin/env python3
"""
Tiki Web Scraper — Source #2 Data Collector
Scrapes product detail pages from tiki.vn to collect:
- Product descriptions, specifications, images
- Warranty info, return policy
- Additional metadata not available via API

This serves as the SECOND data source (yêu cầu tối thiểu 2 nguồn).
Uses BeautifulSoup + requests for HTML parsing.
"""

import os
import json
import csv
import logging
from datetime import datetime

try:
    from curl_cffi import requests
    CURL_CFFI_AVAILABLE = True
except ImportError:
    import requests
    CURL_CFFI_AVAILABLE = False

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

try:
    from .config import (
        TIKI_BASE_URL, TIKI_PRODUCT_DETAIL_URL,
        RAW_DATA_DIR, PRODUCT_DETAILS_CSV, PRODUCT_DETAILS_JSON,
        MAX_DETAIL_PAGES, SCRAPE_DELAY_MIN, SCRAPE_DELAY_MAX,
        LOG_FORMAT, LOG_DATE_FORMAT,
    )
    from .rate_limiter import PoliteRateLimiter
    from .progress_tracker import ProgressTracker
except ImportError:
    from config import (
        TIKI_BASE_URL, TIKI_PRODUCT_DETAIL_URL,
        RAW_DATA_DIR, PRODUCT_DETAILS_CSV, PRODUCT_DETAILS_JSON,
        MAX_DETAIL_PAGES, SCRAPE_DELAY_MIN, SCRAPE_DELAY_MAX,
        LOG_FORMAT, LOG_DATE_FORMAT,
    )
    from rate_limiter import PoliteRateLimiter
    from progress_tracker import ProgressTracker

logging.basicConfig(level=logging.INFO, format=LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
logger = logging.getLogger("TikiScraper")

DETAIL_FIELDS = [
    "product_id", "short_description", "description_html",
    "specifications", "images", "warranty_info", "return_policy",
    "all_categories", "breadcrumbs", "configurable_options",
    "crawled_at", "data_source",
]


class TikiWebScraper:
    """
    Scrapes Tiki product detail pages via the product detail API endpoint.
    
    Tiki serves product details through a JSON API at:
    https://tiki.vn/api/v2/products/{product_id}
    
    This provides much richer data than the listing API, including:
    - Full HTML description
    - Specification tables
    - All product images
    - Warranty and return policy
    - Category breadcrumbs
    - Configurable options (colors, sizes, etc.)
    """

    def __init__(self, output_dir=None):
        self.rate_limiter = PoliteRateLimiter(
            min_delay=SCRAPE_DELAY_MIN,
            max_delay=SCRAPE_DELAY_MAX,
        )
        if CURL_CFFI_AVAILABLE:
            self.session = requests.Session(impersonate="safari17_0")
        else:
            self.session = requests.Session()
        self.output_dir = output_dir or RAW_DATA_DIR
        os.makedirs(self.output_dir, exist_ok=True)
        self.progress = ProgressTracker()
        self.all_details = []

        # Load existing details for dedup
        self._load_existing_details()

    def _load_existing_details(self):
        """Load existing scraped details when resuming."""
        details_path = os.path.join(self.output_dir, PRODUCT_DETAILS_CSV)
        if os.path.exists(details_path):
            try:
                with open(details_path, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    self.all_details = list(reader)
                logger.info(f"📂 Loaded {len(self.all_details)} existing product details")
            except Exception as e:
                logger.warning(f"Could not load existing details: {e}")

    def scrape_product_details(self, products, max_count=None):
        """
        Scrape detailed info for a list of products.
        
        Args:
            products: List of product dicts (must have 'product_id' and 'url_path')
            max_count: Maximum number of products to scrape (None = use config default)
        """
        logger.info("=" * 60)
        logger.info("🌐 PHASE 4: Web Scraping Product Details (Source #2)")
        logger.info("=" * 60)

        self.progress.set_phase("details")
        max_count = max_count or MAX_DETAIL_PAGES
        products_to_scrape = products[:max_count]

        logger.info(f"🎯 Scraping details for {len(products_to_scrape)} products")
        total_new = 0

        for idx, product in enumerate(products_to_scrape, 1):
            pid = int(product.get("product_id", product.get("id", 0)))

            # Skip already scraped
            if self.progress.is_product_detail_done(pid):
                continue

            product_name = product.get("name", "")[:40]
            logger.info(f"  [{idx}/{len(products_to_scrape)}] Product {pid}: \"{product_name}...\"")

            detail = self._scrape_single_product(pid)

            if detail:
                self.all_details.append(detail)
                self.progress.update_detail_progress(pid)
                total_new += 1
                logger.info(f"    ✅ Scraped successfully")
            else:
                self.progress.increment_errors()
                logger.warning(f"    ❌ Failed to scrape")

            # Periodic flush
            if idx % 50 == 0:
                self._save_all()
                logger.info(f"  💾 Flushed {len(self.all_details)} details to disk")

        # Final save
        self._save_all()
        logger.info(f"\n🌐 TOTAL: {len(self.all_details)} product details ({total_new} new)\n")
        return self.all_details

    def _scrape_single_product(self, product_id):
        """Scrape detailed info for a single product via the detail API."""
        url = TIKI_PRODUCT_DETAIL_URL.format(product_id=product_id)

        resp = self.rate_limiter.request_with_retry(
            self.session, "GET", url,
            params={"platform": "web", "spid": product_id},
        )

        if not resp:
            return None

        try:
            data = resp.json()
        except (json.JSONDecodeError, KeyError):
            return None

        return self._parse_detail(data, product_id)

    def _parse_detail(self, data, product_id):
        """Parse product detail JSON response into our schema."""
        try:
            # Description
            short_desc = data.get("short_description", "")
            desc_html = data.get("description", "")

            # Clean HTML description text (basic strip)
            desc_text = desc_html
            if BeautifulSoup and desc_html:
                try:
                    soup = BeautifulSoup(desc_html, "html.parser")
                    desc_text = soup.get_text(separator="\n", strip=True)
                except Exception:
                    pass

            # Specifications
            specifications = {}
            specs_list = data.get("specifications", [])
            for spec_group in specs_list:
                group_name = spec_group.get("name", "General")
                attrs = spec_group.get("attributes", [])
                for attr in attrs:
                    attr_name = attr.get("name", "")
                    attr_value = attr.get("value", "")
                    if attr_name:
                        specifications[attr_name] = attr_value

            # Images
            images = []
            img_list = data.get("images", [])
            for img in img_list:
                if isinstance(img, dict):
                    large_url = img.get("large_url", img.get("base_url", ""))
                    if large_url:
                        images.append(large_url)
                elif isinstance(img, str):
                    images.append(img)

            # Warranty
            warranty_info = data.get("warranty_info", [])
            warranty_text = ""
            if isinstance(warranty_info, list):
                parts = []
                for w in warranty_info:
                    if isinstance(w, dict):
                        parts.append(f"{w.get('name', '')}: {w.get('value', '')}")
                    elif isinstance(w, str):
                        parts.append(w)
                warranty_text = " | ".join(parts)
            elif isinstance(warranty_info, str):
                warranty_text = warranty_info

            # Return policy
            return_policy = ""
            return_info = data.get("return_and_exchange_policy", "")
            if return_info:
                return_policy = str(return_info)

            # Category breadcrumbs
            breadcrumbs = data.get("breadcrumbs", [])
            breadcrumb_names = []
            for bc in breadcrumbs:
                if isinstance(bc, dict):
                    breadcrumb_names.append(bc.get("name", ""))

            # Configurable options (colors, sizes, etc.)
            config_options = data.get("configurable_options", [])
            config_summary = []
            for opt in config_options:
                if isinstance(opt, dict):
                    opt_name = opt.get("name", "")
                    values = opt.get("values", [])
                    opt_values = [v.get("label", "") for v in values if isinstance(v, dict)]
                    config_summary.append({"name": opt_name, "values": opt_values})

            # All categories
            all_cats = []
            categories_data = data.get("categories", {})
            if isinstance(categories_data, dict):
                all_cats = [categories_data.get("name", "")]
            elif isinstance(categories_data, list):
                all_cats = [c.get("name", "") for c in categories_data if isinstance(c, dict)]

            return {
                "product_id": product_id,
                "short_description": short_desc[:5000] if short_desc else "",
                "description_html": desc_text[:10000] if desc_text else "",
                "specifications": json.dumps(specifications, ensure_ascii=False),
                "images": json.dumps(images, ensure_ascii=False),
                "warranty_info": warranty_text,
                "return_policy": return_policy[:2000] if return_policy else "",
                "all_categories": json.dumps(all_cats, ensure_ascii=False),
                "breadcrumbs": json.dumps(breadcrumb_names, ensure_ascii=False),
                "configurable_options": json.dumps(config_summary, ensure_ascii=False),
                "crawled_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "data_source": "tiki_web",
            }
        except Exception as e:
            logger.error(f"Error parsing detail for product {product_id}: {e}")
            return None

    def _save_all(self):
        """Save all details to CSV and JSON."""
        if not self.all_details:
            return

        # CSV
        filepath_csv = os.path.join(self.output_dir, PRODUCT_DETAILS_CSV)
        try:
            with open(filepath_csv, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=DETAIL_FIELDS, extrasaction="ignore")
                writer.writeheader()
                writer.writerows(self.all_details)
        except Exception as e:
            logger.error(f"Failed to save CSV: {e}")

        # JSON
        filepath_json = os.path.join(self.output_dir, PRODUCT_DETAILS_JSON)
        try:
            with open(filepath_json, "w", encoding="utf-8") as f:
                json.dump(self.all_details, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save JSON: {e}")


# ================================================================
# CLI Entry Point
# ================================================================

def main():
    """Run web scraper standalone (requires products already crawled)."""
    import argparse

    parser = argparse.ArgumentParser(description="🌐 Tiki Web Scraper — Source #2")
    parser.add_argument("--max-count", type=int, default=MAX_DETAIL_PAGES, help="Max products to scrape")
    args = parser.parse_args()

    # Load products from CSV
    products_csv = os.path.join(RAW_DATA_DIR, "tiki_products.csv")
    if not os.path.exists(products_csv):
        logger.error(f"Products CSV not found: {products_csv}")
        logger.error("Run tiki_api_crawler.py first to crawl products!")
        return

    products = []
    with open(products_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        products = list(reader)

    # Sort by review count (most popular first)
    products.sort(key=lambda x: int(x.get("review_count", 0)), reverse=True)

    logger.info(f"Loaded {len(products)} products from {products_csv}")

    scraper = TikiWebScraper()
    scraper.scrape_product_details(products, max_count=args.max_count)

    logger.info("🏁 Scraping complete!")


if __name__ == "__main__":
    main()
