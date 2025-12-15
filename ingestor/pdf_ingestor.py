# pdf_ingestor.py
import os
import io
from pathlib import Path
import pdfplumber
import camelot
from pdf2image import convert_from_path
from PIL import Image
import pytesseract
import pandas as pd
import math
from typing import List, Tuple
import numpy as np
from sklearn.cluster import KMeans

# Utility: group words into lines by y coordinate
def words_to_text(words: List[dict], y_tolerance: float = 3.0) -> str:
    """
    words: list of dicts having 'text', 'x0','top','x1','bottom'
    returns reconstructed text grouped by approximate lines.
    """
    if not words:
        return ""

    # sort by top then x0
    words_sorted = sorted(words, key=lambda w: (round(w["top"] / y_tolerance), w["x0"]))
    lines = []
    current_line_key = None
    current_line_words = []

    for w in words_sorted:
        key = round(w["top"] / y_tolerance)
        if current_line_key is None:
            current_line_key = key
            current_line_words = [w["text"]]
        elif key == current_line_key:
            current_line_words.append(w["text"])
        else:
            lines.append(" ".join(current_line_words))
            current_line_key = key
            current_line_words = [w["text"]]

    if current_line_words:
        lines.append(" ".join(current_line_words))

    return "\n".join(lines)


def bbox_contains(bbox: Tuple[float, float, float, float], word_bbox: Tuple[float, float, float, float]) -> bool:
    """Return True if word_bbox center is inside bbox"""
    x0, top, x1, bottom = bbox
    wx0, wtop, wx1, wbottom = word_bbox
    cx = (wx0 + wx1) / 2.0
    cy = (wtop + wbottom) / 2.0
    return (cx >= x0 and cx <= x1 and cy >= top and cy <= bottom)


class PDFIngestor:

    @staticmethod
    def extract_tables_markdown(pdf_path: str) -> Tuple[str, List[pd.DataFrame]]:
        """
        Use Camelot to extract tables. Try stream first (good for no border tables),
        then lattice. Return Markdown string and list of DataFrames.
        """
        md_output = ""
        dfs = []

        # Try to extract with stream on all pages
        try:
            tables_stream = camelot.read_pdf(pdf_path, pages="all", flavor="stream", strip_text='\n')
        except Exception:
            tables_stream = []

        # If stream found nothing, try lattice
        if len(tables_stream) == 0:
            try:
                tables_stream = camelot.read_pdf(pdf_path, pages="all", flavor="lattice", strip_text='\n')
            except Exception:
                tables_stream = []

        # Convert found tables to markdown
        if len(tables_stream) > 0:
            md_output += "\n\n=== EXTRACTED TABLES ===\n\n"
            for i, table in enumerate(tables_stream):
                try:
                    df = table.df.copy()
                    # Clean multi-line cells: replace \n with space
                    df = df.applymap(lambda x: str(x).replace("\n", " ").strip())
                    dfs.append(df)
                    md_output += f"\nTable {i+1}:\n"
                    # Use pandas to_markdown if available, fallback to CSV-like
                    try:
                        md_output += df.to_markdown(index=False) + "\n\n"
                    except Exception:
                        md_output += df.to_csv(index=False, sep="\t") + "\n\n"
                except Exception:
                    continue

        return md_output, dfs

    @staticmethod
    def extract_text_excluding_table_regions(pdf_path: str) -> str:
        """
        Use pdfplumber to extract words and exclude words that fall inside table bbox
        detected by pdfplumber's table detection (page.find_tables()).
        This reduces merging of table content into paragraph text.
        """
        out_text = []
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                # detect table bboxes on this page using pdfplumber's table finder
                table_bboxes = []
                try:
                    for table in page.find_tables():
                        # table.bbox is (x0, top, x1, bottom)
                        table_bboxes.append(table.bbox)
                except Exception:
                    table_bboxes = []

                # extract words (gives positions)
                words = page.extract_words(x_tolerance=3, y_tolerance=3)
                # filter out words inside any table bbox
                filtered_words = []
                for w in words:
                    w_bbox = (float(w.get("x0")), float(w.get("top")), float(w.get("x1")), float(w.get("bottom")))
                    inside_table = False
                    for tb in table_bboxes:
                        if bbox_contains(tb, w_bbox):
                            inside_table = True
                            break
                    if not inside_table:
                        filtered_words.append(w)

                page_text = words_to_text(filtered_words, y_tolerance=3.0)
                if page_text.strip():
                    out_text.append(page_text.strip())
                else:
                    # if page has no text (or very little), append empty marker
                    out_text.append("")

        return "\n\n".join([p for p in out_text if p.strip()])

    @staticmethod
    def pages_need_ocr(pdf_path: str) -> List[int]:
        """
        Heuristic: identify pages that include images or have very few words -> OCR them.
        Returns list of page indices (1-based) that should be OCR'd.
        """
        ocr_pages = []
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages, start=1):
                # if page contains images -> consider OCR
                has_image = False
                try:
                    if page.images and len(page.images) > 0:
                        has_image = True
                except Exception:
                    has_image = False

                # count words
                words = page.extract_words(x_tolerance=3, y_tolerance=3)
                num_words = len(words) if words else 0

                # heuristic thresholds
                if has_image or num_words < 30:
                    ocr_pages.append(i)
        return ocr_pages

    @staticmethod
    def extract_ocr_from_pages(pdf_path: str, pages: List[int]) -> str:
        """
        Convert specified pages to images and run Tesseract OCR on them.
        pages: list of 1-based page numbers
        """
        if not pages:
            return ""

        # convert only specified pages
        ocr_text = "\n\n=== OCR TEXT ===\n\n"
        try:
            images = convert_from_path(pdf_path, dpi=300, first_page=min(pages), last_page=max(pages))
        except Exception as e:
            # fallback: convert all pages
            try:
                images = convert_from_path(pdf_path, dpi=300)
            except Exception:
                return ""

        # images list corresponds to pages from first_page..last_page - handle mapping
        # safer approach: convert full and map by index
        all_images = convert_from_path(pdf_path, dpi=300)
        for idx in pages:
            img = all_images[idx - 1]  # 0-based index
            # optional pre-processing - convert to grayscale
            img_gray = img.convert("L")
            text = pytesseract.image_to_string(img_gray)
            ocr_text += f"\n--- OCR Page {idx} ---\n{text}\n"

        return ocr_text
    @staticmethod
    def extract_soft_tables(pdf_path):
        """
        Detects soft-boundary tables using keyword detection + auto column detection.
        Returns list of DataFrames.
        """

        import pdfplumber
        import camelot

        KEYWORDS = [
            "Number of independent Board members",
            "Number of females on Board",
            "Number of nationalities on Board",
            "Board composition by average tenure",
            "Board composition by average age",
            "Board members’ average attendance"
        ]

        dfs = []

        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):

                text = page.extract_text() or ""
                if not any(k in text for k in KEYWORDS):
                    continue  # skip irrelevant pages

                # --- Step 1: get all words (with x positions) ---
                words = page.extract_words()
                xs = sorted([float(w["x0"]) for w in words])

                # --- Step 2: cluster x positions into 4 groups (Metrics + 2024 + 2023 + 2022)
                xs_arr = np.array(xs).reshape(-1, 1)
                from sklearn.cluster import KMeans
                kmeans = KMeans(n_clusters=4, n_init="auto").fit(xs_arr)
                centers = sorted([c[0] for c in kmeans.cluster_centers_])

                # Convert these cluster centers into column boundaries
                col_positions = ",".join([str(round(c, 1)) for c in centers])

                # --- Step 3: run Camelot stream with detected columns ---
                try:
                    tables = camelot.read_pdf(
                        pdf_path,
                        pages=str(page_num),
                        flavor="stream",
                        columns=col_positions,
                        row_tol=10,
                        column_tol=10
                    )
                    for t in tables:
                        dfs.append(t.df)
                except:
                    pass

        return dfs
    @staticmethod
    def parse(file_path: str):
        """
        Main parse function used by DocumentIngestor.
        Returns dict: {"text": ..., "tables": <list of markdowns joined>, "tables_dfs": [DataFrames], "ocr_used": bool}
        """
        try:
            fp = Path(file_path)
            if not fp.exists():
                return {"error": "File not found"}

            # 1) Extract tables with Camelot (stream preferred)
            table_dfs_soft = PDFIngestor.extract_soft_tables(file_path)
            table_md = ""
            table_dfs = []

            # convert soft-extracted tables
            for df in table_dfs_soft:
                df = df.applymap(lambda x: str(x).strip())
                table_dfs.append(df)
                table_md += df.to_markdown(index=False) + "\n\n"

            # fallback to regular Camelot if soft detection fails
            if not table_dfs:
                table_md, table_dfs = PDFIngestor.extract_tables_markdown(file_path)

            # 2) Extract page text excluding detected table areas
            plain_text = PDFIngestor.extract_text_excluding_table_regions(file_path)

            # 3) Decide which pages need OCR (images or too few words) then OCR those pages
            ocr_pages = PDFIngestor.pages_need_ocr(file_path)
            ocr_text = PDFIngestor.extract_ocr_from_pages(file_path, ocr_pages) if ocr_pages else ""

            # 4) Combine: plain text + table_md + ocr_text
            final_text_parts = []
            if plain_text.strip():
                final_text_parts.append(plain_text.strip())
            if table_md.strip():
                final_text_parts.append(table_md.strip())
            if ocr_text.strip():
                final_text_parts.append(ocr_text.strip())

            final_text = "\n\n".join(final_text_parts)

            return {
                "text": final_text,
                "tables": table_md,
                "tables_dfs": table_dfs,
                "ocr_used": bool(ocr_text.strip())
            }

        except Exception as e:
            return {"error": str(e)}
