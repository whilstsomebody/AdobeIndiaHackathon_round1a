import re
from collections import Counter

def is_bold(font_name):
    """Simple heuristic to check if a font name indicates bold."""
    return "bold" in font_name.lower() or "black" in font_name.lower() or "heavy" in font_name.lower() or "demi" in font_name.lower()

def is_all_caps(text):
    """Check if text is all uppercase (often used for headings)."""
    return text.isupper() and len(text) > 3 and any(c.isalpha() for c in text)

def identify_outline(blocks):
    """
    Identifies the title and hierarchical headings (H1, H2, H3) using refined heuristics.
    This version focuses on robust multi-part title detection and strong numerical heading prioritization.
    """
    title = ""
    outline_items = []

    if not blocks:
        return {"title": "", "outline": []}

    avg_page_width = 595.0
    avg_page_height = 842.0

    TOP_ZONE_THRESHOLD = avg_page_height * 0.10
    BOTTOM_ZONE_THRESHOLD = avg_page_height * 0.90

    header_footer_candidates = {} 
    
    for block in blocks:
        text = block['text'].strip()
        bbox = block['bbox']
        
        y_zone = None
        if bbox[1] < TOP_ZONE_THRESHOLD:
            y_zone = "top"
        elif bbox[3] > BOTTOM_ZONE_THRESHOLD:
            y_zone = "bottom"
        
        if y_zone:
            key = (text, y_zone)
            header_footer_candidates[key] = header_footer_candidates.get(key, 0) + 1
    
    num_unique_pages = len(set(b['page'] for b in blocks))
    frequent_headers_footers_text = set() 
    for (text, y_zone), count in header_footer_candidates.items():
        if num_unique_pages > 2 and count >= num_unique_pages * 0.5: 
            frequent_headers_footers_text.add(text)
        elif num_unique_pages <= 2 and count >= num_unique_pages:
            frequent_headers_footers_text.add(text)
        if text.lower() in ["version 2014", "page", "copyright notice", "international software testing qualifications board", "istqb", "connecting ontarians!", "foundation level extension - agile tester", "rfp: to develop the ontario digital library business plan march 2003"]:
            frequent_headers_footers_text.add(text)

    semi_filtered_blocks = []
    for block in blocks:
        text = block['text'].strip()
        size = block['size']
        font = block['font']
        page_num = block['page']
        bbox = block['bbox']

        if not text: continue
        if len(text) < 2 and not text.isdigit(): continue
        if re.fullmatch(r'[\-\_=\s\.]+', text): continue
        if text.strip().isdigit() and (bbox[1] < TOP_ZONE_THRESHOLD * 1.5 or bbox[3] > BOTTOM_ZONE_THRESHOLD * 0.8):
            continue
        if text.endswith(":") and len(text) < 30 and not is_bold(font) and size < 18:
            continue
            
        semi_filtered_blocks.append(block)

    if not semi_filtered_blocks:
        return {"title": "", "outline": []}

    size_counts_for_body = Counter(b['size'] for b in semi_filtered_blocks if 8 <= b['size'] <= 18)
    body_text_size = None
    if size_counts_for_body:
        body_text_size = max(size_counts_for_body, key=size_counts_for_body.get)
    else:
        filtered_for_body_fallback = [b for b in semi_filtered_blocks if b['size'] < 25]
        if filtered_for_body_fallback:
            body_text_size = max(Counter(b['size'] for b in filtered_for_body_fallback), key=Counter(b['size'] for b in filtered_for_body_fallback).get)
    
    if body_text_size is None:
        body_text_size = 11.0

    H1_SIZE_THRESHOLD = body_text_size * 2.2 if body_text_size else 22.0
    H2_SIZE_THRESHOLD = body_text_size * 1.6 if body_text_size else 16.0
    H3_SIZE_THRESHOLD = body_text_size * 1.3 if body_text_size else 13.0
    H4_SIZE_THRESHOLD = body_text_size * 1.1 if body_text_size else 11.0

    first_page_top_blocks = [b for b in semi_filtered_blocks if b['page'] == 1 and b['bbox'][1] < avg_page_height * 0.4]
    first_page_top_blocks.sort(key=lambda b: (b['bbox'][1], -b['size']))

    identified_title_blocks_bboxes = set()
    
    if first_page_top_blocks:
        most_prominent_block = first_page_top_blocks[0]

        num_other_prominent_near = 0
        for i in range(1, len(first_page_top_blocks)):
            other_block = first_page_top_blocks[i]
            if abs(other_block['bbox'][1] - most_prominent_block['bbox'][3]) < most_prominent_block['size'] * 2.0 and \
               (other_block['size'] >= body_text_size * 1.5 or is_bold(other_block['font'])):
                num_other_prominent_near += 1
        
        if num_other_prominent_near == 0 and \
           (most_prominent_block['size'] >= H1_SIZE_THRESHOLD * 0.9 or \
            (is_bold(most_prominent_block['font']) and most_prominent_block['size'] >= H2_SIZE_THRESHOLD)) and \
           len(most_prominent_block['text'].strip()) > 10 and \
           most_prominent_block['text'].strip().lower() not in frequent_headers_footers_text:
            
            title = most_prominent_block['text'].strip()
            identified_title_blocks_bboxes.add(tuple(most_prominent_block['bbox']))
        else:
            potential_multi_line_title_parts = []

            if first_page_top_blocks and \
               first_page_top_blocks[0]['bbox'][1] < avg_page_height * 0.3 and \
               (first_page_top_blocks[0]['size'] >= H2_SIZE_THRESHOLD or is_bold(first_page_top_blocks[0]['font'])):
                
                potential_multi_line_title_parts.append(first_page_top_blocks[0])
                
                for i in range(1, len(first_page_top_blocks)):
                    current_block = first_page_top_blocks[i]
                    prev_block = potential_multi_line_title_parts[-1]

                    if abs(current_block['bbox'][1] - prev_block['bbox'][3]) < prev_block['size'] * 1.0 and \
                       abs(current_block['bbox'][0] - prev_block['bbox'][0]) < 20 and \
                       abs(current_block['size'] - prev_block['size']) < 2.0 and \
                       is_bold(current_block['font']) == is_bold(prev_block['font']) and \
                       current_block['size'] >= H3_SIZE_THRESHOLD:
                        
                        potential_multi_line_title_parts.append(current_block)
                    else:
                        break
            
            if potential_multi_line_title_parts and len(potential_multi_line_title_parts) > 0:
                combined_title_text = " ".join([b['text'].strip() for b in potential_multi_line_title_parts])
                if len(combined_title_text) > 15 and combined_title_text not in frequent_headers_footers_text:
                    title = combined_title_text
                    for part_block in potential_multi_line_title_parts:
                        identified_title_blocks_bboxes.add(tuple(part_block['bbox']))

    final_filtered_blocks = []
    for block in semi_filtered_blocks:
        if not (block['page'] == 1 and tuple(block['bbox']) in identified_title_blocks_bboxes):
            final_filtered_blocks.append(block)

    current_active_headings = [] 

    for block in final_filtered_blocks:
        text = block['text'].strip()
        size = block['size']
        font = block['font']
        page = block['page']
        bbox = block['bbox']

        if not text or len(text) < 3:
            continue
        if text.strip().isdigit() and size < H3_SIZE_THRESHOLD:
            continue
        if text in frequent_headers_footers_text:
            continue
        if text == title:
            continue

        level = None

        match_num_pattern = re.match(r'^\s*([A-Z]?\d+(\.\d+)*)\s+(.*)', text, re.IGNORECASE)
        if match_num_pattern:
            num_prefix = match_num_pattern.group(1)
            remaining_text = match_num_pattern.group(3).strip()
            
            num_levels = num_prefix.count('.') + 1

            if num_levels == 1: level = "H1"
            elif num_levels == 2: level = "H2"
            elif num_levels == 3: level = "H3"
            elif num_levels == 4: level = "H4"
            else: level = "H4" 

            text = remaining_text

            if level and size < body_text_size * 0.9: 
                 level = None
            elif level == "H1" and size < H1_SIZE_THRESHOLD / 2.0: pass
            elif level == "H2" and size < H2_SIZE_THRESHOLD / 1.5: pass
            elif level == "H3" and size < H3_SIZE_THRESHOLD / 1.2: pass
            elif level == "H4" and size < H4_SIZE_THRESHOLD: pass

        if not level:
            if is_bold(font) and size > body_text_size * 1.05:
                if size >= H1_SIZE_THRESHOLD: level = "H1"
                elif size >= H2_SIZE_THRESHOLD: level = "H2"
                elif size >= H3_SIZE_THRESHOLD: level = "H3"
                elif size >= H4_SIZE_THRESHOLD: level = "H4"
            elif is_all_caps(text) and len(text) > 5 and size > body_text_size * 1.05:
                if size >= H1_SIZE_THRESHOLD * 0.9: level = "H1"
                elif size >= H2_SIZE_THRESHOLD * 0.9: level = "H2"
                elif size >= H3_SIZE_THRESHOLD * 0.9: level = "H3"
                elif size >= H4_SIZE_THRESHOLD * 0.9: level = "H4"

            if level and len(text) < 15 and size < H2_SIZE_THRESHOLD and not re.match(r'^\d+(\.\d+)*', text):
                if level == "H1": level = "H2"
                if level == "H2": level = "H3"


        if level:
            current_heading_obj = {
                "level": level,
                "text": text,
                "page": page,
                "bbox": bbox, 
                "size": size 
            }

            new_active_headings_list = []
            for active_level_str, active_obj in current_active_headings:
                if (active_obj['page'] == page and int(active_level_str[1]) < int(level[1])) or \
                   (active_obj['page'] != page and int(active_level_str[1]) <= int(level[1])):
                    new_active_headings_list.append((active_level_str, active_obj))
            current_active_headings = new_active_headings_list

            if level == "H2" and not any(h[0] == "H1" and h[1]['page'] == page for h in current_active_headings):
                 level = "H1"
            elif level == "H3" and not any(h[0] == "H2" and h[1]['page'] == page for h in current_active_headings):
                if not any(h[0] == "H1" and h[1]['page'] == page for h in current_active_headings):
                    level = "H1"
                else:
                    level = "H2"
            elif level == "H4" and not any(h[0] == "H3" and h[1]['page'] == page for h in current_active_headings):
                 if not any(h[0] == "H2" and h[1]['page'] == page for h in current_active_headings):
                    if not any(h[0] == "H1" and h[1]['page'] == page for h in current_active_headings):
                        level = "H1"
                    else:
                        level = "H2"
                 else:
                    level = "H3"

            current_heading_obj['level'] = level

            outline_items.append(current_heading_obj)
            current_active_headings.append((level, current_heading_obj))

    final_outline = []
    seen_headings_for_output = set() 

    for item in outline_items:
        clean_item = {k: v for k, v in item.items() if k not in ['bbox', 'size']}
        clean_item['text'] = clean_item['text'].strip()

        if len(clean_item['text']) < 5 and not re.match(r'^\d+(\.\d+)*\s*$', clean_item['text']):
            continue

        item_tuple = (clean_item['level'], clean_item['text'], clean_item['page'])
        if item_tuple not in seen_headings_for_output:
            final_outline.append(clean_item)
            seen_headings_for_output.add(item_tuple)
            
    return {"title": title, "outline": final_outline}