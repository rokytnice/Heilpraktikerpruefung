import json
import os
import glob
import re
from pypdf import PdfReader

# Configuration
JSON_PATH = "app/src/main/assets/exams.json"
PDF_DIR = "fragen/"

# Month mapping
MONTH_MAP = {
    "March": "Maerz",
    "October": "Oktober"
}

def normalize_text(text):
    """Removes whitespace and converts to lowercase for comparison."""
    return re.sub(r'\s+', ' ', text).strip().lower()

def extract_text_from_pdf(pdf_path):
    """Extracts text from a PDF file."""
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + " "
        return text
    except Exception as e:
        return ""

def find_pdf_file(year, month_en):
    """Finds the PDF file corresponding to the exam year and month."""
    month_de = MONTH_MAP.get(month_en, month_en)

    # List all files in the directory
    files = os.listdir(PDF_DIR)

    # Filter files that contain both the year and the German month
    candidates = []
    for f in files:
        if str(year) in f and month_de in f and f.lower().endswith(".pdf"):
            candidates.append(os.path.join(PDF_DIR, f))

    return candidates

def verify_exam(exam):
    """Verifies a single exam entry against its PDF."""
    exam_id = exam.get("id")
    year = exam.get("year")
    month = exam.get("month")
    questions = exam.get("questions", [])

    print(f"--- Verifying Exam: {year} {month} ({exam_id}) ---")

    if not questions:
        print(f"WARNING: No questions found in JSON for {exam_id}.")
        return

    pdf_files = find_pdf_file(year, month)

    if not pdf_files:
        print(f"ERROR: No matching PDF file found in {PDF_DIR} for {month} {year}.")
        return

    print(f"Found PDF candidate(s): {pdf_files}")

    # Try to extract text from the best candidate (or all)
    pdf_text = ""
    for pdf_path in pdf_files:
        text = extract_text_from_pdf(pdf_path)
        if len(text.strip()) > 100: # Heuristic for readable text
            pdf_text += text
            print(f"Successfully extracted text from {pdf_path} ({len(text)} chars).")
        else:
            print(f"WARNING: PDF {pdf_path} appears to be an image scan or empty (text length: {len(text)}).")

    if not pdf_text:
        print(f"ERROR: Could not extract readable text from any PDF for {month} {year}. Manual verification required.")
        return

    pdf_text_normalized = normalize_text(pdf_text)

    match_count = 0
    mismatch_count = 0

    for q in questions:
        q_text = q.get("text", "")
        q_text_norm = normalize_text(q_text)

        # We search for a significant portion of the question to handle minor OCR errors or formatting
        # Using a substring check of the first 50 chars might be too strict if there's a typo.
        # Let's try to find the full normalized string first.

        if q_text_norm in pdf_text_normalized:
            match_count += 1
        else:
            # Fallback: Try searching for a substring (first half)
            substring_len = len(q_text_norm) // 2
            if substring_len > 10 and q_text_norm[:substring_len] in pdf_text_normalized:
                 match_count += 1
                 # print(f"  Question {q.get('id')}: Partial match found.")
            else:
                mismatch_count += 1
                print(f"  MISMATCH: Question {q.get('id')} text not found in PDF.")
                print(f"    JSON: {q_text[:100]}...")
                # Optional: print surrounding text in PDF to see if it's there but garbled? No, too verbose.

    print(f"Result: {match_count} questions matched, {mismatch_count} potential mismatches out of {len(questions)} questions.")

def main():
    if not os.path.exists(JSON_PATH):
        print(f"Error: JSON file not found at {JSON_PATH}")
        return

    try:
        with open(JSON_PATH, 'r', encoding='utf-8') as f:
            exams = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return

    for exam in exams:
        verify_exam(exam)
        print("\n")

if __name__ == "__main__":
    main()
