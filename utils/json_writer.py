import json
import os

def write_json_output(data, output_filepath):
    """
    Writes the given data dictionary to a JSON file.
    """
    with open(output_filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Output saved to: {output_filepath}")