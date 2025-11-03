import re
from pdfminer.high_level import extract_pages , extract_text
import tabula
text = extract_text("table.pdf")
#print(text)

tables = tabula.read_pdf("table_pic.pdf", pages='all', multiple_tables=True, lattice=True)
print(tables)
