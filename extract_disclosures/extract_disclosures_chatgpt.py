import os
import re
import json
import pdfplumber

INPUT_FOLDER = "reference_raw"
OUTPUT_FOLDER = "reference_data_gpt_new/topic_standards"

# Strict: ONLY real disclosure headers
DISCLOSURE_HEADER_REGEX = re.compile(
    r"^Disclosure\s+(\d{3})-(\d+)\s+(.+)$"
)

SECTION_KEYWORDS = {
    "REQUIREMENTS": "requirements",
    "BACKGROUND": "background",
    "GUIDANCE": "guidance",
    "RECOMMENDATIONS": "recommendations",
    "COMPILATION REQUIREMENTS": "requirements"
}

def extract_topic_standard(pdf_path):
    disclosures = []
    current = None
    current_section = None
    current_topic = None

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text(x_tolerance=2)
            if not text:
                continue

            for raw_line in text.split("\n"):
                line = raw_line.strip()
                if not line:
                    continue

                upper = line.upper()

                # ---- Stop at glossary ----
                if upper == "GLOSSARY":
                    if current:
                        disclosures.append(current)
                    return disclosures

                # ---- Topic header (e.g., "GRI 207: Tax 2019") ----
                if upper.startswith("GRI ") and ":" in upper and "DISCLOSURE" not in upper:
                    current_topic = line
                    continue

                # ---- REAL disclosure header ----
                match = DISCLOSURE_HEADER_REGEX.match(line)
                if match:
                    if current:
                        disclosures.append(current)

                    std = match.group(1)
                    disc_num = match.group(2)

                    current = {
                        "standard": f"GRI {std}",
                        "disclosure_id": f"{std}-{disc_num}",
                        "title": line,
                        "topic": current_topic,
                        "requirements": [],
                        "background": [],
                        "guidance": [],
                        "recommendations": []
                    }
                    current_section = None
                    continue

                # ---- Section detection ----
                if upper in SECTION_KEYWORDS:
                    current_section = SECTION_KEYWORDS[upper]
                    continue

                # ---- Skip cross-disclosure references ----
                if line.startswith("Disclosure") and "is related to" in line:
                    continue

                # ---- Capture content ----
                if current and current_section:
                    current[current_section].append(line)

    if current:
        disclosures.append(current)

    return disclosures


def save_output(disclosures, pdf_name):
    base = os.path.join(OUTPUT_FOLDER, pdf_name)
    os.makedirs(base, exist_ok=True)

    for d in disclosures:
        fname = d["disclosure_id"] + ".json"
        path = os.path.join(base, fname)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(d, f, indent=2, ensure_ascii=False)


def main():
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    for file in os.listdir(INPUT_FOLDER):
        if not file.lower().endswith(".pdf"):
            continue

        # Only Topic Standards
        if not re.search(r"GRI\s+(2\d{2}|3\d{2}|4\d{2})", file):
            continue

        print(f"Processing Topic Standard: {file}")
        pdf_path = os.path.join(INPUT_FOLDER, file)

        disclosures = extract_topic_standard(pdf_path)
        save_output(disclosures, file.replace(".pdf", ""))

        print(f"✔ Extracted {len(disclosures)} disclosures")

if __name__ == "__main__":
    main()
