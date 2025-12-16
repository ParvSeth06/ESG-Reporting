# clean_text.py

import re
import unicodedata
from pathlib import Path


class TextCleaner:

    @staticmethod
    def load_text(file_path: str) -> str:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    @staticmethod
    def save_text(text: str, output_path: str):
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)

    @staticmethod
    def normalize_unicode(text: str) -> str:
        return unicodedata.normalize("NFKC", text)

    @staticmethod
    def remove_page_markers(text: str) -> str:
        # Remove lines that ONLY contain digits (page numbers)
        return re.sub(r"\n\s*\d+\s*\n", "\n", text)

    @staticmethod
    def remove_headers_footers(text: str) -> str:
        # Removes repeating header/footer patterns page-by-page
        lines = text.split("\n")
        freq = {}

        # Count occurrences
        for line in lines:
            cleaned = line.strip()
            if cleaned:
                freq[cleaned] = freq.get(cleaned, 0) + 1

        # Detect header/footer: repeated in > 30% pages
        threshold = max(10, int(len(lines) * 0.3))
        remove_lines = {line for line, count in freq.items() if count > threshold}

        return "\n".join(line for line in lines if line.strip() not in remove_lines)

    @staticmethod
    def fix_broken_sentences(text: str) -> str:
        # Fix "This is a sentence\nthat continues" → "This is a sentence that continues"
        return re.sub(r"(?<!\.|\?|!)\n(?=[a-zA-Z0-9])", " ", text)

    @staticmethod
    def fix_hyphens(text: str) -> str:
        # Fix hyphen splits across lines: "envi-\nronment" → "environment"
        text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)
        return text

    @staticmethod
    def remove_multiple_newlines(text: str) -> str:
        return re.sub(r"\n{2,}", "\n\n", text)

    @staticmethod
    def remove_multiple_spaces(text: str) -> str:
        return re.sub(r"[ \t]{2,}", " ", text)

    @staticmethod
    def remove_bullet_junk(text: str) -> str:
        # Normalize bullet points
        text = re.sub(r"[●•◦▪]", "-", text)  # Convert bullets → hyphens
        text = re.sub(r"\n\s*[-*]\s*\n", "\n", text)  # Remove empty bullets
        return text

    @staticmethod
    def remove_non_text_symbols(text: str) -> str:
        # Remove junk unicode symbols commonly found in PDFs
        text = re.sub(r"[^\x00-\x7F]+", " ", text)
        return text

    @staticmethod
    def dedupe_lines(text: str) -> str:
        seen = set()
        output = []
        for line in text.split("\n"):
            striped = line.strip()
            if striped and striped not in seen:
                seen.add(striped)
                output.append(line)
        return "\n".join(output)

    @staticmethod
    def clean(file_path: str, output_path: str = None):
        raw_text = TextCleaner.load_text(file_path)

        text = raw_text
        text = TextCleaner.normalize_unicode(text)
        text = TextCleaner.remove_page_markers(text)
        text = TextCleaner.remove_headers_footers(text)
        text = TextCleaner.fix_hyphens(text)
        text = TextCleaner.fix_broken_sentences(text)
        text = TextCleaner.remove_bullet_junk(text)
        text = TextCleaner.remove_non_text_symbols(text)
        text = TextCleaner.remove_multiple_spaces(text)
        text = TextCleaner.remove_multiple_newlines(text)
        text = TextCleaner.dedupe_lines(text)

        if not output_path:
            output_path = str(Path(file_path).with_name(Path(file_path).stem + "_clean.txt"))

        TextCleaner.save_text(text, output_path)

        return output_path


if __name__ == "__main__":
    input_file =r"ingestor/output/ilovepdf_merged.txt"
    cleaned_file = TextCleaner.clean(input_file)
    print("Cleaned text saved to:", cleaned_file)
