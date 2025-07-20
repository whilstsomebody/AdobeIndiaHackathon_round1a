# main.py

import os
import sys
from utils.pdf_parser import extract_text_blocks_with_details
from utils.outline_extractor import identify_outline
from utils.json_writer import write_json_output

def process_single_pdf(pdf_path, output_dir):
    """
    Processes a single PDF file to extract outline and save as JSON.
    """
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found at {pdf_path}")
        return

    print(f"Processing PDF: {os.path.basename(pdf_path)}")

    blocks = extract_text_blocks_with_details(pdf_path)
    output_data = identify_outline(blocks)
    output_filename = os.path.join(output_dir, os.path.basename(pdf_path).replace(".pdf", ".json"))
    write_json_output(output_data, output_filename)


def main():
    input_dir = "/app/input"
    output_dir = "/app/output"

    os.makedirs(output_dir, exist_ok=True)

    pdf_files = [f for f in os.listdir(input_dir) if f.lower().endswith(".pdf")]
    if not pdf_files:
        print(f"No PDF files found in {input_dir}. Exiting.")
        sys.exit(0)

    print(f"Found {len(pdf_files)} PDF(s) to process.")
    for pdf_file in pdf_files:
        pdf_path = os.path.join(input_dir, pdf_file)
        process_single_pdf(pdf_path, output_dir)

if __name__ == "__main__":
    main()