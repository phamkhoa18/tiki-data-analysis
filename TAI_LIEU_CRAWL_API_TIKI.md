# TÀI LIỆU KỸ THUẬT: HƯỚNG DẪN THU THẬP DỮ LIỆU & TRA CỨU API TIKI.VN
> **Hệ Thống Phân Tích Dữ Liệu Lớn Thương Mại Điện Tử Tiki (Tiki Big Data Analytics Platform)**  
> *Tài liệu kỹ thuật phục vụ Báo cáo Đồ án Hệ sinh thái Hadoop & Dữ liệu lớn*

---

## 1. TỔNG QUAN KIẾN TRÚC API TIKI.VN

Tiki.vn xây dựng hệ thống theo kiến trúc **Microservices & Headless E-commerce**. Toàn bộ dữ liệu hiển thị trên giao diện web và ứng dụng di động đều được nạp thông qua các giao diện lập trình ứng dụng công khai (**Public RESTful APIs**).

* **Giao thức**: HTTPS / HTTP/2 (TLS 1.3)
* **Định dạng dữ liệu trả về**: JSON (JavaScript Object Notation)
* **Cơ chế phân trang**: Phân trang theo tham số `page` và `limit`
* **Hệ thống phòng vệ (Security)**: ByteDance WAF (Byte-nginx) kiểm tra dấu vân tay trình duyệt (TLS Fingerprint JA3/HTTP2) và tự động kích hoạt JavaScript Challenge khi phát hiện truy cập tự động tần suất cao.

---

## 2. BẢNG TRA CỨU CATEGORY ID CÁC NGÀNH HÀNG TIKI

Trong hệ thống Tiki, mỗi ngành hàng (danh mục) được định danh bằng một mã số nguyên duy nhất (**Category ID**). Dưới đây là bảng mã danh mục chuẩn của 10 ngành hàng lớn nhất trên Tiki:

| STT | Category ID | Tên Ngành Hàng (Category Name) | URL Slug | URL Gọi API Mẫu Trực Tiếp |
| :---: | :---: | :--- | :--- | :--- |
| **1** | `1789` | Điện Thoại - Máy Tính Bảng | `dien-thoai-may-tinh-bang` | `https://tiki.vn/api/v2/products?category=1789&limit=40&page=1` |
| **2** | `1815` | Thiết Bị Số - Phụ Kiện Số | `thiet-bi-kts-phu-kien-so` | `https://tiki.vn/api/v2/products?category=1815&limit=40&page=1` |
| **3** | `1882` | Điện Gia Dụng | `dien-gia-dung` | `https://tiki.vn/api/v2/products?category=1882&limit=40&page=1` |
| **4** | `8322` | Nhà Sách Tiki | `nha-sach-tiki` | `https://tiki.vn/api/v2/products?category=8322&limit=40&page=1` |
| **5** | `1520` | Làm Đẹp - Sức Khỏe | `lam-dep-suc-khoe` | `https://tiki.vn/api/v2/products?category=1520&limit=40&page=1` |
| **6** | `915` | Thời Trang Nam | `thoi-trang-nam` | `https://tiki.vn/api/v2/products?category=915&limit=40&page=1` |
| **7** | `931` | Thời Trang Nữ | `thoi-trang-nu` | `https://tiki.vn/api/v2/products?category=931&limit=40&page=1` |
| **8** | `1883` | Nhà Cửa - Đời Sống | `nha-cua-doi-song` | `https://tiki.vn/api/v2/products?category=1883&limit=40&page=1` |
| **9** | `4384` | Bách Hóa Online | `bach-hoa-online` | `https://tiki.vn/api/v2/products?category=4384&limit=40&page=1` |
| **10** | `1975` | Thể Thao - Dã Ngoại | `the-thao-da-ngoai` | `https://tiki.vn/api/v2/products?category=1975&limit=40&page=1` |

### 🔍 Cách Tự Tìm Category ID Của Bất Kỳ Ngành Nào Khác:
1. **Cách 1 (Qua URL)**: Mở trình duyệt vào danh mục bất kỳ trên Tiki (ví dụ: `https://tiki.vn/laptop/c8095`). Phần số sau chữ `c` chính là **Category ID** (ở đây là `8095`).
2. **Cách 2 (Qua DevTools F12)**:
   - Bấm `F12` (hoặc chuột phải chọn *Inspect*) ➔ Chọn tab **Network** ➔ Chọn lọc **Fetch/XHR**.
   - F5 tải lại trang danh mục ➔ Tìm request có tên `products?limit=...`.
   - Xem mục **Payload / Query String Parameters**, trường `category` chính là ID của danh mục đó.

---

## 3. CHI TIẾT CÁC API ENDPOINTS & THAM SỐ TRUY VẤN

### 3.1. API Lấy Danh Sách Sản Phẩm (Products Listing API)
* **Endpoint**: `GET https://tiki.vn/api/v2/products`
* **Mục đích**: Lấy danh sách sản phẩm theo danh mục, có phân trang và sắp xếp.
* **Bảng tham số truy vấn (Query Parameters)**:

| Tham số (Param) | Kiểu dữ liệu | Bắt buộc | Giá trị ví dụ | Giải thích ý nghĩa |
| :--- | :---: | :---: | :--- | :--- |
| `category` | Integer | Có | `1789` | Mã Category ID của ngành hàng cần lấy. |
| `page` | Integer | Không | `1` | Số thứ tự trang (bắt đầu từ 1 đến 50). |
| `limit` | Integer | Không | `40` | Số lượng sản phẩm mỗi trang (tối ưu nhất là 40). |
| `sort` | String | Không | `top_seller` | Tiêu chí sắp xếp sản phẩm:<br>• `top_seller`: Bán chạy nhất<br>• `default`: Nổi bật / Phổ biến<br>• `newest`: Hàng mới nhất<br>• `price,asc`: Giá thấp đến cao<br>• `price,desc`: Giá cao đến thấp |
| `urlKey` | String | Không | `dien-thoai-smartphone` | Đường dẫn phụ danh mục con (tùy chọn). |

* **Cấu trúc dữ liệu JSON trả về (Key Fields)**:
```json
{
  "data": [
    {
      "id": 279418598,
      "sku": "5448826284393",
      "name": "Điện Thoại Samsung Galaxy A07 5G 4GB/128GB - Hàng Chính Hãng",
      "url_path": "dien-thoai-samsung-galaxy-a07-5g-4gb-128gb-p279418598.html",
      "price": 4999000,
      "original_price": 5890000,
      "discount": 891000,
      "discount_rate": 15,
      "rating_average": 4.8,
      "review_count": 34,
      "quantity_sold": {"text": "Đã bán 110", "value": 110},
      "brand_name": "Samsung",
      "seller_name": "Tiki Trading",
      "is_from_official_store": true,
      "is_authentic": 1,
      "badges_new": [{"code": "tikinow", "text": "Giao siêu tốc 2h"}],
      "origin": "Trung Quốc"
    }
  ],
  "paging": {
    "total": 2000,
    "current_page": 1,
    "last_page": 50,
    "per_page": 40
  }
}
```

---

### 3.2. API Lấy Thông Số Kỹ Thuật Chi Tiết (Product Detail API - Nguồn #2)
* **Endpoint**: `GET https://tiki.vn/api/v2/products/{product_id}`
* **Mục đích**: Bóc tách sâu thông số kỹ thuật (Specifications), thông tin bảo hành (Warranty), chính sách đổi trả và mô tả sản phẩm.
* **Tham số**:
  - `{product_id}`: ID số của sản phẩm (ví dụ: `279418598`).
* **Dữ liệu trích xuất giá trị**:
  - `specifications`: Bảng cấu hình chi tiết (RAM, ROM, chip xử lý, chất liệu, kích thước...).
  - `warranty_info`: Thời gian và hình thức bảo hành (ví dụ: "12 tháng điện tử chính hãng").
  - `description`: Toàn bộ bài viết mô tả chi tiết sản phẩm.
  - `images`: Danh sách toàn bộ URL ảnh chất lượng cao của sản phẩm.

---

### 3.3. API Tìm Kiếm Theo Từ Khóa (Product Search API)
* **Endpoint**: `GET https://tiki.vn/api/v2/products?q={keyword}`
* **Ví dụ**: `https://tiki.vn/api/v2/products?q=tai+nghe+bluetooth&limit=40`
* **Mục đích**: Thu thập sản phẩm theo xu hướng từ khóa người dùng tìm kiếm thay vì danh mục cố định.

---

## 4. CÁC API THAY THẾ (FALLBACK APIS) KHI BỊ CHẶN HOẶC ĐỔI CẤU TRÚC

Trong kỹ thuật thu thập dữ liệu lớn (Big Data Web Scraping), nếu một cổng kết nối API bị chặn hoặc thay đổi, kiến trúc dự án hỗ trợ các cổng thay thế sau:

### 4.1. Cổng Thay Thế 1: Mobile App REST API (`api.tiki.vn`)
Tiki có hệ thống API riêng dành cho ứng dụng di động iOS/Android:
* **Endpoint**: `https://api.tiki.vn/v2/products?category={category_id}&limit=40&page={page}`
* **Ưu điểm**: Endpoint này thường có cơ chế rate limit lỏng hơn so với web và không bị chèn các thẻ kiểm tra Cookie của trình duyệt.
* **Header yêu cầu**:
  ```http
  User-Agent: Tiki/2024.1 (iPhone; iOS 17.5; Scale/3.00)
  Accept: application/json
  ```

### 4.2. Cổng Thay Thế 2: Thanos Microservice API
* **Endpoint**: `http://thanos.tiki.services/full/v2/products?category={category_id}`
* **Ghi chú**: Đây là backend service nội bộ của Tiki phục vụ render dữ liệu listing. Khi web frontend bị quá tải, một số request có thể gọi trực tiếp qua route này.

### 4.3. Cổng Thay Thế 3: Web HTML Scraping với BeautifulSoup (Nguồn #2 Dự Phòng)
Nếu toàn bộ JSON API bị chặn Captcha, hệ thống chuyển sang chế độ cào HTML trực tiếp:
* **URL**: `https://tiki.vn/{url_slug}`
* **Bộ bóc tách**: Thư viện Python `BeautifulSoup4` phân tích mã HTML:
  - Tên sản phẩm: thẻ `h1`
  - Giá bán: class `.product-price__current-price`
  - Bảng thông số: thẻ `table` trong khối thông số kỹ thuật.

### 4.4. Cơ Chế Tự Động Vượt Tường Lửa WAF (ByteDance WAF Bypass)
Dự án được tích hợp sẵn module `waf_solver.py`:
1. Khi máy chủ trả về mã HTML thử thách JavaScript (`_0x...`), module tự động chuyển đoạn mã vào sandbox Node.js.
2. Sandbox chạy mã trong **50ms** để tính toán token hợp lệ và xuất ra cookie `_wafchallengeid`.
3. Gán cookie này vào phiên làm việc (`Session`), giúp quá trình cào tiếp tục trơn tru mà không cần can thiệp thủ công.

---

## 5. HƯỚNG DẪN SỬ DỤNG SCRIPT CÀO SẢN PHẨM CHUYÊN NGHIỆP

File mã nguồn độc lập nằm tại: [source-code/crawler/crawl_tiki_products.py](file:///Users/khoait/Documents/SourceCompany/bigdata_doan/source-code/crawler/crawl_tiki_products.py)

### 5.1. Lệnh cào toàn bộ 10 ngành hàng (Mặc định 5 trang = 200 sp/ngành):
```bash
python3 source-code/crawler/crawl_tiki_products.py --pages 5 --output dataset/tiki_products_clean_full.csv
```

### 5.2. Lệnh cào chuyên sâu 1 ngành hàng cụ thể:
Ví dụ cào riêng ngành **Điện Thoại - Máy Tính Bảng (Category ID: 1789)** với 10 trang (400 sản phẩm):
```bash
python3 source-code/crawler/crawl_tiki_products.py --category 1789 --pages 10 --output dataset/dien_thoai_products.csv
```

### 5.3. Lệnh cào theo tiêu chí Giá thấp đến cao (Săn hàng rẻ):
```bash
python3 source-code/crawler/crawl_tiki_products.py --category 1815 --pages 3 --sort "price,asc"
```

---

## 6. CẤU TRÚC TỆP DỮ LIỆU SẢN PHẨM CHUẨN (DATA DICTIONARY - 35 CỘT)

Tệp dữ liệu đầu ra: [dataset/tiki_products_clean_full.csv](file:///Users/khoait/Documents/SourceCompany/bigdata_doan/dataset/tiki_products_clean_full.csv) (2,307 sản phẩm) gồm 35 cột thuộc tính chuẩn hóa:

| STT | Tên Cột (Field Name) | Kiểu dữ liệu | Ý nghĩa Nghiệp Vụ & Giá trị mẫu |
| :---: | :--- | :---: | :--- |
| **1** | `product_id` | Integer (PK) | Mã ID duy nhất của sản phẩm (Ví dụ: `279418598`). |
| **2** | `name` | String | Tên đầy đủ của sản phẩm. |
| **3** | `sku` | String | Mã quản lý kho hàng hóa. |
| **4** | `category_id` | Integer (FK) | Mã ngành hàng (Ví dụ: `1789`). |
| **5** | `category_name` | String | Tên ngành hàng (Điện thoại Smartphone, Gia dụng...). |
| **6** | `brand_id` | Integer | Mã thương hiệu trong hệ thống. |
| **7** | `brand_name` | String | Tên thương hiệu (Apple, Samsung, Lock&Lock...). |
| **8** | `price` | Integer | Giá bán hiện tại bằng VNĐ (Ví dụ: `4999000`). |
| **9** | `original_price` | Integer | Giá niêm yết ban đầu trước khi giảm (Ví dụ: `5890000`). |
| **10** | `discount` | Integer | Số tiền được giảm = `original_price - price` (VNĐ). |
| **11** | `discount_rate` | Float | Tỷ lệ chiết khấu % (Ví dụ: `15.1%`). |
| **12** | `price_segment` | String | Phân khúc giá: Giá rẻ, Phổ thông, Trung cấp, Cận cao cấp, Cao cấp. |
| **13** | `quantity_sold` | Integer | Số lượng sản phẩm đã bán thành công thực tế (Ví dụ: `110`). |
| **14** | `revenue_estimate` | BigInt | Doanh thu ước tính = `price * quantity_sold` (VNĐ). |
| **15** | `rating_average` | Float | Điểm đánh giá sao trung bình (1.0 đến 5.0 sao). |
| **16** | `review_count` | Integer | Tổng số lượt nhận xét từ người mua hàng. |
| **17** | `performance_score` | Float | Chỉ số hiệu năng = $\log_{10}(\text{quantity\_sold} + 1) \times \text{rating}$. |
| **18** | `product_tier` | String | Xếp hạng: Ngôi Sao (Star), Bò Sữa (Cash Cow), Tiềm Năng, Tiêu Chuẩn. |
| **19** | `seller_id` | Integer | Mã số của cửa hàng bán sản phẩm. |
| **20** | `seller_name` | String | Tên nhà bán hàng (Ví dụ: "Tiki Trading", "Apple Flagship"). |
| **21** | `seller_type` | String | Phân loại: "Gian Hàng Chính Hãng (Mall)" hoặc "Nhà Bán Marketplace". |
| **22** | `is_official_store` | Boolean | True nếu là gian hàng chính hãng được Tiki xác thực. |
| **23** | `is_authentic` | Boolean | Cam kết hàng chính hãng 100%. |
| **24** | `is_tiki_now` | Boolean | Có hỗ trợ giao hàng siêu tốc 2 giờ hay không. |
| **25** | `is_freeship_xtra` | Boolean | Có tham gia gói miễn phí vận chuyển Freeship Xtra hay không. |
| **26** | `origin` | String | Nơi sản xuất / Xuất xứ (Việt Nam, Trung Quốc, Nhật Bản, Mỹ...). |
| **27** | `inventory_status` | String | Tình trạng kho hàng ("available" - còn hàng). |
| **28** | `warranty_info` | String | Chính sách bảo hành (Nguồn #2 - Scraper). |
| **29** | `return_policy` | String | Chính sách đổi trả hàng hóa (Nguồn #2 - Scraper). |
| **30** | `specifications` | Text | Bảng thông số kỹ thuật chi tiết của sản phẩm (Nguồn #2 - Scraper). |
| **31** | `short_description` | Text | Đoạn tóm tắt đặc tính nổi bật của sản phẩm. |
| **32** | `product_url` | String | Đường dẫn liên kết trực tiếp đến trang web sản phẩm. |
| **33** | `thumbnail_url` | String | Đường dẫn ảnh đại diện sản phẩm chất lượng cao. |
| **34** | `data_source` | String | Nguồn thu thập dữ liệu (`tiki_api` kết hợp `tiki_web`). |
| **35** | `crawled_at` | DateTime | Thời gian thực thi cào dữ liệu (Năm-Tháng-Ngày Giờ:Phút:Giây). |

---

## 7. HỆ THỐNG LƯU TRỮ CSDL QUAN HỆ (RDBMS) & PHI CẤU TRÚC (NOSQL)

Dữ liệu thu thập sau khi cào và làm sạch được hỗ trợ chuyển đổi lưu trữ sang cả 2 mô hình cơ sở dữ liệu hiện đại thông qua công cụ độc lập: [source-code/crawler/storage_exporter.py](file:///Users/khoait/Documents/SourceCompany/bigdata_doan/source-code/crawler/storage_exporter.py)

### 7.1. Lưu trữ CSDL Quan Hệ SQLite (RDBMS)
- **Tập tin cơ sở dữ liệu**: [dataset/tiki_database.db](file:///Users/khoait/Documents/SourceCompany/bigdata_doan/dataset/tiki_database.db)
- **Cấu trúc bảng chuẩn (3NF)**:
  - Bảng `categories`: Lưu 10 danh mục (PK: `category_id`).
  - Bảng `sellers`: Lưu thông tin 315 nhà bán hàng (PK: `seller_id`).
  - Bảng `products`: Lưu 2,307 sản phẩm (PK: `product_id`, FK: `category_id`, `seller_id`).
  - Bảng `reviews`: Lưu 35,632 đánh giá (PK: `review_id`, FK: `product_id`).
- **Chỉ mục (Index)**: Đã tạo Index trên các cột thường xuyên truy vấn (`category_id`, `price`, `rating_average`, `sentiment`).
- **Lệnh thực thi nạp dữ liệu vào SQLite**:
  ```bash
  python3 source-code/crawler/storage_exporter.py --type sqlite
  ```
- **Lệnh chạy truy vấn SQL mẫu (Top bán chạy, Doanh thu ngành)**:
  ```bash
  python3 source-code/crawler/storage_exporter.py --type query
  ```

### 7.2. Lưu trữ CSDL Phi Cấu Trúc NoSQL (MongoDB-ready JSON Documents)
- **Tập tin Document NoSQL**: [dataset/nosql_documents/products_collection.jsonl](file:///Users/khoait/Documents/SourceCompany/bigdata_doan/dataset/nosql_documents/products_collection.jsonl)
- **Mô hình**: Document lồng nhau (Embedded JSON). Mỗi sản phẩm nhúng trực tiếp thông tin Pricing, Brand, Seller, Policies và mẫu các Reviews của khách hàng.
- **Lệnh thực thi xuất NoSQL Documents**:
  ```bash
  python3 source-code/crawler/storage_exporter.py --type nosql
  ```
- **Lệnh nạp vào MongoDB (nếu môi trường có MongoDB)**:
  ```bash
  mongoimport --db tiki_db --collection products --file dataset/nosql_documents/products_collection.jsonl
  ```

---

## 8. HỆ THỐNG SAO LƯU & PHỤC HỒI DỮ LIỆU (BACKUP & RESTORE)

Dự án trang bị công cụ quản trị sao lưu phục hồi dữ liệu chuyên nghiệp: [source-code/crawler/backup_manager.py](file:///Users/khoait/Documents/SourceCompany/bigdata_doan/source-code/crawler/backup_manager.py)

### 8.1. Lệnh tạo bản sao lưu snapshot ngay lập tức (Backup):
Tự động nén toàn bộ dataset và CSDL thành file zip có gắn timestamp, tự động tính toán mã băm MD5 Checksum:
```bash
python3 source-code/crawler/backup_manager.py --backup --desc "Bản sao lưu dữ liệu Tiki sau khi cào"
```
*Tập tin sao lưu được lưu tại thư mục: [dataset/backups/](file:///Users/khoait/Documents/SourceCompany/bigdata_doan/dataset/backups/)*

### 8.2. Lệnh xem danh sách các bản sao lưu đã tạo:
```bash
python3 source-code/crawler/backup_manager.py --list
```

### 8.3. Lệnh phục hồi dữ liệu từ bản sao lưu (Restore):
Khôi phục nguyên vẹn toàn bộ dữ liệu từ bản snapshot gần nhất (có xác minh MD5 checksum trước khi bung nén):
```bash
python3 source-code/crawler/backup_manager.py --restore latest
```

---

## 9. TỔNG KẾT BỘ LỆNH CÀO & QUẢN TRỊ DỮ LIỆU DÀNH CHO GIẢNG VIÊN

| Thao tác | Câu lệnh thực thi Terminal | Kết quả đầu ra |
| :--- | :--- | :--- |
| **1. Cào toàn bộ 10 ngành** | `python3 source-code/crawler/crawl_tiki_products.py --pages 5` | [dataset/tiki_products_clean_full.csv](file:///Users/khoait/Documents/SourceCompany/bigdata_doan/dataset/tiki_products_clean_full.csv) (35 cột chuẩn) |
| **2. Cào riêng 1 ngành hàng** | `python3 source-code/crawler/crawl_tiki_products.py --category 1789 --pages 10` | 400 sản phẩm ngành Điện thoại |
| **3. Xuất CSDL SQLite & NoSQL**| `python3 source-code/crawler/storage_exporter.py --type all` | SQLite DB (`.db`) & NoSQL JSONL |
| **4. Chạy truy vấn SQL test** | `python3 source-code/crawler/storage_exporter.py --type query` | Kết quả truy vấn SQL hiển thị trực tiếp |
| **5. Tạo bản sao lưu (Backup)** | `python3 source-code/crawler/backup_manager.py --backup` | File snapshot `.zip` trong `dataset/backups/` |
| **6. Khôi phục dữ liệu (Restore)**| `python3 source-code/crawler/backup_manager.py --restore latest` | Dữ liệu được hoàn nguyên 100% |

