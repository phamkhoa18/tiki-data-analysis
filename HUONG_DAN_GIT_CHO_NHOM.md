# 🌿 HƯỚNG DẪN SỬ DỤNG GIT & TẠO NHÁNH (BRANCH) CHO NHÓM

Tài liệu này hướng dẫn các thành viên trong nhóm cách phối hợp làm việc trên GitHub mà **không bị đè code, mất code hay xung đột (conflict)**.

---

## ⚠️ NGUYÊN TẮC VÀNG
1. **Tuyệt đối KHÔNG commit hay code trực tiếp trên nhánh `main`**.
2. **Mỗi người / mỗi tính năng PHẢI làm việc trên 1 nhánh (branch) riêng**.
3. **Trước khi bắt đầu code**: Luôn cập nhật code mới nhất từ nhánh `main` về máy.
4. **Sau khi làm xong**: Đẩy nhánh của mình lên GitHub rồi tạo **Pull Request (PR)** để gộp vào `main`.

---

## 🚀 QUY TRÌNH LÀM VIỆC TỪNG BƯỚC

### Bước 1: Tải dự án về máy tính của bạn (Chỉ làm lần đầu)
Mở Terminal / Git Bash trên máy của bạn và chạy:

```bash
git clone https://github.com/phamkhoa18/tiki-data-analysis.git
cd tiki-data-analysis
```

---

### Bước 2: Cập nhật code mới nhất từ nhánh `main`
Mỗi khi bắt đầu ngày làm việc mới hoặc trước khi tạo nhánh mới:

```bash
# 1. Chuyển về nhánh main
git checkout main

# 2. Kéo code mới nhất từ GitHub về máy
git pull origin main
```

---

### Bước 3: Tạo nhánh (branch) riêng cho phần việc của bạn
Tạo nhánh mới từ nhánh `main` và chuyển sang nhánh đó ngay:

```bash
git checkout -b <tên-nhánh-của-bạn>
```

#### 📌 Quy ước đặt tên nhánh cho từng thành viên:
- **Phạm Đăng Khoa:**
  - Ví dụ: `git checkout -b feature/khoa-pyspark-etl`
  - Hoặc: `git checkout -b dev-khoa`
- **Phạm Minh Nhật:**
  - Ví dụ: `git checkout -b feature/nhat-crawler-nlp`
  - Hoặc: `git checkout -b dev-nhat`
- **Nguyễn Văn Sang:**
  - Ví dụ: `git checkout -b feature/sang-dashboard-rfm`
  - Hoặc: `git checkout -b dev-sang`

> 💡 **Mẹo:** Kiểm tra xem mình đang đứng ở nhánh nào:
> ```bash
> git branch
> ```
> *(Nhánh có dấu sao `*` màu xanh là nhánh bạn đang làm việc).*

---

### Bước 4: Viết code và Lưu lại (Commit)
Sau khi bạn đã viết xong hoặc sửa file trong thư mục:

```bash
# 1. Xem danh sách các file bạn đã thay đổi
git status

# 2. Thêm tất cả file đã thay đổi vào danh sách chuẩn bị lưu
git add .

# 3. Lưu commit kèm theo lời nhắn rõ ràng (bạn vừa làm gì)
git commit -m "feat: cập nhật module crawler lấy thêm đánh giá Tiki"
```

---

### Bước 5: Đẩy nhánh của bạn lên GitHub
Đẩy nhánh riêng của bạn lên kho lưu trữ từ xa:

```bash
# Lần đầu tiên đẩy nhánh này lên:
git push -u origin <tên-nhánh-của-bạn>

# Ví dụ cho bạn Nhật:
git push -u origin feature/nhat-crawler-nlp
```

---

### Bước 6: Tạo Pull Request (PR) để gộp code vào `main`
1. Truy cập vào repo: https://github.com/phamkhoa18/tiki-data-analysis
2. Bạn sẽ thấy thông báo màu vàng hiện lên: **"Compare & pull request"**. Bấm vào nút đó.
3. Điền tiêu đề và mô tả ngắn gọn phần việc bạn vừa làm.
4. Bấm **"Create pull request"**.
5. Nhóm kiểm tra code rồi bấm **"Merge pull request"** để gộp vào nhánh chính `main`.

---

## 🛠️ CÁC LỆNH CỨU HỘ KHI CẦN (CHEAT SHEET)

| Trường hợp | Lệnh thực hiện | Giải thích |
|---|---|---|
| **Xem đang ở nhánh nào** | `git branch` | Hiện danh sách các nhánh cục bộ |
| **Chuyển sang nhánh khác** | `git checkout <tên-nhánh>` | Di chuyển giữa các nhánh |
| **Xóa bỏ thay đổi chưa commit** | `git restore .` | Phục hồi lại code ban đầu nếu lỡ sửa sai |
| **Xóa nhánh cục bộ sau khi đã merge** | `git branch -d <tên-nhánh>` | Giúp danh sách nhánh gọn gàng |
| **Xem lịch sử commit** | `git log --oneline -n 5` | Xem 5 commit gần nhất |

---

## 📞 HỖ TRỢ & LIÊN HỆ NHÓM
Nếu gặp lỗi conflict hoặc không đẩy được code, hãy nhắn ngay cho nhóm trong nhóm Zalo/Messenger trước khi dùng các lệnh ép buộc (`--force`) để tránh làm mất code của nhau!
