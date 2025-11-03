# main.py
"""
Main script to execute the GRI Reporting Agent workflow.
"""
import json
import os

from config import (
    MASTER_TEMPLATE_PATH, RAW_DOCUMENT_PATH, FINAL_REPORT_PATH, OUTPUT_DIR
)
from document_parser import load_and_segment_document
#from extraction_engine import GRIProcessor  # this is SDK
from extraction_engine_langchain import GRIProcessor    # this is langchain version

def run_agent():
    """
    Orchestrates the entire data extraction and report generation process.
    """
    # Create output directory if it doesn't exist
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    # 1. Initialize the processor with the master template
    processor = GRIProcessor(template_path=MASTER_TEMPLATE_PATH)
    if not processor.master_template:
        print("Halting execution due to template loading error.")
        return

    # 2. Load and segment the raw source document
    document_chunks = load_and_segment_document(file_path=RAW_DOCUMENT_PATH)
    if not document_chunks:
        print("Halting execution due to document loading error.")
        return

    # 3. Execute the "Single Pass" processing
    print("\n--- Starting Single-Pass Data Ingestion ---\n")
    for chunk in document_chunks:
        print(f"Processing {chunk['id']}...")
        processor.process_chunk(chunk)
    print("\n--- Single-Pass Ingestion Complete ---\n")
    
    # 4. Generate and save the final structured report
    final_report = processor.get_final_report_structure()
    
    try:
        with open(FINAL_REPORT_PATH, 'w', encoding='utf-8') as f:
            json.dump(final_report, f, indent=4)
        print(f"Successfully generated final report at: {FINAL_REPORT_PATH}")
    except Exception as e:
        print(f"Error saving final report: {e}")

if __name__ == "__main__":
    run_agent()