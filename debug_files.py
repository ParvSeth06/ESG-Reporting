import pdfplumber

pdf_path = "reference_raw/GRI 202 Market Presence 2016.pdf"  # change if needed

with pdfplumber.open(pdf_path) as pdf:
    page = pdf.pages[0]  # first page has bold headings
    
    words = page.extract_words(extra_attrs=["fontname", "size"])
    
    print("=== UNIQUE FONT NAMES USED ON PAGE 1 ===")
    fonts = set()
    for w in words:
        fonts.add(w["fontname"])
    for f in sorted(fonts):
        print(f)
    
    print("\n=== SAMPLE EXTRACTED WORDS WITH FONT ===")
    for w in words[:40]:
        print(f"{w['text']:<25} | {w['fontname']} | size={w['size']}")
