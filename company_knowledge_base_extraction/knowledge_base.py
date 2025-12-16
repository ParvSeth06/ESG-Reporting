import os
import pdfplumber
import pytesseract
from PIL import Image
import io
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

# --- CONFIGURATION ---
load_dotenv() 

PDF_FILE_PATH = "ilovepdf_merged.pdf"
VECTOR_DB_FOLDER = "company_knowledge_base"

# POINT THIS TO YOUR TESSERACT EXECUTABLE IF ON WINDOWS
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extract_tables_from_page(page):
    """
    Extracts tables and converts them to Markdown format to preserve structure.
    """
    tables_text = ""
    try:
        tables = page.extract_tables()
        for table in tables:
            # Filter out empty rows/cells
            cleaned_table = [[cell if cell else "" for cell in row] for row in table]
            if not cleaned_table: continue
            
            # Convert to simple Markdown table format for LLM readability
            # | Header 1 | Header 2 |
            # | --- | --- |
            # | Val 1 | Val 2 |
            
            # (Simplified approach: Pipe separated values)
            for row in cleaned_table:
                tables_text += "| " + " | ".join(filter(None, row)) + " |\n"
            tables_text += "\n---\n"
    except Exception as e:
        print(f"    Table extraction warning: {e}")
    return tables_text

def extract_text_from_images(page):
    """
    Extracts images from the page and runs OCR to get text inside charts/photos.
    """
    image_text = ""
    try:
        for image_obj in page.images:
            # Get image data
            x0, top, x1, bottom = image_obj['x0'], image_obj['top'], image_obj['x1'], image_obj['bottom']
            # Crop the page to the image area (improves context)
            cropped_page = page.crop((x0, top, x1, bottom))
            im = diff_page_image = cropped_page.to_image(resolution=300)
            
            # Convert to PIL Image
            pil_image = im.original
            
            # Run OCR
            text = pytesseract.image_to_string(pil_image).strip()
            if text:
                image_text += f"\n[Text from Image]:\n{text}\n"
    except Exception as e:
        # OCR might fail if Tesseract isn't installed or image is weird
        pass 
    return image_text

def build_knowledge_base():
    print(f"--- Step 1: Deep Extraction from {PDF_FILE_PATH} ---")
    documents = []
    
    try:
        with pdfplumber.open(PDF_FILE_PATH) as pdf:
            total_pages = len(pdf.pages)
            for i, page in enumerate(pdf.pages):
                print(f"Processing Page {i + 1}/{total_pages}...", end="\r")
                
                # 1. Standard Text
                raw_text = page.extract_text(x_tolerance=1, y_tolerance=1) or ""
                
                # 2. Table Extraction (Structured)
                table_content = extract_tables_from_page(page)
                
                # 3. OCR Extraction (Images/Charts)
                # Note: This is slow. If it's too slow, comment this line out.
                ocr_content = extract_text_from_images(page)
                
                # Combine all sources
                combined_content = f"""
                --- PAGE {i+1} TEXT ---
                {raw_text}
                
                --- PAGE {i+1} TABLES ---
                {table_content}
                
                --- PAGE {i+1} IMAGE DATA ---
                {ocr_content}
                """
                
                doc = Document(
                    page_content=combined_content,
                    metadata={"source": PDF_FILE_PATH, "page_number": i + 1}
                )
                documents.append(doc)
                
    except Exception as e:
        print(f"\nError reading PDF: {e}")
        return

    print(f"\nSuccessfully extracted {len(documents)} pages.")

    # 2. CHUNK THE TEXT
    print("\n--- Step 2: Splitting text into chunks ---")
    # We use a larger chunk size to keep tables together
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=3000, 
        chunk_overlap=300, 
        separators=["\n\n", "\n", " ", ""]
    )
    splits = text_splitter.split_documents(documents)
    print(f"Created {len(splits)} distinct text chunks.")

    # 3. INITIALIZE LOCAL EMBEDDINGS
    print("\n--- Step 3: Creating Embeddings (Running Locally) ---")
    print("Using HuggingFace 'all-MiniLM-L6-v2'...")
    
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    # 4. SAVE TO CHROMA DB
    print(f"Saving to {VECTOR_DB_FOLDER}...")
    
    # Batch processing to be safe (though local doesn't strictly need it)
    batch_size = 100
    for i in range(0, len(splits), batch_size):
        batch = splits[i : i + batch_size]
        print(f"Embedding batch {i // batch_size + 1}...")
        vectorstore = Chroma.from_documents(
            documents=batch,
            embedding=embeddings,
            persist_directory=VECTOR_DB_FOLDER
        )
    
    print(f"\nSUCCESS! Knowledge base built and saved to: './{VECTOR_DB_FOLDER}'")

if __name__ == "__main__":
    if os.path.exists(PDF_FILE_PATH):
        build_knowledge_base()
    else:
        print(f"Error: Could not find file '{PDF_FILE_PATH}'")