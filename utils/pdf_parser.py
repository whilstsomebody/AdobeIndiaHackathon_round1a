from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTTextLine, LTChar

def extract_pdf_elements(pdf_path):
    elements = []

    for page_number, layout in enumerate(extract_pages(pdf_path), start=1):
        for element in layout:
            if isinstance(element, LTTextContainer):
                text = element.get_text().strip()
                font_sizes = []

                for line in element:
                    if isinstance(line, LTTextLine):
                        for char in line:
                            if isinstance(char, LTChar):
                                font_sizes.append(char.size)

                avg_size = sum(font_sizes) / len(font_sizes) if font_sizes else 0

                elements.append({
                    "text": text,
                    "size": avg_size,
                    "x0": element.x0,
                    "x1": element.x1,
                    "y0": element.y0,
                    "page": page_number,
                })

    return elements
