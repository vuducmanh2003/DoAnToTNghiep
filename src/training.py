import pandas as pd
import os
import sys
from sklearn.model_selection import train_test_split
from transformers import MobileBertForSequenceClassification, MobileBertTokenizer, Trainer, TrainingArguments, EarlyStoppingCallback
from datasets import Dataset
from sklearn.metrics import precision_recall_fscore_support, accuracy_score, confusion_matrix, roc_curve, auc
from concurrent.futures import ThreadPoolExecutor
import torch
import numpy as np
import matplotlib.pyplot as plt

# Đọc dữ liệu đầu vào
def read_text(filename, label):
    directory = 'D://PTIT/Datn/Code/anti-phishing/data_for_training/phishing_samples' if label == 1 else 'D://PTIT/Datn/Code/anti-phishing/data_for_training/benign_samples'
    try:
        return open(os.path.join(directory, filename), encoding="utf-8", errors="ignore").read()
    except:
        return ""

# Tính toán metrics cho Trainer
def compute_metrics(eval_pred):
    logits, labels = eval_pred
    predictions = np.argmax(logits, axis=-1)
    precision, recall, f1, _ = precision_recall_fscore_support(labels, predictions, average='binary')
    acc = accuracy_score(labels, predictions)
    return {
        'accuracy': acc,
        'f1': f1,
        'precision': precision,
        'recall': recall
    }

# Kiểm tra tham số dòng lệnh
if len(sys.argv) < 2:
    print("Usage: script.py <test|full>")
    sys.exit(1)

mode = sys.argv[1]
print(f"Running in mode: {mode}")

tokenizer = MobileBertTokenizer.from_pretrained("google/mobilebert-uncased")

# Load các file dùng để huấn luyện
phish_files = [f for f in os.listdir('D:/PTIT/Datn/Code/anti-phishing/data_for_training/phishing_samples') if f.endswith('.txt')]
benign_files = [f for f in os.listdir('D:/PTIT/Datn/Code/anti-phishing/data_for_training/benign_samples') if f.endswith('.txt')]

phishing = [(f, 1) for f in phish_files]
benign = [(f, 0) for f in benign_files]

data = phishing + benign
df = pd.DataFrame(data, columns=['file', 'label'])

def parallel_read(file_label):
    return read_text(*file_label)

print("Reading files...")
with ThreadPoolExecutor(max_workers=8) as executor:
    texts = list(executor.map(parallel_read, zip(df['file'], df['label'])))
df['text'] = texts

# Chọn 1000 mẫu ngẫu nhiên cho chế độ test
if mode == "test":
    df = df.sample(1000, random_state=42)

print(f"Total samples after processing: {len(df)}")

# 1. Chia Train/Test (20% cho test)
train_df, test_df = train_test_split(df, test_size=0.2, random_state=42, stratify=df['label'])

# 2. Chia Train/Validation (Lấy 10% từ tập Train để làm Validation)
train_df, val_df = train_test_split(train_df, test_size=0.1, random_state=42, stratify=train_df['label'])

def tokenize_function(examples):
    return tokenizer(examples["text"], padding="max_length", truncation=True, max_length=128)

# Convert pandas dataframe to HuggingFace Dataset
train_dataset = Dataset.from_pandas(train_df)
val_dataset = Dataset.from_pandas(val_df)
test_dataset = Dataset.from_pandas(test_df)

# Tokenize datasets
print("Tokenizing datasets...")
train_dataset = train_dataset.map(tokenize_function, batched=True)
val_dataset = val_dataset.map(tokenize_function, batched=True)
test_dataset = test_dataset.map(tokenize_function, batched=True)

# Set format for pytorch
train_dataset.set_format(type='torch', columns=['input_ids', 'token_type_ids', 'attention_mask', 'label'])
val_dataset.set_format(type='torch', columns=['input_ids', 'token_type_ids', 'attention_mask', 'label'])
test_dataset.set_format(type='torch', columns=['input_ids', 'token_type_ids', 'attention_mask', 'label'])

# Model setup
model = MobileBertForSequenceClassification.from_pretrained("google/mobilebert-uncased", num_labels=2)

args = TrainingArguments(
    output_dir="./results",
    evaluation_strategy="epoch",
    save_strategy="epoch",
    load_best_model_at_end=True,
    metric_for_best_model="f1",
    learning_rate=2e-5,
    per_device_train_batch_size=32,
    per_device_eval_batch_size=32,
    num_train_epochs=10,
    weight_decay=0.01,
    gradient_accumulation_steps=1,
    logging_dir='./logs',
    logging_steps=10
)

trainer = Trainer(
    model=model,
    args=args,
    train_dataset=train_dataset,
    eval_dataset=val_dataset,
    compute_metrics=compute_metrics,
    callbacks=[EarlyStoppingCallback(early_stopping_patience=2)]
)

print("Starting training...")
trainer.train()

# Dự đoán trên tập Test
print("Evaluating on Test Set...")
predictions = trainer.predict(test_dataset)
preds = np.argmax(predictions.predictions, axis=-1)

# Confusion Matrix
cm = confusion_matrix(test_df["label"], preds)

plt.figure(figsize=(5, 4))
plt.imshow(cm, cmap="Blues")
plt.title("Confusion Matrix")
plt.colorbar()

plt.xticks([0, 1], ["Benign", "Phishing"])
plt.yticks([0, 1], ["Benign", "Phishing"])

for i in range(2):
    for j in range(2):
        plt.text(j, i, cm[i, j], ha="center", va="center")

plt.xlabel("Predicted Label")
plt.ylabel("True Label")
plt.tight_layout()

plt.savefig("evaluation_plots/confusion_matrix.png", dpi=300)
plt.close()

# ROC Curve + AUC
probs = torch.softmax(
    torch.tensor(predictions.predictions), dim=1
).numpy()[:, 1]

fpr, tpr, _ = roc_curve(test_df["label"], probs)
roc_auc = auc(fpr, tpr)

plt.figure()
plt.plot(fpr, tpr, label=f"ROC curve (AUC = {roc_auc:.4f})")
plt.plot([0, 1], [0, 1], linestyle="--", color="gray")
plt.xlabel("False Positive Rate")
plt.ylabel("True Positive Rate")
plt.title("ROC Curve")
plt.legend(loc="lower right")
plt.grid()
plt.tight_layout()

plt.savefig("evaluation_plots/roc_curve.png", dpi=300)
plt.close()

# Tính metrics cuối cùng
precision, recall, f1, _ = precision_recall_fscore_support(test_df['label'], preds, average='binary')
accuracy = accuracy_score(test_df['label'], preds)

print("------------------------------------------------")
print(f"Final Test Results:")
print(f"Accuracy : {accuracy:.4f}")
print(f"Precision: {precision:.4f}")
print(f"Recall   : {recall:.4f}")
print(f"F1 Score : {f1:.4f}")
print("------------------------------------------------")

# Lưu model và tokenizer
model.save_pretrained('./model')
tokenizer.save_pretrained('./model')

print('Model saved')
