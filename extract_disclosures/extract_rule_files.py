import os
import re
import json
import pdfplumber

# =========================
# CONFIG
# =========================
INPUT_FOLDER = "reference_raw"
OUTPUT_FOLDER = "reference_data_gpt_new/rule_files"

SHALL_PATTERN = re.compile(r"\bshall\b", re.IGNORECASE)
MUST_PATTERN = re.compile(r"\bmust\b", re.IGNORECASE)

SECTION_HEADERS = {
    "REPORTING PRINCIPLES": "reporting_principles",
    "REPORTING IN ACCORDANCE": "process_rules",
    "USING THIS STANDARD": "process_rules",
    "SECTOR DISCLOSURES": "sector_specific_rules",
    "SECTOR STANDARD": "sector_specific_rules",
}

# =========================
# HELPERS
# =========================

def clean(text):
    return re.sub(r"\s+", " ", text).strip()

def is_requirement(line):
    return SHALL_PATTERN.search(line) or MUST_PATTERN.search(line)

def is_section_header(line):
    return any(h in line.upper() for h in SECTION_HEADERS)

def detect_standard_type(name):
    if "GRI 11" in name:
        return "sector"
    return "universal"

# =========================
# CORE EXTRACTION
# =========================

def extract_rules(pdf_path):
    standard_name = os.path.basename(pdf_path).replace(".pdf", "")
    standard_type = detect_standard_type(standard_name)

    output = {
        "standard": standard_name,
        "type": standard_type,
        "mandatory_requirements": [],
        "reporting_principles": [],
        "process_rules": [],
        "sector_specific_rules": []
    }

    current_section = None
    current_requirement = None

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            text = page.extract_text(x_tolerance=2)
            if not text:
                continue

            lines = text.split("\n")

            for line in lines:
                line = clean(line)
                if not line:
                    continue

                # -------- Detect section --------
                if is_section_header(line):
                    for header, section in SECTION_HEADERS.items():
                        if header in line.upper():
                            current_section = section
                    continue

                # -------- Mandatory requirements --------
                if is_requirement(line):
                    # start a new requirement block
                    current_requirement = {
                        "text": line,
                        "sub_requirements": [],
                        "page": page_num
                    }
                    output["mandatory_requirements"].append(current_requirement)
                    continue

                # -------- Sub-points (a., i., •) --------
                if current_requirement and re.match(r"^[a-z]\.|^[ivx]+\.", line.lower()):
                    current_requirement["sub_requirements"].append(line)
                    continue

                # -------- Reporting principles --------
                if current_section == "reporting_principles":
                    output["reporting_principles"].append({
                        "text": line,
                        "page": page_num
                    })
                    continue

                # -------- Process rules --------
                if current_section == "process_rules":
                    output["process_rules"].append({
                        "text": line,
                        "page": page_num
                    })
                    continue

                # -------- Sector specific --------
                if current_section == "sector_specific_rules":
                    output["sector_specific_rules"].append({
                        "text": line,
                        "page": page_num
                    })

    return output

# =========================
# MAIN
# =========================

def main():
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    for file in os.listdir(INPUT_FOLDER):
        if not file.lower().endswith(".pdf"):
            continue

        path = os.path.join(INPUT_FOLDER, file)
        print(f"Processing {file}...")

        extracted = extract_rules(path)

        out_path = os.path.join(
            OUTPUT_FOLDER,
            file.replace(".pdf", "_rules.json")
        )

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(extracted, f, indent=2, ensure_ascii=False)

        print(f"✔ Saved {out_path}")

if __name__ == "__main__":
    main()
