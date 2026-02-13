import json
import os
import re
import sys
from pypdf import PdfReader
from difflib import SequenceMatcher

# Configuration
EXAMS_JSON_PATH = "app/src/main/assets/exams.json"
PDF_DIR = "fragen"
REPORT_FILE = "pypdf_verification_report.md"

def normalize_text(text):
    """Normalize text by removing extra whitespace and special characters."""
    if not text:
        return ""
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def verify_text_match(app_text, pdf_text, threshold=0.85):
    """
    Verifies if app_text is present in pdf_text.
    Returns: (is_match, score)
    """
    norm_app = normalize_text(app_text)
    if not norm_app:
        return True, 1.0

    if norm_app in pdf_text:
        return True, 1.0

    # For now, let's stick to simple "in" check on normalized PDF text.
    # If not found, we return False.
    # Calculating score on full PDF is expensive.

    # Remove all non-alphanumeric to be very lenient
    clean_app = re.sub(r'\W+', '', norm_app).lower()
    clean_pdf = re.sub(r'\W+', '', pdf_text).lower()

    if clean_app in clean_pdf:
        return True, 0.95

    return False, 0.0

def get_pdf_filename(exam_id):
    year, month = exam_id.split('-')
    month_german = "Maerz" if month == "march" else "Oktober"

    # Heuristics for PDF naming
    patterns = [
        f"HPP_Pruefung_{month_german}_{year}",
        f"{month_german}-{year}",
        f"Oktober-{year}" if month == "october" else f"Maerz-{year}",
        f"{month_german} {year}"
    ]

    for f in os.listdir(PDF_DIR):
        if not f.endswith(".pdf"): continue
        for p in patterns:
            if f.startswith(p) or p in f:
                return os.path.join(PDF_DIR, f)
    return None

def extract_pdf_text(pdf_path):
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return normalize_text(text)
    except Exception as e:
        print(f"Error extracting text from {pdf_path}: {e}")
        return ""

def extract_solution_key(pdf_text):
    """
    Attempts to find a solution key in the text.
    Returns a dict {question_num: [correct_indices]} or None.
    """
    # Look for "Lösungsschlüssel" or "Antworten" followed by numbers and letters
    # Pattern: "1 A", "2 B", "25 A, D, E"
    # Added \b at the end to ensure we capture whole words (e.g. avoid '1 Einfachauswahl' -> '1 E')

    matches = re.findall(r'(\d{1,2})\s+([A-E](?:[,\s]+[A-E])*\b)', pdf_text)

    if not matches:
        return None

    solutions = {}
    for num_str, ans_str in matches:
        num = int(num_str)
        # Convert A, B, C... to 0, 1, 2...
        indices = []
        for char in ans_str.upper():
            if 'A' <= char <= 'E':
                indices.append(ord(char) - ord('A'))
        if indices:
            solutions[num] = sorted(list(set(indices)))

    # Filter out noise (e.g. page numbers or random matches)
    # We expect a sequence (typically > 5 entries to be valid)
    if len(solutions) < 5:
        return None

    return solutions

def compare_solutions(app_indices, pdf_indices):
    return sorted(app_indices) == sorted(pdf_indices)

def main():
    if not os.path.exists(EXAMS_JSON_PATH):
        print(f"Error: {EXAMS_JSON_PATH} not found.")
        return

    with open(EXAMS_JSON_PATH, 'r') as f:
        exams = json.load(f)

    report_lines = []
    report_lines.append("# Verification Report (with pypdf)")
    report_lines.append("")

    total_exams = len(exams)
    exams_with_pdf = 0
    exams_verified = 0

    for exam in exams:
        exam_id = exam.get('id')
        print(f"Processing {exam_id}...")

        pdf_path = get_pdf_filename(exam_id)
        if not pdf_path:
            report_lines.append(f"## {exam_id}")
            report_lines.append(f"- **MISSING PDF**: Could not find a matching PDF file.")
            report_lines.append("")
            continue

        exams_with_pdf += 1
        pdf_text = extract_pdf_text(pdf_path)
        if not pdf_text:
            report_lines.append(f"## {exam_id}")
            report_lines.append(f"- **READ ERROR**: Could not extract text from {pdf_path}")
            report_lines.append("")
            continue

        report_lines.append(f"## {exam_id}")
        report_lines.append(f"PDF: `{pdf_path}`")

        # Try to extract solution key
        pdf_solutions = extract_solution_key(pdf_text)
        if pdf_solutions:
            report_lines.append(f"- **Solution Key**: Found ({len(pdf_solutions)} entries)")
        else:
            report_lines.append(f"- **Solution Key**: Not found or could not be parsed.")

        issues = []

        questions = exam.get('questions', [])
        for q in questions:
            q_id = q.get('id')
            q_text = q.get('text', '')

            # 1. Verify Question Text
            match, score = verify_text_match(q_text, pdf_text)
            if not match:
                # Try stripping "A)" or similar prefixes from app text
                clean_q_text = re.sub(r'^[A-Z]\)\s*', '', q_text)
                match, score = verify_text_match(clean_q_text, pdf_text)

            if not match:
                issues.append(f"Q{q_id}: Question text not found in PDF.")
                # issues.append(f"   App: {q_text[:50]}...")

            # 2. Verify Options
            options = q.get('options', [])
            for i, opt in enumerate(options):
                match_opt, score_opt = verify_text_match(opt, pdf_text)
                if not match_opt:
                     issues.append(f"Q{q_id}: Option {i+1} text not found.")
                     # issues.append(f"   App: {opt[:30]}...")

            # 3. Verify Statements (for Aussagenkombination)
            statements = q.get('statements', [])
            for i, stmt in enumerate(statements):
                 match_stmt, score_stmt = verify_text_match(stmt, pdf_text)
                 if not match_stmt:
                     issues.append(f"Q{q_id}: Statement {i+1} text not found.")

            # 4. Verify Solution (if key found)
            if pdf_solutions and q_id in pdf_solutions:
                pdf_correct = pdf_solutions[q_id]
                app_correct = q.get('correctIndices', [])

                if not compare_solutions(app_correct, pdf_correct):
                    issues.append(f"Q{q_id}: Solution mismatch. App: {app_correct}, PDF: {pdf_correct}")

        if issues:
            report_lines.append(f"- Found {len(issues)} issues:")
            for issue in issues[:50]: # Limit report size
                report_lines.append(f"  - {issue}")
            if len(issues) > 50:
                report_lines.append(f"  - ... and {len(issues)-50} more.")
        else:
            report_lines.append("- All content verified against PDF text.")
            exams_verified += 1

        report_lines.append("")

    # Summary
    report_lines.append("# Summary")
    report_lines.append(f"- Total Exams: {total_exams}")
    report_lines.append(f"- Exams with PDF: {exams_with_pdf}")
    report_lines.append(f"- Fully Verified (Text): {exams_verified}")

    with open(REPORT_FILE, "w") as f:
        f.write("\n".join(report_lines))

    print(f"Report generated: {REPORT_FILE}")

if __name__ == "__main__":
    main()
