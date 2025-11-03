# extraction_engine.py
"""
The core AI logic for the GRI Reporting Agent.
Implements the "Single Pass" strategy and "No AI Generation" guardrail.
"""
import pandas as pd
import json
from typing import Dict, List

import google.generativeai as genai

from data_models import DisclosureEntry
from config import GEMINI_API_KEY, LLM_MODEL_NAME

# --- LLM Configuration ---
if not GEMINI_API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable not set.")
genai.configure(api_key=GEMINI_API_KEY)

class GRIProcessor:
    """
    Orchestrates the loading of the GRI template and the extraction process.
    """
    def __init__(self, template_path: str):
        self.master_template: Dict[str, DisclosureEntry] = self._load_template(template_path)
        self.llm = genai.GenerativeModel(LLM_MODEL_NAME)
        print(f"GRI Processor initialized with {len(self.master_template)} template fields.")

    def _load_template(self, template_path: str) -> Dict[str, DisclosureEntry]:
        """Loads the master template CSV into a dictionary of DisclosureEntry objects."""
        try:
            df = pd.read_csv(template_path)
            template = {}
            for _, row in df.iterrows():
                # Create a unique key for each disclosure requirement
                key = f"{row['GRI 11 Ref. No.']}_{row['Data Field (Quantitative / Qualitative / Metric)']}_{row['Disclosure Source']}"
                template[key] = DisclosureEntry(
                    ref_no=row['GRI 11 Ref. No.'],
                    topic=row['GRI 11 Topic'],
                    disclosure_source=row['Disclosure Source'],
                    data_field=row['Data Field (Quantitative / Qualitative / Metric)'],
                    data_type=row['Type']
                )
            return template
        except FileNotFoundError:
            print(f"Error: Master template not found at {template_path}")
            return {}

    def _get_llm_extraction_prompt(self, chunk_content: str) -> str:
        """Generates the precise prompt for the LLM to perform extraction."""
        unfilled_fields = [
            {
                "key": key,
                "ref_no": entry.ref_no,
                "description": entry.data_field
            }
            for key, entry in self.master_template.items() if not entry.data and entry.data_type == 'Narrative'
        ]
        
        if not unfilled_fields:
            return None

        prompt = f"""
        You are an expert ESG data extraction assistant. Your task is to analyze a given text chunk from a company's sustainability report and map its content to a predefined list of GRI disclosure fields.

        Here is a list of UNFILLED GRI disclosure fields from our template:
        ---
        {json.dumps(unfilled_fields, indent=2)}
        ---
        Here is the raw text chunk from the company report:
        ---
        {chunk_content}
        ---

        Based ONLY on the provided text chunk, identify which of the fields from the list are directly and explicitly answered.
        Your response MUST be a valid JSON list of objects. For each match you find, create a JSON object with two keys: "key" (the unique key from the list) and "extracted_data" (the exact sentence or phrase from the text that answers the requirement).

        CRITICAL RULES:
        1. DO NOT infer, invent, summarize, or generate any information. Extract text VERBATIM.
        2. DO NOT answer with conversational text. Your output must ONLY be the JSON list.
        3. If no fields from the list can be answered by the text, you MUST return an empty JSON list: [].
        """
        return prompt

    def process_chunk(self, chunk: Dict[str, str]):
        """Processes a single chunk of data (paragraph or table)."""
        chunk_id = chunk['id']
        content = chunk['content']
        
        # Simple heuristic: Check for table-like structures (can be improved with better parsing)
        # For this example, we'll treat all text chunks as potential narratives for the LLM
        
        prompt = self._get_llm_extraction_prompt(content)
        if not prompt:
            # All narrative fields have been filled
            return
        
        try:
            response = self.llm.generate_content(prompt)
            # Clean up the response to ensure it's valid JSON
            cleaned_response = response.text.strip().replace('```json', '').replace('```', '')
            extracted_mappings = json.loads(cleaned_response)

            if not isinstance(extracted_mappings, list):
                print(f"Warning: LLM returned non-list data for {chunk_id}. Skipping.")
                return

            for mapping in extracted_mappings:
                key = mapping.get("key")
                data = mapping.get("extracted_data")

                if key and data and key in self.master_template:
                    print(f"  -> Mapping found for {key} in {chunk_id}")
                    self.master_template[key].add_data(data, chunk_id)

        except (json.JSONDecodeError, Exception) as e:
            print(f"Error processing LLM response for {chunk_id}: {e}")

    def get_final_report_structure(self) -> List[Dict]:
        """Compiles the final report, including omissions."""
        report = []
        for entry in self.master_template.values():
            report.append({
                "GRI_Ref_No": entry.ref_no,
                "GRI_Topic": entry.topic,
                "Disclosure_Source": entry.disclosure_source,
                "Data_Field": entry.data_field,
                "Status": entry.status,
                "Data_Extracted": entry.data,
                "Audit_Trail_Source_Chunks": entry.source_chunks
            })
        return report