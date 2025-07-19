import json

def write_output(title, outline, output_path):
    data = {
        "title": title,
        "outline": outline
    }
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
