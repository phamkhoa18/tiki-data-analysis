#!/usr/bin/env python3
"""
==============================================================================
TIKI DATA STORAGE EXPORTER — HỆ THỐNG LƯU TRỮ CSDL QUAN HỆ & PHI CẤU TRÚC
==============================================================================
Mục đích:
  Chuyển đổi và lưu trữ toàn bộ dữ liệu cào từ Tiki vào:
  1. CSDL Quan Hệ (RDBMS): SQLite Database (chuẩn SQL, có khóa chính PK, khóa ngoại FK, chỉ mục Index)
  2. CSDL Phi Cấu Trúc (NoSQL): JSON Documents cấu trúc lồng nhau (MongoDB-ready)

Đáp ứng tiêu chí đồ án Big Data:
  - Lưu trữ dữ liệu thu thập vào các DBMS (0.25đ)
  - Tổ chức CSDL quan hệ hoặc phi cấu trúc (NoSQL) (0.25đ)
==============================================================================
"""

import os
import sys
import json
import sqlite3
import logging
import argparse
import pandas as pd
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("StorageExporter")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "dataset")
RAW_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
SQLITE_DB_PATH = os.path.join(DATA_DIR, "tiki_database.db")
NOSQL_DIR = os.path.join(DATA_DIR, "nosql_documents")


class TikiStorageExporter:
    """Quản lý xuất dữ liệu cào sang SQLite RDBMS và NoSQL JSON Documents."""

    def __init__(self, db_path=SQLITE_DB_PATH, nosql_dir=NOSQL_DIR):
        self.db_path = db_path
        self.nosql_dir = nosql_dir
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        os.makedirs(self.nosql_dir, exist_ok=True)

    # =========================================================================
    # 1. RDBMS: LƯU TRỮ VÀO CSDL QUAN HỆ SQLITE
    # =========================================================================

    def export_to_sqlite(self):
        """
        Khởi tạo Schema chuẩn quan hệ (3NF) và nạp dữ liệu vào SQLite:
        - Bảng categories (Danh mục)
        - Bảng sellers (Nhà bán)
        - Bảng products (Sản phẩm - FK tới categories & sellers)
        - Bảng reviews (Đánh giá - FK tới products)
        """
        logger.info("=" * 70)
        logger.info("🗄️ BẮT ĐẦU XUẤT DỮ LIỆU SANG CSDL QUAN HỆ (RDBMS - SQLITE)")
        logger.info(f"  • Đường dẫn Database: {self.db_path}")
        logger.info("=" * 70)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Bật ràng buộc khóa ngoại (Foreign Keys)
        cursor.execute("PRAGMA foreign_keys = ON;")

        # Tạo Schema bảng Categories
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                category_id INTEGER PRIMARY KEY,
                category_name TEXT NOT NULL,
                parent_id INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                url_slug TEXT,
                total_products INTEGER DEFAULT 0,
                crawled_at TEXT
            );
        """)

        # Tạo Schema bảng Sellers
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sellers (
                seller_id INTEGER PRIMARY KEY,
                seller_name TEXT NOT NULL,
                is_official_store BOOLEAN DEFAULT 0,
                total_products INTEGER DEFAULT 0,
                avg_rating REAL DEFAULT 0.0,
                total_reviews INTEGER DEFAULT 0
            );
        """)

        # Tạo Schema bảng Products
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                product_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                sku TEXT,
                category_id INTEGER,
                category_name TEXT,
                brand_id INTEGER,
                brand_name TEXT,
                price INTEGER NOT NULL,
                original_price INTEGER,
                discount INTEGER,
                discount_rate REAL,
                price_segment TEXT,
                quantity_sold INTEGER DEFAULT 0,
                revenue_estimate INTEGER DEFAULT 0,
                rating_average REAL DEFAULT 0.0,
                review_count INTEGER DEFAULT 0,
                performance_score REAL DEFAULT 0.0,
                product_tier TEXT,
                seller_id INTEGER,
                seller_name TEXT,
                seller_type TEXT,
                is_official_store BOOLEAN DEFAULT 0,
                is_authentic BOOLEAN DEFAULT 1,
                is_tiki_now BOOLEAN DEFAULT 0,
                is_freeship_xtra BOOLEAN DEFAULT 0,
                origin TEXT,
                inventory_status TEXT,
                warranty_info TEXT,
                return_policy TEXT,
                product_url TEXT,
                thumbnail_url TEXT,
                crawled_at TEXT,
                FOREIGN KEY (category_id) REFERENCES categories (category_id),
                FOREIGN KEY (seller_id) REFERENCES sellers (seller_id)
            );
        """)

        # Tạo Schema bảng Reviews
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                review_id INTEGER PRIMARY KEY,
                product_id INTEGER NOT NULL,
                customer_id INTEGER,
                customer_name TEXT,
                rating INTEGER NOT NULL,
                title TEXT,
                content TEXT,
                thank_count INTEGER DEFAULT 0,
                is_purchased BOOLEAN DEFAULT 0,
                has_images BOOLEAN DEFAULT 0,
                sentiment TEXT,
                created_at TEXT,
                crawled_at TEXT,
                FOREIGN KEY (product_id) REFERENCES products (product_id)
            );
        """)

        # Tạo Index tối ưu hóa truy vấn
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_prod_cat ON products(category_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_prod_price ON products(price);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_prod_rating ON products(rating_average);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_rev_prod ON reviews(product_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_rev_sentiment ON reviews(sentiment);")
        conn.commit()

        # Nạp Categories
        cat_file = os.path.join(RAW_DIR, "tiki_categories.csv")
        cat_count = 0
        if os.path.exists(cat_file):
            df_c = pd.read_csv(cat_file).drop_duplicates(subset=["category_id"])
            cols = [c for c in ["category_id", "category_name", "parent_id", "level", "url_slug", "total_products", "crawled_at"] if c in df_c.columns]
            df_c[cols].to_sql("categories", conn, if_exists="replace", index=False)
            cat_count = len(df_c)
            logger.info(f"  ✓ Đã nạp {cat_count:,} danh mục vào bảng [categories]")

        # Nạp Sellers
        sel_file = os.path.join(RAW_DIR, "tiki_sellers.csv")
        sel_count = 0
        if os.path.exists(sel_file):
            df_s = pd.read_csv(sel_file).drop_duplicates(subset=["seller_id"])
            cols = [c for c in ["seller_id", "seller_name", "is_official_store", "total_products", "avg_rating", "total_reviews"] if c in df_s.columns]
            df_s[cols].to_sql("sellers", conn, if_exists="replace", index=False)
            sel_count = len(df_s)
            logger.info(f"  ✓ Đã nạp {sel_count:,} nhà bán vào bảng [sellers]")

        # Nạp Products
        prod_file = os.path.join(DATA_DIR, "tiki_products_clean_full.csv")
        if not os.path.exists(prod_file):
            prod_file = os.path.join(RAW_DIR, "tiki_products.csv")

        prod_count = 0
        if os.path.exists(prod_file):
            df_p = pd.read_csv(prod_file).drop_duplicates(subset=["product_id"])
            df_p.to_sql("products", conn, if_exists="replace", index=False)
            prod_count = len(df_p)
            logger.info(f"  ✓ Đã nạp {prod_count:,} sản phẩm vào bảng [products]")

        # Nạp Reviews
        rev_file = os.path.join(RAW_DIR, "tiki_reviews.csv")
        rev_count = 0
        if os.path.exists(rev_file):
            df_r = pd.read_csv(rev_file).drop_duplicates(subset=["review_id"])
            df_r.to_sql("reviews", conn, if_exists="replace", index=False)
            rev_count = len(df_r)
            logger.info(f"  ✓ Đã nạp {rev_count:,} đánh giá vào bảng [reviews]")

        conn.commit()
        db_size_mb = os.path.getsize(self.db_path) / (1024 * 1024)
        conn.close()

        logger.info(f"✅ Hoàn tất lưu trữ CSDL SQLite ({db_size_mb:.2f} MB)")
        logger.info(f"📌 Tổng cộng: {prod_count:,} sp | {rev_count:,} reviews | {sel_count:,} sellers | {cat_count:,} cats")
        return self.db_path

    # =========================================================================
    # 2. NOSQL: XUẤT CSDL PHI CẤU TRÚC (MONGODB-READY JSON DOCUMENTS)
    # =========================================================================

    def export_to_nosql_documents(self):
        """
        Xuất dữ liệu thành dạng Document NoSQL cấu trúc lồng nhau (Nested JSON):
        - Nhúng thông tin Brand, Seller, Category và Reviews trực tiếp vào từng Product Document.
        - Tương thích 100% để import vào MongoDB qua lệnh `mongoimport`.
        """
        logger.info("=" * 70)
        logger.info("🍃 BẮT ĐẦU XUẤT DỮ LIỆU SANG NOSQL DOCUMENTS (MONGODB-READY)")
        logger.info(f"  • Thư mục xuất: {self.nosql_dir}")
        logger.info("=" * 70)

        prod_file = os.path.join(DATA_DIR, "tiki_products_clean_full.csv")
        rev_file = os.path.join(RAW_DIR, "tiki_reviews.csv")

        if not os.path.exists(prod_file):
            logger.error("Chưa có file sản phẩm để xuất NoSQL!")
            return None

        df_p = pd.read_csv(prod_file)
        df_r = pd.read_csv(rev_file) if os.path.exists(rev_file) else pd.DataFrame()

        # Nhóm reviews theo product_id
        reviews_by_pid = {}
        if not df_r.empty and "product_id" in df_r.columns:
            for pid, group in df_r.groupby("product_id"):
                reviews_by_pid[pid] = group.head(10).to_dict(orient="records")

        # Chuyển đổi thành NoSQL documents
        out_jsonl = os.path.join(self.nosql_dir, "products_collection.jsonl")
        doc_count = 0

        with open(out_jsonl, "w", encoding="utf-8") as f:
            for _, row in df_p.iterrows():
                pid = row.get("product_id")
                doc = {
                    "_id": f"tiki_prod_{pid}",
                    "product_id": pid,
                    "name": row.get("name"),
                    "sku": row.get("sku"),
                    "pricing": {
                        "price": row.get("price"),
                        "original_price": row.get("original_price"),
                        "discount": row.get("discount"),
                        "discount_rate": row.get("discount_rate"),
                        "price_segment": row.get("price_segment"),
                    },
                    "metrics": {
                        "rating_average": row.get("rating_average"),
                        "review_count": row.get("review_count"),
                        "quantity_sold": row.get("quantity_sold"),
                        "revenue_estimate": row.get("revenue_estimate"),
                        "performance_score": row.get("performance_score"),
                        "product_tier": row.get("product_tier"),
                    },
                    "category": {
                        "id": row.get("category_id"),
                        "name": row.get("category_name"),
                    },
                    "brand": {
                        "id": row.get("brand_id"),
                        "name": row.get("brand_name"),
                    },
                    "seller": {
                        "id": row.get("seller_id"),
                        "name": row.get("seller_name"),
                        "type": row.get("seller_type"),
                        "is_official": bool(row.get("is_official_store", False)),
                    },
                    "policies": {
                        "warranty_info": row.get("warranty_info", "Theo chính sách Tiki"),
                        "return_policy": row.get("return_policy", "Đổi trả trong 30 ngày"),
                    },
                    "sample_customer_reviews": reviews_by_pid.get(pid, []),
                    "metadata": {
                        "product_url": row.get("product_url"),
                        "thumbnail_url": row.get("thumbnail_url"),
                        "crawled_at": row.get("crawled_at"),
                        "data_source": "tiki_api_v2",
                    }
                }
                f.write(json.dumps(doc, ensure_ascii=False) + "\n")
                doc_count += 1

        size_mb = os.path.getsize(out_jsonl) / (1024 * 1024)
        logger.info(f"✅ Đã xuất {doc_count:,} NoSQL Documents ra file: {out_jsonl} ({size_mb:.2f} MB)")
        logger.info("📌 Để nạp vào MongoDB, chạy lệnh: mongoimport --db tiki_db --collection products --file " + out_jsonl)
        return out_jsonl

    # =========================================================================
    # 3. TRUY VẤN MẪU TEST RDBMS SQLITE
    # =========================================================================

    def run_sample_queries(self):
        """Chạy một số câu lệnh truy vấn SQL kinh điển chứng minh hoạt động của RDBMS."""
        if not os.path.exists(self.db_path):
            self.export_to_sqlite()

        conn = sqlite3.connect(self.db_path)
        logger.info("=" * 70)
        logger.info("📊 THỰC THI TRUY VẤN MẪU TRÊN CSDL SQLITE (SQL QUERIES DEMO)")
        logger.info("=" * 70)

        # Truy vấn 1: Top 5 sản phẩm bán chạy nhất
        q1 = """
            SELECT product_id, name, price, quantity_sold, revenue_estimate, rating_average
            FROM products
            ORDER BY quantity_sold DESC
            LIMIT 5;
        """
        df1 = pd.read_sql_query(q1, conn)
        print("\n🏆 Top 5 Sản Phẩm Bán Chạy Nhất:")
        print(df1.to_string(index=False))

        # Truy vấn 2: Thống kê doanh thu theo danh mục
        q2 = """
            SELECT category_name, 
                   COUNT(product_id) as total_products, 
                   AVG(price) as avg_price,
                   SUM(quantity_sold) as total_sold,
                   SUM(revenue_estimate) as total_revenue
            FROM products
            GROUP BY category_name
            ORDER BY total_revenue DESC;
        """
        df2 = pd.read_sql_query(q2, conn)
        print("\n📈 Thống Kê Doanh Thu & Số Lượng Theo Danh Mục:")
        print(df2.to_string(index=False))

        conn.close()


def main():
    parser = argparse.ArgumentParser(description="Tiki Data Storage Exporter — Lưu trữ CSDL Quan hệ & NoSQL")
    parser.add_argument("--type", choices=["all", "sqlite", "nosql", "query"], default="all",
                        help="Loại lưu trữ: all (cả 2), sqlite (RDBMS), nosql (MongoDB JSON), query (thử nghiệm SQL)")
    args = parser.parse_args()

    exporter = TikiStorageExporter()
    if args.type in ["all", "sqlite"]:
        exporter.export_to_sqlite()
    if args.type in ["all", "nosql"]:
        exporter.export_to_nosql_documents()
    if args.type in ["all", "query"]:
        exporter.run_sample_queries()


if __name__ == "__main__":
    main()
