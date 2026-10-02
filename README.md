# Đồ Án Big Data: Phân Tích Hệ Thống Dữ Liệu Sàn Thương Mại Điện Tử TIKI
## (Tiki E-Commerce Big Data Analytics Platform)

### 👥 Thông Tin Nhóm Sinh Viên
1. **Phạm Đăng Khoa** (MSSV: 24810114)
2. **Phạm Minh Nhật** (MSSV: 24810119)
3. **Nguyễn Văn Sang** (MSSV: 24810114)

---

### 📦 DỮ LIỆU ĐÃ THU THẬP & SẴN SÀNG SỬ DỤNG (DÀNH CHO CÁC THÀNH VIÊN TRONG NHÓM)

Dữ liệu thực tế từ Tiki.vn đã được cào, làm sạch và chuẩn hóa 100%. Các thành viên trong nhóm chỉ cần kéo code về (`git pull`) và lấy các tệp CSV dưới đây để làm phần việc của mình:

| Tệp Dữ Liệu | Đường Dẫn | Số Lượng Bản Ghi | Mục Đích Sử Dụng |
| :--- | :--- | :---: | :--- |
| **Sản phẩm sạch (Master)** | [`dataset/tiki_products_clean_full.csv`](dataset/tiki_products_clean_full.csv) | **2,307** sản phẩm | 35 thuộc tính chuẩn (giá, sold, rating, tier, specs...). Dùng cho **Spark ETL, Phân tích K-Means, Dashboard**. |
| **Đánh giá khách hàng** | [`dataset/raw/tiki_reviews.csv`](dataset/raw/tiki_reviews.csv) | **35,632** nhận xét | Đánh giá sao, nội dung bình luận tiếng Việt, sentiment. Dùng cho **Vietnamese NLP, Sentiment Mining, Recommendation**. |
| **Bảng phẳng 360 độ** | [`dataset/tiki_master_dataset_all_in_one.csv`](dataset/tiki_master_dataset_all_in_one.csv) | **36,166** dòng | Hợp nhất toàn bộ Sản phẩm + Đánh giá + Nhà bán. Dùng cho **Data Lake Parquet Snappy**. |
| **CSDL Quan hệ SQLite** | [`dataset/tiki_database.db`](dataset/tiki_database.db) | 4 bảng chuẩn 3NF | Lưu trữ DBMS quan hệ (categories, sellers, products, reviews). |
| **CSDL NoSQL JSON** | [`dataset/nosql_documents/`](dataset/nosql_documents/) | **2,307** documents | MongoDB-ready Documents. |

> 📖 **Tra cứu chi tiết ý nghĩa 35 cột thuộc tính và sơ đồ quan hệ ERD tại:**  
> 👉 [**`dataset/CAU_TRUC_DU_LIEU_CRAWL.md`**](dataset/CAU_TRUC_DU_LIEU_CRAWL.md)

---

### 📂 PHÂN CHIA THƯ MỤC CÔNG VIỆC CHO TỪNG THÀNH VIÊN

Mỗi thành viên trong nhóm code đúng vào thư mục chức năng đã được tạo sẵn khung:

```
bigdata_doan/
├── source-code/
│   ├── crawler/        # [HOÀN THÀNH] Module cào & quản trị dữ liệu Tiki
│   ├── etl_spark/      # [KHOA] Module làm sạch, chuyển đổi sang Parquet Snappy phân vùng Data Lake
│   ├── analytics_ml/   # [NHẬT] Thuật toán học máy: Phân tích giá, NLP cảm xúc, ALS Gợi ý sản phẩm
│   ├── streaming/      # [SANG/NHẬT] Giả lập luồng sự kiện Clickstream Kafka & Spark Streaming
│   ├── dashboard/      # [SANG] Giao diện trực quan hóa tương tác (Streamlit)
│   ├── docker/         # Môi trường chạy Spark Master/Worker và Kafka
│   └── requirements.txt# Thư viện Python cần cài đặt
├── dataset/
│   ├── raw/            # Dữ liệu cào gốc (products, reviews, categories, sellers)
│   ├── tiki_products_clean_full.csv   # FILE CHÍNH 2,307 SẢN PHẨM CHUẨN ĐỂ LÀM BÀI
│   ├── tiki_master_dataset_all_in_one.csv # BẢNG MASTER 360 ĐỘ
│   ├── tiki_database.db               # CSDL SQLite RDBMS
│   ├── nosql_documents/# CSDL NoSQL JSON Documents
│   ├── backups/        # Bản sao lưu snapshot dữ liệu có mã băm MD5
│   └── processed/      # Thư mục để các bạn xuất kết quả sau khi chạy Spark ETL / ML
├── reports/            # Báo cáo Word (*.docx), Slides (*.pptx), Bảng tự chấm (*.xlsx)
├── refs/               # Tài liệu tham khảo nghiên cứu
├── libs/               # Danh sách thư viện và tài liệu hướng dẫn
├── readme.txt          # File thông tin đề tài theo mẫu quy định nộp bài của Thầy
├── TAI_LIEU_CRAWL_API_TIKI.md # Tài liệu kỹ thuật tra cứu API & hướng dẫn chạy crawler
└── pack_submission.py  # Công cụ 1 lệnh nén file zip nộp bài chuẩn quy định
```

---

### 🌿 QUY TRÌNH LÀM VIỆC TRÊN GIT CHO CÁC THÀNH VIÊN

1. **Kéo dữ liệu và mã nguồn mới nhất về máy**:
   ```bash
   git checkout main
   git pull origin main
   ```
2. **Tạo nhánh riêng để làm việc (Không code đè lên `main`)**:
   ```bash
   # Ví dụ cho Khoa:
   git checkout -b feature/khoa-spark-etl
   
   # Ví dụ cho Nhật:
   git checkout -b feature/nhat-ml-nlp
   
   # Ví dụ cho Sang:
   git checkout -b feature/sang-dashboard-rfm
   ```
3. **Lấy dữ liệu CSV để code**:
   - Dữ liệu sản phẩm: đọc từ `dataset/tiki_products_clean_full.csv`
   - Dữ liệu đánh giá: đọc từ `dataset/raw/tiki_reviews.csv`
4. **Code xong thì commit và đẩy lên GitHub**:
   ```bash
   git add .
   git commit -m "feat: hoàn thành module ..."
   git push -u origin <tên-nhánh-của-bạn>
   ```
5. **Vào GitHub tạo Pull Request (PR)** gộp vào `main`.

---

### ⚙️ HƯỚNG DẪN THỰC THI MODULE CRAWLER (CHO THẦY CÔ CHẤM BÀI)

1. **Cài đặt môi trường**:
   ```bash
   pip install -r libs/requirements.txt
   ```
2. **Chạy cào dữ liệu sản phẩm mới (Tùy chọn)**:
   ```bash
   python3 source-code/crawler/crawl_tiki_products.py --pages 5
   ```
3. **Xuất CSDL Quan hệ SQLite & NoSQL**:
   ```bash
   python3 source-code/crawler/storage_exporter.py --type all
   ```
4. **Tạo bản sao lưu dữ liệu (Backup Snapshot)**:
   ```bash
   python3 source-code/crawler/backup_manager.py --backup
   ```
5. **Đóng gói file nén nộp bài theo chuẩn `<Mã lớp>_<STT nhóm>_<Tên đề tài>.zip`**:
   ```bash
   python3 pack_submission.py --class 06 --group 01
   ```
