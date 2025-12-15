
# -----------------------------
# File: document_parser.py
# -----------------------------
"""Main orchestrator (starter).
Usage:
  from document_parser import DocumentParser
  dp = DocumentParser('path/to/report.pdf')
  result = dp.run()

This starter maps simple keyword searches to GRI-like keys.
"""

import os
import json
import re
from typing import Dict, Any

# local imports (assumes these files are in the same package/directory)
from pdf_reader import extract_pdf_text, extract_pdf_tables
from docx_reader import extract_docx_text, extract_docx_tables
from text_cleaner import clean_hyphenation, remove_headers_footers, split_into_sections
from table_extractor import df_to_records


# Simple starter keyword mapping (expand for production)
GRI_KEYWORDS = {
    'GRI_302_Energy': ['energy consumption', 'electricity', 'kwh', 'mwh', 'fuel', 'diesel', 'natural gas'],
    'GRI_305_Emissions': ['scope 1', 'scope 2', 'ghg', 'co2', 'co2e', 'emissions'],
    'GRI_303_Water': ['water withdrawal', 'water consumption', 'm3', 'cubic metres', 'litres'],
    'GRI_401_Employment': ['employees', 'headcount', 'turnover', 'new hires', 'staff']
}


class DocumentParser:
    def __init__(self, path: str):
        self.path = path
        self.ext = os.path.splitext(path)[1].lower()
        self.raw_text = ""
        self.tables = []

    def read(self):
        if self.ext == '.pdf':
            self.raw_text = extract_pdf_text(self.path)
            self.tables = extract_pdf_tables(self.path)
        elif self.ext in ('.docx', '.doc'):
            self.raw_text = extract_docx_text(self.path)
            self.tables = extract_docx_tables(self.path)
        else:
            raise ValueError(f"Unsupported extension: {self.ext}")

        # Basic cleaning
        txt = clean_hyphenation(self.raw_text)
        txt = remove_headers_footers(txt)
        self.raw_text = txt

    def extract_by_keywords(self) -> Dict[str, Any]:
        out = {}
        lowered = self.raw_text.lower()
        for k, keywords in GRI_KEYWORDS.items():
            matches = []
            for kw in keywords:
                if kw.lower() in lowered:
                    # grab a small window around the first occurrence (starter)
                    m = re.search(re.escape(kw), lowered)
                    if m:
                        start = max(0, m.start() - 200)
                        end = min(len(lowered), m.end() + 200)
                        snippet = self.raw_text[start:end].strip()
                        matches.append(snippet)
            out[k] = matches
        return out

    def extract_from_tables(self):
        records = {}
        for i, df in enumerate(self.tables):
            try:
                recs = df_to_records(df)
            except Exception:
                recs = []
            records[f'table_{i}'] = recs
        return records

    def run(self) -> Dict[str, Any]:
        self.read()
        text_results = self.extract_by_keywords()
        table_results = self.extract_from_tables()

        final = {
            'meta': {'source_path': self.path},
            'text_matches': text_results,
            'tables': table_results
        }
        return final


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('path')
    parser.add_argument('--out', default='gri_output.json')
    args = parser.parse_args()

    dp = DocumentParser(args.path)
    result = dp.run()
    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print('Wrote', args.out)
