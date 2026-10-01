# BÁO CÁO ĐỒ ÁN MÔN HỌC: CÔNG NGHỆ DỮ LIỆU LỚN (BIG DATA)
## ĐỀ TÀI: PHÂN TÍCH HỆ THỐNG DỮ LIỆU SÀN THƯƠNG MẠI ĐIỆN TỬ TIKI VÀ HỆ THỐNG GỢI Ý THÔNG MINH
**(TIKI E-COMMERCE BIG DATA ANALYTICS & AI RECOMMENDATION SYSTEM)**

- **Lớp học phần:** 06_BigData
- **Nhóm thực hiện:** Nhóm 01
- **Sinh viên thực hiện:**
  1. **Phạm Đăng Khoa** (MSSV: 24810114) – *Trưởng nhóm*
  2. **Phạm Minh Nhật** (MSSV: 24810119) – *Thành viên*
  3. **Nguyễn Văn Sang** (MSSV: 24810114) – *Thành viên*
- **Thời gian hoàn thành:** Năm học 2024 - 2025

---

## MỤC LỤC
1. [Tóm Tắt Dự Án (Executive Summary)](#1-tóm-tắt-dự-án)
2. [Chương 1: Giới Thiệu & Bài Toán Big Data Tại Tiki](#2-chương-1-giới-thiệu--bài-toán-big-data-tại-tiki)
3. [Chương 2: Kiến Trúc Hệ Thống (System Architecture)](#3-chương-2-kiến-trúc-hệ-thống)
4. [Chương 3: Thu Thập & Tiền Xử Lý Dữ Liệu Lớn](#4-chương-3-thu-thập--tiền-xử-lý-dữ-liệu-lớn)
5. [Chương 4: Phân Tích Kinh Doanh & Thị Phần Danh Mục](#5-chương-4-phân-tích-kinh-doanh--thị-phần-danh-mục)
6. [Chương 5: Khai Phá Cảm Xúc Khách Hàng (Vietnamese NLP)](#6-chương-5-khai-phá-cảm-xúc-khách-hàng)
7. [Chương 6: Hệ Thống Gợi Ý Sản Phẩm Spark MLlib ALS](#7-chương-6-hệ-thống-gợi-ý-sản-phẩm-spark-mllib-als)
8. [Chương 7: Phân Cụm Khách Hàng RFM](#8-chương-7-phân-cụm-khách-hàng-rfm)
9. [Chương 8: Xử Lý Luồng Dữ Liệu Thời Gian Thực (Streaming)](#9-chương-8-xử-lý-luồng-dữ-liệu-thời-gian-thực)
10. [Chương 9: Bảng Điều Khiển Trực Quan Hóa (Dashboard)](#10-chương-9-bảng-điều-khiển-trực-quan-hóa)
11. [Chương 10: Kết Luận & Hướng Phát Triển](#11-chương-10-kết-luận--hướng-phát-triển)

---

## 1. Tóm Tắt Dự Án
Đồ án xây dựng một giải pháp Big Data hoàn chỉnh giải quyết các bài toán cốt lõi của sàn thương mại điện tử Tiki:
- **Tầng Thu Thập (Ingestion Layer):** Thu thập dữ liệu catalog sản phẩm và nhận xét của khách hàng từ Tiki API.
- **Tầng Lưu Trữ (Storage Layer):** Data Lake dạng cột Parquet nén Snappy, phân vùng tối ưu hóa theo `category_id`.
- **Tầng Tính Toán (Processing Engine):** Apache Spark 3.5 thực thi các tác vụ tính toán phân tán (Batch & Streaming).
- **Tầng Trí Tuệ Nhân Tạo & NLP:**
  - Mô hình Matrix Factorization ALS (Spark MLlib) gợi ý sản phẩm cá nhân hóa.
  - Phân tích cảm xúc theo khía cạnh (Aspect-based Sentiment Analysis) cho tiếng Việt.
  - Phân cụm khách hàng theo mô hình RFM (K-Means).
- **Tầng Ứng Dụng (Application Layer):** Web Dashboard tương tác bằng Streamlit phục vụ nhà quản trị và đội ngũ tiếp thị.

---

## 2. Chương 1: Giới Thiệu & Bài Toán Big Data Tại Tiki
Trong bối cảnh sàn TMĐT Tiki xử lý hàng triệu phiên truy cập mỗi ngày, dữ liệu phát sinh có đặc trưng 4V:
- **Volume:** Hàng chục triệu sản phẩm và hàng trăm triệu đánh giá theo thời gian.
- **Velocity:** Dữ liệu lượt xem trang, thêm vào giỏ, và đơn đặt hàng phát sinh liên tục theo từng mili-giây.
- **Variety:** Dữ liệu có cấu trúc (bảng giá, tồn kho), bán cấu trúc (JSON API), và phi cấu trúc (bình luận văn bản tiếng Việt).
- **Value:** Khai thác insight thị trường, dự báo xu hướng sản phẩm hot và tối ưu hóa chuyển đổi.

---

## 3. Chương 2: Kiến Trúc Hệ Thống

```
+-------------------------------------------------------------------------+
|                         TIKI DATA SOURCES                               |
|   Tiki Public REST APIs (Products, Reviews)  |  Live User Clickstream   |
+------------------------------------+------------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------------+
|                        INGESTION & BUFFER LAYER                         |
|      Polite Tiki Rate Limiter      |      Apache Kafka Event Broker     |
+------------------------------------+------------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------------+
|                  APACHE SPARK DISTRIBUTED ENGINE                        |
|  - Spark SQL: Schema Validation, Missing Imputation, Feature Cleanse   |
|  - Spark Streaming: Sliding Window Real-time Trend Detection           |
|  - Spark MLlib: ALS Collaborative Filtering & K-Means RFM Clustering   |
+------------------------------------+------------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------------+
|                         DATA LAKE STORAGE                               |
|         Apache Parquet (Snappy Compressed, Partitioned by Category)     |
+------------------------------------+------------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------------+
|                       PRESENTATION & SERVING                            |
|             Streamlit Interactive Multi-Tab Web Dashboard               |
+-------------------------------------------------------------------------+
```

---

## 4. Bảng Đánh Giá Kết Quả Thực Nghiệm

| STT | Thành phần hệ thống | Thuật toán / Công nghệ | Kết quả đạt được |
|:---:|---------------------|------------------------|------------------|
| 1 | Pipeline Batch ETL | PySpark + PyArrow Parquet | 1.34s cho 7,500 records |
| 2 | Hệ thống gợi ý | Spark MLlib ALS | Test RMSE = 1.5890, MAE = 1.2331 |
| 3 | Khai phá cảm xúc NLP | Aspect-based Lexicon & Regex | Phân loại 3 nhãn, bóc tách 4 khía cạnh |
| 4 | Phân cụm khách hàng | RFM Scoring + K-Means | 4 cụm phân khúc chiến lược |
| 5 | Luồng sự kiện Realtime | Spark Streaming / Kafka | Cửa sổ trượt 5 phút, độ trễ < 100ms |
