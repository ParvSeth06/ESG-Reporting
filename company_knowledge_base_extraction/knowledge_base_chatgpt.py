import os
import pdfplumber
import pytesseract
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

# --- CONFIG ---
load_dotenv()

PDF_FILE_PATH = "ilovepdf_merged.pdf"
VECTOR_DB_FOLDER = "company_knowledge_base"

# Uncomment on Windows if needed
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# ---------------------------------------------------
# Helpers
# ---------------------------------------------------

def guess_section(text: str) -> str:
    """Lightweight heuristic to tag ESG sections."""
    text = text.lower()
    if any(k in text for k in ["emission", "carbon", "ghg", "climate"]):
        return "environment_emissions"
    if any(k in text for k in ["energy", "electricity", "fuel"]):
        return "environment_energy"
    if any(k in text for k in ["employee", "workforce", "training", "diversity"]):
        return "social_employees"
    if any(k in text for k in ["safety", "injury", "accident"]):
        return "social_health_safety"
    if any(k in text for k in ["board", "governance", "ethics", "compliance"]):
        return "governance"
    return "general"

def extract_tables_from_page(page):
    """
    Extract tables and format them for LLM consumption.
    """
    table_text = ""
    try:
        tables = page.extract_tables()
        for idx, table in enumerate(tables):
            if not table:
                continue

            table_text += f"\n[TABLE START {idx+1}]\n"
            for row in table:
                cleaned = [cell.strip() if cell else "" for cell in row]
                table_text += "| " + " | ".join(cleaned) + " |\n"
            table_text += "[TABLE END]\n"
    except Exception:
        pass

    return table_text

def extract_text_from_images(page):
    """
    OCR text from images/charts with explicit tagging.
    """
    ocr_text = ""
    try:
        for img in page.images:
            cropped = page.crop((img["x0"], img["top"], img["x1"], img["bottom"]))
            image = cropped.to_image(resolution=300).original
            text = pytesseract.image_to_string(image).strip()
            if text:
                ocr_text += (
                    "\n[OCR_IMAGE_TEXT | LOW_CONFIDENCE]\n"
                    + text
                    + "\n"
                )
    except Exception:
        pass

    return ocr_text

# ---------------------------------------------------
# Main Pipeline
# ---------------------------------------------------

def build_knowledge_base():
    print(f"\n--- Extracting company data from {PDF_FILE_PATH} ---")
    documents = []

    with pdfplumber.open(PDF_FILE_PATH) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            raw_text = page.extract_text(x_tolerance=1, y_tolerance=1) or ""
            table_text = extract_tables_from_page(page)
            ocr_text = extract_text_from_images(page)

            section_hint = guess_section(raw_text)

            combined_text = f"""
[PAGE {page_number}]

[NATIVE TEXT]
{raw_text}

{table_text}

{ocr_text}
"""

            documents.append(
                Document(
                    page_content=combined_text.strip(),
                    metadata={
                        "source": PDF_FILE_PATH,
                        "page": page_number,
                        "section_hint": section_hint,
                        "document_type": "company_report"
                    }
                )
            )

    print(f"✔ Extracted {len(documents)} pages")

    # ---- Chunking ----
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=2800,
        chunk_overlap=300,
        separators=["\n\n", "\n", " ", ""]
    )

    splits = splitter.split_documents(documents)
    print(f"✔ Created {len(splits)} semantic chunks")

    # ---- Embeddings ----
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    # ---- Vector DB ----
    print(f"✔ Saving embeddings to {VECTOR_DB_FOLDER}")
    Chroma.from_documents(
        documents=splits,
        embedding=embeddings,
        persist_directory=VECTOR_DB_FOLDER
    )

    print("\n✅ Company knowledge base successfully built.")

if __name__ == "__main__":
    if os.path.exists(PDF_FILE_PATH):
        build_knowledge_base()
    else:
        print(f"❌ PDF not found: {PDF_FILE_PATH}")
