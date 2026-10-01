# Đồ Án Big Data: Phân Tích Hệ Thống Dữ Liệu Sàn Thương Mại Điện Tử TIKI
## (Tiki E-Commerce Big Data Analytics & AI Recommendation System)

### Thông Tin Nhóm Sinh Viên
1. **Phạm Đăng Khoa** (MSSV: 24810114)
2. **Phạm Minh Nhật** (MSSV: 24810119)
3. **Nguyễn Văn Sang** (MSSV: 24810114)

---

### 🌿 Hướng Dẫn Git & Tạo Nhánh (Branch) Cho Thành Viên Nhóm
> 📖 *Tài liệu chi tiết xem tại:* [HUONG_DAN_GIT_CHO_NHOM.md](HUONG_DAN_GIT_CHO_NHOM.md)

**Quy tắc:** Tuyệt đối **không code trực tiếp trên nhánh `main`**. Mỗi người tạo 1 nhánh riêng để làm việc.

#### 1. Lấy code mới nhất về máy trước khi làm việc:
```bash
git checkout main
git pull origin main
```

#### 2. Tạo nhánh riêng của mình:
```bash
# Cú pháp: git checkout -b feature/<tên-bạn>-<nhiệm-vụ>

# Ví dụ cho Khoa:
git checkout -b feature/khoa-pyspark-etl

# Ví dụ cho Nhật:
git checkout -b feature/nhat-crawler-nlp

# Ví dụ cho Sang:
git checkout -b feature/sang-dashboard-rfm
```

#### 3. Viết code xong thì lưu (commit) và đẩy lên GitHub:
```bash
git status
git add .
git commit -m "feat: mô tả công việc bạn vừa hoàn thành"

# Đẩy nhánh lên GitHub (lần đầu):
git push -u origin <tên-nhánh-của-bạn>
```

#### 4. Tạo Pull Request (PR):
- Vào link repo: https://github.com/phamkhoa18/tiki-data-analysis
- Bấm nút xanh **"Compare & pull request"** để gộp code vào `main`.

---

### Cấu Trúc Thư Mục Chuẩn Nộp Bài
Dự án được cấu trúc đúng theo hướng dẫn nộp đồ án:

```
bigdata_doan/
├── source-code/               # Toàn bộ mã nguồn hệ thống
│   ├── crawler/              # Thu thập dữ liệu từ Tiki Public REST API
│   ├── etl_spark/            # Xử lý làm sạch, chuẩn hóa với Apache Spark
│   ├── analytics_ml/         # Phân tích kinh doanh, NLP tiếng Việt, ALS Recommender, RFM
│   ├── streaming/            # Giả lập luồng sự kiện clickstream Kafka & Spark Streaming
│   ├── dashboard/            # Web Dashboard trực quan hóa tương tác (Streamlit)
│   ├── docker/               # Cấu hình Docker Compose (Spark Master/Worker, Kafka, Zookeeper)
│   ├── pipeline_runner.py    # Script chạy toàn bộ pipeline ETL & ML end-to-end
│   └── requirements.txt      # Danh sách thư viện cần cài đặt
├── dataset/                  # Dữ liệu phục vụ hệ thống
│   ├── raw/                  # Dữ liệu gốc (products, reviews, categories)
│   ├── processed/            # Dữ liệu Parquet đã làm sạch & phân vùng Data Lake
│   └── generate_dataset.py   # Script sinh/cập nhật dữ liệu mẫu
├── reports/                  # Báo cáo, slide thuyết trình, bảng phân công & tự chấm
│   ├── BaoCao_DoAn_BigData_TIKI.docx
│   ├── Slide_ThuyetTrinh_TIKI_BigData.pptx
│   └── Bang_Phan_Cong_Va_Tu_Cham_Diem.xlsx
├── refs/                     # Tài liệu tham khảo, bài báo khoa học, BibTeX
├── libs/                     # Danh sách thư viện và tài liệu hướng dẫn môi trường
├── readme.txt                # Tập tin thông tin đề tài và nhóm theo đúng mẫu
├── HUONG_DAN_GIT_CHO_NHOM.md # Hướng dẫn chi tiết quy trình Git & tạo branch
└── pack_submission.py        # Công cụ 1-click đóng gói file ZIP nộp đồ án
```

---

### Hướng Dẫn Chạy Nhanh

#### 1. Cài đặt thư viện
```bash
pip install -r libs/requirements.txt
```

#### 2. Chạy toàn bộ pipeline ETL, Analytics & ML
```bash
python3 source-code/pipeline_runner.py
```

#### 3. Khởi chạy Web Dashboard
```bash
streamlit run source-code/dashboard/app.py
```

#### 4. Đóng gói file nén nộp bài theo chuẩn `<Mã lớp>_<STT nhóm>_<Tên đề tài>.zip`
```bash
python3 pack_submission.py --class 06 --group 01
```
*(File zip sẽ được tạo tự động với đầy đủ các thư mục theo đúng yêu cầu giảng viên)*
