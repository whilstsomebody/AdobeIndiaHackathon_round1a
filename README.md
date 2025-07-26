<<<<<<< Updated upstream
# Adobe India Hackathon - Connecting the Dots (Round 1A)

## Challenge Theme: Understand Your Document

### The Mission (Round 1A)

The goal of this round is to develop a solution that can intelligently extract a structured outline from a raw PDF document. This outline primarily consists of the document's Title and its main headings (H1, H2, H3), presented in a clean, hierarchical JSON format. This structured output serves as the foundational "brains" for smarter document experiences.

### My Approach

My solution employs a heuristic-based approach combined with a robust PDF parsing library to accurately identify and extract the document's outline. This method is chosen to meet the strict performance, size, and offline requirements of the hackathon.

1.  **PDF Parsing and Text Extraction (`utils/pdf_parser.py`):**
    * I utilize `PyMuPDF` (the `fitz` library) for efficient and detailed text extraction. This library allows access to crucial layout information such as font size, font name, and bounding box coordinates for each text span[cite: 143].
    * The `pdf_parser.py` is designed to aggressively merge visually contiguous text spans and lines into coherent logical blocks. This is vital for handling complex PDF layouts and overcoming text fragmentation issues (e.g., words being split into multiple individual characters due to rendering). It also includes initial text normalization (e.g., removing repeating characters like 'eeee' into 'e') to clean artifacts.

2.  **Outline Identification Heuristics (`utils/outline_extractor.py`):**
    The core logic for identifying titles and headings resides here. It uses a multi-stage heuristic process:
    * **Initial Filtering:** Blocks are initially filtered to remove obvious noise, such as very short strings, lines of dashes, or typical page numbers and footers, which are identified based on their content, size, and consistent vertical position across multiple pages.
    * **Body Text Size Estimation:** A baseline `body_text_size` is estimated by finding the most frequent font size within a typical text range. This relative sizing is more robust than absolute thresholds.
    * **Prioritized Title Detection:**
        * The algorithm first specifically looks for the document's main title on the first page.
        * It employs a strategy to identify a single, overwhelmingly dominant block (for simple documents like forms) or to combine multiple vertically-aligned and prominent blocks (for multi-line titles).
        * Identified title blocks are then **explicitly removed** from the list of blocks considered for general headings, ensuring the title is unique.
    * **Hierarchical Heading Classification (H1, H2, H3, H4):**
        * **Numerical Prefixes (Primary):** The strongest indicator for heading level is a numerical or alphabetical prefix (e.g., "1. Introduction", "2.1 Sub-section", "A. Topic"). These patterns are given high priority to determine the H1, H2, H3, or H4 level.
        * **Font Size and Style (Fallback/Refinement):** If no numerical pattern is present, or for validation, heading levels are determined by relative font size (compared to `body_text_size`), boldness, and all-caps styling.
        * **Hierarchical Context:** The system tracks the levels of previously identified headings to promote or demote a current heading (e.g., an H2 might be promoted to an H1 if no H1 has appeared on the current page yet) to maintain a logical hierarchy.
        * **Multi-Line Headings:** The logic attempts to consolidate text blocks that are visually part of the same heading but were split across lines.

### Models or Libraries Used

* **`PyMuPDF` (Python library for MuPDF, imported as `fitz`)**: Used for robust and high-performance PDF text extraction and layout analysis. It's an open-source library and its footprint is well within the required limits.
* **`re` (Python's built-in `re` module)**: Used for regular expression matching to identify numerical heading patterns and for text normalization.
* **`collections.Counter` (Python's built-in `collections` module)**: Used for efficient counting of font sizes to determine the most frequent body text size.

No external machine learning models (like large language models for NLP) are directly used for classification in Round 1A, ensuring compliance with the `Model size ≤ 200MB` constraint. The solution is entirely CPU-based and operates offline.

### How to Build and Run The Solution

The solution is designed to run within a Docker container, ensuring a consistent and isolated execution environment as expected by the hackathon organizers.

**Prerequisites:**
* Docker Desktop (or Docker Engine for Linux) installed and running.

**Steps:**

1.  **Navigate to the Project Root:**
    Open the terminal/command prompt and change directory to the root of the project:
    ```bash
    cd PDF_outline_extractor/
    ```

2.  **Place Input PDFs:**
    Place all the PDF files to process (e.g., `sample.pdf`, `file01.pdf`, `file02.pdf`, etc.) inside the `input/` directory within the project structure.

3.  **Build the Docker Image:**
    This command compiles the application and its dependencies into a Docker image.
    ```bash
    docker build --platform linux/amd64 -t adobeindiahackathon:round1a .
    ```
    * `-t adobeindiahackathon:round1a`: Tags your image with the name `adobeindiahackathon` and tag `round1a`.
    * `.`: Specifies that the `Dockerfile` is in the current directory.

4.  **Run the Docker Container:**
    This executes the `main.py` script inside the Docker container. The container will process all PDFs found in its `/app/input` directory and write the resulting JSON outlines to `/app/output`.
    ```bash
    docker run --rm -v "$(pwd)/input:/app/input" -v "$(pwd)/output:/app/output" --network none adobeindiahackathon:round1a
    ```
    * `--rm`: Automatically removes the container after it finishes, keeping the system clean.
    * `-v "$(pwd)/input:/app/input"`: Mounts your local `input/` directory to `/app/input` inside the container.
    * `-v "$(pwd)/output:/app/output"`: Mounts your local `output/` directory to `/app/output` inside the container.
    * `--network none`: **Crucially, this disables all network access for the container during runtime**, ensuring offline execution as required.

5.  **Check the Output:**
    After the `docker run` command completes, the generated JSON outline files (e.g., `filename.json` for each `filename.pdf`) will be available in the local `output/` directory.
=======
PDF Extractor
>>>>>>> Stashed changes
