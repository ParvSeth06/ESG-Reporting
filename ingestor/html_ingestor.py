# html_ingestor.py
from bs4 import BeautifulSoup
from pathlib import Path

class HTMLIngestor:
    """
    Extracts text and tables from HTML.
    Returns:
        {
            "text": text_only,
            "tables": [...],
            "source_type": "html"
        }
    """

    @staticmethod
    def parse(file_path: str):
        file_path = Path(file_path)
        if not file_path.exists():
            return {"error": "HTML file not found"}

        try:
            html = file_path.read_text(encoding="utf-8", errors="ignore")
            soup = BeautifulSoup(html, "lxml")

            text = soup.get_text(separator="\n", strip=True)

            tables = []
            for table in soup.find_all("table"):
                rows = []
                for row in table.find_all("tr"):
                    cells = [cell.get_text(strip=True) for cell in row.find_all(["td", "th"])]
                    rows.append(cells)
                tables.append(rows)

            return {
                "text": text,
                "tables": tables,
                "source_type": "html"
            }

        except Exception as e:
            return {"error": f"HTML parse error: {str(e)}"}
