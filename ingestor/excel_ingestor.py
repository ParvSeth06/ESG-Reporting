# excel_ingestor.py
import pandas as pd
from pathlib import Path

class ExcelIngestor:
    """
    Extracts all sheets as dataframes + converts to text for LLM usage.
    Returns:
        {
            "sheets": {sheet_name: df},
            "text": "sheet descriptions",
            "source_type": "excel"
        }
    """

    @staticmethod
    def parse(file_path: str):
        file_path = Path(file_path)
        if not file_path.exists():
            return {"error": "Excel file not found"}

        try:
            xl = pd.ExcelFile(file_path)
            sheets = {}

            sheet_texts = []

            for sheet in xl.sheet_names:
                df = xl.parse(sheet)
                sheets[sheet] = df

                sheet_texts.append(
                    f"\n### Sheet: {sheet}\n" + df.to_string(index=False)
                )

            return {
                "sheets": sheets,
                "text": "\n".join(sheet_texts),
                "source_type": "excel"
            }

        except Exception as e:
            return {"error": f"Excel parse error: {str(e)}"}
