# main.py

import os
import sys
# All imports are now from 'utils' since the structure is simplified back
from utils.pdf_parser import extract_text_blocks_with_details
from utils.outline_extractor import identify_outline
from utils.json_writer import write_json_output

def main():
    input_dir = "/app/input"
    output_dir = "/app/output"

    os.makedirs(output_dir, exist_ok=True)

    # --- Round 1A Logic (Outline Extraction) ---
    pdf_files = [f for f in os.listdir(input_dir) if f.lower().endswith(".pdf")]

    if pdf_files:
        print(f"Round 1A: Found {len(pdf_files)} PDF files for outline generation.")
        for pdf_file in pdf_files:
            pdf_path = os.path.join(input_dir, pdf_file)
            print(f"Round 1A: Generating outline for: {pdf_file}")
            
            blocks = extract_text_blocks_with_details(pdf_path)
            outline_data = identify_outline(blocks)
            output_filename = os.path.join(output_dir, os.path.basename(pdf_file).replace(".pdf", ".json"))
            write_json_output(outline_data, output_filename)
    else:
        print("Round 1A: No PDF files found in input directory. Exiting.")
        sys.exit(0)

if __name__ == "__main__":
    main()