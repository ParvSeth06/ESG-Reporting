import os
import re
import json
import pdfplumber

# =========================
# CONFIG
# =========================

INPUT_FOLDER = "gri_standards_raw"   # GRI 1,2,3,11 PDFs
OUTPUT_FILE = "gri_semantic_knowledge.json"

# =========================
# REGEX PATTERNS
# =========================

DISCLOSURE_REGEX = re.compile(r"Disclosure\s+(\d+[-–]\d+)")
SHALL_REGEX = re.compile(r"\bshall\b|\bmust\b|\bis required to\b", re.IGNORECASE)
GUIDANCE_REGEX = re.compile(r"\bshould\b|\bmay\b|\bcan\b", re.IGNORECASE)
SUBITEM_REGEX = re.compile(r"^[a-z]\.|^[ivx]+\.", re.IGNORECASE)

# =========================
# HELPERS
# =========================

def classify_standard(filename):
    if filename.startswith("GRI 1"):
        return "foundation"
    if filename.startswith("GRI 2"):
        return "universal"
    if filename.startswith("GRI 3"):
        return "universal"
    if filename.startswith("GRI 11"):
        return "sector"
    return "other"

def detect_principle(line):
    principles = [
        "accuracy", "completeness", "balance",
        "comparability", "reliability", "timeliness"
    ]
    for p in principles:
        if p in line.lower():
            return p
    return None

# =========================
# CORE EXTRACTION
# =========================

def extract_gri_requirements(pdf_path):
    extracted = []

    standard_name = os.path.basename(pdf_path).replace(".pdf", "")
    standard_code = standard_name.split(":")[0]
    standard_type = classify_standard(standard_name)

    current_disclosure = None
    sub_items = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            text = page.extract_text(x_tolerance=2)
            if not text:
                continue

            for line in text.split("\n"):
                line = line.strip()
                if not line:
                    continue

                # ---- Disclosure detection ----
                disc_match = DISCLOSURE_REGEX.search(line)
                if disc_match:
                    current_disclosure = disc_match.group(1)
                    sub_items = []
                    continue

                # ---- Sub-requirements (a., b., i., ii.) ----
                if SUBITEM_REGEX.match(line):
                    sub_items.append(line)
                    continue

                # ---- Mandatory requirements ----
                if SHALL_REGEX.search(line):
                    extracted.append({
                        "standard": standard_code,
                        "standard_type": standard_type,
                        "section": f"Disclosure {current_disclosure}" if current_disclosure else "General",
                        "disclosure_id": current_disclosure,
                        "requirement_type": "sector_specific" if standard_type == "sector" else "mandatory",
                        "trigger_word": "shall/must",
                        "text": line,
                        "sub_items": sub_items.copy(),
                        "page": page_num
                    })
                    sub_items.clear()
                    continue

                # ---- Guidance ----
                if GUIDANCE_REGEX.search(line):
                    extracted.append({
                        "standard": standard_code,
                        "standard_type": standard_type,
                        "section": f"Disclosure {current_disclosure}" if current_disclosure else "General",
                        "disclosure_id": current_disclosure,
                        "requirement_type": "guidance",
                        "trigger_word": "should/may",
                        "text": line,
                        "sub_items": [],
                        "page": page_num
                    })
                    continue

                # ---- Reporting principles (GRI 1) ----
                principle = detect_principle(line)
                if principle:
                    extracted.append({
                        "standard": standard_code,
                        "standard_type": "foundation",
                        "section": "Reporting Principles",
                        "disclosure_id": None,
                        "requirement_type": "principle",
                        "trigger_word": principle,
                        "text": line,
                        "sub_items": [],
                        "page": page_num
                    })

    return extracted

# =========================
# MAIN
# =========================

def main():
    all_requirements = []

    for file in os.listdir(INPUT_FOLDER):
        if file.lower().endswith(".pdf"):
            path = os.path.join(INPUT_FOLDER, file)
            print(f"Processing {file}...")
            all_requirements.extend(extract_gri_requirements(path))

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_requirements, f, indent=2, ensure_ascii=False)

    print(f"\n✅ GRI semantic knowledge saved to {OUTPUT_FILE}")
    print(f"Total extracted rules: {len(all_requirements)}")

if __name__ == "__main__":
    main()
