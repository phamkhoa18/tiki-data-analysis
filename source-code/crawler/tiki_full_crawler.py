#!/usr/bin/env python3
"""
🕷️ Tiki Full Crawler — Master Orchestrator
Runs the complete data collection pipeline:
  Phase 1: Crawl categories metadata
  Phase 2: Crawl products across 10 categories (API — Source #1)
  Phase 3: Crawl reviews for products with ratings (API — Source #1)
  Phase 4: Scrape product details (Web — Source #2)
  Phase 5: Validate, clean, and export all data

Usage:
  # Full pipeline (recommended)
  python tiki_full_crawler.py

  # Fresh start (ignore previous progress)
  python tiki_full_crawler.py --fresh

  # Quick test (5 pages per category, skip web scraping)
  python tiki_full_crawler.py --max-pages 5 --skip-details

  # Only products (skip reviews and details)
  python tiki_full_crawler.py --skip-reviews --skip-details
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime

try:
    from .config import (
        RAW_DATA_DIR, MAX_PRODUCT_PAGES, MAX_REVIEW_PAGES,
        MAX_DETAIL_PAGES, LOG_FORMAT, LOG_DATE_FORMAT,
    )
    from .tiki_api_crawler import TikiAPICrawler
    from .tiki_web_scraper import TikiWebScraper
    from .data_validator import DataValidator
except ImportError:
    from config import (
        RAW_DATA_DIR, MAX_PRODUCT_PAGES, MAX_REVIEW_PAGES,
        MAX_DETAIL_PAGES, LOG_FORMAT, LOG_DATE_FORMAT,
    )
    from tiki_api_crawler import TikiAPICrawler
    from tiki_web_scraper import TikiWebScraper
    from data_validator import DataValidator

logging.basicConfig(level=logging.INFO, format=LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
logger = logging.getLogger("TikiPipeline")


def print_banner():
    """Print a cool banner."""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   🕷️  TIKI DATA CRAWLER — Big Data Project                  ║
║   ─────────────────────────────────────────────              ║
║   📦 Products + ⭐ Reviews + 🌐 Details                     ║
║   🔗 Source #1: Tiki REST API                                ║
║   🔗 Source #2: Tiki Product Detail Pages                    ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def run_full_pipeline(args):
    """Run the complete Tiki data collection pipeline."""
    start_time = datetime.now()
    print_banner()

    logger.info(f"🚀 Starting Tiki Full Crawler Pipeline")
    logger.info(f"   Max pages/category: {args.max_pages}")
    logger.info(f"   Max review pages/product: {args.max_review_pages}")
    logger.info(f"   Max detail pages: {args.max_details}")
    logger.info(f"   Skip reviews: {args.skip_reviews}")
    logger.info(f"   Skip details: {args.skip_details}")
    logger.info(f"   Fresh start: {args.fresh}")
    logger.info("")

    # ========================================
    # Phase 1-3: API Crawler
    # ========================================
    crawler = TikiAPICrawler(fresh=args.fresh)

    # Phase 1: Categories
    crawler.crawl_categories()

    # Phase 2: Products
    crawler.crawl_products(max_pages_per_cat=args.max_pages)

    # Phase 3: Reviews
    if not args.skip_reviews:
        crawler.crawl_reviews(max_pages_per_product=args.max_review_pages)

    # Extract sellers
    crawler.extract_sellers()

    # ========================================
    # Phase 4: Web Scraper (Source #2)
    # ========================================
    if not args.skip_details:
        scraper = TikiWebScraper()
        products_for_scraping = crawler.get_products_for_detail_scraping(max_count=args.max_details)
        scraper.scrape_product_details(products_for_scraping, max_count=args.max_details)

    # ========================================
    # Phase 5: Validate & Clean
    # ========================================
    logger.info("=" * 60)
    logger.info("🧹 PHASE 5: Data Validation & Cleaning")
    logger.info("=" * 60)

    validator = DataValidator()

    # Validate products
    cleaned_products = validator.validate_products(crawler.all_products)
    crawler.all_products = cleaned_products
    crawler._save_csv(cleaned_products, "tiki_products.csv",
                      list(cleaned_products[0].keys()) if cleaned_products else [])
    crawler._save_json(cleaned_products, "tiki_products.json")

    # Validate reviews
    if crawler.all_reviews:
        cleaned_reviews = validator.validate_reviews(crawler.all_reviews)
        crawler.all_reviews = cleaned_reviews
        crawler._save_csv(cleaned_reviews, "tiki_reviews.csv",
                          list(cleaned_reviews[0].keys()) if cleaned_reviews else [])
        crawler._save_json(cleaned_reviews, "tiki_reviews.json")

    validation_stats = validator.get_stats()
    logger.info(f"  🧹 Validation stats: {json.dumps(validation_stats, indent=2)}")

    # ========================================
    # Final Summary
    # ========================================
    elapsed = datetime.now() - start_time
    logger.info(crawler.progress.get_summary())

    summary = f"""
╔══════════════════════════════════════════════════════════════╗
║  🏁 CRAWL COMPLETE                                          ║
╠══════════════════════════════════════════════════════════════╣
║  📦 Products:  {len(crawler.all_products):>8,}                                   ║
║  ⭐ Reviews:   {len(crawler.all_reviews):>8,}                                   ║
║  🏪 Sellers:   (see tiki_sellers.csv)                        ║
║  📋 Categories: {len(crawler.all_categories):>6}                                     ║
║  ⏱️  Duration:  {str(elapsed).split('.')[0]:>15}                          ║
║                                                              ║
║  📁 Output: {RAW_DATA_DIR:<45}  ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(summary)

    # Save summary report
    report = {
        "crawl_completed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "duration_seconds": elapsed.total_seconds(),
        "total_products": len(crawler.all_products),
        "total_reviews": len(crawler.all_reviews),
        "total_categories": len(crawler.all_categories),
        "validation_stats": validation_stats,
        "rate_limiter_stats": crawler.rate_limiter.get_stats(),
        "output_directory": RAW_DATA_DIR,
        "data_sources": ["tiki_api (products + reviews)", "tiki_web (product details)"],
        "files_generated": [
            "tiki_categories.csv", "tiki_categories.json",
            "tiki_products.csv", "tiki_products.json",
            "tiki_reviews.csv", "tiki_reviews.json",
            "tiki_sellers.csv", "tiki_sellers.json",
            "tiki_product_details.csv", "tiki_product_details.json",
        ],
    }
    report_path = os.path.join(RAW_DATA_DIR, "crawl_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    logger.info(f"📄 Crawl report saved to: {report_path}")

    # Auto-generate consolidated Master CSV
    try:
        from .create_master_csv import build_master_dataset
    except ImportError:
        from create_master_csv import build_master_dataset
    build_master_dataset()
    import shutil
    m_src = os.path.join(os.path.dirname(RAW_DATA_DIR), "processed", "tiki_master_dataset_all_in_one.csv")
    m_dst = os.path.join(os.path.dirname(RAW_DATA_DIR), "tiki_master_dataset_all_in_one.csv")
    if os.path.exists(m_src):
        shutil.copy2(m_src, m_dst)


def main():
    parser = argparse.ArgumentParser(
        description="🕷️ Tiki Full Crawler — Master Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tiki_full_crawler.py                          # Full pipeline
  python tiki_full_crawler.py --fresh                  # Fresh start
  python tiki_full_crawler.py --max-pages 5            # Quick test
  python tiki_full_crawler.py --skip-reviews           # Products only
  python tiki_full_crawler.py --skip-details           # Skip web scraping
        """,
    )
    parser.add_argument("--fresh", action="store_true",
                        help="Start fresh crawl (ignore previous progress)")
    parser.add_argument("--max-pages", type=int, default=MAX_PRODUCT_PAGES,
                        help=f"Max pages per category (default: {MAX_PRODUCT_PAGES})")
    parser.add_argument("--max-review-pages", type=int, default=MAX_REVIEW_PAGES,
                        help=f"Max review pages per product (default: {MAX_REVIEW_PAGES})")
    parser.add_argument("--max-details", type=int, default=MAX_DETAIL_PAGES,
                        help=f"Max products to scrape details (default: {MAX_DETAIL_PAGES})")
    parser.add_argument("--skip-reviews", action="store_true",
                        help="Skip crawling reviews")
    parser.add_argument("--skip-details", action="store_true",
                        help="Skip web scraping product details")

    args = parser.parse_args()
    run_full_pipeline(args)


if __name__ == "__main__":
    main()
