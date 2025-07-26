import fitz
import re

def extract_text_blocks_with_details(pdf_path):
    """
    Extracts text blocks (lines) along with font size, name, and page number from a PDF.
    Focuses on reliable line extraction and initial span merging.
    """
    doc = fitz.open(pdf_path)
    all_extracted_lines = []

    for page_num, page in enumerate(doc):
        page_dict = page.get_text("dict")
        sorted_raw_blocks = sorted(page_dict["blocks"], key=lambda b: b["bbox"][1])

        for b_raw in sorted_raw_blocks:
            if b_raw['type'] == 0:
                for l_raw in sorted(b_raw["lines"], key=lambda l: l["bbox"][1]):
                    merged_spans = []
                    for s_raw in sorted(l_raw["spans"], key=lambda s: s["bbox"][0]):
                        span_text = s_raw["text"]
                        if not span_text.strip(): continue

                        if merged_spans and \
                           s_raw['bbox'][0] - merged_spans[-1]['bbox'][2] < 3 and \
                           abs(s_raw['size'] - merged_spans[-1]['size']) < 0.1 and \
                           s_raw['font'] == merged_spans[-1]['font']:
                            
                            merged_spans[-1]['text'] += span_text
                            merged_spans[-1]['bbox'][2] = s_raw['bbox'][2]
                            merged_spans[-1]['bbox'][1] = min(merged_spans[-1]['bbox'][1], s_raw['bbox'][1])
                            merged_spans[-1]['bbox'][3] = max(merged_spans[-1]['bbox'][3], s_raw['bbox'][3])
                        else:
                            merged_spans.append({
                                "text": span_text,
                                "font": s_raw["font"],
                                "size": s_raw["size"],
                                "bbox": list(s_raw["bbox"]),
                            })
                    
                    if merged_spans:
                        line_text = "".join([s['text'] for s in merged_spans]).strip()
                        line_text = re.sub(r'(.)\1{3,}', r'\1', line_text)
                        line_text = re.sub(r'\s+', ' ', line_text).strip()
                        
                        if not line_text: continue

                        dominant_span = max(merged_spans, key=lambda s: s['size'] * len(s['text']))
                        
                        line_x0 = min(s['bbox'][0] for s in merged_spans)
                        line_y0 = min(s['bbox'][1] for s in merged_spans)
                        line_x1 = max(s['bbox'][2] for s in merged_spans)
                        line_y1 = max(s['bbox'][3] for s in merged_spans)

                        all_extracted_lines.append({
                            "text": line_text,
                            "font": dominant_span['font'],
                            "size": dominant_span['size'],
                            "bbox": [line_x0, line_y0, line_x1, line_y1],
                            "page": page_num + 1
                        })
    
    doc.close()
    return all_extracted_lines