import os
import time
import pdfplumber
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
# CHANGE: Import HuggingFace Embeddings instead of Google
from langchain_huggingface import HuggingFaceEmbeddings

# --- CONFIGURATION ---
load_dotenv() 

PDF_FILE_PATH = "ilovepdf_merged.pdf"
VECTOR_DB_FOLDER = "company_knowledge_base"

# Note: We don't strictly need an API key for local HuggingFace embeddings,
# but we keep the load_dotenv in case you use other keys later.

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
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return

    # 2. CHUNK THE TEXT
    print("\n--- Step 2: Splitting text into chunks ---")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=2000, 
        chunk_overlap=250, 
        separators=["\n\n", "\n", " ", ""]
    )
    splits = text_splitter.split_documents(documents)
    total_chunks = len(splits)
    print(f"Created {total_chunks} distinct text chunks.")

    # 3. INITIALIZE EMBEDDINGS
    print("\n--- Step 3: Creating Embeddings (Running Locally) ---")
    print("Using HuggingFaceEmbeddings (all-MiniLM-L6-v2)...")
    
    # CHANGE: This runs locally on your CPU/GPU. No API limits!
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    # 4. SAVE TO CHROMA DB
    # Since this is local, we don't need complex batching for rate limits.
    # We can process larger batches safely.
    
    print(f"Saving to {VECTOR_DB_FOLDER}...")
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