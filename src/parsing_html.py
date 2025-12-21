import os
import argparse
from tqdm import tqdm
from bs4 import BeautifulSoup, NavigableString, Tag
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

def save_output_to_file(filename, flattened_content, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    output_filename = os.path.join(output_dir, filename + ".txt")
    with open(output_filename, 'w', encoding="utf-8") as file:
        file.write(flattened_content)

def process_folder(folder_path, output_dir):
    html_files = [f for f in os.listdir(folder_path) if f.endswith(".txt")]
    for html_file in tqdm(html_files, desc="Processing HTML files"):
        full_path = os.path.join(folder_path, html_file)
        html_content = fetch_website_content(full_path)
        if html_content is None:
            continue
        flattened_content = generate_text_representation(html_content)
        base_name = os.path.splitext(html_file)[0]
        save_output_to_file(base_name, flattened_content, output_dir)

def main():
    parser = argparse.ArgumentParser(description='Process phishing or benign websites.')
    parser.add_argument('type', choices=['phishing', 'benign'], help='Specify the type of websites to process.')
    args = parser.parse_args()

    if args.type == 'phishing':
        folder_path = os.path.expanduser('D://PTIT/Datn/Code/anti-phishing/dataset_for_training/phishing_websites')
        output_dir = 'D://PTIT/Datn/Code/anti-phishing/data_for_training/phishing_samples'
    elif args.type == 'benign':
        folder_path = os.path.expanduser('D://PTIT/Datn/Code/anti-phishing/dataset_for_training/benign_websites')
        output_dir = 'D://PTIT/Datn/Code/anti-phishing/data_for_training/benign_samples'
    
    if os.path.exists(folder_path):
        process_folder(folder_path, output_dir)
    else:
        print(f"The folder {folder_path} does not exist.")

if __name__ == "__main__":
    main()

