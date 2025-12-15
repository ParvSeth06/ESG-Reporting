import os
import re
import pdfplumber

# --- CONFIGURATION ---
# The script will create this folder and save everything inside it
OUTPUT_FOLDER = "reference_data" 

def is_valid_disclosure_header(text):
    """
    Strict check to ensure a line is actually a Disclosure Header 
    and not just a sentence referencing a disclosure.
    """
    text = text.strip()
    
    # 1. Must start exactly with "Disclosure"
    if not text.startswith("Disclosure"):
        return False
        
    # 2. Must contain the specific number pattern (e.g., "202-1")
    # This regex looks for digits-digits pattern
    if not re.search(r"Disclosure\s+\d{3}-\d+", text):
        return False

    # 3. SAFETY CHECK: Ignore sentences containing reference words.
    # If the line says "See Disclosure 202-1", we ignore it.
    reference_words = ["see ", "refer ", "accordance", "reported", "compiled", "requirement"]
    if any(word in text.lower() for word in reference_words):
        return False

    # 4. Length check: Headers are usually concise (< 150 chars)
    if len(text) > 150:
        return False

    return True

def extract_disclosures(pdf_path):
    disclosures = []
    current_block = None
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                # Extract text. 'x_tolerance' helps keep columns together.
                text = page.extract_text(x_tolerance=2)
                
                if not text: continue
                
                lines = text.split('\n')
                
                for line in lines:
                    line = line.strip()
                    if not line: continue
                    
                    upper_line = line.upper()

                    # --- 1. STOP: GLOSSARY ---
                    if upper_line == "GLOSSARY":
                        if current_block: disclosures.append(current_block)
                        return disclosures

                    # --- 2. START: MANAGEMENT SECTION ---
                    # Look for "Topic management disclosures"
                    if "TOPIC MANAGEMENT DISCLOSURES" in upper_line:
                        # Save previous block if it exists
                        if current_block: disclosures.append(current_block)
                        
                        current_block = {
                            "title": "Topic Management Disclosures",
                            "content": [line]
                        }
                        continue

                    # --- 3. DIVIDER: TOPIC DISCLOSURES ---
                    # This ends the management section. We wait for the first "Disclosure X-Y"
                    if "TOPIC DISCLOSURES" in upper_line and "MANAGEMENT" not in upper_line:
                        if current_block: disclosures.append(current_block)
                        current_block = None
                        continue

                    # --- 4. START: SPECIFIC DISCLOSURE ---
                    if is_valid_disclosure_header(line):
                        if current_block: disclosures.append(current_block)
                        
                        current_block = {
                            "title": line,
                            "content": []
                        }
                        continue

                    # --- 5. CAPTURE CONTENT ---
                    if current_block:
                        # Optional: Skip page headers/footers to keep text clean
                        # e.g., skips "GRI 202: Market Presence 2016" or standalone page numbers
                        if "GRI 202:" in line or line.isdigit():
                            continue
                            
                        current_block["content"].append(line)

    except Exception as e:
        print(f"Error processing {pdf_path}: {e}")

    # Append the final block if we reached the end
    if current_block:
        disclosures.append(current_block)

    return disclosures

def save_disclosures(disclosures, pdf_name):
    # This creates the sub-folder for the specific PDF inside the main folder
    base_folder = os.path.join(OUTPUT_FOLDER, pdf_name)
    os.makedirs(base_folder, exist_ok=True)

    for i, disc in enumerate(disclosures):
        # Sanitize filename (remove colons, slashes, etc.)
        safe_title = "".join([c for c in disc["title"] if c.isalnum() or c in (' ', '_', '-')]).strip()
        safe_title = safe_title.replace(" ", "_")[:50]
        
        if not safe_title: safe_title = f"Section_{i}"

        filename = os.path.join(base_folder, f"{safe_title}.txt")
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(disc["title"] + "\n\n")
            f.write("\n".join(disc["content"]))

def main():
    input_folder = "reference_raw"
    
    # Create input folder if user doesn't have it
    if not os.path.exists(input_folder):
        os.makedirs(input_folder)
        print(f"Created '{input_folder}'. Please put your PDFs inside it.")
        return

    # Create the main output folder
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)
        print(f"Created output folder: '{OUTPUT_FOLDER}'")

    for file in os.listdir(input_folder):
        if file.lower().endswith(".pdf"):
            pdf_path = os.path.join(input_folder, file)
            print(f"\n=== Processing: {file} ===")
            
            disclosures = extract_disclosures(pdf_path)
            
            if disclosures:
                save_disclosures(disclosures, file.replace(".pdf",""))
                print(f"Success! Saved {len(disclosures)} files to: {OUTPUT_FOLDER}/{file.replace('.pdf','')}")
                for d in disclosures:
                    print(f" - {d['title']}")
            else:
                print("No disclosures found.")

if __name__ == "__main__":
    main()