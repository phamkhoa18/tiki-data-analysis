# HƯỚNG DẪN CÀI ĐẶT & QUẢN LÝ THƯ VIỆN (LIBS)
## Đề tài: Phân tích hệ thống dữ liệu thương mại điện tử TIKI

---

### 1. Danh sách các phần mềm, công cụ nền tảng (Platform & Frameworks)

| STT | Phần mềm / Nền tảng | Phiên bản khuyến nghị | Mục đích sử dụng trong đồ án |
|-----|----------------------|-----------------------|------------------------------|
| 1   | **Python**           | 3.9 - 3.11            | Ngôn ngữ lập trình chính cho toàn bộ pipeline |
| 2   | **Apache Spark**     | 3.4.x / 3.5.x         | Động cơ tính toán phân tán, xử lý Big Data Batch & Streaming, MLlib |
| 3   | **Java JDK**         | 11 hoặc 17 (OpenJDK)  | Yêu cầu bắt buộc để vận hành JVM cho Apache Spark |
| 4   | **Apache Kafka**     | 3.5+ (Docker)         | Message Broker giả lập luồng clickstream & sự kiện đơn hàng thời gian thực |
| 5   | **Docker & Compose** | 24.x+                 | Đóng gói và triển khai cụm Spark Master/Worker, Zookeeper, Kafka |
| 6   | **Streamlit**        | 1.30+                 | Framework xây dựng giao diện Dashboard phân tích dữ liệu trực quan |

---

### 2. Danh mục các thư viện Python chuyên dụng

#### 2.1. Phân tán & Lưu trữ dữ liệu lớn (Big Data & Data Lake)
- `pyspark`: Cung cấp API Python cho Spark SQL, Spark DataFrames, MLlib và Structured Streaming.
- `pyarrow`: Hỗ trợ định dạng cột Parquet nén Snappy, tối ưu I/O cho Data Lake.
- `findspark`: Tự động định vị và nạp biến môi trường SPARK_HOME trong môi trường Python.

#### 2.2. Xử lý & Phân tích dữ liệu (Data Manipulation & Analytics)
- `pandas`, `numpy`, `scipy`: Xử lý mảng đa chiều, tính toán thống kê mô tả, tương quan, tỷ lệ chiết khấu, biến động giá.

#### 2.3. Khai phá văn bản & Học máy (NLP & Machine Learning)
- `regex`, `nltk`: Chuẩn hóa tiếng Việt, loại bỏ stopwords, lọc ký tự đặc biệt và xử lý emoji trong bình luận Tiki.
- `scikit-learn`: Phân cụm RFM khách hàng (K-Means), tính toán TF-IDF, đánh giá chỉ số Silhouette.
- `PyTorch`: Mô hình mạng nơ-ron học sâu hỗ trợ phân loại cảm xúc (Sentiment Analysis).
- `pyspark.ml.recommendation.ALS`: Thuật toán Alternating Least Squares gợi ý sản phẩm cá nhân hóa dựa trên ma trận người dùng - sản phẩm.

#### 2.4. Trực quan hóa & Bảng điều khiển (Visualization & Web Dashboard)
- `streamlit`: Giao diện tương tác trực tiếp qua trình duyệt web.
- `plotly`: Biểu đồ tương tác đa chiều (Scatter, Sunburst, Treemap, Boxplot).
- `matplotlib`, `seaborn`: Đồ thị phân phối xác suất, ma trận nhiệt tương quan.

#### 2.5. Thu thập dữ liệu (Web & API Ingestion)
- `requests`, `aiohttp`: Thu thập dữ liệu bất đồng bộ song song từ API công khai của Tiki (`/api/v2/products`, `/api/v2/reviews`).
- `beautifulsoup4`: Trích xuất và bóc tách dữ liệu văn bản từ HTML mô tả sản phẩm.

#### 2.6. Tự động hóa báo cáo
- `python-docx`: Tự động sinh file báo cáo đồ án `BaoCao_DoAn_BigData_TIKI.docx`.
- `python-pptx`: Tự động sinh slide thuyết trình `Slide_ThuyetTrinh_TIKI_BigData.pptx`.
- `openpyxl`, `xlsxwriter`: Tự động sinh bảng phân công và tự chấm điểm `Bang_Phan_Cong_Va_Tu_Cham_Diem.xlsx`.

---

### 3. Quy trình cài đặt môi trường

```bash
# Bước 1: Tạo môi trường ảo (Virtual Environment)
python3 -m venv venv

# Bước 2: Kích hoạt môi trường ảo
# Trên macOS / Linux:
source venv/bin/activate
# Trên Windows:
# venv\Scripts\activate

# Bước 3: Nâng cấp pip và cài đặt thư viện
pip install --upgrade pip
pip install -r libs/requirements.txt
```
