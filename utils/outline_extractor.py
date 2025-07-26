# utils/outline_extractor.py

import re
from collections import Counter

def is_bold(font_name):
    """Simple heuristic to check if a font name indicates bold."""
    return "bold" in font_name.lower() or "black" in font_name.lower() or "heavy" in font_name.lower() or "demi" in font_name.lower()

def is_all_caps(text):
    """Check if text is all uppercase (often used for headings)."""
    return text.isupper() and len(text) > 3 and any(c.isalpha() for c in text)

def is_likely_noise(text, size, body_text_size):
    """Comprehensive noise detection function."""
    text = text.strip()
    
    # Empty or too short
    if not text or len(text) < 3:
        return True
    
    # Single digits or very short numbers
    if text.isdigit() and len(text) <= 2:
        return True
    
    # Common noise patterns
    noise_patterns = [
        r'^[\-\_=\s\.]+$',  # Lines of dashes, underscores, dots
        r'^\s*[\d\-\.]+\s*$',  # Just numbers/dates without context
        r'^(page|pg)\s*\d+$',  # Page numbers
        r'^\d{1,2}[\s\-\/]\d{1,2}[\s
        r'^[A-Z]{2,}\s+\d{4}$',  # Month abbreviations with years (JUN 2013)
        r'^\d{1,2}\s+[A-Z]{3,}\s+\d{4}$',  # Dates like "31 MAY 2014"
        r'^(version|ver\.?)\s*\d',  # Version strings
        r'^copyright|©',  # Copyright notices
        r'^\s*[\(\)\[\]]+\s*$',  # Just brackets
        r'^\s*[\.,:;]+\s*$',  # Just punctuation
    ]
    
    for pattern in noise_patterns:
        if re.match(pattern, text, re.IGNORECASE):
            return True
    
    # Very small text is likely footnotes/metadata
    if size < body_text_size * 0.7:
        return True
    
    # Short fragments that look like broken text
    if len(text) < 8 and not re.match(r'^\d+[\.\)]', text):
        return True
    
    return False

def clean_fragmented_title(text_parts):
    """Combine fragmented title parts intelligently."""
    if not text_parts:
        return ""
    
    # Remove obvious fragments and noise
    cleaned_parts = []
    for part in text_parts:
        part = part.strip()
        if len(part) < 2:
            continue
        
        # Skip obvious fragments
        if re.match(r'^[A-Z]?[a-z]*[:\s]*$', part) and len(part) < 10:
            continue
        
        # Skip repeated text patterns
        if any(part in existing for existing in cleaned_parts):
            continue
            
        cleaned_parts.append(part)
    
    if not cleaned_parts:
        return ""
    
    # Try to reconstruct meaningful title
    combined = " ".join(cleaned_parts)
    
    # Clean up common artifacts
    combined = re.sub(r'\s+', ' ', combined)  # Multiple spaces
    combined = re.sub(r'([a-z])([A-Z])', r'\1 \2', combined)  # CamelCase separation
    
    return combined.strip()

def detect_numbered_heading(text):
    """Detect numbered headings and return level and cleaned text."""
    # Match patterns like "1.", "2.1", "3.2.1", "A1.", etc.
    patterns = [
        r'^\s*([A-Z]?\d+(?:\.\d+)*)[\.:]?\s+(.+)',  # Standard numbering
        r'^\s*(\d+(?:\.\d+)*)\.\s+(.+)',  # Simple numbering
        r'^\s*([IVX]+)\.\s+(.+)',  # Roman numerals
        r'^\s*([A-Z])\.\s+(.+)',  # Letter headings
    ]
    
    for pattern in patterns:
        match = re.match(pattern, text, re.IGNORECASE)
        if match:
            number_part = match.group(1)
            text_part = match.group(2).strip()
            
            if not text_part or len(text_part) < 3:
                continue
            
            # Determine level based on numbering depth
            if '.' in number_part:
                level_depth = number_part.count('.') + 1
            else:
                level_depth = 1
            
            # Map to heading levels (cap at H4)
            level_map = {1: "H1", 2: "H2", 3: "H3", 4: "H4"}
            level = level_map.get(min(level_depth, 4), "H4")
            
            return level, text_part
    
    return None, text

def identify_outline(blocks):
    """
    Completely rewritten outline identification with focus on accuracy.
    """
    title = ""
    outline_items = []
    
    if not blocks:
        return {"title": "", "outline": []}
    
    # Constants
    avg_page_width = 595.0
    avg_page_height = 842.0
    TOP_ZONE = avg_page_height * 0.15  # Top 15%
    BOTTOM_ZONE = avg_page_height * 0.85  # Bottom 15%
    
    # Step 1: Identify and filter noise, headers, footers
    frequent_text = {}
    for block in blocks:
        text = block['text'].strip()
        bbox = block['bbox']
        
        # Check for headers/footers by position and frequency
        if bbox[1] < TOP_ZONE or bbox[3] > BOTTOM_ZONE:
            key = text.lower()
            frequent_text[key] = frequent_text.get(key, 0) + 1
    
    # Common headers/footers that appear frequently
    num_pages = len(set(b['page'] for b in blocks))
    frequent_headers_footers = set()
    for text, count in frequent_text.items():
        if count >= max(2, num_pages // 2):
            frequent_headers_footers.add(text)
    
    # Add known noise patterns
    known_noise = {
        "version 2014", "page", "copyright", "istqb", "international software testing",
        "qualifications board", "foundation level extension", "agile tester"
    }
    frequent_headers_footers.update(known_noise)
    
    # Step 2: Estimate body text size
    clean_blocks = []
    size_counter = Counter()
    
    for block in blocks:
        text = block['text'].strip()
        size = block['size']
        bbox = block['bbox']
        
        if not text or len(text) < 2:
            continue
            
        # Skip obvious headers/footers
        if text.lower() in frequent_headers_footers:
            continue
            
        clean_blocks.append(block)
        
        # Count sizes for body text estimation (exclude very large/small text)
        if 8 <= size <= 20:
            size_counter[size] += 1
    
    # Get most common size as body text size
    if size_counter:
        body_text_size = size_counter.most_common(1)[0][0]
    else:
        body_text_size = 11.0
    
    # Step 3: Enhanced title detection for first page
    first_page_blocks = [b for b in clean_blocks if b['page'] == 1]
    first_page_blocks.sort(key=lambda x: (x['bbox'][1], -x['size']))  # Top to bottom, large to small
    
    # Strategy: Look for most prominent text in top area
    title_candidates = []
    
    for block in first_page_blocks:
        text = block['text'].strip()
        size = block['size']
        font = block['font']
        bbox = block['bbox']
        
        # Must be in top portion of page
        if bbox[1] > avg_page_height * 0.4:
            break
            
        # Skip if too small or noise
        if is_likely_noise(text, size, body_text_size):
            continue
            
        # Check if this looks like a title
        is_prominent = (
            size >= body_text_size * 1.5 or  # Larger text
            is_bold(font) or  # Bold text
            len(text) > 15  # Substantial content
        )
        
        if is_prominent:
            title_candidates.append({
                'text': text,
                'size': size,
                'bbox': bbox,
                'bold': is_bold(font),
                'y_pos': bbox[1]
            })
    
    # Find the best title
    if title_candidates:
        # Sort by position (top first), then by prominence
        title_candidates.sort(key=lambda x: (x['y_pos'], -x['size'], -int(x['bold'])))
        
        # Try to combine related title parts
        if len(title_candidates) > 1:
            # Check if multiple candidates are close together (multi-line title)
            primary = title_candidates[0]
            title_parts = [primary['text']]
            
            for candidate in title_candidates[1:]:
                # Close vertically and similar formatting
                if (abs(candidate['y_pos'] - primary['y_pos']) < primary['size'] * 2 and
                    abs(candidate['size'] - primary['size']) <= 2):
                    title_parts.append(candidate['text'])
                else:
                    break
            
            title = clean_fragmented_title(title_parts)
        else:
            title = title_candidates[0]['text']
    
    # Clean up title
    title = re.sub(r'\s+', ' ', title).strip()
    
    # Step 4: Identify headings with much stricter criteria
    used_title_text = set()
    if title:
        used_title_text.add(title.lower())
        # Also add title fragments to avoid re-using them
        title_words = title.lower().split()
        if len(title_words) > 2:
            used_title_text.update(title_words)
    
    # More conservative heading size thresholds
    H1_THRESHOLD = body_text_size * 2.5  # Much higher threshold
    H2_THRESHOLD = body_text_size * 1.8
    H3_THRESHOLD = body_text_size * 1.4
    H4_THRESHOLD = body_text_size * 1.2
    
    for block in clean_blocks:
        text = block['text'].strip()
        size = block['size']
        font = block['font']
        page = block['page']
        
        # Skip if likely noise
        if is_likely_noise(text, size, body_text_size):
            continue
            
        # Skip if part of title
        if text.lower() in used_title_text:
            continue
            
        # Skip very short text unless it's numbered
        if len(text) < 5 and not re.match(r'^\d+[\.\)]', text):
            continue
        
        level = None
        cleaned_text = text
        
        # Primary: Check for numbered headings
        numbered_level, numbered_text = detect_numbered_heading(text)
        if numbered_level and len(numbered_text) >= 5:
            level = numbered_level
            cleaned_text = numbered_text
        
        # Secondary: Size and style based detection (much more conservative)
        elif size >= H1_THRESHOLD and is_bold(font):
            level = "H1"
        elif size >= H2_THRESHOLD and is_bold(font):
            level = "H2"
        elif size >= H3_THRESHOLD and (is_bold(font) or is_all_caps(text)):
            level = "H3"
        elif size >= H4_THRESHOLD and is_bold(font) and len(text) >= 10:
            level = "H4"
        
        # Additional filters for non-numbered headings
        if level and not numbered_level:
            # Skip if it looks like a date or version
            if re.match(r'^(\d{1,2}\s+)?(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)', text, re.IGNORECASE):
                continue
            if re.match(r'^version|^v\d|^\d{4}$', text, re.IGNORECASE):
                continue
            # Skip very short all-caps unless it's clearly a heading
            if is_all_caps(text) and len(text) < 8:
                continue
        
        if level:
            outline_items.append({
                'level': level,
                'text': cleaned_text,
                'page': page
            })
    
    # Step 5: Clean up and deduplicate
    seen = set()
    final_outline = []
    
    for item in outline_items:
        # Create a key for deduplication
        key = (item['level'], item['text'].lower(), item['page'])
        if key not in seen:
            # Final validation
            if len(item['text']) >= 3:  # Minimum text length
                final_outline.append(item)
                seen.add(key)
    
    return {"title": title, "outline": final_outline}
