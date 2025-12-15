# document_ingestor.py

from pathlib import Path
from file_type import detect_file_type

# Import all ingestors
from pdf_ingestor import PDFIngestor
from docx_ingestor import DOCXIngestor
from excel_ingestor import ExcelIngestor
from html_ingestor import HTMLIngestor
from image_ocr_ingestor import ImageOCRIngestor
from ppt_ingestor import PPTIngestor


class DocumentIngestor:

    @staticmethod
    def load(file_path: str, save_text=True, output_folder="output"):
        file_path = Path(file_path)

        if not file_path.exists():
            return {"error": "File does not exist"}

        info = detect_file_type(str(file_path))

        if "extension" not in info:
            return {"error": "Could not detect file extension"}

        ext = info["extension"].lower()

        parser_map = {
            "pdf": PDFIngestor,
            "docx": DOCXIngestor,
            "xlsx": ExcelIngestor,
            "xls": ExcelIngestor,
            "html": HTMLIngestor,
            "htm": HTMLIngestor,
            "pptx": PPTIngestor,
            "png": ImageOCRIngestor,
            "jpg": ImageOCRIngestor,
            "jpeg": ImageOCRIngestor,
            "tiff": ImageOCRIngestor,
        }

        if ext not in parser_map:
            return {"error": f"Unsupported file type ({ext})"}

        parser = parser_map[ext]
        result = parser.parse(str(file_path))

        # If extraction failed, return result as-is
        if "error" in result:
            return result

        # Save extracted text to TXT file
        if save_text:
            output_dir = Path(output_folder)
            output_dir.mkdir(exist_ok=True)

            txt_path = output_dir / f"{file_path.stem}.txt"

            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(result.get("text", ""))

            result["saved_to"] = str(txt_path)

        return result
