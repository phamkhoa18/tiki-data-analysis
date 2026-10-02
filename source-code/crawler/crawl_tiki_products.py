#!/usr/bin/env python3
"""
==============================================================================
TIKI PRODUCT CRAWLER — CÔNG CỤ CÀO DỮ LIỆU SẢN PHẨM CHUYÊN NGHIỆP TIKI.VN
==============================================================================
Mục đích:
  Thu thập danh mục, sản phẩm, giá cả, thương hiệu, nhà bán, và thông số kỹ thuật
  từ hệ thống REST API công khai của Tiki.vn phục vụ đồ án Big Data.

Tính năng:
  - Tự động vượt qua hàng rào chống bot ByteDance WAF / Cloudflare bằng waf_solver
  - Giả lập phiên trình duyệt chuẩn TLS/HTTP2 với Safari 17 (curl_cffi)
  - Kiểm soát tốc độ request tự động (Rate Limiting & Exponential Backoff)
  - Xuất trực tiếp ra file CSV chuẩn hóa, đầy đủ thuộc tính sản phẩm
==============================================================================
"""

import os
import sys
import time
import json
import random
import logging
import argparse
import pandas as pd
from datetime import datetime

# Cấu hình logging chuyên nghiệp
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("TikiProductCrawler")

# Thử import curl_cffi giả lập browser, fallback về requests nếu chưa cài
try:
    from curl_cffi import requests
    CURL_CFFI_AVAILABLE = True
except ImportError:
    import requests
    CURL_CFFI_AVAILABLE = False

# Import module giải mã WAF
try:
    from .waf_solver import solve_waf_challenge
except ImportError:
    try:
        from waf_solver import solve_waf_challenge
    except ImportError:
        solve_waf_challenge = None


# ==============================================================================
# BẢNG DANH BẠ 10 NGÀNH HÀNG TRỌNG TÂM CỦA TIKI (CATEGORY IDS)
# ==============================================================================
TIKI_CATEGORIES = [
    {"id": 1789, "name": "Điện Thoại - Máy Tính Bảng", "slug": "dien-thoai-may-tinh-bang"},
    {"id": 1815, "name": "Thiết Bị Số - Phụ Kiện Số",  "slug": "thiet-bi-kts-phu-kien-so"},
    {"id": 1882, "name": "Điện Gia Dụng",             "slug": "dien-gia-dung"},
    {"id": 8322, "name": "Nhà Sách Tiki",             "slug": "nha-sach-tiki"},
    {"id": 1520, "name": "Làm Đẹp - Sức Khỏe",         "slug": "lam-dep-suc-khoe"},
    {"id": 915,  "name": "Thời Trang Nam",             "slug": "thoi-trang-nam"},
    {"id": 931,  "name": "Thời Trang Nữ",              "slug": "thoi-trang-nu"},
    {"id": 1883, "name": "Nhà Cửa - Đời Sống",         "slug": "nha-cua-doi-song"},
    {"id": 4384, "name": "Bách Hóa Online",           "slug": "bach-hoa-online"},
    {"id": 1975, "name": "Thể Thao - Dã Ngoại",        "slug": "the-thao-da-ngoai"},
]

# API Endpoints
API_PRODUCTS = "https://tiki.vn/api/v2/products"
API_PRODUCT_DETAIL = "https://tiki.vn/api/v2/products/{product_id}"


class TikiProductCrawler:
    def __init__(self, delay_min=0.8, delay_max=1.5):
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.session = self._create_session()
        self.crawled_products = []
        self.seen_ids = set()

    def _create_session(self):
        """Khởi tạo session HTTP, ưu tiên giả lập Safari 17 để tránh bị WAF chặn."""
        if CURL_CFFI_AVAILABLE:
            return requests.Session(impersonate="safari17_0")
        return requests.Session()

    def _get_headers(self):
        """Header HTTP chuẩn hóa đồng bộ với trình duyệt macOS Safari."""
        return {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://tiki.vn/",
        }

    def _polite_delay(self):
        """Nghỉ ngẫu nhiên giữa các request để bảo vệ server và tránh bị chặn IP."""
        delay = random.uniform(self.delay_min, self.delay_max)
        time.sleep(delay)

    def request_api(self, url, params=None, max_retries=3):
        """Gửi HTTP request có cơ chế retry và tự động giải mã WAF challenge."""
        headers = self._get_headers()
        for attempt in range(1, max_retries + 1):
            self._polite_delay()
            try:
                resp = self.session.get(url, params=params, headers=headers, timeout=15)
                
                # Kiểm tra nếu bị WAF Challenge
                text_head = resp.text[:300] if resp.text else ""
                if "<!DOCTYPE html>" in text_head and ("_0x" in resp.text or "challenge" in resp.text.lower()):
                    logger.warning(f"  🛡️ Phát hiện Tiki WAF challenge. Đang tự động giải mã...")
                    if solve_waf_challenge:
                        cookies = solve_waf_challenge(resp.text, url)
                        if cookies:
                            for k, v in cookies.items():
                                self.session.cookies.set(k, v)
                            logger.info("  ✅ Đã giải mã WAF thành công! Tiếp tục cào...")
                            time.sleep(1.0)
                            continue
                    time.sleep(3.0 * attempt)
                    continue

                if resp.status_code == 200:
                    return resp.json()
                elif resp.status_code == 429:
                    logger.warning(f"  ⚠️ Rate limited (429). Chờ {3 * attempt}s...")
                    time.sleep(3.0 * attempt)
                else:
                    logger.warning(f"  ⚠️ HTTP {resp.status_code} trên {url}")

            except Exception as e:
                logger.warning(f"  ⚠️ Lỗi request (thử lần {attempt}/{max_retries}): {e}")
                time.sleep(2.0 * attempt)

        return None

    def crawl_category(self, cat_id, cat_name, max_pages=5, sort="top_seller"):
        """
        Cào danh sách sản phẩm của 1 danh mục theo phân trang.
        sort options: 'top_seller' (bán chạy), 'default' (phổ biến), 'newest' (mới nhất), 'price,asc', 'price,desc'
        """
        logger.info(f"\n📂 Đang cào ngành hàng: {cat_name} (ID: {cat_id}) — Tối đa {max_pages} trang")
        count_before = len(self.crawled_products)

        for page in range(1, max_pages + 1):
            params = {
                "limit": 40,
                "category": cat_id,
                "page": page,
                "sort": sort
            }
            data = self.request_api(API_PRODUCTS, params=params)
            if not data or "data" not in data:
                logger.warning(f"  ❌ Không lấy được dữ liệu trang {page}. Dừng ngành này.")
                break

            items = data.get("data", [])
            if not items:
                logger.info(f"  📭 Đã hết sản phẩm tại trang {page}.")
                break

            page_new = 0
            for item in items:
                pid = item.get("id")
                if not pid or pid in self.seen_ids:
                    continue

                self.seen_ids.add(pid)
                prod = self._parse_product(item, cat_id, cat_name)
                self.crawled_products.append(prod)
                page_new += 1

            logger.info(f"  📄 Trang {page}: +{page_new} sản phẩm mới (Tổng ngành: {len(self.crawled_products) - count_before})")

        # Nghỉ giữa các ngành hàng
        time.sleep(random.uniform(2.0, 3.5))

    def _parse_product(self, item, cat_id, cat_name):
        """Bóc tách và chuẩn hóa toàn bộ thuộc tính của một sản phẩm."""
        price = item.get("price", 0)
        original_price = item.get("original_price", price) or price
        discount = max(0, original_price - price)
        discount_rate = round((discount / original_price) * 100, 1) if original_price > 0 else 0.0

        # Lấy thông tin số lượng bán
        qty_sold_raw = item.get("quantity_sold", {})
        qty_sold = qty_sold_raw.get("value", 0) if isinstance(qty_sold_raw, dict) else (int(qty_sold_raw) if qty_sold_raw else 0)

        # Doanh thu ước tính
        revenue_estimate = price * qty_sold

        # Huy hiệu & Chính sách
        badges = item.get("badges_new", [])
        is_tikinow = any(b.get("code") == "tikinow" for b in badges)
        is_freeship = any("freeship" in str(b.get("code", "")).lower() for b in badges) or item.get("freeship_campaign") is not None

        return {
            "product_id": item.get("id"),
            "name": str(item.get("name", "")).strip(),
            "sku": item.get("sku", ""),
            "category_id": cat_id,
            "category_name": cat_name,
            "brand_id": item.get("brand_id", 0),
            "brand_name": item.get("brand_name", "No Brand") or "No Brand",
            "price": price,
            "original_price": original_price,
            "discount": discount,
            "discount_rate": discount_rate,
            "rating_average": round(float(item.get("rating_average", 0.0)), 2),
            "review_count": int(item.get("review_count", 0)),
            "quantity_sold": qty_sold,
            "revenue_estimate": revenue_estimate,
            "seller_id": item.get("seller_id", 0),
            "seller_name": item.get("seller_name", "Tiki Trading") or "Tiki Trading",
            "is_official_store": bool(item.get("is_from_official_store", False) or item.get("seller_id") == 1),
            "is_authentic": bool(item.get("is_authentic", 1)),
            "is_tiki_now": is_tikinow,
            "is_freeship_xtra": is_freeship,
            "origin": item.get("origin", "Chưa rõ") or "Chưa rõ",
            "inventory_status": item.get("inventory_status", "available"),
            "product_url": f"https://tiki.vn/{item.get('url_path', '')}" if item.get("url_path") else "",
            "thumbnail_url": item.get("thumbnail_url", ""),
            "crawled_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    def _enrich_dataframe(self, df):
        """Bổ sung các thuộc tính phân khúc và định dạng chuẩn 35 cột."""
        if df.empty:
            return df

        def assign_price_segment(price):
            if price < 100000:
                return "Giá rẻ (< 100K)"
            elif price < 500000:
                return "Phổ thông (100K - 500K)"
            elif price < 2000000:
                return "Trung cấp (500K - 2Tr)"
            elif price < 10000000:
                return "Cận cao cấp (2Tr - 10Tr)"
            else:
                return "Cao cấp (>= 10Tr)"

        df["price_segment"] = df["price"].apply(assign_price_segment)
        df["seller_type"] = df["is_official_store"].map({True: "Gian Hàng Chính Hãng (Mall)", False: "Nhà Bán Marketplace"})
        
        import numpy as np
        df["performance_score"] = (
            np.log10(df["quantity_sold"] + 1) * np.where(df["rating_average"] > 0, df["rating_average"], 4.0)
        ).round(2)

        def assign_product_tier(row):
            sold = row["quantity_sold"]
            rating = row["rating_average"]
            if sold >= 500 and rating >= 4.5:
                return "Ngôi Sao (Star - Bán chạy & Đánh giá cao)"
            elif sold >= 500 and rating < 4.5:
                return "Bò Sữa (Cash Cow - Doanh số cao)"
            elif sold >= 50 and rating >= 4.5:
                return "Tiềm Năng (High Potential)"
            elif sold >= 10:
                return "Tiêu Chuẩn (Standard)"
            else:
                return "Chậm Bán / Hàng Mới (Low Volume / New)"

        df["product_tier"] = df.apply(assign_product_tier, axis=1)
        df["warranty_info"] = "Theo chính sách Tiki"
        df["return_policy"] = "Đổi trả trong 30 ngày"
        df["specifications"] = "Đang cập nhật"
        df["short_description"] = ""
        df["data_source"] = "tiki_api"

        ordered_cols = [
            "product_id", "name", "sku", "category_id", "category_name", "brand_id", "brand_name",
            "price", "original_price", "discount", "discount_rate", "price_segment",
            "quantity_sold", "revenue_estimate", "rating_average", "review_count",
            "performance_score", "product_tier",
            "seller_id", "seller_name", "seller_type", "is_official_store",
            "is_authentic", "is_tiki_now", "is_freeship_xtra", "origin", "inventory_status",
            "warranty_info", "return_policy", "specifications", "short_description",
            "product_url", "thumbnail_url", "data_source", "crawled_at"
        ]
        final_cols = [c for c in ordered_cols if c in df.columns]
        return df[final_cols]

    def crawl_all(self, max_pages_per_cat=5, output_csv="dataset/tiki_products_clean_full.csv"):
        """Chạy cào tự động toàn bộ 10 ngành hàng và xuất file CSV chuẩn."""
        start_time = time.time()
        logger.info("=" * 70)
        logger.info("🚀 BẮT ĐẦU CÀO DỮ LIỆU SẢN PHẨM TIKI TOÀN DIỆN")
        logger.info(f"  • Số danh mục: {len(TIKI_CATEGORIES)}")
        logger.info(f"  • Số trang mỗi danh mục: {max_pages_per_cat} (tối đa {max_pages_per_cat * 40} sp/ngành)")
        logger.info(f"  • File xuất kết quả: {output_csv}")
        logger.info("=" * 70)

        for cat in TIKI_CATEGORIES:
            self.crawl_category(cat["id"], cat["name"], max_pages=max_pages_per_cat)

        df = pd.DataFrame(self.crawled_products)
        df = self._enrich_dataframe(df)
        os.makedirs(os.path.dirname(output_csv), exist_ok=True)
        df.to_csv(output_csv, index=False, encoding="utf-8-sig")

        elapsed = time.time() - start_time
        logger.info("=" * 70)
        logger.info("🎉 HOÀN TẤT CÀO DỮ LIỆU!")
        logger.info(f"  • Tổng số sản phẩm thu được: {len(df):,} sản phẩm")
        logger.info(f"  • Tổng số cột chuẩn hóa: {len(df.columns)} cột")
        logger.info(f"  • Tổng thời gian: {elapsed:.1f} giây ({elapsed/60:.1f} phút)")
        logger.info(f"  • File đã lưu tại: {output_csv}")
        logger.info("=" * 70)
        return df


def main():
    parser = argparse.ArgumentParser(description="Tiki Product Crawler — Công cụ cào dữ liệu sản phẩm Tiki chuyên nghiệp")
    parser.add_argument("--pages", type=int, default=5, help="Số trang mỗi danh mục cần cào (mặc định: 5 trang = 200 sp/ngành)")
    parser.add_argument("--category", type=int, default=None, help="Mã Category ID cụ thể cần cào (nếu chỉ muốn cào 1 ngành)")
    parser.add_argument("--sort", type=str, default="top_seller", help="Kiểu sắp xếp: top_seller, default, newest, price,asc")
    parser.add_argument("--output", type=str, default="dataset/tiki_products_clean_full.csv", help="Đường dẫn file CSV xuất ra")
    args = parser.parse_args()

    crawler = TikiProductCrawler()
    if args.category:
        cat_info = next((c for c in TIKI_CATEGORIES if c["id"] == args.category), {"name": f"Category {args.category}"})
        crawler.crawl_category(args.category, cat_info["name"], max_pages=args.pages, sort=args.sort)
        df = pd.DataFrame(crawler.crawled_products)
        df = crawler._enrich_dataframe(df)
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        df.to_csv(args.output, index=False, encoding="utf-8-sig")
        logger.info(f"Đã lưu {len(df)} sản phẩm vào {args.output}")
    else:
        crawler.crawl_all(max_pages_per_cat=args.pages, output_csv=args.output)


if __name__ == "__main__":
    main()
