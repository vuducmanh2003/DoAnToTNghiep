from bs4 import BeautifulSoup, NavigableString, Tag
from transformers import MobileBertTokenizer, MobileBertForSequenceClassification
import torch
import re

TARGET_TAGS = {
    "a", "form", "input", "button", "iframe", "script", "title", "meta",
    "img", "label", "p", "header", "footer", "ul", "ol", "li", "noscript"
}

def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def fetch_website_content(path):
    try:
        for enc in ("utf-8", "latin1"):
            try:
                with open(path, "r", encoding=enc) as file:
                    return file.read()
            except Exception:
                pass
        print(f"[WARN] Cannot read file: {path}")
        return None
    except Exception as e:
        print(f"[ERROR] {path}: {e}")
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

def main():
    html_file_path="D://PTIT/Datn/Code/anti-phishing/src/example_parsing_html/lmsattt.html"

    model = MobileBertForSequenceClassification.from_pretrained('D://PTIT/Datn/Code/anti-phishing/src/model')
    tokenizer = MobileBertTokenizer.from_pretrained('D://PTIT/Datn/Code/anti-phishing/src/model')

    html_content = fetch_website_content(html_file_path)
    text = generate_text_representation(html_content)

    print("\n================ TOKENIZATION ================")
    tokens = tokenizer.tokenize(text)
    print("Total tokens:", len(tokens))
    print("Tokens:")
    print(tokens)

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

    print("\n================ MODEL INPUTS ================")
    print("input_ids shape:", inputs["input_ids"].shape)
    print("attention_mask shape:", inputs["attention_mask"].shape)

    print("First 30 input_ids:")
    print(inputs["input_ids"][0][:30])

    print("First 30 attention_mask:")
    print(inputs["attention_mask"][0][:30])

    model.eval()
    with torch.no_grad():
        outputs = model(**inputs)

        logits = outputs.logits
        print("\n================ LOGITS ================")
        print(logits)

        probs = torch.softmax(logits, dim=-1)
        print("\n================ PROBABILITIES ================")
        print(probs)

        predicted_class = torch.argmax(logits, dim=-1)

    prediction = predicted_class.item()
    label_map = {0: 'benign', 1: 'phishing'}
    result = label_map[prediction]

    print("\n================ FINAL RESULT ================")
    print("Predicted number:", prediction)
    print("Predicted label:", result)

if __name__ == "__main__":
    main()


