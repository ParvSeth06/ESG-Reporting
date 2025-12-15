
# -----------------------------
# File: text_cleaner.py
# -----------------------------
"""Simple text cleaning utilities.
Functions:
- clean_hyphenation(text)
- remove_headers_footers(text, header_keywords=[], footer_keywords=[])
- split_into_sections(text)
"""

import re
from typing import List


def clean_hyphenation(text: str) -> str:
    # Join words broken with hyphen at EOL: "sustainabil-\nity" -> "sustainability"
    text = re.sub(r"-\n\s*", "", text)
    # Replace line breaks within paragraphs with spaces (but preserve double newlines as paragraph breaks)
    text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)
    # Collapse many spaces
    text = re.sub(r" {2,}", " ", text)
    return text


def remove_headers_footers(text: str, header_keywords: List[str] = None, footer_keywords: List[str] = None) -> str:
    # Very lightweight: remove lines that look like page headers/footers using keywords or page number patterns
    lines = text.splitlines()
    out_lines = []
    header_keywords = header_keywords or []
    footer_keywords = footer_keywords or []

    for ln in lines:
        low = ln.strip().lower()
        if any(hk.lower() in low for hk in header_keywords):
            continue
        if any(fk.lower() in low for fk in footer_keywords):
            continue
        # remove isolated page numbers like "Page 12" or just numbers on a line
        if re.fullmatch(r"(page\s*\d+|\d{1,3})", low):
            continue
        out_lines.append(ln)

    return "\n".join(out_lines)


def split_into_sections(text: str, min_paragraph_length: int = 50) -> List[str]:
    """Split on two or more newlines and filter out tiny paragraphs."""
    paras = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]
    paras = [p for p in paras if len(p) >= min_paragraph_length]
    return paras

