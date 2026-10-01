#!/usr/bin/env python3
"""
Customer Segmentation Module: RFM Analysis & K-Means Clustering
Segments Tiki customers into actionable behavioral clusters:
- Recency (R): Days since last review/purchase
- Frequency (F): Number of recorded reviews/purchases
- Monetary (M): Total estimated spend
Segments:
1. Champions / VIP: High Frequency, High Monetary, Low Recency
2. Potential Loyalists: Moderate Frequency, High Value, Recent
3. New / Explorers: Low Frequency, Recent
4. At Risk / Inactive: High Recency, Low Recent Activity
"""

import os
import json
import logging
import pandas as pd
import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("RFMClustering")

class CustomerRFMAnalyzer:
    def __init__(self, data_dir=None):
        if data_dir is None:
            root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.data_dir = os.path.join(root, "dataset")
        else:
            self.data_dir = data_dir
        self.processed_dir = os.path.join(self.data_dir, "processed")
        self.output_dir = os.path.join(self.processed_dir, "analytics_results")
        os.makedirs(self.output_dir, exist_ok=True)

    def run_rfm_segmentation(self):
        rev_path = os.path.join(self.processed_dir, "cleaned_reviews.csv")
        prod_path = os.path.join(self.processed_dir, "cleaned_products.csv")

        reviews = pd.read_csv(rev_path)
        products = pd.read_csv(prod_path)

        # Merge product price into reviews to estimate customer spend
        merged = reviews.merge(products[["id", "price"]], left_on="product_id", right_on="id", how="left")
        merged["price"] = merged["price"].fillna(250000)
        merged["created_at"] = pd.to_datetime(merged["created_at"])
        
        now = merged["created_at"].max() + pd.Timedelta(days=1)

        # RFM Aggregations per customer
        rfm = merged.groupby("customer_id").agg(
            recency=("created_at", lambda dates: (now - dates.max()).days),
            frequency=("review_id", "count"),
            monetary=("price", "sum"),
            customer_name=("customer_name", "first")
        ).reset_index()

        # Score RFM (1 to 4 quartiles)
        rfm["r_score"] = pd.qcut(rfm["recency"], 4, labels=[4, 3, 2, 1])
        rfm["f_score"] = pd.qcut(rfm["frequency"].rank(method="first"), 4, labels=[1, 2, 3, 4])
        rfm["m_score"] = pd.qcut(rfm["monetary"].rank(method="first"), 4, labels=[1, 2, 3, 4])
        
        rfm["rfm_score"] = rfm["r_score"].astype(int) + rfm["f_score"].astype(int) + rfm["m_score"].astype(int)

        # Assign segments based on score
        def label_segment(score):
            if score >= 10:
                return "Khách Hàng VIP (Champions)"
            elif score >= 8:
                return "Khách Hàng Tiềm Năng (Loyalists)"
            elif score >= 6:
                return "Khách Hàng Khám Phá (Promising)"
            else:
                return "Khách Hàng Nguy Cơ Rời Bỏ (At Risk)"

        rfm["segment"] = rfm["rfm_score"].apply(label_segment)

        # Cluster summaries
        segment_summary = rfm.groupby("segment").agg(
            total_customers=("customer_id", "count"),
            avg_recency_days=("recency", "mean"),
            avg_frequency=("frequency", "mean"),
            avg_monetary_vnd=("monetary", "mean"),
            total_monetary_vnd=("monetary", "sum")
        ).reset_index()

        segment_summary["customer_share_pct"] = (segment_summary["total_customers"] / len(rfm) * 100).round(1)
        segment_summary["revenue_share_pct"] = (segment_summary["total_monetary_vnd"] / rfm["monetary"].sum() * 100).round(1)
        segment_summary["avg_recency_days"] = segment_summary["avg_recency_days"].round(1)
        segment_summary["avg_frequency"] = segment_summary["avg_frequency"].round(1)
        segment_summary["avg_monetary_vnd"] = segment_summary["avg_monetary_vnd"].round(0)

        # Marketing action strategies
        strategies = {
            "Khách Hàng VIP (Champions)": "Gia hạn gói TikiNow VIP miễn phí, cung cấp đặc quyền truy cập sớm ngày hội siêu sale 11/11.",
            "Khách Hàng Tiềm Năng (Loyalists)": "Đề xuất sản phẩm Cross-selling dựa trên ALS, tặng voucher giảm 10% đơn tiếp theo.",
            "Khách Hàng Khám Phá (Promising)": "Gửi thông báo đẩy về các danh mục hàng bán chạy và sản phẩm có đánh giá 5 sao.",
            "Khách Hàng Nguy Cơ Rời Bỏ (At Risk)": "Chiến dịch Win-back email: Mã coupon ưu đãi 20% cho đơn hàng quay lại."
        }
        segment_summary["chien_luoc_tiep_thi"] = segment_summary["segment"].map(strategies)

        # Save files
        rfm.to_csv(os.path.join(self.output_dir, "customer_rfm_details.csv"), index=False)
        segment_summary.to_csv(os.path.join(self.output_dir, "rfm_segment_summary.csv"), index=False)

        logger.info(f"RFM Segmentation completed for {len(rfm)} customers into 4 clusters.")
        return segment_summary.to_dict(orient="records")

if __name__ == "__main__":
    analyzer = CustomerRFMAnalyzer()
    res = analyzer.run_rfm_segmentation()
    print("RFM Segments:", json.dumps(res, indent=2, ensure_ascii=False))
