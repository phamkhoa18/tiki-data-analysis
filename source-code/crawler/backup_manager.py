#!/usr/bin/env python3
"""
==============================================================================
TIKI DATASET BACKUP & RESTORE MANAGER
==============================================================================
Mục đích:
  Quản trị sao lưu (Backup) và phục hồi (Restore) toàn bộ dữ liệu cào Tiki.
  
Tính năng:
  - Sao lưu toàn bộ dataset (CSV, JSON, SQLite DB) thành bản snapshot nén ZIP
  - Đặt tên file tự động theo timestamp: tiki_backup_YYYYMMDD_HHMMSS.zip
  - Tính mã băm MD5 Checksum đảm bảo tính toàn vẹn 100% của dữ liệu
  - Quản lý nhật ký sao lưu (Backup History) dạng JSON
  - Phục hồi (Restore) an toàn nguyên trạng từ bản sao lưu bất kỳ

Đáp ứng tiêu chí đồ án Big Data:
  - Sao lưu, phục hồi dữ liệu (0.25đ)
==============================================================================
"""

import os
import sys
import json
import shutil
import hashlib
import zipfile
import logging
import argparse
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("BackupManager")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "dataset")
BACKUP_DIR = os.path.join(DATA_DIR, "backups")
HISTORY_FILE = os.path.join(BACKUP_DIR, "backup_history.json")


def calculate_md5(file_path):
    """Tính mã băm MD5 của một tập tin để kiểm tra tính toàn vẹn."""
    hasher = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


class TikiBackupManager:
    def __init__(self, data_dir=DATA_DIR, backup_dir=BACKUP_DIR):
        self.data_dir = data_dir
        self.backup_dir = backup_dir
        os.makedirs(self.backup_dir, exist_ok=True)

    def _load_history(self):
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def _save_history(self, history):
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)

    def create_backup(self, description="Tự động sao lưu dữ liệu cào"):
        """
        Nén và sao lưu các tệp dữ liệu cốt lõi (raw, processed, master CSV, database).
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"tiki_backup_{timestamp}.zip"
        backup_path = os.path.join(self.backup_dir, backup_filename)

        logger.info("=" * 70)
        logger.info(f"📦 BẮT ĐẦU SAO LƯU DỮ LIỆU CRAWL: {backup_filename}")
        logger.info("=" * 70)

        # Danh sách các tệp & thư mục cần sao lưu
        target_items = [
            "raw",
            "processed",
            "nosql_documents",
            "tiki_database.db",
            "tiki_products_clean_full.csv",
            "tiki_master_dataset_all_in_one.csv",
        ]

        total_files = 0
        with zipfile.ZipFile(backup_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for item in target_items:
                item_path = os.path.join(self.data_dir, item)
                if os.path.isdir(item_path):
                    for root, _, files in os.walk(item_path):
                        for file in files:
                            # Không sao lưu thư mục backups lồng nhau
                            if "backups" in root:
                                continue
                            file_full = os.path.join(root, file)
                            rel_path = os.path.relpath(file_full, self.data_dir)
                            zipf.write(file_full, rel_path)
                            total_files += 1
                elif os.path.isfile(item_path):
                    rel_path = os.path.basename(item_path)
                    zipf.write(item_path, rel_path)
                    total_files += 1

        size_mb = os.path.getsize(backup_path) / (1024 * 1024)
        checksum = calculate_md5(backup_path)

        # Lưu lịch sử
        history = self._load_history()
        entry = {
            "backup_file": backup_filename,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "size_mb": round(size_mb, 2),
            "files_count": total_files,
            "md5_checksum": checksum,
            "description": description,
        }
        history.append(entry)
        self._save_history(history)

        logger.info(f"✅ ĐÃ TẠO BẢN SAO LƯU THÀNH CÔNG!")
        logger.info(f"  • Đường dẫn: {backup_path}")
        logger.info(f"  • Dung lượng: {size_mb:.2f} MB ({total_files} tập tin)")
        logger.info(f"  • Mã băm MD5 Checksum: {checksum}")
        logger.info("=" * 70)
        return backup_path

    def list_backups(self):
        """Liệt kê toàn bộ các bản sao lưu hiện có trong hệ thống."""
        history = self._load_history()
        print("\n" + "=" * 75)
        print("📋 DANH SÁCH CÁC BẢN SAO LƯU DỮ LIỆU TIKI (BACKUP CATALOG)")
        print("=" * 75)
        if not history:
            print("  (Chưa có bản sao lưu nào. Hãy chạy lệnh --backup để tạo)")
            return

        for idx, item in enumerate(history, 1):
            print(f"[{idx}] {item['backup_file']}")
            print(f"    • Thời gian: {item['created_at']} | Dung lượng: {item['size_mb']} MB | Số tệp: {item['files_count']}")
            print(f"    • MD5 Checksum: {item['md5_checksum']}")
            print(f"    • Ghi chú: {item.get('description', '')}")
            print("-" * 75)

    def restore_backup(self, backup_name=None):
        """
        Khôi phục dữ liệu từ bản sao lưu được chỉ định hoặc bản sao lưu gần nhất.
        """
        history = self._load_history()
        if not history:
            logger.error("Không có bản sao lưu nào trong hệ thống để phục hồi!")
            return False

        if not backup_name or backup_name == "latest":
            target_entry = history[-1]
        else:
            target_entry = next((item for item in history if item["backup_file"] == backup_name), None)
            if not target_entry:
                # Tìm theo tên file không đuôi
                target_entry = next((item for item in history if backup_name in item["backup_file"]), None)

        if not target_entry:
            logger.error(f"Không tìm thấy bản sao lưu: {backup_name}")
            return False

        backup_file = target_entry["backup_file"]
        backup_path = os.path.join(self.backup_dir, backup_file)
        if not os.path.exists(backup_path):
            logger.error(f"Tập tin vật lý không tồn tại: {backup_path}")
            return False

        logger.info("=" * 70)
        logger.info(f"🔄 BẮT ĐẦU PHỤC HỒI DỮ LIỆU TỪ BẢN SAO LƯU: {backup_file}")
        logger.info(f"  • Thời gian tạo: {target_entry['created_at']}")
        logger.info(f"  • Đang kiểm tra mã băm MD5 Checksum...")

        # Xác minh checksum
        current_md5 = calculate_md5(backup_path)
        if current_md5 != target_entry["md5_checksum"]:
            logger.error("⚠️ CẢNH BÁO: Checksum không khớp! Tệp sao lưu có dấu hiệu bị lỗi hoặc can thiệp.")
            return False
        logger.info("  ✓ Checksum khớp 100%! Bắt đầu giải nén phục hồi...")

        # Bung nén đè lên dataset
        with zipfile.ZipFile(backup_path, "r") as zipf:
            zipf.extractall(self.data_dir)

        logger.info(f"🎉 PHỤC HỒI DỮ LIỆU HOÀN TẤT THÀNH CÔNG!")
        logger.info(f"  • Toàn bộ dữ liệu tại '{self.data_dir}' đã được khôi phục về trạng thái {target_entry['created_at']}.")
        logger.info("=" * 70)
        return True


def main():
    parser = argparse.ArgumentParser(description="Tiki Dataset Backup & Restore Manager")
    parser.add_argument("--backup", action="store_true", help="Tạo một bản sao lưu mới ngay lập tức")
    parser.add_argument("--list", action="store_true", help="Liệt kê danh sách các bản sao lưu hiện có")
    parser.add_argument("--restore", type=str, nargs="?", const="latest", default=None,
                        help="Phục hồi dữ liệu từ bản sao lưu (nhập tên file hoặc 'latest' cho bản mới nhất)")
    parser.add_argument("--desc", type=str, default="Sao lưu dữ liệu cào Tiki", help="Mô tả nội dung bản sao lưu")
    args = parser.parse_args()

    manager = TikiBackupManager()

    if args.backup:
        manager.create_backup(description=args.desc)
    elif args.list:
        manager.list_backups()
    elif args.restore:
        manager.restore_backup(backup_name=args.restore)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
