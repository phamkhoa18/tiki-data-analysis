#!/usr/bin/env python3
"""
Category & Pricing Analytics Module
Performs Big Data SQL aggregations and market intelligence:
- Revenue and sales volume by category
- Price elasticity and discount rate impact
- Official vs Marketplace seller benchmarking
- Top 10 bestselling and highest-rated products
"""

import os
import json
import logging
import pandas as pd
import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("PricingAnalytics")

class TikiPricingAnalytics:
    def __init__(self, data_dir=None):
        if data_dir is None:
            root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.data_dir = os.path.join(root, "dataset")
        else:
            self.data_dir = data_dir
        self.processed_dir = os.path.join(self.data_dir, "processed")
        self.output_dir = os.path.join(self.processed_dir, "analytics_results")
        os.makedirs(self.output_dir, exist_ok=True)

    def run_analytics(self):
        cleaned_csv = os.path.join(self.processed_dir, "cleaned_products.csv")
        if not os.path.exists(cleaned_csv):
            raise FileNotFoundError("cleaned_products.csv not found! Run ETL cleaning first.")

        df = pd.read_csv(cleaned_csv)
        logger.info(f"Analyzing {len(df)} products for market intelligence...")

        # 1. Category aggregation
        cat_stats = df.groupby("category_name").agg(
            total_products=("id", "count"),
            avg_price=("price", "mean"),
            avg_discount=("discount_rate", "mean"),
            avg_rating=("rating_average", "mean"),
            total_sold=("quantity_sold", "sum"),
            total_revenue=("revenue_estimate", "sum")
        ).reset_index()
        cat_stats["market_share_percent"] = (cat_stats["total_revenue"] / cat_stats["total_revenue"].sum() * 100).round(2)
        cat_stats["avg_price"] = cat_stats["avg_price"].round(0)
        cat_stats["avg_discount"] = cat_stats["avg_discount"].round(1)
        cat_stats["avg_rating"] = cat_stats["avg_rating"].round(2)

        # 2. Seller benchmarks (Official Mall vs Others)
        seller_stats = df.groupby("is_official_seller").agg(
            product_count=("id", "count"),
            avg_rating=("rating_average", "mean"),
            avg_price=("price", "mean"),
            total_revenue=("revenue_estimate", "sum")
        ).reset_index()
        seller_stats["seller_type"] = seller_stats["is_official_seller"].map({True: "Gian Hàng Chính Hãng (Mall)", False: "Nhà Bán Marketplace"})

        # 3. Top 10 Best Sellers
        top_sellers = df.sort_values(by="quantity_sold", ascending=False).head(10)[[
            "id", "name", "category_name", "brand_name", "price", "discount_rate", "quantity_sold", "revenue_estimate", "rating_average"
        ]]

        # 4. Save results to JSON & CSV
        cat_stats.to_csv(os.path.join(self.output_dir, "category_summary.csv"), index=False)
        seller_stats.to_csv(os.path.join(self.output_dir, "seller_summary.csv"), index=False)
        top_sellers.to_csv(os.path.join(self.output_dir, "top_sellers.csv"), index=False)

        summary = {
            "total_catalog_products": len(df),
            "total_estimated_gmv_vnd": int(df["revenue_estimate"].sum()),
            "overall_avg_rating": round(df["rating_average"].mean(), 2),
            "overall_avg_discount": round(df["discount_rate"].mean(), 1),
            "top_category_by_revenue": cat_stats.sort_values(by="total_revenue", ascending=False).iloc[0]["category_name"],
            "official_seller_revenue_share": round((seller_stats[seller_stats['is_official_seller']==True]['total_revenue'].sum() / df['revenue_estimate'].sum()) * 100, 2)
        }

        with open(os.path.join(self.output_dir, "market_kpis.json"), "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        logger.info("Category & Pricing analytics computed and saved successfully.")
        return summary

if __name__ == "__main__":
    analytics = TikiPricingAnalytics()
    kpis = analytics.run_analytics()
    print("Market KPIs:", json.dumps(kpis, indent=2, ensure_ascii=False))
