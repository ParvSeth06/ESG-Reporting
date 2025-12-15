import filetype
from pathlib import Path

def detect_file_type(file_path: str):
    file_path = Path(file_path)

    if not file_path.exists():
        return {"error": "File not found"}

    # Try detecting based on binary signature
    kind = filetype.guess(file_path)

    if kind:
        return {
            "mime": kind.mime,
            "extension": kind.extension,
            "source": "binary-signature"
        }

    # Fallback to extension
    return {
        "mime": "unknown",
        "extension": file_path.suffix.replace(".", ""),
        "source": "extension-fallback"
    }

if __name__ == "__main__":
    path = r"D:\ESG-reporting\ESG-Reporting\ilovepdf_merged.pdf"
    print(detect_file_type(path))
