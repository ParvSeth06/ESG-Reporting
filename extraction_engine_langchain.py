# extraction_engine_langchain.py
"""
The core AI logic for the GRI Reporting Agent, refactored to use LangChain
for robust structured output and better scalability.
"""
import pandas as pd
import json

from typing import Dict, List, Optional

# LangChain components
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field # This is the correct import path after upgrade

from data_models import DisclosureEntry
from config import LLM_MODEL_NAME

# --- LangChain Pydantic Model for Structured Extraction ---
# This class defines the exact JSON structure we want the LLM to return.
class GRIExtraction(BaseModel):
    """A single piece of extracted information corresponding to a GRI field."""
    key: str = Field(description="The unique key from the list of fields to populate.")
    extracted_data: str = Field(description="The exact sentence or phrase from the source text that answers the requirement. Verbatim extraction is required.")

class GRIExtractionList(BaseModel):
    """A list of GRIExtraction objects."""
    extractions: List[GRIExtraction] = Field(description="A list of all data points extracted from the text chunk.")


class GRIProcessor:
    """
    Orchestrates the loading of the GRI template and the extraction process using LangChain.
    """
    def __init__(self, template_path: str):
        self.master_template: Dict[str, DisclosureEntry] = self._load_template(template_path)
        self.llm = ChatGoogleGenerativeAI(model=LLM_MODEL_NAME, temperature=0.0)
        print(f"GRI Processor (LangChain) initialized with {len(self.master_template)} template fields.")

    def _load_template(self, template_path: str) -> Dict[str, DisclosureEntry]:
        """Loads the master template CSV into a dictionary of DisclosureEntry objects."""
        try:
            df = pd.read_csv(template_path)
            template = {}
            # Ensure columns are named correctly as in your CSV file
            df.columns = [col.strip() for col in df.columns]
            
            for _, row in df.iterrows():
                # Create a unique key for each disclosure requirement
                key = f"{row['GRI 11 Ref. No.']}_{row['Data Field (Quantitative / Qualitative / Metric)']}_{row['Disclosure Source']}"
                template[key] = DisclosureEntry(
                    ref_no=str(row['GRI 11 Ref. No.']),
                    topic=row['GRI 11 Topic'],
                    disclosure_source=row['Disclosure Source'],
                    data_field=row['Data Field (Quantitative / Qualitative / Metric)'],
                    data_type=row['Type']
                )
            return template
        except FileNotFoundError:
            print(f"Error: Master template not found at {template_path}")
            return {}
        except KeyError as e:
            print(f"Error: A required column is missing from your master_template.csv: {e}")
            return {}

    def process_chunk(self, chunk: Dict[str, str]):
        """Processes a single chunk of data using a LangChain structured output chain."""
        chunk_id = chunk['id']
        content = chunk['content']
        
        unfilled_fields = [
            {"key": key, "description": entry.data_field}
            for key, entry in self.master_template.items() if not entry.data and entry.data_type == 'Narrative'
        ]

        if not unfilled_fields:
            return

        # 1. Define the LangChain chain for structured extraction
        prompt = ChatPromptTemplate.from_template(
            """
            You are an expert ESG data extraction assistant. Your task is to analyze a given text chunk from a company's sustainability report and map its content to a predefined list of GRI disclosure fields.

            Here is a list of UNFILLED GRI disclosure fields:
            ---
            {unfilled_fields}
            ---
            Here is the raw text chunk from the company report:
            ---
            {chunk_content}
            ---

            CRITICAL RULES:
            1. Extract the exact sentence or phrase that directly answers a field. DO NOT summarize or generate new text.
            2. If a field from the list is not explicitly answered in the text, DO NOT include it in your output.
            3. Your final output must conform to the required JSON schema.
            """
        )
        
        # This chain forces the LLM to output in the format of our Pydantic model
        extraction_chain = prompt | self.llm.with_structured_output(GRIExtractionList)

        # 2. Invoke the chain
        try:
            response: GRIExtractionList = extraction_chain.invoke({
                "unfilled_fields": json.dumps(unfilled_fields, indent=2),
                "chunk_content": content
            })

            if response and response.extractions:
                for mapping in response.extractions:
                    key = mapping.key
                    data = mapping.extracted_data
                    
                    if key and data and key in self.master_template:
                        # --- STRICT DATA GUARDRAIL ---
                        # Double-check that the LLM didn't hallucinate or add filler text
                        if "not found" in data.lower() or "not applicable" in data.lower():
                            print(f"Warning: LLM returned filler text for {key}. Data rejected.")
                            continue

                        print(f"  -> Mapping found for {key} in {chunk_id}")
                        self.master_template[key].add_data(data, chunk_id)

        except Exception as e:
            print(f"Error processing LangChain response for {chunk_id}: {e}")
            
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