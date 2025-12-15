# image_ocr_ingestor.py
import pytesseract
from PIL import Image
from pathlib import Path

class ImageOCRIngestor:
    """
    Extracts text from images using Tesseract OCR.
    Works for PNG, JPG, JPEG, TIFF.
    """

    @staticmethod
    def parse(file_path: str):
        file_path = Path(file_path)
        if not file_path.exists():
            return {"error": "Image file not found"}

        try:
            img = Image.open(file_path)
            text = pytesseract.image_to_string(img)

            return {
                "text": text,
                "source_type": "image_ocr"
            }

        except Exception as e:
            return {"error": f"OCR parse error: {str(e)}"}
