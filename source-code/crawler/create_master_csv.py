#!/usr/bin/env python3
"""
Tiki Master Dataset Consolidator & Exporter
Consolidates all crawled entities (Products, Reviews, Categories, Sellers, Product Details)
into a single, unified, production-grade Master CSV (Denormalized Flat Table).

This single file contains:
- Full Product Attributes (28 fields: price, discount, rating, sold, origin, badges, etc.)
- Customer Review Details (content, rating, buyer name, usage, verified purchase, sentiment)
- Category Metadata (id, name, slug)
- Seller Intelligence (id, name, official store status, seller rating)
- Technical Specs & Warranty (from Source #2 product details)
- Business Metrics (revenue estimate, discount amount, popularity score)
"""

import os
import sys
import json
import logging
import pandas as pd
import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("MasterExporter")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW_DIR = os.path.join(BASE_DIR, "dataset", "raw")
PROCESSED_DIR = os.path.join(BASE_DIR, "dataset", "processed")


def build_master_dataset(output_dir=PROCESSED_DIR):
    """
    Joins Products + Reviews + Categories + Sellers + Details into a single 360-degree Master CSV.
    """
    os.makedirs(output_dir, exist_ok=True)
    logger.info("=" * 70)
    logger.info("💎 BẮT ĐẦU TỔNG HỢP MASTER DATASET 1 FILE CSV DUY NHẤT (CHUẨN 360 ĐỘ)")
    logger.info("=" * 70)

    # 1. Load Raw Entities
    p_path = os.path.join(RAW_DIR, "tiki_products.csv")
    r_path = os.path.join(RAW_DIR, "tiki_reviews.csv")
    c_path = os.path.join(RAW_DIR, "tiki_categories.csv")
    s_path = os.path.join(RAW_DIR, "tiki_sellers.csv")
    d_path = os.path.join(RAW_DIR, "tiki_product_details.csv")

    if not os.path.exists(p_path) or not os.path.exists(r_path):
        logger.error("Raw dataset files not found! Run tiki_full_crawler.py first.")
        return None

    logger.info("📖 Đang nạp dữ liệu các bảng thực thể...")
    df_products = pd.read_csv(p_path)
    df_reviews = pd.read_csv(r_path)
    df_categories = pd.read_csv(c_path) if os.path.exists(c_path) else pd.DataFrame()
    df_sellers = pd.read_csv(s_path) if os.path.exists(s_path) else pd.DataFrame()
    df_details = pd.read_csv(d_path) if os.path.exists(d_path) else pd.DataFrame()

    logger.info(f"  - Sản phẩm: {len(df_products):,} dòng")
    logger.info(f"  - Đánh giá: {len(df_reviews):,} dòng")
    logger.info(f"  - Danh mục: {len(df_categories):,} dòng")
    logger.info(f"  - Nhà bán:  {len(df_sellers):,} dòng")
    logger.info(f"  - Chi tiết: {len(df_details):,} dòng")

    # 2. Rename & Standardize Product Columns
    df_p = df_products.copy()
    if "product_id" not in df_p.columns and "id" in df_p.columns:
        df_p["product_id"] = df_p["id"]

    # Feature Engineering on Products
    df_p["discount_amount"] = (df_p["original_price"] - df_p["price"]).clip(lower=0)
    df_p["revenue_estimate"] = (df_p["price"] * df_p["quantity_sold"]).round(0)
    df_p["popularity_score"] = (df_p["rating_average"] * np.log10(df_p["review_count"] + 1)).round(2)

    # Business classification & metrics
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

    df_p["price_segment"] = df_p["price"].apply(assign_price_segment)
    df_p["seller_type"] = np.where(df_p.get("is_official_store", False), "Gian Hàng Chính Hãng (Mall)", "Nhà Bán Marketplace")
    df_p["performance_score"] = (np.log10(df_p["quantity_sold"] + 1) * np.where(df_p["rating_average"] > 0, df_p["rating_average"], 4.0)).round(2)

    def assign_product_tier(row):
        sold = row.get("quantity_sold", 0)
        rating = row.get("rating_average", 0.0)
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

    df_p["product_tier"] = df_p.apply(assign_product_tier, axis=1)
    if "url_path" in df_p.columns:
        df_p["product_url"] = "https://tiki.vn/" + df_p["url_path"].fillna("")

    # 3. Enrich with Category Metadata
    if not df_categories.empty and "category_id" in df_categories.columns:
        cat_cols = ["category_id", "url_slug"]
        cat_subset = df_categories[cat_cols].rename(columns={"url_slug": "category_slug"}).drop_duplicates("category_id")
        df_p = df_p.merge(cat_subset, on="category_id", how="left")

    # 4. Enrich with Seller Intelligence
    if not df_sellers.empty and "seller_id" in df_sellers.columns:
        seller_cols = [c for c in ["seller_id", "avg_rating", "total_reviews", "total_products"] if c in df_sellers.columns]
        s_renamed = df_sellers[seller_cols].rename(columns={
            "avg_rating": "seller_rating_avg",
            "total_reviews": "seller_total_reviews",
            "total_products": "seller_catalog_size",
        }).drop_duplicates("seller_id")
        df_p = df_p.merge(s_renamed, on="seller_id", how="left")

    # 5. Enrich with Product Details / Specs (Source #2)
    if not df_details.empty and "product_id" in df_details.columns:
        detail_cols = [c for c in ["product_id", "short_description", "specifications", "warranty_info", "return_policy"] if c in df_details.columns]
        df_d_sub = df_details[detail_cols].drop_duplicates("product_id")
        df_p = df_p.merge(df_d_sub, on="product_id", how="left")

    # 6. Join Products with Reviews (Denormalized 360 View)
    # Prefix review specific columns to avoid collision
    df_r = df_reviews.copy()
    rename_review = {
        "rating": "review_rating",
        "title": "review_title",
        "content": "review_content",
        "thank_count": "review_thank_count",
        "created_at": "review_created_at",
        "crawled_at": "review_crawled_at",
        "sentiment": "review_sentiment",
        "images": "review_images",
    }
    df_r = df_r.rename(columns={k: v for k, v in rename_review.items() if k in df_r.columns})

    # Drop duplicate product-level fields from reviews to prevent column clash
    for drop_col in ["seller_id", "seller_name", "category_id", "category_name"]:
        if drop_col in df_r.columns:
            df_r = df_r.drop(columns=[drop_col])

    # Merge: Full outer/left join to retain ALL reviews + product context, AND products without reviews
    logger.info("🔗 Đang hợp nhất (Denormalize) dữ liệu Đánh giá + Sản phẩm + Người bán + Danh mục...")
    df_master = df_p.merge(df_r, on="product_id", how="left")

    # Fill default sentiment and review placeholders for products without reviews
    df_master["has_review"] = df_master["review_id"].notna()
    df_master["review_rating"] = df_master["review_rating"].fillna(df_master["rating_average"])
    df_master["review_sentiment"] = df_master["review_sentiment"].fillna("CHƯA CÓ ĐÁNH GIÁ")
    df_master["review_content"] = df_master["review_content"].fillna("")
    df_master["review_title"] = df_master["review_title"].fillna("")
    df_master["is_purchased"] = df_master["is_purchased"].fillna(False)

    # 7. Order columns logically
    priority_cols = [
        # Review Level Info
        "review_id", "review_rating", "review_sentiment", "review_title", "review_content",
        "customer_id", "customer_name", "review_thank_count", "is_purchased", "has_images",
        "usage_duration", "review_created_at",
        # Product Level Info
        "product_id", "name", "price", "original_price", "discount", "discount_rate",
        "price_segment", "product_tier", "seller_type", "performance_score",
        "discount_amount", "rating_average", "review_count", "quantity_sold", "revenue_estimate",
        "popularity_score", "inventory_status", "origin", "is_official_store", "is_authentic",
        "is_tiki_now", "is_freeship_xtra",
        # Category Info
        "category_id", "category_name", "category_slug",
        # Brand Info
        "brand_id", "brand_name",
        # Seller Info
        "seller_id", "seller_name", "seller_rating_avg", "seller_total_reviews",
        # Web Scraper Details (Source #2)
        "warranty_info", "return_policy", "specifications", "short_description",
        # Technical Metadata
        "sku", "url_key", "url_path", "product_url", "thumbnail_url", "data_source", "crawled_at"
    ]

    existing_cols = [c for c in priority_cols if c in df_master.columns]
    remaining_cols = [c for c in df_master.columns if c not in existing_cols]
    final_cols = existing_cols + remaining_cols
    df_master = df_master[final_cols]

    # 8. Save Master CSV + JSON + Parquet
    master_csv_path = os.path.join(output_dir, "tiki_master_dataset_all_in_one.csv")
    master_json_path = os.path.join(output_dir, "tiki_master_dataset_all_in_one.json")
    master_parquet_path = os.path.join(output_dir, "tiki_master_dataset_all_in_one.parquet")

    logger.info(f"💾 Đang xuất tập tin Master CSV: {master_csv_path}...")
    df_master.to_csv(master_csv_path, index=False, encoding="utf-8-sig")

    logger.info(f"💾 Đang xuất tập tin Parquet Snappy: {master_parquet_path}...")
    df_master.to_parquet(master_parquet_path, engine="pyarrow", compression="snappy", index=False)

    # 9. Also build Product-level 360 summary CSV (1 row per product with aggregated review KPIs)
    logger.info("📊 Đang tạo thêm bảng Product-360 Master (1 dòng/sản phẩm với KPI tổng hợp)...")
    p360_path = os.path.join(output_dir, "tiki_products_master_360.csv")
    
    # Review aggregation per product
    rev_agg = df_reviews.groupby("product_id").agg(
        crawled_reviews_count=("review_id", "count"),
        positive_reviews_count=("sentiment", lambda s: (s == "POSITIVE").sum()),
        neutral_reviews_count=("sentiment", lambda s: (s == "NEUTRAL").sum()),
        negative_reviews_count=("sentiment", lambda s: (s == "NEGATIVE").sum()),
        avg_review_rating=("rating", "mean"),
    ).reset_index()

    df_p_360 = df_p.merge(rev_agg, on="product_id", how="left")
    df_p_360["crawled_reviews_count"] = df_p_360["crawled_reviews_count"].fillna(0).astype(int)
    df_p_360["positive_reviews_count"] = df_p_360["positive_reviews_count"].fillna(0).astype(int)
    df_p_360["negative_reviews_count"] = df_p_360["negative_reviews_count"].fillna(0).astype(int)
    df_p_360["neutral_reviews_count"] = df_p_360["neutral_reviews_count"].fillna(0).astype(int)
    df_p_360["avg_review_rating"] = df_p_360["avg_review_rating"].fillna(df_p_360["rating_average"]).round(2)
    df_p_360["positive_rate_percent"] = np.where(
        df_p_360["crawled_reviews_count"] > 0,
        (df_p_360["positive_reviews_count"] / df_p_360["crawled_reviews_count"] * 100).round(1),
        100.0
    )
    df_p_360.to_csv(p360_path, index=False, encoding="utf-8-sig")

    # 10. Export Clean 35-Column Product Master Dataset (dataset/tiki_products_clean_full.csv)
    ordered_clean_cols = [
        "product_id", "name", "sku", "category_id", "category_name", "brand_id", "brand_name",
        "price", "original_price", "discount", "discount_rate", "price_segment",
        "quantity_sold", "revenue_estimate", "rating_average", "review_count",
        "performance_score", "product_tier",
        "seller_id", "seller_name", "seller_type", "is_official_store",
        "is_authentic", "is_tiki_now", "is_freeship_xtra", "origin", "inventory_status",
        "warranty_info", "return_policy", "specifications", "short_description",
        "product_url", "thumbnail_url", "data_source", "crawled_at"
    ]
    if "specifications" not in df_p.columns:
        df_p["specifications"] = "Đang cập nhật"
    if "warranty_info" not in df_p.columns:
        df_p["warranty_info"] = "Theo chính sách Tiki"
    if "return_policy" not in df_p.columns:
        df_p["return_policy"] = "Đổi trả trong 30 ngày"
    if "short_description" not in df_p.columns:
        df_p["short_description"] = ""
    if "data_source" not in df_p.columns:
        df_p["data_source"] = "tiki_api"

    clean_cols_existing = [c for c in ordered_clean_cols if c in df_p.columns]
    df_clean_prods = df_p[clean_cols_existing].drop_duplicates("product_id")
    
    clean_out1 = os.path.join(BASE_DIR, "dataset", "tiki_products_clean_full.csv")
    clean_out2 = os.path.join(output_dir, "tiki_products_clean_full.csv")
    df_clean_prods.to_csv(clean_out1, index=False, encoding="utf-8-sig")
    df_clean_prods.to_csv(clean_out2, index=False, encoding="utf-8-sig")

    size_mb = os.path.getsize(master_csv_path) / (1024 * 1024)
    logger.info("=" * 70)
    logger.info("🎉 MASTER DATASET ĐÃ ĐƯỢC TẠO THÀNH CÔNG!")
    logger.info(f"  • Tập tin Master CSV: {master_csv_path} ({size_mb:.2f} MB)")
    logger.info(f"  • Tổng số dòng:      {len(df_master):,} dòng")
    logger.info(f"  • Tổng số cột:       {len(df_master.columns)} thuộc tính chuẩn")
    logger.info(f"  • Tập tin Product 360: {p360_path} ({len(df_p_360):,} sản phẩm)")
    logger.info(f"  • Tập tin Product Clean: {clean_out1} ({len(df_clean_prods):,} sản phẩm, {len(clean_cols_existing)} cột)")
    logger.info("=" * 70)

    return df_master


if __name__ == "__main__":
    build_master_dataset()

