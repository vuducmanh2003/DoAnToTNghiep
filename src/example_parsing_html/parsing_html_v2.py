from bs4 import BeautifulSoup
import json

IMPORTANT_CLASSES = [
    "login", "header", "footer", "nav", "main", "content",
    "form", "input", "btn", "button", "card", "container"
]

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

def generate_json(html):
    soup = BeautifulSoup(html, "html.parser")

    # Remove script/style
    for script in soup(["script", "style"]):
        script.decompose()

    data = {
        "title": "",
        "headings": [],
        "paragraphs": [],
        "links": [],
        "forms": [],
        "lists": [],
        "footer": "",
        "iframes": [],
        "meta": [],
        "maps": [],
        "labels": [],
        "images": [],
        "tables": [],
        "selects": [],
        "important_sections": []
    }

    # Title
    if soup.title:
        data["title"] = soup.title.get_text(strip=True).lower()

    # Headings + paragraphs
    for tag in ["h1", "h2", "h3", "p"]:
        for el in soup.find_all(tag):
            text = el.get_text(strip=True).lower()
            if not text:
                continue
            if tag == "p":
                data["paragraphs"].append(text)
            else:
                data["headings"].append({tag: text})

    # Links
    for a in soup.find_all("a"):
        data["links"].append({
            "text": a.get_text(strip=True).lower(),
            "href": a.get("href", "")
        })
    
    # Labels
    for lab in soup.find_all("label"):
        data["labels"].append({
            "for": lab.get("for", ""),
            "text": lab.get_text(strip=True).lower()
        })

    # Lists (ul / ol / li)
    for lst in soup.find_all(["ul", "ol"]):
        items = []
        for li in lst.find_all("li"):
            t = li.get_text(strip=True).lower()
            if t:
                items.append(t)
        if items:
            data["lists"].append({
                "type": lst.name,
                "items": items
            })

    # Footer
    if soup.find("footer"):
        data["footer"] = soup.find("footer").get_text(strip=True).lower()

    # Iframes
    for iframe in soup.find_all("iframe"):
        data["iframes"].append({
            "src": iframe.get("src", ""),
            "text": iframe.get_text(strip=True).lower()
        })

    # Meta tags
    for meta in soup.find_all("meta"):
        entry = {}
        for attr in ["name", "property", "http-equiv", "content"]:
            value = meta.get(attr)
            if value:
                entry[attr] = value.lower()
        if entry:
            data["meta"].append(entry)

    # Image maps (map + area)
    for mp in soup.find_all("map"):
        map_entry = {
            "name": mp.get("name", ""),
            "areas": []
        }
        for ar in mp.find_all("area"):
            map_entry["areas"].append({
                "href": ar.get("href", ""),
                "alt": ar.get("alt", ""),
                "coords": ar.get("coords", "")
            })
        data["maps"].append(map_entry)

    # Images
    for img in soup.find_all("img"):
        data["images"].append({
            "src": img.get("src", ""),
            "alt": img.get("alt", "").lower(),
            "title": img.get("title", "").lower()
        })
    
    # Tables
    for table in soup.find_all("table"):
        table_entry = {"rows": []}
        for tr in table.find_all("tr"):
            row = []
            for cell in tr.find_all(["th", "td"]):
                row.append(cell.get_text(strip=True).lower())
            if row:
                table_entry["rows"].append(row)
        data["tables"].append(table_entry)

    # Select + options
    for sel in soup.find_all("select"):
        entry = {
            "name": sel.get("name", ""),
            "options": []
        }
        for opt in sel.find_all("option"):
            entry["options"].append({
                "value": opt.get("value", ""),
                "text": opt.get_text(strip=True).lower()
            })
        data["selects"].append(entry)
    
    # Important div / span
    for tag in soup.find_all(["div", "span"]):
        classes = tag.get("class", [])
        if not classes:
            continue

        # check nếu class của div/spam thuộc nhóm quan trọng
        if any(c.lower() in IMPORTANT_CLASSES for c in classes):
            data["important_sections"].append({
                "tag": tag.name,
                "class": classes,
                "text": tag.get_text(strip=True).lower()
            })

    # Forms
    for form in soup.find_all("form"):
        form_data = {"inputs": [], "buttons": []}

        for inp in form.find_all("input"):
            t = inp.get("type", "")
            name = inp.get("name", "")
            placeholder = inp.get("placeholder", "")

            # checkbox needs label
            label_text = ""
            if t == "checkbox":
                label = inp.find_next("label")
                label_text = label.get_text(strip=True).lower() if label else ""

            form_data["inputs"].append({
                "type": t,
                "name": name,
                "placeholder": placeholder,
                "label": label_text if t == "checkbox" else ""
            })

        for btn in form.find_all("button"):
            form_data["buttons"].append({
                "text": btn.get_text(strip=True).lower(),
                "type": btn.get("type", ""),
                "id": btn.get("id", ""),
                "class": " ".join(btn.get("class", [])) if btn.get("class") else ""
            })

        data["forms"].append(form_data)

    return data

def json_to_text(data, prefix=""):
    texts = []

    if isinstance(data, dict):
        for key, value in data.items():
            if value in ("", [], {}, None):
                continue
            new_prefix = f"{prefix}[{key.upper()}]"
            texts.extend(json_to_text(value, new_prefix))

    elif isinstance(data, list):
        for item in data:
            texts.extend(json_to_text(item, prefix))

    else:
        text = str(data).strip()
        if text:
            texts.append(f"{prefix} {text}".strip())

    return texts

def flatten_json_to_text(json_data):
    lines = json_to_text(json_data)
    return "\n".join(lines)

def main():
    html_file_path="D://PTIT/Datn/Code/anti-phishing/src/example_parsing_html/lmsattt.html"
    html_content = fetch_website_content(html_file_path)
    json_content = generate_json(html_content)
    flattened_content = flatten_json_to_text(json_to_text(json_content))
    output_filename="D://PTIT/Datn/Code/anti-phishing/src/example_parsing_html/lmsattt_v2.txt"
    with open(output_filename, 'w', encoding="utf-8") as file:
        file.write(flattened_content)

if __name__ == "__main__":
    main()