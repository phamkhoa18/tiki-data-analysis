----- Thông tin đề tài ---------------------
STT: 01
Tên đề tài: Phân tích hệ thống dữ liệu sàn thương mại điện tử TIKI (Tiki E-commerce Big Data Analytics Platform)
Lớp học phần: 06_BigData
Năm học: HK1/2024-2025
--------------------------------------------
Thông tin nhóm
1. Phạm Đăng Khoa (24810114) – SĐT: 0987654321 – Email: 24810114@student.edu.vn
2. Phạm Minh Nhật (24810119) – SĐT: 0912345678 – Email: 24810119@student.edu.vn
3. Nguyễn Văn Sang (24810114) – SĐT: 0909123456 – Email: sang.nv@student.edu.vn
--------------------------------------------
Cấu trúc tổ chức thư mục:
- source-code/: Mã nguồn chương trình (chứa module crawler, etl_spark, analytics_ml, streaming, dashboard)
- reports/: Báo cáo đề tài (*.docx), slides thuyết trình (*.pptx), bảng tự chấm & phân công (*.xlsx)
- dataset/: Dữ liệu thu thập, CSDL và từ điển dữ liệu (tiki_products_clean_full.csv, tiki_database.db, CAU_TRUC_DU_LIEU_CRAWL.md, backups)
- refs/: Danh mục tài liệu tham khảo nghiên cứu
- libs/: Danh sách phần mềm và thư viện liên quan (requirements.txt)
- readme.txt: Tập tin thông tin đề tài theo quy định
--------------------------------------------
Hướng dẫn thực thi Module Thu Thập Dữ Liệu (Crawler):
1. Cài đặt thư viện:
   pip install -r libs/requirements.txt

2. Cào dữ liệu sản phẩm từ Tiki:
   python3 source-code/crawler/crawl_tiki_products.py --pages 5

3. Xuất CSDL Quan hệ SQLite & NoSQL Documents:
   python3 source-code/crawler/storage_exporter.py --type all

4. Sao lưu dữ liệu cào (Backup Snapshot):
   python3 source-code/crawler/backup_manager.py --backup
