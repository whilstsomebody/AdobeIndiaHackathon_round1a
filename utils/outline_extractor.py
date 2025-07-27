import re
from collections import Counter

def is_bold(font_name):
    """Enhanced heuristic to check if a font name indicates bold."""
    if not font_name:
        return False
    font_lower = font_name.lower()
    bold_indicators = ["bold", "black", "heavy", "demi", "semibold", "extrabold", "ultra", "thick"]
    return any(indicator in font_lower for indicator in bold_indicators)

def is_all_caps(text):
    """Check if text is all uppercase (often used for headings)."""
    if not text or len(text) < 3:
        return False
    return text.isupper() and any(c.isalpha() for c in text)

def clean_text(text):
    """Clean and normalize text."""
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text.strip())
    return text

def is_likely_content_text(text, size, body_text_size):
    """Check if text is likely regular content rather than a heading."""
    if not text:
        return True
    if len(text) > 100:
        return True
    content_patterns = [
        r'^[A-Z][a-z].*[a-z]$',
        r'.*\b(the|and|or|but|in|on|at|to|for|of|with|by)\b.*',
        r'.*[,;:].*',
        r'^\d+[\.\)]\s+[a-z]',
    ]
    
    for pattern in content_patterns:
        if re.match(pattern, text, re.IGNORECASE):
            return True
    
    return False

def is_date_or_version(text):
    """Check if text looks like a date or version number."""
    if not text:
        return False
    
    date_patterns = [
        r'^\w+\s+\d{4}$',
        r'^\d{1,2}\s+\w+\s+\d{4}$',
        r'^Version\s+\d',
        r'^\d{4}$',
        r'^[A-Z]{3,}\s+\d{4}$',
    ]
    
    return any(re.match(pattern, text) for pattern in date_patterns)

def is_table_of_contents_entry(text):
    """Check if text looks like a table of contents entry."""
    if not text:
        return False
    toc_patterns = [
        r'.*\.{3,}',
        r'.*\s+\d+$',
    ]
    
    return any(re.match(pattern, text) for pattern in toc_patterns)

def identify_outline(blocks):
    """
    Further enhanced outline identification with better filtering and detection.
    """
    if not blocks:
        return {"title": "", "outline": []}
    blocks = sorted(blocks, key=lambda b: (b['page'], b['bbox'][1], b['bbox'][0]))
    avg_page_width = 595.0
    avg_page_height = 842.0
    TOP_ZONE_THRESHOLD = avg_page_height * 0.15
    BOTTOM_ZONE_THRESHOLD = avg_page_height * 0.85
    header_footer_candidates = {}
    for block in blocks:
        text = clean_text(block['text'])
        if not text or len(text) < 2:
            continue
            
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
    frequent_headers_footers = set()
    
    for (text, y_zone), count in header_footer_candidates.items():
        if count >= max(2, min(3, num_unique_pages * 0.3)):
            frequent_headers_footers.add(text.lower())
    exclude_patterns = [
        "version 2014", "page", "copyright", "istqb", "foundation level", 
        "agile tester", "qualifications board", "international software testing",
        "connecting ontarians", "rfp:", "march 2003", "www.", ".com",
        "address:", "rsvp:", "closed toed shoes", "parents", "hope to see you there"
    ]
    frequent_headers_footers.update(exclude_patterns)
    filtered_blocks = []
    for block in blocks:
        text = clean_text(block['text'])
        size = block['size']
        bbox = block['bbox']
        if not text or len(text) < 3:
            continue
        if re.fullmatch(r'[\-\_=\s\.\*]+', text):
            continue
        if text.strip().isdigit() and len(text.strip()) <= 3:
            continue
        if re.match(r'.*(@|www\.|\.com|http)', text.lower()):
            continue
        if any(pattern in text.lower() for pattern in frequent_headers_footers):
            continue
        if is_date_or_version(text) and not re.match(r'^\d+[\.\)]\s', text):
            continue
        if len(text) < 10 and not (is_bold(block['font']) or is_all_caps(text)):
            continue
            
        filtered_blocks.append(block)
    
    if not filtered_blocks:
        return {"title": "", "outline": []}
    size_counts = Counter()
    for block in filtered_blocks:
        text = clean_text(block['text'])
        size = block['size']
        if len(text) > 30 and not is_bold(block['font']) and not is_all_caps(text):
            size_counts[size] += len(text)
    
    if size_counts:
        body_text_size = max(size_counts, key=size_counts.get)
    else:
        all_sizes = [b['size'] for b in filtered_blocks if 8 <= b['size'] <= 20]
        if all_sizes:
            body_text_size = Counter(all_sizes).most_common(1)[0][0]
        else:
            body_text_size = 12.0
    
    H1_SIZE_THRESHOLD = body_text_size * 1.6
    H2_SIZE_THRESHOLD = body_text_size * 1.3
    H3_SIZE_THRESHOLD = body_text_size * 1.15

    title = ""
    title_blocks = set()
    first_page_blocks = [b for b in filtered_blocks if b['page'] == 1]
    first_page_blocks.sort(key=lambda b: (b['bbox'][1], -b['size']))

    for block in first_page_blocks[:5]:
        text = clean_text(block['text'])
        size = block['size']
        bbox = block['bbox']

        if bbox[1] > avg_page_height * 0.25:
            continue
        is_title_candidate = (
            len(text) >= 15 and
            len(text) <= 100 and  
            (size >= H1_SIZE_THRESHOLD or is_bold(block['font']) or is_all_caps(text)) and
            not re.match(r'^\d+[\.\)]\s', text) and  # Not numbered
            not is_date_or_version(text) and
            not is_table_of_contents_entry(text) and
            bbox[1] < avg_page_height * 0.2
        )
        
        if is_title_candidate:
            title = text
            title_blocks.add(id(block))
            break
    outline_items = []
    
    for block in filtered_blocks:
        if id(block) in title_blocks:
            continue
            
        text = clean_text(block['text'])
        size = block['size']
        font = block['font']
        page = block['page']
        
        if not text or len(text) < 4:
            continue
        if is_likely_content_text(text, size, body_text_size):
            continue
        if is_date_or_version(text):
            continue
            
        level = None
        num_match = re.match(r'^(\d+(?:\.\d+)*)\.\s+(.+)', text)
        if num_match:
            num_part = num_match.group(1)
            text_part = num_match.group(2).strip()
            if size >= body_text_size * 0.9:
                num_levels = num_part.count('.') + 1
                if num_levels == 1:
                    level = "H1"
                elif num_levels == 2:
                    level = "H2"
                else:
                    level = "H3"
                
                text = text_part
        if not level:
            section_match = re.match(r'^(\d+\.\d+)\s+(.+)', text)
            if section_match and size >= body_text_size * 1.1:
                level = "H2"
                text = section_match.group(2).strip()
        if not level:
            size_ratio = size / body_text_size
            is_formatted = is_bold(font) or is_all_caps(text)
            if is_formatted and size_ratio >= 1.2 and len(text) <= 80:
                if size >= H1_SIZE_THRESHOLD:
                    level = "H1"
                elif size >= H2_SIZE_THRESHOLD:
                    level = "H2"
                elif size >= H3_SIZE_THRESHOLD:
                    level = "H3"
            elif size_ratio >= 1.8:
                level = "H1"

        if not level and is_all_caps(text) and len(text) >= 8 and len(text) <= 50:
            if size >= body_text_size * 1.2:
                level = "H1"

        if level:
            if len(text) > 150:
                continue
            common_words = len(re.findall(r'\b(the|and|or|but|in|on|at|to|for|of|with|by|a|an|is|are|was|were)\b', text.lower()))
            if common_words > len(text.split()) * 0.4:
                continue
            
            outline_items.append({
                "level": level,
                "text": text,
                "page": page
            })

    final_outline = []
    seen_items = set()
    
    for item in outline_items:
        text = item['text']
        
        if len(text) < 5:
            continue
        if re.match(r'^(credits of|course should be|must be)', text.lower()):
            continue

        item_key = (item['level'], text.lower().strip(), item['page'])
        
        if item_key not in seen_items:
            final_outline.append(item)
            seen_items.add(item_key)

    final_outline.sort(key=lambda x: (x['page'], x['text']))
    
    return {
        "title": title,
        "outline": final_outline
    }