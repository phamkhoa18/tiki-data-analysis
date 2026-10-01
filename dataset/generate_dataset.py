#!/usr/bin/env python3
"""
Tiki Big Data Dataset Generator
Generates realistic, rich e-commerce datasets for Tiki platform:
- Products: SKU, name, price, discount, ratings, reviews count, brand, seller, category, sales quantity
- Reviews: Review ID, product ID, customer ID, rating, sentiment, Vietnamese comment content, thank count, purchase date
"""

import json
import random
import csv
import os
from datetime import datetime, timedelta

def generate_datasets(num_products=1500, num_reviews=6000, seed=42):
    random.seed(seed)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    raw_dir = os.path.join(current_dir, "raw")
    os.makedirs(raw_dir, exist_ok=True)

    categories = [
        {"id": 1789, "name": "Điện Thoại - Máy Tính Bảng", "slug": "dien-thoai-may-tinh-bang"},
        {"id": 1815, "name": "Thiết Bị Số - Phụ Kiện Số", "slug": "thiet-bi-so-phu-kien-so"},
        {"id": 1882, "name": "Điện Gia Dụng", "slug": "dien-gia-dung"},
        {"id": 8322, "name": "Nhà Sách Tiki", "slug": "nha-sach-tiki"},
        {"id": 1520, "name": "Làm Đẹp - Sức Khỏe", "slug": "lam-dep-suc-khoe"},
        {"id": 915, "name": "Thời Trang Nam", "slug": "thoi-trang-nam"},
        {"id": 1883, "name": "Nhà Cửa - Đời Sống", "slug": "nha-cua-doi-song"},
    ]

    brands_by_cat = {
        1789: ["Apple", "Samsung", "Xiaomi", "OPPO", "Vivo", "Realme", "ASUS"],
        1815: ["Sony", "Anker", "Baseus", "Logitech", "JBL", "Marshall", "Sandisk", "UGREEN"],
        1882: ["Philips", "Lock&Lock", "Tefal", "Sunhouse", "Panasonic", "Kangaroo", "Sharp", "Cosori"],
        8322: ["NXB Trẻ", "NXB Kim Đồng", "Alpha Books", "Nhã Nam", "First News", "NXB Phụ Nữ"],
        1520: ["La Roche-Posay", "L'Oreal Paris", "Innisfree", "Vichy", "Laneige", "The Ordinary", "Cocoon"],
        915: ["Coolmate", "An Phước", "Routine", "Canifa", "Owen", "Biluxury", "Aristino"],
        1883: ["Duy Tân", "Inochi", "Lock&Lock", "Tupperware", "Rạng Đông", "Điện Quang"],
    }

    product_templates = {
        1789: [
            "Điện thoại {brand} Pro Max {spec} Chính Hãng VN/A",
            "Điện thoại thông minh {brand} Ultra 5G {spec}",
            "Máy tính bảng {brand} Tab Wifi + Cellular {spec}",
            "Điện thoại gập {brand} Flip thế hệ mới",
        ],
        1815: [
            "Tai nghe không dây Bluetooth {brand} Chống ồn chủ động ANC",
            "Củ sạc nhanh {brand} GaN 65W Cổng Type-C PD Quick Charge",
            "Chuột không dây công thái học {brand} Silent Click",
            "Bàn phím cơ không dây {brand} RGB Hot-swap",
            "Loa Bluetooth di động {brand} Âm bass mạnh mẽ chống nước IPX7",
            "Cáp sạc đa năng {brand} bọc dù siêu bền truyền dữ liệu tốc độ cao",
        ],
        1882: [
            "Nồi chiên không dầu điện tử {brand} Dung tích 6.5L Giảm 85% dầu mỡ",
            "Robot hút bụi lau nhà thông minh {brand} Laser LiDAR Tự động đổ rác",
            "Máy lọc không khí {brand} Màng lọc HEPA diệt khuẩn khử mùi",
            "Nồi cơm điện cao tần {brand} Lòng nồi chống dính cao cấp",
            "Máy xay sinh tố cầm tay đa năng {brand} Lưỡi dao inox 304",
        ],
        8322: [
            "Sách - Tâm Lý Học Về Tiền - Morgan Housel ({brand})",
            "Sách - Nhà Giả Kim - Paulo Coelho ({brand})",
            "Sách - Thiết Kế Cuộc Đời Đáng Sống - Designing Your Life ({brand})",
            "Sách - Tư Duy Nhanh Và Chậm - Daniel Kahneman ({brand})",
            "Sách - Đắc Nhân Tâm - Khổ Lớn Đặc Biệt ({brand})",
            "Sách - Kỹ Năng Quản Lý Thời Gian Cho Người Bận Rộn ({brand})",
            "Sách - Nguyên Lý Big Data & Học Máy Ứng Dụng ({brand})",
        ],
        1520: [
            "Kem chống nắng kiểm soát dầu {brand} SPF 50+ PA++++ 50ml",
            "Serum phục hồi làm dịu da cấp ẩm {brand} Niacinamide 10%",
            "Nước tẩy trang dịu nhẹ cho da nhạy cảm {brand} Micellar Water 400ml",
            "Sữa rửa mặt tạo bọt sạch sâu se khít lỗ chân lông {brand}",
            "Kem dưỡng ẩm tái tạo phục hồi màng bảo vệ da {brand} 50ml",
        ],
        915: [
            "Áo thun nam Cotton Compact chống nhăn co giãn {brand}",
            "Quần lót nam Boxer sợi Modal kháng khuẩn công nghệ may Seamless {brand}",
            "Áo sơ mi nam công sở dài tay cao cấp {brand}",
            "Quần dài Kaki dáng Slimfit co giãn tôn dáng {brand}",
        ],
        1883: [
            "Bộ hộp cơm thủy tinh chịu nhiệt {brand} Có túi giữ nhiệt cao cấp",
            "Bình giữ nhiệt Inox 316 cao cấp {brand} Giữ nhiệt 24 giờ 800ml",
            "Kệ để đồ đa năng thông minh tiết kiệm diện tích {brand}",
            "Bộ lau nhà tự vắt thông minh xoay 360 độ {brand}",
        ]
    }

    sellers = [
        {"id": 1, "name": "Tiki Trading", "is_official": True},
        {"id": 102, "name": "Apple Flagship Store", "is_official": True},
        {"id": 105, "name": "Samsung Official Store", "is_official": True},
        {"id": 108, "name": "Anker Official Mall", "is_official": True},
        {"id": 112, "name": "Nhà Sách FAHASA Official", "is_official": True},
        {"id": 115, "name": "Coolmate Flagship Store", "is_official": True},
        {"id": 201, "name": "Điện Máy Gia Dụng Xanh", "is_official": False},
        {"id": 204, "name": "Phụ Kiện Công Nghệ Số 1", "is_official": False},
        {"id": 210, "name": "Mỹ Phẩm Xách Tay Authentic", "is_official": False},
        {"id": 220, "name": "Thời Trang Bụi Phố", "is_official": False},
    ]

    # Generate products
    products = []
    base_date = datetime(2024, 1, 1)

    for i in range(1, num_products + 1):
        cat = random.choice(categories)
        cat_id = cat["id"]
        brand_list = brands_by_cat.get(cat_id, ["Tiki Select"])
        brand = random.choice(brand_list)
        template = random.choice(product_templates.get(cat_id, ["Sản phẩm chất lượng cao {brand}"]))
        spec = random.choice(["128GB", "256GB", "512GB", "V2", "Pro", "Max", "2024 Edition"])
        
        prod_name = template.format(brand=brand, spec=spec)
        seller = random.choice(sellers)

        # Price generation based on category
        if cat_id == 1789:
            orig_price = random.randint(80, 450) * 100000
        elif cat_id == 1815:
            orig_price = random.randint(3, 80) * 100000
        elif cat_id == 1882:
            orig_price = random.randint(10, 150) * 100000
        elif cat_id == 8322:
            orig_price = random.randint(6, 40) * 10000
        elif cat_id == 1520:
            orig_price = random.randint(15, 120) * 10000
        else:
            orig_price = random.randint(10, 80) * 10000

        discount_rate = random.choice([0, 5, 10, 15, 20, 25, 30, 35, 40, 50])
        price = int(orig_price * (100 - discount_rate) / 100)
        
        rating_avg = round(random.choices(
            [4.9, 4.8, 4.7, 4.5, 4.2, 3.8, 3.2, 2.5],
            weights=[30, 30, 20, 10, 5, 3, 1, 1]
        )[0], 1)
        
        review_count = int(random.expovariate(1/120)) + 5
        qty_sold = int(review_count * random.uniform(3.5, 8.0))

        created_days = random.randint(1, 365)
        created_at = (base_date + timedelta(days=created_days)).strftime("%Y-%m-%d %H:%M:%S")

        prod = {
            "id": 100000 + i,
            "sku": f"TIKI-{cat_id}-{i:06d}",
            "name": prod_name,
            "price": price,
            "original_price": orig_price,
            "discount_rate": discount_rate,
            "rating_average": rating_avg,
            "review_count": review_count,
            "quantity_sold": qty_sold,
            "category_id": cat_id,
            "category_name": cat["name"],
            "brand_name": brand,
            "seller_id": seller["id"],
            "seller_name": seller["name"],
            "is_official_seller": seller["is_official"],
            "is_tiki_now": random.choice([True, True, False]), # 2/3 have TikiNow fast delivery
            "is_authentic": True,
            "inventory_status": random.choices(["available", "low_stock", "out_of_stock"], weights=[85, 12, 3])[0],
            "created_at": created_at
        }
        products.append(prod)

    # Customer reviews generator
    vietnamese_positive_reviews = [
        ("Giao hàng siêu nhanh TikiNow 2h", "Sản phẩm đóng gói rất cẩn thận, bọc bóng khí nhiều lớp. Mở ra dùng thử rất mượt và ưng ý! 5 sao cho Tiki."),
        ("Hàng chính hãng, chất lượng tuyệt vời", "Đã check serial và bảo hành điện tử chính hãng. Sử dụng rất êm, đáng đồng tiền bát gạo."),
        ("Rất hài lòng về sản phẩm", "Mua đợt sale áp mã giảm giá rẻ hơn ngoài siêu thị cả triệu. Đóng gói đẹp, shipper nhiệt tình thân thiện."),
        ("Chất lượng vượt mong đợi", "Màu sắc rất đẹp, phụ kiện đầy đủ nguyên seal tem mác. Sẽ tiếp tục ủng hộ shop lâu dài."),
        ("Tuyệt vời ông mặt trời", "Giao hàng đúng hẹn, hàng chuẩn như mô tả. Xài rất thích, pin trâu và máy chạy mượt mà."),
        ("Đáng tiền, khuyên mọi người nên mua", "Sau 1 tuần sử dụng thấy hiệu năng rất ổn định, không có lỗi gì phát sinh. Rất đáng tiền."),
        ("Sách rất hay và truyền cảm hứng", "Bìa đẹp, giấy xịn, giao hàng nhanh chóng không bị móp méo gáy sách. Nội dung vô cùng sâu sắc."),
        ("Shop phục vụ rất chu đáo", "Tư vấn nhiệt tình, đổi trả nếu có vấn đề rất rõ ràng. Cho shop 10 điểm uy tín."),
    ]

    vietnamese_neutral_reviews = [
        ("Dùng tạm được, không quá xuất sắc", "Chất lượng đúng với tầm giá tiền, không quá vượt trội nhưng dùng nhu cầu cơ bản thì ổn."),
        ("Sản phẩm bình thường", "Giao hàng hơi chậm mất 3 ngày mới tới. Hàng bọc hơi sơ sài nhưng may mắn bên trong không bị hỏng."),
        ("Tạm ổn so với giá sale", "Dùng cũng được, pin hơi tụt nhanh hơn mong đợi một chút. Xem xét thêm thời gian tới."),
        ("Đóng gói chưa thực sự cẩn thận", "Hộp hơi móp méo chút ít, may mà đồ bên trong còn nguyên vẹn. Mong shop cải thiện đóng gói."),
    ]

    vietnamese_negative_reviews = [
        ("Giao hàng quá chậm, dịch vụ thất vọng", "Hẹn 2 ngày mà cả tuần mới nhận được hàng. Nhắn tin hỗ trợ thì trả lời chậm và chung chung."),
        ("Chất lượng không như mô tả", "Hàng có vẻ ọp ẹp, không giống như ảnh quảng cáo. Rất thất vọng về trải nghiệm lần này."),
        ("Hàng bị lỗi sau 2 ngày dùng", "Mới dùng được 2 hôm đã phát sinh lỗi chập chờn. Yêu cầu đổi trả bảo hành mất nhiều thời gian quá."),
        ("Đóng gói cẩu thả, hộp bị móp rách", "Hàng điện tử giá trị cao mà bọc có 1 lớp mỏng, hộp bị dập nát. Rất bực mình!"),
    ]

    customer_names = [
        "Nguyễn Văn An", "Trần Thị Mai", "Lê Hoàng Long", "Phạm Minh Tuấn", "Vũ Hải Đăng",
        "Hoàng Thảo My", "Đặng Quốc Bảo", "Bùi Kim Ngân", "Đỗ Hữu Nghĩa", "Ngô Bích Phương",
        "Dương Tuấn Kiệt", "Lý Thanh Hà", "Trương Quang Huy", "Mai Phương Thúy", "Phan Gia Huy",
        "Trịnh Thu Thảo", "Võ Đức Trí", "Tạ Quỳnh Như", "Lâm Quốc Khánh", "Cao Hoài Nam"
    ]

    reviews = []
    for r_idx in range(1, num_reviews + 1):
        target_prod = random.choice(products)
        customer_id = random.randint(1001, 1000 + min(num_reviews // 3, 800))
        cust_name = customer_names[customer_id % len(customer_names)]
        
        # Rating distribution: ~70% positive (4-5 star), ~15% neutral (3 star), ~15% negative (1-2 star)
        sentiment_choice = random.choices(["pos", "neu", "neg"], weights=[70, 15, 15])[0]
        
        if sentiment_choice == "pos":
            rating = random.choice([5, 5, 5, 4])
            title, content = random.choice(vietnamese_positive_reviews)
            sentiment_label = "POSITIVE"
        elif sentiment_choice == "neu":
            rating = 3
            title, content = random.choice(vietnamese_neutral_reviews)
            sentiment_label = "NEUTRAL"
        else:
            rating = random.choice([1, 1, 2])
            title, content = random.choice(vietnamese_negative_reviews)
            sentiment_label = "NEGATIVE"

        # Aspect ratings
        deliv_rating = max(1, min(5, rating + random.choice([-1, 0, 0, 1])))
        prod_quality = max(1, min(5, rating + random.choice([0, 0, 1, -1])))

        review_date = (base_date + timedelta(days=random.randint(10, 360))).strftime("%Y-%m-%d %H:%M:%S")

        rev = {
            "review_id": 5000000 + r_idx,
            "product_id": target_prod["id"],
            "product_name": target_prod["name"],
            "category_id": target_prod["category_id"],
            "customer_id": customer_id,
            "customer_name": cust_name,
            "rating": rating,
            "sentiment": sentiment_label,
            "title": title,
            "content": content,
            "thank_count": random.choices([0, 1, 2, 5, 12], weights=[60, 20, 10, 7, 3])[0],
            "delivery_rating": deliv_rating,
            "quality_rating": prod_quality,
            "is_buyer": True,
            "created_at": review_date
        }
        reviews.append(rev)

    # Save to CSV and JSON
    products_csv = os.path.join(raw_dir, "tiki_products.csv")
    products_json = os.path.join(raw_dir, "tiki_products.json")
    reviews_csv = os.path.join(raw_dir, "tiki_reviews.csv")
    reviews_json = os.path.join(raw_dir, "tiki_reviews.json")

    with open(products_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=products[0].keys())
        writer.writeheader()
        writer.writerows(products)

    with open(products_json, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)

    with open(reviews_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=reviews[0].keys())
        writer.writeheader()
        writer.writerows(reviews)

    with open(reviews_json, "w", encoding="utf-8") as f:
        json.dump(reviews, f, ensure_ascii=False, indent=2)

    print(f"Generated {len(products)} products -> {products_csv}")
    print(f"Generated {len(reviews)} reviews -> {reviews_csv}")

if __name__ == "__main__":
    generate_datasets()
