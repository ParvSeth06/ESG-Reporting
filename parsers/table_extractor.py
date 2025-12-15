
# -----------------------------
# File: table_extractor.py
# -----------------------------
"""Starter table extraction helpers.
Provides normalization and simple numeric parsing for tables.
"""

import re
from typing import List


def normalize_numeric_string(s: str) -> str:
    """Normalize numeric strings by removing commas and fixing common OCR issues.
    Returns the cleaned string (not converted to float to avoid exceptions in starter code).
    """
    if s is None:
        return ""
    s = str(s).strip()
    # common noise
    s = s.replace(',', '')
    s = s.replace('\u2013', '-')  # en-dash
    s = re.sub(r"[^0-9\.\-%kKmMtTCOae ]+", "", s)  # keep digits, ., -, %, k/M/T, units
    return s


def df_to_records(df) -> List[dict]:
    """Convert a pandas DataFrame to list of dicts using the first row as header if it looks like header.
    This is a heuristic starter approach.
    """
    import pandas as pd

    if df.shape[0] >= 2:
        # Heuristic: if first row has any non-numeric value, treat it as header
        first_row = df.iloc[0].astype(str)
        if any(re.search('[A-Za-z]', x) for x in first_row):
            headers = first_row.tolist()
            body = df.iloc[1:]
            body.columns = headers
        else:
            # fallback: create generic column names
            body = df
            body.columns = [f"col_{i}" for i in range(df.shape[1])]
    else:
        body = df
        body.columns = [f"col_{i}" for i in range(df.shape[1])]

    records = []
    for _, row in body.iterrows():
        rec = {str(c): normalize_numeric_string(row[c]) for c in body.columns}
        records.append(rec)

    return records

