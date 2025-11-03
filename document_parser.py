# document_parser.py
"""
Handles the ingestion and segmentation of the raw source document.
For this version, it processes a simple text file, splitting it into chunks.
"""
from typing import List, Dict

def load_and_segment_document(file_path: str) -> List[Dict[str, str]]:
    """
    Loads a text document and segments it into processable chunks.
    Each chunk is a dictionary with an ID and its content.

    Args:
        file_path (str): The path to the raw text document.

    Returns:
        List[Dict[str, str]]: A list of segmented chunks.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: Raw document not found at {file_path}")
        return []
    
    # Simple segmentation: split by double newlines (represents paragraphs or tables)
    raw_chunks = content.split('\n\n')
    
    segmented_document = []
    for i, chunk_content in enumerate(raw_chunks):
        if chunk_content.strip(): # Ignore empty chunks
            segmented_document.append({
                "id": f"chunk_{i+1}",
                "content": chunk_content.strip()
            })
            
    print(f"Successfully loaded and segmented document into {len(segmented_document)} chunks.")
    return segmented_document