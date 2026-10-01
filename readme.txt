----- Thông tin đề tài ---------------------
STT: 01
Tên đề tài: Phân tích hệ thống dữ liệu sàn thương mại điện tử TIKI (Tiki E-commerce Big Data Analytics & Recommendation System)
Lớp học phần: 06_BigData
Năm học: HK1/2024-2025
--------------------------------------------
Thông tin nhóm
1. Phạm Đăng Khoa (24810114) – SĐT: 0987654321 – Email: 24810114@student.edu.vn
2. Phạm Minh Nhật (24810119) – SĐT: 0912345678 – Email: 24810119@student.edu.vn
3. Nguyễn Văn Sang (24810114) – SĐT: 0909123456 – Email: sang.nv@student.edu.vn
--------------------------------------------
Hướng dẫn chạy nhanh dự án:
1. Cài đặt môi trường:
   pip install -r libs/requirements.txt
2. Chạy toàn bộ pipeline ETL & Analytics:
   python3 source-code/pipeline_runner.py
3. Khởi chạy Dashboard trực quan hóa (Streamlit):
   streamlit run source-code/dashboard/app.py
4. Đóng gói nộp bài chuẩn quy định:
   python3 pack_submission.py --class 06 --group 01
