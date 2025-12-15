
"""Starter PDF reader utilities.
Requires: pdfplumber (pip install pdfplumber)
Functions:
- extract_pdf_text(path) -> str
- extract_pdf_tables(path) -> list[pandas.DataFrame]
"""

import io
import re
from typing import List

import pandas as pd

try:
    import pdfplumber
except Exception as e:
    pdfplumber = None


def extract_pdf_text(path: str) -> str:
    """Extracts continuous text from a PDF using pdfplumber.
    Falls back to returning empty string if pdfplumber isn't available.
    """
    if not pdfplumber:
        raise ImportError("pdfplumber not installed. Install with `pip install pdfplumber`")

    texts = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            texts.append(page_text)

    raw = "\n".join(texts)
    # Basic normalization: remove repeated form feeds and multiple blank lines
    raw = re.sub(r"\n{3,}", "\n\n", raw)
    return raw


def extract_pdf_tables(path: str) -> List[pd.DataFrame]:
    """Try to extract tables from PDF pages with pdfplumber.
    Returns a list of DataFrames (may be empty).
    """
    if not pdfplumber:
        raise ImportError("pdfplumber not installed. Install with `pip install pdfplumber`")

    tables = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            try:
                raw_tables = page.extract_tables()
            except Exception:
                raw_tables = []

            for t in raw_tables:
                # Convert to DataFrame (simple approach)
                df = pd.DataFrame(t)
                # Drop completely-empty columns/rows
                df = df.dropna(axis=0, how="all").dropna(axis=1, how="all")
                if df.shape[0] and df.shape[1]:
                    tables.append(df)

    return tables

