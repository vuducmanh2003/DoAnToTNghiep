import os
import shutil
import re

# CẤU HÌNH
SQL_FILE = "D://PTIT/Datn/Code/anti-phishing/dataset_for_prediction/index.sql"                      # file .sql chứa 80000 bản ghi
HTML_FOLDER = "D://PTIT/Datn/Code/anti-phishing/dataset_for_prediction/dataset-part-8"              # thư mục chứa các file .html
BENIGN_FOLDER = "D://PTIT/Datn/Code/anti-phishing/dataset_for_prediction/benign_websites"           # output cho result = 0
PHISHING_FOLDER = "D://PTIT/Datn/Code/anti-phishing/dataset_for_prediction/phishing_websites"       # output cho result = 1

# BƯỚC 1: Đọc file SQL và parse các bản ghi
pattern = re.compile(
    r"\(\s*([0-9]+)\s*,\s*'((?:\\'|[^'])*)'\s*,\s*'((?:\\'|[^'])*)'\s*,\s*([01])\s*,\s*'((?:\\'|[^'])*)'\s*\)"
)

mapping = {}   # key: filename.html → value: result (0/1)

with open(SQL_FILE, "r", encoding="utf-8", errors="ignore") as f:
    content = f.read()

matches = pattern.findall(content)

for rec_id, url, website, result, created_date in matches:
    mapping[website.strip()] = int(result)

print(f"Đã load {len(mapping)} bản ghi từ file SQL.")

# BƯỚC 2: Duyệt thư mục HTML và so sánh
count_phishing = 0
count_benign = 0
count_not_found = 0

for filename in os.listdir(HTML_FOLDER):
    if not filename.endswith(".html"):
        continue

    filepath = os.path.join(HTML_FOLDER, filename)

    if filename in mapping:
        result = mapping[filename]

        if result == 1:
            shutil.move(filepath, os.path.join(PHISHING_FOLDER, filename))
            count_phishing += 1
        else:
            shutil.move(filepath, os.path.join(BENIGN_FOLDER, filename))
            count_benign += 1
    else:
        count_not_found += 1

print("=== KẾT QUẢ ===")
print("Phishing files:", count_phishing)
print("Benign files:", count_benign)
print("Không tìm thấy trong SQL:", count_not_found)