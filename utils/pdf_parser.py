import fitz

def extract_text_blocks_with_details(pdf_path):
    """
    Extracts text blocks along with font size, name, and page number from a PDF.
    Attempts to merge logically contiguous text spans and lines.
    """
    doc = fitz.open(pdf_path)
    all_extracted_blocks = []

    for page_num, page in enumerate(doc):
        page_blocks = page.get_text("dict")["blocks"]

        processed_page_blocks = []

        for b in page_blocks:
            if b['type'] == 0:
                current_line_text = ""
                current_line_font = ""
                current_line_size = 0.0
                current_line_bbox = [float('inf'), float('inf'), float('-inf'), float('-inf')]

                for line in b["lines"]:
                    merged_line_text = ""
                    line_spans = []
                    for span in line["spans"]:
                        span_text = span["text"].strip()
                        if not span_text:
                            continue

                        if line_spans and \
                           abs(line_spans[-1]['bbox'][2] - span['bbox'][0]) < 5 and \
                           line_spans[-1]['font'] == span['font'] and \
                           abs(line_spans[-1]['size'] - span['size']) < 0.1:
                            
                            line_spans[-1]['text'] += " " + span_text
                            line_spans[-1]['bbox'][2] = span['bbox'][2]
                            line_spans[-1]['bbox'][1] = min(line_spans[-1]['bbox'][1], span['bbox'][1])
                            line_spans[-1]['bbox'][3] = max(line_spans[-1]['bbox'][3], span['bbox'][3])
                        else:
                            line_spans.append({
                                "text": span_text,
                                "font": span["font"],
                                "size": span["size"],
                                "bbox": list(span["bbox"]),
                            })

                    if line_spans:
                        merged_line_text = " ".join([s['text'] for s in line_spans])
                        dominant_span = max(line_spans, key=lambda s: s['size'] * len(s['text'])) if line_spans else line_spans[0]
                        current_line_font = dominant_span['font']
                        current_line_size = dominant_span['size']

                        x0 = min(s['bbox'][0] for s in line_spans)
                        y0 = min(s['bbox'][1] for s in line_spans)
                        x1 = max(s['bbox'][2] for s in line_spans)
                        y1 = max(s['bbox'][3] for s in line_spans)
                        current_line_bbox = [x0, y0, x1, y1]

                        processed_page_blocks.append({
                            "text": merged_line_text,
                            "font": current_line_font,
                            "size": current_line_size,
                            "bbox": current_line_bbox,
                            "page": page_num + 1
                        })
        
        all_extracted_blocks.extend(processed_page_blocks)
    
    doc.close()
    return all_extracted_blocks