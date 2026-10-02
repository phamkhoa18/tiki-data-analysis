#!/usr/bin/env python3
"""
Submission Packager Tool
Packages project into required submission format:
<Mã lớp>_<STT nhóm>_<Tên đề tài>.zip
Containing:
- source-code/
- reports/
- dataset/
- refs/
- libs/
- readme.txt
"""

import os
import shutil
import zipfile
import argparse

def package_submission(class_code="06", group_no="01", topic_name="PhanTichHeThongDuLieuTIKI"):
    root_dir = os.path.dirname(os.path.abspath(__file__))
    folder_name = f"{class_code}_{group_no}_{topic_name}"
    target_folder = os.path.join(root_dir, folder_name)
    zip_filename = f"{folder_name}.zip"
    zip_path = os.path.join(root_dir, zip_filename)

    print(f"📦 Đang chuẩn bị gói nộp bài: {folder_name}...")

    # Required items
    required_dirs = ["source-code", "reports", "dataset", "refs", "libs"]
    required_files = ["readme.txt", "TAI_LIEU_CRAWL_API_TIKI.md"]

    # Remove temporary target folder if exists
    if os.path.exists(target_folder):
        shutil.rmtree(target_folder)
    os.makedirs(target_folder, exist_ok=True)

    # Copy directories
    for d in required_dirs:
        src = os.path.join(root_dir, d)
        dst = os.path.join(target_folder, d)
        if os.path.exists(src):
            shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"))
            print(f"  ✓ Đã sao chép thư mục: {d}/")
        else:
            print(f"  ⚠️ Cảnh báo: Chưa tìm thấy thư mục {d}/")

    # Copy files
    for f in required_files:
        src = os.path.join(root_dir, f)
        dst = os.path.join(target_folder, f)
        if os.path.exists(src):
            shutil.copy2(src, dst)
            print(f"  ✓ Đã sao chép tập tin: {f}")
        else:
            print(f"  ⚠️ Cảnh báo: Chưa tìm thấy tập tin {f}")

    # Create ZIP archive
    print(f"🗜️ Đang nén thành tập tin {zip_filename}...")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(target_folder):
            for file in files:
                abs_path = os.path.join(root, file)
                rel_path = os.path.relpath(abs_path, root_dir)
                zipf.write(abs_path, rel_path)

    # Clean up temporary folder
    shutil.rmtree(target_folder)

    zip_size_mb = os.path.getsize(zip_path) / (1024 * 1024)
    print(f"✅ Hoàn tất! Đã tạo file nén: {zip_path} ({zip_size_mb:.2f} MB)")
    print(f"📌 Sẵn sàng nộp cho giảng viên theo đúng định dạng yêu cầu.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tạo file zip nộp bài đồ án")
    parser.add_argument("--class_code", "--class", default="06", help="Mã lớp (mặc định: 06)")
    parser.add_argument("--group_no", "--group", default="01", help="STT nhóm (mặc định: 01)")
    parser.add_argument("--topic", default="PhanTichHeThongDuLieuTIKI", help="Tên đề tài không dấu")
    args = parser.parse_args()

    package_submission(args.class_code, args.group_no, args.topic)
