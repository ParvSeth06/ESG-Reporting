from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTChar, LTTextLine, LTTextBox

all_text = []
for page_layout in extract_pages('reference_raw/GRI 302 Energy 2016.pdf'):
    for element in page_layout:
        if isinstance(element, LTTextContainer):
            text = element.get_text().strip()
            if text:
                all_text.append(text)

print('Total text blocks:', len(all_text))
for i, text in enumerate(all_text):
    print(f'Block {i}: {repr(text)}')
    if 'Disclosure' in text:
        print(f'Found Disclosure in block {i}')
        break
