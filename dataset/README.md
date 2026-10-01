# TẬP DỮ LIỆU ĐỒ ÁN BIG DATA: SÀN THƯƠNG MẠI ĐIỆN TỬ TIKI

Tập dữ liệu phục vụ nghiên cứu và phân tích hệ thống Big Data của Tiki, bao gồm dữ liệu sản phẩm, phân cấp danh mục, và đánh giá/bình luận của khách hàng.

---

## 1. Cấu trúc thư mục dữ liệu

```
dataset/
├── generate_dataset.py           # Script tự động sinh dữ liệu mẫu quy mô lớn
├── raw/                          # Dữ liệu thô ban đầu (CSV / JSON)
│   ├── tiki_categories.csv       # Danh mục sản phẩm đa cấp
│   ├── tiki_products.csv         # Bảng thông tin sản phẩm (1,500+ records)
│   ├── tiki_products.json        # Định dạng JSON cho NoSQL / MongoDB
│   ├── tiki_reviews.csv          # Bảng đánh giá của khách hàng (6,000+ records)
│   └── tiki_reviews.json         # Bình luận khách hàng dạng JSON
└── processed/                    # Dữ liệu sau khi làm sạch bởi Spark (Parquet)
    ├── parquet_products/         # Lưu trữ dạng cột nén Snappy
    ├── parquet_reviews/          # Phân vùng theo category_id
    └── analytics_results/        # Kết quả tổng hợp chỉ số kinh doanh & ML
```

---

## 2. Từ điển dữ liệu (Data Dictionary)

### 2.1. Bảng sản phẩm (`tiki_products.csv`)

| Tên trường | Kiểu dữ liệu | Ý nghĩa |
|------------|--------------|---------|
| `id` | Integer | Định danh duy nhất sản phẩm (Product ID) |
| `sku` | String | Mã quản lý kho hàng (Stock Keeping Unit) |
| `name` | String | Tên đầy đủ sản phẩm |
| `price` | BigInt | Giá bán hiện tại sau chiết khấu (VNĐ) |
| `original_price`| BigInt | Giá niêm yết ban đầu của nhà bán (VNĐ) |
| `discount_rate` | Integer | Tỷ lệ giảm giá (%) |
| `rating_average`| Float | Điểm đánh giá trung bình (1.0 - 5.0 sao) |
| `review_count` | Integer | Tổng số lượt nhận xét từ người mua |
| `quantity_sold` | Integer | Ước tính số lượng đã bán thành công |
| `category_id` | Integer | Khóa ngoại liên kết danh mục |
| `category_name` | String | Tên danh mục ngành hàng |
| `brand_name` | String | Thương hiệu sản phẩm |
| `seller_id` | Integer | ID nhà bán hàng |
| `seller_name` | String | Tên gian hàng bán sản phẩm |
| `is_official_seller` | Boolean | Gian hàng chính hãng (Tiki Trading/Mall) |
| `is_tiki_now` | Boolean | Hỗ trợ giao hàng siêu tốc 2 giờ |
| `inventory_status` | String | Trạng thái kho hàng (`available`, `low_stock`) |
| `created_at` | Timestamp | Thời điểm đăng bán sản phẩm |

### 2.2. Bảng đánh giá & nhận xét (`tiki_reviews.csv`)

| Tên trường | Kiểu dữ liệu | Ý nghĩa |
|------------|--------------|---------|
| `review_id` | BigInt | Định danh duy nhất của lượt đánh giá |
| `product_id` | Integer | Khóa ngoại liên kết bảng sản phẩm |
| `product_name` | String | Tên sản phẩm được đánh giá |
| `customer_id` | Integer | Định danh khách hàng (ẩn danh) |
| `customer_name`| String | Tên hiển thị người mua hàng |
| `rating` | Integer | Số sao đánh giá (1 đến 5 sao) |
| `sentiment` | String | Nhãn cảm xúc (`POSITIVE`, `NEUTRAL`, `NEGATIVE`) |
| `title` | String | Tiêu đề nhận xét của khách |
| `content` | Text | Nội dung chi tiết bình luận tiếng Việt |
| `thank_count` | Integer | Số lượt người khác bấm Hữu ích |
| `delivery_rating` | Integer | Đánh giá dịch vụ giao nhận (1 - 5) |
| `quality_rating` | Integer | Đánh giá chất lượng thực tế sản phẩm (1 - 5) |
| `created_at` | Timestamp | Thời điểm gửi đánh giá |
