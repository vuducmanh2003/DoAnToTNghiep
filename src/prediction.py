import os
import csv
import torch
from transformers import MobileBertForSequenceClassification, MobileBertTokenizer

def read_file(file_path):
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def main():
    PREDICTION_DIR = "D://PTIT/Datn/Code/anti-phishing/data_for_prediction/phishing_samples"
    MODEL_PATH = "D://PTIT/Datn/Code/anti-phishing/src/model"

    OUTPUT_CSV = "D://PTIT/Datn/Code/anti-phishing/src/phishing_prediction_results.csv"
    OUTPUT_TXT = "D://PTIT/Datn/Code/anti-phishing/src/phishing_prediction_summary.txt"

    MAX_FILES = 10000
    TRUE_LABEL = "phishing"

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    model = MobileBertForSequenceClassification.from_pretrained(MODEL_PATH).to(device)
    tokenizer = MobileBertTokenizer.from_pretrained(MODEL_PATH)

    model.eval()

    files = sorted(os.listdir(PREDICTION_DIR))[:MAX_FILES]

    correct = 0
    incorrect = 0
    results = []

    for idx, filename in enumerate(files, 1):
        file_path = os.path.join(PREDICTION_DIR, filename)

        text = read_file(file_path)

        inputs = tokenizer.encode_plus(
            text,
            add_special_tokens=True,
            max_length=128,
            return_token_type_ids=False,
            padding='max_length',
            truncation=True,
            return_attention_mask=True,
            return_tensors='pt'
        )

        inputs = {k: v.to(device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = model(**inputs)
            logits = outputs.logits
            predicted_class = torch.argmax(logits, dim=-1).item()

        label_map = {0: 'benign', 1: 'phishing'}
        prediction = label_map[predicted_class]

        is_correct = prediction == TRUE_LABEL
        if is_correct:
            correct += 1
        else:
            incorrect += 1

        results.append([
            filename,
            prediction,
            is_correct
        ])

        if idx % 500 == 0:
            print(f"Processed {idx}/{len(files)} files")

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["filename", "prediction", "correct"])
        writer.writerows(results)

    total = correct + incorrect
    accuracy = (correct / total) * 100 if total > 0 else 0

    with open(OUTPUT_TXT, "w", encoding="utf-8") as f:
        f.write(f"Total files: {total}\n")
        f.write(f"Correct predictions: {correct}\n")
        f.write(f"Incorrect predictions: {incorrect}\n")
        f.write(f"Accuracy: {accuracy:.2f}%\n")

    print("Done!")
    print(f"Accuracy: {accuracy:.2f}%")
    print(f"CSV saved to: {OUTPUT_CSV}")
    print(f"Summary saved to: {OUTPUT_TXT}")

if __name__ == "__main__":
    main()