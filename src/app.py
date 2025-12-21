from flask_cors import CORS
from flask import Flask, request, jsonify
from transformers import MobileBertTokenizer, MobileBertForSequenceClassification
import torch
from bs4 import BeautifulSoup, NavigableString, Tag
import requests
import re

app = Flask(__name__)
CORS(app)

# Load the trained model and tokenizer
model = MobileBertForSequenceClassification.from_pretrained('D://PTIT/Datn/Code/anti-phishing/src/model')
tokenizer = MobileBertTokenizer.from_pretrained('D://PTIT/Datn/Code/anti-phishing/src/model')

TARGET_TAGS = {
    "a", "form", "input", "button", "iframe", "script", "title", "meta",
    "img", "label", "p", "header", "footer", "ul", "ol", "li", "noscript"
}

def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def fetch_html(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # 4xx/5xx errors
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching URL {url}: {e}")
        return None

def generate_text_representation(html_content):
    soup = BeautifulSoup(html_content, "lxml")

    for script in soup(["style"]):
        script.decompose()

    parsed = []

    def traverse(node):
        if isinstance(node, NavigableString):
            return

        if isinstance(node, Tag):
            tag = node.name.lower()

            if tag in TARGET_TAGS:

                # A
                if tag == "a":
                    text = clean_text(node.get_text())
                    href = node.get("href", "No URL provided")
                    parsed.append(f'LINK: {{ text: "{text or "<EMPTY>"}", href: "{href}" }}')

                # FORM
                elif tag == "form":
                    action = node.get("action")
                    method = node.get("method")
                    parsed.append(f'FORM: {{ action: "{action or ""}", method: "{method or ""}" }}')
                
                elif tag == "label":
                    for_value = node.get("for")
                    text = clean_text(node.get_text())
                    parsed.append(f'LABEL: {{ for: "{for_value or ""}", "text": "{text or "<EMPTY>"}" }}')

                # INPUT / CHECKBOX
                elif tag == "input":
                    input_type = node.get("type")
                    name = node.get("name")
                    placeholder = node.get("placeholder")

                    if input_type == "checkbox":
                        label_element = node.find_next('label')
                        label_text = clean_text(label_element.get_text()) if label_element else "<EMPTY>"
                        parsed.append(f'CHECKBOX: {{ label: "{label_text}", input: {{ type: "checkbox", name: "{name or ""}", placeholder: "{placeholder or ""}" }} }}')
                    else:
                        parsed.append(f'INPUT: {{ type: "{input_type or ""}", name: "{name or ""}", placeholder: "{placeholder or ""}" }}')

                # BUTTON
                elif tag == "button":
                    text = clean_text(node.get_text())
                    parsed.append(f'BUTTON: {{ text: "{text or "<EMPTY>"}" }}')

                # IFRAME
                elif tag == "iframe":
                    src = node.get("src")
                    parsed.append(f'IFRAME: {{ src: "{src or ""} }}')

                # SCRIPT
                elif tag == "script":
                    src = node.get("src")
                    if src:
                        parsed.append(f'SCRIPT: {{ src: "{src}" }}')
                    else:
                        parsed.append(f'SCRIPT: {{ <SCRIPT INLINE> }}')

                # META
                elif tag == "meta":
                    name = node.get("name") or node.get("property")
                    content = node.get("content")
                    parsed.append(f'META: {{ name: "{name or ""}", content: "{content or "<EMPTY>"}" }}')
                        
                # IMG
                elif tag == "img":
                    src = node.get("src")
                    alt = node.get("alt")
                    parsed.append(f'IMG: {{ src: "{src or ""}", alt: "{alt or "<EMPTY>"}" }}')

                # TEXT TAGS
                elif tag in {"p", "ul", "ol", "li", "header", "noscript", "title"}:
                    text = clean_text(node.get_text())
                    parsed.append(f'{tag.upper()}: {{ text: "{text or "<EMPTY>"}" }}')

            for child in node.children:
                traverse(child)

    traverse(soup)
    return "\n".join(parsed)

def predict_phishing(html_content):
    processed_text = generate_text_representation(html_content)
    
    inputs = tokenizer.encode_plus(
        processed_text,
        add_special_tokens=True,
        max_length=128,
        return_token_type_ids=False,
        padding='max_length',
        truncation=True,
        return_attention_mask=True,
        return_tensors='pt'
    )

    model.eval()
    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits
        predicted_class = torch.argmax(logits, dim=-1)

    return predicted_class.item()

@app.route('/check_url', methods=['POST'])
def check_url():
    data = request.json
    url = data.get('url', '')
    html_content = fetch_html(url)
    
    if html_content:
        prediction = predict_phishing(html_content)
        label_map = {0: 'benign', 1: 'phishing'}
        result = label_map[prediction]
        return jsonify({'result': result})
    else:
        return jsonify({'result': 'Error fetching HTML content'}), 400

if __name__ == '__main__':
    app.run(port=5024)


