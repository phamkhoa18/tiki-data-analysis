#!/usr/bin/env python3
"""
Tiki Crawler Configuration
Centralized settings for API endpoints, categories, rate limits, and output paths.
"""

import os

# ============================================================
# API Endpoints
# ============================================================
TIKI_BASE_URL = "https://tiki.vn"
TIKI_PRODUCTS_API = f"{TIKI_BASE_URL}/api/v2/products"
TIKI_REVIEWS_API = f"{TIKI_BASE_URL}/api/v2/reviews"
TIKI_PRODUCT_DETAIL_URL = f"{TIKI_BASE_URL}/api/v2/products/{{product_id}}"

# ============================================================
# Categories to Crawl (10 danh mục lớn trên Tiki)
# ============================================================
CATEGORIES = [
    {"id": 1789, "name": "Điện Thoại - Máy Tính Bảng",   "slug": "dien-thoai-may-tinh-bang"},
    {"id": 1815, "name": "Thiết Bị Số - Phụ Kiện Số",     "slug": "thiet-bi-so-phu-kien-so"},
    {"id": 1882, "name": "Điện Gia Dụng",                 "slug": "dien-gia-dung"},
    {"id": 8322, "name": "Nhà Sách Tiki",                 "slug": "nha-sach-tiki"},
    {"id": 1520, "name": "Làm Đẹp - Sức Khỏe",           "slug": "lam-dep-suc-khoe"},
    {"id": 915,  "name": "Thời Trang Nam",                "slug": "thoi-trang-nam"},
    {"id": 931,  "name": "Thời Trang Nữ",                 "slug": "thoi-trang-nu"},
    {"id": 1883, "name": "Nhà Cửa - Đời Sống",            "slug": "nha-cua-doi-song"},
    {"id": 4384, "name": "Bách Hóa Online",               "slug": "bach-hoa-online"},
    {"id": 1975, "name": "Thể Thao - Dã Ngoại",           "slug": "the-thao-da-ngoai"},
]

# ============================================================
# Crawl Parameters
# ============================================================
# Products
PRODUCTS_PER_PAGE = 40          # Max items per API page (Tiki limit)
MAX_PRODUCT_PAGES = 50          # Max pages per category (50 × 40 = 2000 products/cat)
PRODUCT_SORT = "top_seller"     # Sort: top_seller, default, newest, price_asc, price_desc

# Reviews
REVIEWS_PER_PAGE = 20           # Max reviews per API page
MAX_REVIEW_PAGES = 5            # Max pages per product (5 × 20 = 100 reviews/product)
MIN_REVIEW_COUNT = 1            # Only crawl products with at least this many reviews
REVIEW_SORT = "score|desc"      # Sort: score|desc (most helpful first)

# Web Scraping (Source #2)
MAX_DETAIL_PAGES = 1000         # Max products to scrape detail pages for
SCRAPE_DELAY_MIN = 1.0          # Min delay between web scrape requests (seconds)
SCRAPE_DELAY_MAX = 2.5          # Max delay between web scrape requests (seconds)

# ============================================================
# Rate Limiting & Retry
# ============================================================
API_DELAY_MIN = 0.5             # Min delay between API requests (seconds)
API_DELAY_MAX = 1.2             # Max delay between API requests (seconds)
MAX_RETRIES = 3                 # Max retry attempts per request
RETRY_BACKOFF_BASE = 2.0        # Exponential backoff base (2s, 4s, 8s)
REQUEST_TIMEOUT = 15            # HTTP request timeout (seconds)

# ============================================================
# User Agents (Rotate to avoid detection)
# ============================================================
USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:127.0) Gecko/20100101 Firefox/127.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
]

# ============================================================
# Output Paths
# ============================================================
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW_DATA_DIR = os.path.join(_BASE_DIR, "dataset", "raw")
PROGRESS_FILE = os.path.join(RAW_DATA_DIR, ".crawl_progress.json")

# Output filenames
CATEGORIES_CSV = "tiki_categories.csv"
CATEGORIES_JSON = "tiki_categories.json"
PRODUCTS_CSV = "tiki_products.csv"
PRODUCTS_JSON = "tiki_products.json"
PRODUCT_DETAILS_CSV = "tiki_product_details.csv"
PRODUCT_DETAILS_JSON = "tiki_product_details.json"
REVIEWS_CSV = "tiki_reviews.csv"
REVIEWS_JSON = "tiki_reviews.json"
SELLERS_CSV = "tiki_sellers.csv"
SELLERS_JSON = "tiki_sellers.json"

# Flush buffer size (save to disk every N records)
FLUSH_BUFFER_SIZE = 100

# ============================================================
# Logging
# ============================================================
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
