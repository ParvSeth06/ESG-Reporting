# config.py
"""
Configuration file for the GRI Reporting Agent.
Centralizes API keys, file paths, and model settings.
"""
import os
from dotenv import load_dotenv

# Load environment variables from a .env file if it exists
load_dotenv()

# --- LLM Configuration ---
# IMPORTANT: Your Google API Key should be stored in a file named '.env' in the same directory.
# The .env file should contain one line: GOOGLE_API_KEY="AIzaSy...your...key"
# NEVER hardcode API keys directly into the script.
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
LLM_MODEL_NAME = "gemini-1.5-flash"

# --- File Paths ---
INPUT_DIR = "input"
OUTPUT_DIR = "output"

# Corrected paths: os.path.join combines the directory and filename.
# No need to repeat 'input/' or 'output/' inside the join call.
MASTER_TEMPLATE_PATH = os.path.join(INPUT_DIR, "master_document.csv")
RAW_DOCUMENT_PATH = os.path.join(INPUT_DIR, "raw_data.txt")
FINAL_REPORT_PATH = os.path.join(OUTPUT_DIR, "final_report.json")

# --- Processing Settings ---
# This setting is correct and can be tuned as needed.
TABLE_DETECTION_THRESHOLD = 0.3 # 30% of lines are table-like