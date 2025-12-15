# from document_ingestor import DocumentIngestor

# result = DocumentIngestor.load(r"D:\ESG-reporting\ESG-Reporting\ilovepdf_merged.pdf")

# print(result["saved_to"])

from document_ingestor import DocumentIngestor

# use your existing DocumentIngestor (which calls PDFIngestor.parse)
res = DocumentIngestor.load(r"D:\ESG-reporting\ESG-Reporting\reference\GRI 416 Customer Health and Safety 2016.pdf")
print("Saved to:", res.get("saved_to"))
