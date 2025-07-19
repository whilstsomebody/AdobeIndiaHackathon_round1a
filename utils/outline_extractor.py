import pandas as pd
import joblib
import warnings

model = joblib.load("models/heading_classifier.pkl")

# Define feature order to match training
FEATURE_NAMES = [
    "font_size",
    "is_bold",
    "is_caps",
    "is_numbered",
    "position_y",
    "text_length",
    "is_centered",
]

def extract_features(el):
    text = el["text"]
    return {
        "font_size": el["size"],
        "is_bold": 0,  # not reliable from pdfminer
        "is_caps": int(text.isupper()),
        "is_numbered": int(text.split(" ")[0].replace(".", "").isdigit()),
        "position_y": round(el["y0"] / 1000, 3),
        "text_length": len(text),
        "is_centered": int(abs((el["x0"] + el["x1"]) / 2 - 300) < 50),
    }


def classify_heading_from_features(features_dict):
    df = pd.DataFrame([features_dict], columns=FEATURE_NAMES)
    warnings.filterwarnings("ignore", category=UserWarning)
    label = model.predict(df)[0]
    return {3: "H1", 2: "H2", 1: "H3"}.get(label, None)


def detect_title(elements):
    # Look at only page 1
    page_1_elements = [el for el in elements if el["page"] == 1]
    if not page_1_elements:
        return "Untitled"

    # Sort by font size descending
    sorted_by_size = sorted(page_1_elements, key=lambda el: el["size"], reverse=True)

    for el in sorted_by_size:
        if len(el["text"].strip()) > 5:  # avoid junk like "1", "Fig", etc.
            return el["text"].strip()

    return "Untitled"
