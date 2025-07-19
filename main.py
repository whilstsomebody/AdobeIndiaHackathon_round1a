import os
from utils.pdf_parser import extract_pdf_elements
from utils.outline_extractor import (
    extract_features,
    classify_heading_from_features,
    detect_title,
)
from utils.json_writer import write_output

INPUT_DIR = "/app/input"
OUTPUT_DIR = "/app/output"

for filename in os.listdir(INPUT_DIR):
    if filename.endswith(".pdf"):
        input_path = os.path.join(INPUT_DIR, filename)
        output_path = os.path.join(OUTPUT_DIR, filename.replace(".pdf", ".json"))

        print(f"📄 Processing: {filename}")
        elements = extract_pdf_elements(input_path)

        title = detect_title(elements)
        outline = []

        for el in elements:
            features = extract_features(el)
            heading_level = classify_heading_from_features(features)
            if heading_level:
                outline.append({
                    "level": heading_level,
                    "text": el["text"],
                    "page": el["page"],
                })

        write_output(title, outline, output_path)
        print(f"✅ Output written to: {output_path}")
