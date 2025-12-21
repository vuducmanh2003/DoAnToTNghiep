import os
import shutil

SOURCE_DIR = "D://PTIT/Datn/phish_sample_30k"
TARGET_DIR = "D://PTIT/Datn/Code/anti-phishing/dataset_for_training/phishing_websites"

os.makedirs(TARGET_DIR, exist_ok=True)

counter = 1

for folder_name in os.listdir(SOURCE_DIR):
    folder_path = os.path.join(SOURCE_DIR, folder_name)

    if not os.path.isdir(folder_path):
        continue

    html_path = os.path.join(folder_path, "html.txt")

    if os.path.isfile(html_path):
        new_name = f"html{counter}.txt"
        target_path = os.path.join(TARGET_DIR, new_name)

        shutil.move(html_path, target_path)

        counter += 1

print(f"\nTotal files moved: {counter - 1}")
