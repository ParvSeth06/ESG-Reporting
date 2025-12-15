import os
import time
import pdfplumber
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
# CHANGE: Using local HuggingFace embeddings
from langchain_huggingface import HuggingFaceEmbeddings

# --- CONFIGURATION ---
load_dotenv() 

PDF_FILE_PATH = "ilovepdf_merged.pdf"
VECTOR_DB_FOLDER = "company_knowledge_base"

def build_knowledge_base():
    # 1. LOAD AND EXTRACT
    print(f"--- Step 1: Extracting text from {PDF_FILE_PATH} ---")
    documents = []
    
    try:
        with pdfplumber.open(PDF_FILE_PATH) as pdf:
            total_pages = len(pdf.pages)
            for i, page in enumerate(pdf.pages):
                text = page.extract_text(x_tolerance=2, y_tolerance=2)
                if text:
                    doc = Document(
                        page_content=text,
                        metadata={"source": PDF_FILE_PATH, "page_number": i + 1}
                    )
                    documents.append(doc)
                    if (i + 1) % 10 == 0:
                        print(f"Processed {i + 1}/{total_pages} pages...")
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return

    # 2. CHUNK THE TEXT
    print("\n--- Step 2: Splitting text into chunks ---")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=2000, chunk_overlap=250, separators=["\n\n", "\n", " ", ""]
    )
    splits = text_splitter.split_documents(documents)
    total_chunks = len(splits)
    print(f"Created {total_chunks} distinct text chunks.")

    # 3. INITIALIZE LOCAL EMBEDDINGS
    print("\n--- Step 3: Creating Embeddings (Running Locally) ---")
    print("Using HuggingFace 'all-MiniLM-L6-v2' (No Rate Limits)...")
    
    # This runs locally. It might take a minute to download the model the first time.
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    # 4. SAVE TO CHROMA DB
    print(f"Saving to {VECTOR_DB_FOLDER}...")
    
    # Since this is local, we can add them all at once without fear of 429 errors
    vectorstore = Chroma.from_documents(
        documents=splits,
        embedding=embeddings,
        persist_directory=VECTOR_DB_FOLDER
    )
    
    print(f"\nSUCCESS! Knowledge base built and saved to: './{VECTOR_DB_FOLDER}'")

if __name__ == "__main__":
    if os.path.exists(PDF_FILE_PATH):
        build_knowledge_base()
    else:
        print(f"Error: Could not find file '{PDF_FILE_PATH}'")