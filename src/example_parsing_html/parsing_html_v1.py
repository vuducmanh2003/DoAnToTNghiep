from bs4 import BeautifulSoup

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
    soup = BeautifulSoup(html_content, "html.parser")
    text = soup.get_text(separator="\n")

    lines = []
    for line in text.splitlines():
        clean_line = " ".join(line.split())
        if clean_line:
            lines.append(clean_line)

    return "\n".join(lines)

def main():
    html_file_path="D://PTIT/Datn/Code/anti-phishing/src/example_parsing_html/lmsattt.html"
    html_content = fetch_website_content(html_file_path)
    flattened_content = generate_text_representation(html_content)
    output_filename="D://PTIT/Datn/Code/anti-phishing/src/example_parsing_html/lmsattt_v1.txt"
    with open(output_filename, 'w', encoding="utf-8") as file:
        file.write(flattened_content)

if __name__ == "__main__":
    main()