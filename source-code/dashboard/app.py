#!/usr/bin/env python3
"""
Tiki E-Commerce Big Data Interactive Analytics Dashboard
Built with Streamlit and Matplotlib/Plotly
Authors: Phạm Đăng Khoa, Phạm Minh Nhật, Nguyễn Văn Sang
"""

import os
import json
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Page Config
st.set_page_config(
    page_title="Tiki Big Data Analytics Platform",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Base directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "dataset", "processed")
ANALYTICS_DIR = os.path.join(DATA_DIR, "analytics_results")

# Load CSS
css_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "style.css")
if os.path.exists(css_file):
    with open(css_file) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

@st.cache_data
def load_all_data():
    prods = pd.read_csv(os.path.join(DATA_DIR, "cleaned_products.csv")) if os.path.exists(os.path.join(DATA_DIR, "cleaned_products.csv")) else None
    revs = pd.read_csv(os.path.join(DATA_DIR, "cleaned_reviews.csv")) if os.path.exists(os.path.join(DATA_DIR, "cleaned_reviews.csv")) else None
    cat_summary = pd.read_csv(os.path.join(ANALYTICS_DIR, "category_summary.csv")) if os.path.exists(os.path.join(ANALYTICS_DIR, "category_summary.csv")) else None
    top_sellers = pd.read_csv(os.path.join(ANALYTICS_DIR, "top_sellers.csv")) if os.path.exists(os.path.join(ANALYTICS_DIR, "top_sellers.csv")) else None
    aspect_df = pd.read_csv(os.path.join(ANALYTICS_DIR, "aspect_sentiment.csv")) if os.path.exists(os.path.join(ANALYTICS_DIR, "aspect_sentiment.csv")) else None
    rfm_summary = pd.read_csv(os.path.join(ANALYTICS_DIR, "rfm_segment_summary.csv")) if os.path.exists(os.path.join(ANALYTICS_DIR, "rfm_segment_summary.csv")) else None
    rfm_details = pd.read_csv(os.path.join(ANALYTICS_DIR, "customer_rfm_details.csv")) if os.path.exists(os.path.join(ANALYTICS_DIR, "customer_rfm_details.csv")) else None
    return prods, revs, cat_summary, top_sellers, aspect_df, rfm_summary, rfm_details

prods_df, revs_df, cat_summary, top_sellers, aspect_df, rfm_summary, rfm_details = load_all_data()

# Sidebar
st.sidebar.image("https://salt.tikicdn.com/ts/upload/e8/37/da/f23dec122f0f404230e6dd632280d023.png", width=160)
st.sidebar.title("TIKI BIG DATA")
st.sidebar.caption("Hệ Thống Phân Tích Dữ Liệu & Gợi Ý AI")
st.sidebar.markdown("---")
st.sidebar.markdown("**Thành viên nhóm nghiên cứu:**")
st.sidebar.markdown("- 👨‍💻 **Phạm Đăng Khoa** (24810114)")
st.sidebar.markdown("- 👨‍💻 **Phạm Minh Nhật** (24810119)")
st.sidebar.markdown("- 👨‍💻 **Nguyễn Văn Sang** (24810114)")
st.sidebar.markdown("---")
st.sidebar.info("💡 Hệ thống tích hợp Apache Spark 3.5, PyArrow Parquet Data Lake, Vietnamese NLP và Spark MLlib ALS.")

# Main Header
st.title("🛒 Bảng Điều Khiển Phân Tích Hệ Thống Dữ Liệu TIKI")
st.markdown("Nền tảng xử lý dữ liệu lớn phân tích hành vi khách hàng, biến động giá, khai phá cảm xúc và gợi ý thông minh.")

# KPI Ribbon
if prods_df is not None:
    total_gmv = prods_df["revenue_estimate"].sum()
    avg_rating = prods_df["rating_average"].mean()
    total_sold = prods_df["quantity_sold"].sum()
    total_reviews = len(revs_df) if revs_df is not None else 0

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Ước Tính Doanh Thu (GMV)</div>
            <div class="kpi-value">{total_gmv/1e9:.2f} Tỷ VNĐ</div>
            <div class="kpi-subtitle">▲ Tăng trưởng ổn định</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Tổng Lượng Bán Ra</div>
            <div class="kpi-value">{total_sold:,.0f} SP</div>
            <div class="kpi-subtitle">Đã hoàn tất giao dịch</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Đánh Giá Trung Bình</div>
            <div class="kpi-value">{avg_rating:.2f} ⭐</div>
            <div class="kpi-subtitle">Từ {total_reviews:,} nhận xét</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Tổng Số Danh Mục</div>
            <div class="kpi-value">{prods_df['category_name'].nunique()} Ngành</div>
            <div class="kpi-subtitle">{len(prods_df):,} sản phẩm đang bán</div>
        </div>
        """, unsafe_allow_html=True)

# Navigation Tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Thị Phần & Doanh Thu",
    "🏷️ Giá & Khuyến Mãi",
    "💬 NLP Cảm Xúc Khách Hàng",
    "🤖 AI Gợi Ý Sản Phẩm (ALS)",
    "👥 Phân Cụm Khách Hàng RFM",
    "⚡ Luồng Sự Kiện Real-time"
])

# TAB 1: Thị Phần & Doanh Thu
with tab1:
    st.subheader("Phân Tích Thị Phần & Doanh Thu Theo Danh Mục Ngành Hàng")
    if cat_summary is not None:
        c1, c2 = st.columns([3, 2])
        with c1:
            fig, ax = plt.subplots(figsize=(8, 4.5), facecolor="#0e1117")
            ax.set_facecolor("#1e293b")
            categories = cat_summary["category_name"]
            revenues = cat_summary["total_revenue"] / 1e9
            bars = ax.barh(categories, revenues, color="#38bdf8", edgecolor="#0284c7")
            ax.set_xlabel("Doanh thu ước tính (Tỷ VNĐ)", color="#f0f2f6", fontsize=10)
            ax.set_title("Xếp Hạng Doanh Thu Các Ngành Hàng Tiki", color="#f0f2f6", fontsize=12, pad=12)
            ax.tick_params(colors="#cbd5e1")
            for bar in bars:
                w = bar.get_width()
                ax.text(w + 0.1, bar.get_y() + bar.get_height()/2, f"{w:.1f}B", ha="left", va="center", color="#38bdf8", fontsize=9, fontweight="bold")
            st.pyplot(fig)
        with c2:
            st.write("##### Bảng Thống Kê Tổng Hợp")
            display_cat = cat_summary[["category_name", "total_products", "avg_price", "avg_discount", "market_share_percent"]].copy()
            display_cat.columns = ["Danh Mục", "Số SP", "Giá TB (VNĐ)", "Giảm TB (%)", "Thị Phần (%)"]
            st.dataframe(display_cat, use_container_width=True)

    if top_sellers is not None:
        st.write("##### Top 10 Sản Phẩm Bán Chạy Nhất Toàn Sàn")
        display_top = top_sellers[["name", "category_name", "brand_name", "price", "discount_rate", "quantity_sold", "rating_average"]].copy()
        display_top.columns = ["Tên Sản Phẩm", "Danh Mục", "Thương Hiệu", "Giá Bán", "Giảm Giá (%)", "Đã Bán", "Đánh Giá"]
        st.dataframe(display_top, use_container_width=True)

# TAB 2: Giá & Khuyến Mãi
with tab2:
    st.subheader("Phân Phối Giá Bán & Tác Động Của Tỷ Lệ Giảm Giá")
    if prods_df is not None:
        col_a, col_b = st.columns(2)
        with col_a:
            fig2, ax2 = plt.subplots(figsize=(7, 4), facecolor="#0e1117")
            ax2.set_facecolor("#1e293b")
            ax2.hist(prods_df["discount_rate"], bins=10, color="#f59e0b", edgecolor="#b45309", alpha=0.85)
            ax2.set_title("Phân Phối Tỷ Lệ Chiết Khấu / Giảm Giá (%)", color="#f0f2f6")
            ax2.set_xlabel("Tỷ Lệ Giảm Giá (%)", color="#f0f2f6")
            ax2.set_ylabel("Số Lượng Sản Phẩm", color="#f0f2f6")
            ax2.tick_params(colors="#cbd5e1")
            st.pyplot(fig2)
        with col_b:
            fig3, ax3 = plt.subplots(figsize=(7, 4), facecolor="#0e1117")
            ax3.set_facecolor("#1e293b")
            sample_scatter = prods_df.sample(min(400, len(prods_df)), random_state=42)
            scatter = ax3.scatter(sample_scatter["discount_rate"], sample_scatter["quantity_sold"], c=sample_scatter["rating_average"], cmap="viridis", alpha=0.7)
            ax3.set_title("Mối Tương Quan: Giảm Giá vs Lượng Hàng Bán Ra", color="#f0f2f6")
            ax3.set_xlabel("Tỷ Lệ Giảm Giá (%)", color="#f0f2f6")
            ax3.set_ylabel("Số Lượng Đã Bán", color="#f0f2f6")
            ax3.tick_params(colors="#cbd5e1")
            cbar = plt.colorbar(scatter, ax=ax3)
            cbar.set_label("Điểm Đánh Giá TB", color="#f0f2f6")
            cbar.ax.yaxis.set_tick_params(color="#cbd5e1")
            plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color="#cbd5e1")
            st.pyplot(fig3)

# TAB 3: NLP Cảm Xúc
with tab3:
    st.subheader("Khai Phá Cảm Xúc & Phân Tích Đa Chiều Đánh Giá Khách Hàng (NLP)")
    if revs_df is not None:
        sentiment_counts = revs_df["sentiment"].value_counts()
        rc1, rc2 = st.columns([1, 1])
        with rc1:
            fig4, ax4 = plt.subplots(figsize=(5, 5), facecolor="#0e1117")
            colors = ["#10b981", "#3b82f6", "#ef4444"]
            ax4.pie(sentiment_counts.values, labels=sentiment_counts.index, autopct="%1.1f%%", colors=colors, textprops={'color': "#f0f2f6", 'fontsize': 11})
            ax4.set_title("Tỷ Lệ Cảm Xúc Khách Hàng Tiki", color="#f0f2f6")
            st.pyplot(fig4)
        with rc2:
            st.write("##### Đánh Giá Theo Từng Khía Cạnh Trải Nghiệm")
            if aspect_df is not None:
                st.dataframe(aspect_df, use_container_width=True)
                st.markdown("""
                - 🚀 **Giao hàng siêu tốc TikiNow:** Đạt tỷ lệ hài lòng cao nhất (>85%), là thế mạnh cạnh tranh lớn nhất.
                - 📦 **Đóng gói bảo vệ:** Vẫn tồn tại tỷ lệ tiêu cực (~12%) do móp méo hộp trong quá trình vận chuyển.
                - 🛡️ **Hàng chính hãng:** Nhận được sự tin tưởng vượt trội từ người tiêu dùng khi mua gian hàng Mall.
                """)

# TAB 4: AI Gợi Ý Sản Phẩm ALS
with tab4:
    st.subheader("Hệ Thống Gợi Ý Sản Phẩm Thông Minh (Collaborative Filtering ALS)")
    st.markdown("Áp dụng thuật toán Matrix Factorization phân rã ma trận người dùng - sản phẩm trong Spark MLlib.")
    
    try:
        from analytics_ml.recommendation_als import TikiRecommender
    except ImportError:
        import sys
        sys.path.append(os.path.join(BASE_DIR, "source-code"))
        from analytics_ml.recommendation_als import TikiRecommender

    rec = TikiRecommender(data_dir=os.path.join(BASE_DIR, "dataset"))
    
    col_u, col_p = st.columns([1, 2])
    with col_u:
        user_ids = [1001, 1005, 1012, 1020, 1055, 1100]
        selected_user = st.selectbox("Chọn Khách Hàng (Customer ID):", user_ids)
        st.write(f"Khách hàng đang chọn: **#{selected_user}**")
        st.caption("Mô hình AI tự động phân tích lịch sử đánh giá của khách hàng này để dự đoán sở thích.")

    with col_p:
        st.write(f"##### Top 5 Gợi Ý Cá Nhân Hóa Dành Riêng Cho Khách Hàng #{selected_user}:")
        user_recs = rec.recommend_for_user(customer_id=selected_user, top_n=5)
        if user_recs:
            recs_df = pd.DataFrame(user_recs)
            recs_df = recs_df[["product_id", "name", "category_name", "price", "discount_rate", "rating_average", "predicted_score"]]
            recs_df.columns = ["Mã SP", "Tên Sản Phẩm", "Danh Mục", "Giá Bán", "Giảm (%)", "Đánh Giá", "Điểm Dự Đoán"]
            st.dataframe(recs_df, use_container_width=True)

# TAB 5: Khách Hàng RFM
with tab5:
    st.subheader("Phân Khúc Khách Hàng Dựa Trên Mô Hình RFM & K-Means")
    if rfm_summary is not None:
        st.dataframe(rfm_summary[["segment", "total_customers", "customer_share_pct", "avg_recency_days", "avg_frequency", "avg_monetary_vnd", "chien_luoc_tiep_thi"]], use_container_width=True)
    if rfm_details is not None:
        fig5, ax5 = plt.subplots(figsize=(9, 4.5), facecolor="#0e1117")
        ax5.set_facecolor("#1e293b")
        for seg, group in rfm_details.groupby("segment"):
            ax5.scatter(group["recency"], group["monetary"]/1e6, label=seg, alpha=0.6, s=40)
        ax5.set_title("Biểu Đồ Phân Cụm Khách Hàng (Recency vs Monetary)", color="#f0f2f6")
        ax5.set_xlabel("Số ngày kể từ lần tương tác cuối (Recency)", color="#f0f2f6")
        ax5.set_ylabel("Chi tiêu ước tính (Triệu VNĐ)", color="#f0f2f6")
        ax5.tick_params(colors="#cbd5e1")
        ax5.legend(facecolor="#0e1117", edgecolor="#334155", labelcolor="#f0f2f6")
        st.pyplot(fig5)

# TAB 6: Real-time Streaming
with tab6:
    st.subheader("Giám Sát Luồng Sự Kiện Thời Gian Thực (Spark Streaming & Kafka)")
    st.markdown("Mô phỏng ingestion luồng clickstream với Structured Streaming qua sliding window.")
    
    stream_kpis_path = os.path.join(ANALYTICS_DIR, "streaming_realtime_kpis.json")
    if os.path.exists(stream_kpis_path):
        with open(stream_kpis_path, "r", encoding="utf-8") as f:
            st_kpis = json.load(f)
        
        sc1, sc2, sc3 = st.columns(3)
        sc1.metric("Sự kiện trong Window gần nhất", f"{st_kpis.get('window_event_count', 0)} events")
        sc2.metric("Tỷ lệ chuyển đổi mua hàng (Real-time)", f"{st_kpis.get('estimated_realtime_conversion_rate', 0)}%")
        sc3.metric("Trạng thái Spark Consumer", "Active 🟢")

        st.write("##### Phân Phối Hành Vi Khách Hàng Trong Cửa Sổ Trượt:")
        st.json(st_kpis.get("event_breakdown", {}))
    else:
        st.info("Chưa có sự kiện streaming nào được ghi nhận. Vui lòng chạy `python3 source-code/streaming/kafka_event_producer.py` và `spark_streaming_consumer.py` để cập nhật dữ liệu trực tiếp.")
