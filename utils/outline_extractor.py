# utils/outline_extractor.py

import re
from collections import Counter

def is_bold(font_name):
    """Simple heuristic to check if a font name indicates bold."""
    return "bold" in font_name.lower() or "black" in font_name.lower() or "heavy" in font_name.lower()

def is_all_caps(text):
    """Check if text is all uppercase (often used for headings)."""
    return text.isupper() and len(text) > 1

def calculate_indentation(bbox, page_width_avg):
    """Calculates indentation as a percentage of page width (approx)."""
    return (bbox[0] / page_width_avg) * 100 

def identify_outline(blocks):
    """
    Identifies the title and hierarchical headings (H1, H2, H3) using refined heuristics.
    This version includes better filtering for noise, improved title detection,
    and more robust heading classification based on size, style, position, and numbering.
    """
    title = ""
    outline_items = []

    if not blocks:
        return {"title": "", "outline": []}

    page_width_avg = 595
    filtered_blocks = []
    page_heights = {}
    for block in blocks:
        text = block['text'].strip()
        size = block['size']
        font = block['font']
        page_num = block['page']
        bbox = block['bbox']

        if page_num not in page_heights:
            page_heights[page_num] = 842
        if len(text) < 3 and not text.isdigit():
            continue
        if re.match(r'^[A-Z]{1,3}:$', text) and len(text) < 6:
            continue
        if re.fullmatch(r'-+', text):
            continue
        if text.lower() in ["version", "page"]:
            continue
        if text.strip().isdigit() and (bbox[1] < 100 or bbox[3] > page_heights[page_num] - 50):
             continue

        filtered_blocks.append(block)

    if not filtered_blocks:
        return {"title": "", "outline": []}

    size_counts = Counter(b['size'] for b in filtered_blocks if 8 <= b['size'] <= 16)
    body_text_size = None
    if size_counts:
        body_text_size = max(size_counts, key=size_counts.get)
    elif filtered_blocks:
        body_text_size = max(Counter(b['size'] for b in filtered_blocks), key=Counter(b['size'] for b in filtered_blocks).get)
    else:
        body_text_size = 10

    H1_SIZE_THRESHOLD = body_text_size * 2.0 if body_text_size else 20
    H2_SIZE_THRESHOLD = body_text_size * 1.5 if body_text_size else 15
    H3_SIZE_THRESHOLD = body_text_size * 1.2 if body_text_size else 12

    potential_titles = []
    for block in filtered_blocks:
        if block['page'] == 1:
            text = block['text'].strip()
            size = block['size']
            bbox = block['bbox']
            
            score = 0
            if size > (body_text_size * 2.5 if body_text_size else 24):
                score += 10
            if bbox[1] < 300:
                score += 5
            if is_bold(block['font']):
                score += 3
            if len(text) > 15 and not text.strip().isdigit() and not re.match(r'^\s*(\d+(\.\d+)*|[A-Z])\.\s+', text):
                score += 2

            if score > 10:
                potential_titles.append((score, text, size))
    
    if potential_titles:
        potential_titles.sort(key=lambda x: (-x[0], -x[2], x[1]))
        title = potential_titles[0][1]
    
    last_added_heading_page = -1
    last_added_heading_y = -1

    header_footer_candidates = {}

    for i, block in enumerate(filtered_blocks):
        text = block['text'].strip()
        page = block['page']
        bbox = block['bbox']

        page_h = page_heights.get(page, 842)
        
        if bbox[1] < 0.1 * page_h:
            y_range = "top"
        elif bbox[3] > 0.9 * page_h:
            y_range = "bottom"
        else:
            y_range = None

        if y_range:
            key = (text, y_range)
            header_footer_candidates[key] = header_footer_candidates.get(key, 0) + 1
    
    num_pages = len(set(b['page'] for b in blocks))
    frequent_headers_footers = set()
    for (text, y_range), count in header_footer_candidates.items():
        if count >= num_pages * 0.5:
            frequent_headers_footers.add(text)

    current_h1_obj = None
    current_h2_obj = None

    for block in filtered_blocks:
        text = block['text'].strip()
        size = block['size']
        font = block['font']
        page = block['page']
        bbox = block['bbox']

        if text == title and page == 1:
            continue
        if text in frequent_headers_footers:
            continue

        if len(text) < 4 and not re.match(r'^\d+(\.\d+)?$', text):
            continue
        if re.match(r'^\s*(\d+(\.\d+)*)\s*$', text):
            continue
        if text.endswith(":") and len(text) < 20 and not (is_bold(font) and size > body_text_size * 1.05):
            continue

        level = None
        
        starts_with_num_pattern = re.match(r'^\s*(\d+(\.\d+)*)\s+(.*)', text)
        
        if starts_with_num_pattern:
            num_part = starts_with_num_pattern.group(1)
            text_without_num = starts_with_num_pattern.group(3).strip()
            num_dots = num_part.count('.') + 1

            if num_dots == 1: level = "H1"
            elif num_dots == 2: level = "H2"
            elif num_dots == 3: level = "H3"
            
            text = text_without_num

            if level == "H1" and size < H1_SIZE_THRESHOLD / 1.5: level = None
            elif level == "H2" and size < H2_SIZE_THRESHOLD / 1.5: level = None
            elif level == "H3" and size < H3_SIZE_THRESHOLD / 1.5: level = None

        if not level:
            if is_bold(font):
                if size >= H1_SIZE_THRESHOLD:
                    level = "H1"
                elif size >= H2_SIZE_THRESHOLD:
                    level = "H2"
                elif size >= H3_SIZE_THRESHOLD:
                    level = "H3"
            elif is_all_caps(text) and len(text) > 5 and size > body_text_size:
                if size >= H1_SIZE_THRESHOLD * 0.8: level = "H1"
                elif size >= H2_SIZE_THRESHOLD * 0.8: level = "H2"
                elif size >= H3_SIZE_THRESHOLD * 0.8: level = "H3"


        if level:
            if outline_items and outline_items[-1]['level'] == level and outline_items[-1]['page'] == page:
                prev_bbox = outline_items[-1]['bbox']
                if abs(bbox[1] - prev_bbox[3]) < (size * 1.5):
                    if abs(bbox[0] - prev_bbox[0]) < 10:
                        outline_items[-1]['text'] += " " + text
                        outline_items[-1]['bbox'][2] = bbox[2]
                        outline_items[-1]['bbox'][3] = bbox[3]

            if level == "H1":
                current_h1_obj = {"level": "H1", "text": text, "page": page, "bbox": bbox}
                current_h2_obj = None
            elif level == "H2":
                if current_h1_obj is None:
                    level = "H1"
                    current_h1_obj = {"level": "H1", "text": text, "page": page, "bbox": bbox}
                    current_h2_obj = None
                else:
                    current_h2_obj = {"level": "H2", "text": text, "page": page, "bbox": bbox}
            elif level == "H3":
                if current_h2_obj is None:
                    if current_h1_obj is None:
                        level = "H1"
                        current_h1_obj = {"level": "H1", "text": text, "page": page, "bbox": bbox}
                    else:
                        level = "H2"
                    current_h2_obj = {"level": level, "text": text, "page": page, "bbox": bbox}
                
            
            outline_items.append({
                "level": level,
                "text": text,
                "page": page,
                "bbox": bbox
            })

    final_outline = []
    seen_headings = set()
    for item in outline_items:
        clean_item = {k: v for k, v in item.items() if k != 'bbox'}
        clean_item['text'] = clean_item['text'].strip()

        if len(clean_item['text']) < 5 and not re.match(r'^\d+(\.\d+)*\s*$', clean_item['text']):
            continue
        item_tuple = (clean_item['level'], clean_item['text'], clean_item['page'])
        if item_tuple not in seen_headings:
            final_outline.append(clean_item)
            seen_headings.add(item_tuple)
            
    return {"title": title, "outline": final_outline}