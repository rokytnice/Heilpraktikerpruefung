import json
import os
import re
import sys
from pypdf import PdfReader

# Adjust paths to work from repo root
JSON_PATH = "app/src/main/assets/exams.json"
PDF_DIR = "fragen/"
REPORT_PATH = "integrity_report.txt"

MONTH_MAP = {
    "March": "Maerz",
    "October": "Oktober"
}

def normalize_text(text):
    # Standard normalization: lower, single spaces
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def normalize_text_nospace(text):
    # Aggressive normalization: lower, no spaces, no punctuation
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r'[^a-z0-9]', '', text)
    return text

def extract_text_from_pdf(pdf_path):
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + " "
        return text
    except Exception as e:
        print(f"Error reading PDF {pdf_path}: {e}")
        return ""

def find_pdf_file(year, month_en):
    month_de = MONTH_MAP.get(month_en, month_en)
    if not os.path.exists(PDF_DIR):
        print(f"PDF directory not found: {PDF_DIR}")
        return []
    files = os.listdir(PDF_DIR)
    candidates = []
    for f in files:
        if str(year) in f and month_de in f and f.lower().endswith(".pdf"):
            candidates.append(os.path.join(PDF_DIR, f))
    return candidates

def check_match(needle, haystack_norm, haystack_nospace):
    if not needle or not needle.strip():
        return True # Empty string matches

    # 1. Standard normalization check
    n_norm = normalize_text(needle)
    if n_norm in haystack_norm:
        return True

    # 2. No-space check (for merged words issue)
    n_nospace = normalize_text_nospace(needle)
    # Require minimal length to avoid false positives on short strings like "A", "B"
    if len(n_nospace) > 5 and n_nospace in haystack_nospace:
        return True

    # 3. Partial check (first half) if long enough to catch trailing differences
    if len(n_norm) > 40:
        half_len = len(n_norm) // 2
        if n_norm[:half_len] in haystack_norm:
            return True

    # 4. Partial check (second half) if long enough to catch leading differences
    if len(n_norm) > 40:
        half_len = len(n_norm) // 2
        if n_norm[half_len:] in haystack_norm:
            return True

    return False

def verify():
    if not os.path.exists(JSON_PATH):
        print(f"JSON not found: {JSON_PATH}")
        return

    try:
        with open(JSON_PATH, 'r', encoding='utf-8') as f:
            exams = json.load(f)
    except Exception as e:
        print(f"Error loading JSON: {e}")
        return

    with open(REPORT_PATH, 'w', encoding='utf-8') as report:
        report.write("VERIFICATION REPORT\n")
        report.write("===================\n\n")

        total_exams = 0
        exams_with_issues = 0

        for exam in exams:
            total_exams += 1
            exam_id = exam.get("id")
            year = exam.get("year")
            month = exam.get("month")
            questions = exam.get("questions", [])

            header = f"--- Exam: {year} {month} ({exam_id}) ---"
            print(header)
            report.write(header + "\n")

            if not questions:
                report.write("  WARNING: No questions in JSON.\n\n")
                exams_with_issues += 1
                continue

            pdf_files = find_pdf_file(year, month)
            if not pdf_files:
                report.write(f"  ERROR: No PDF found for {month} {year}.\n\n")
                exams_with_issues += 1
                continue

            pdf_path = pdf_files[0]
            if len(pdf_files) > 1:
                report.write(f"  Note: Multiple PDFs found, using {pdf_path}\n")
            else:
                report.write(f"  Source PDF: {pdf_path}\n")

            raw_pdf_text = extract_text_from_pdf(pdf_path)

            if len(raw_pdf_text) < 100:
                report.write("  ERROR: PDF text empty or too short (Scanned image?).\n\n")
                exams_with_issues += 1
                continue

            # Pre-compute haystack versions
            pdf_text_norm = normalize_text(raw_pdf_text)
            pdf_text_nospace = normalize_text_nospace(raw_pdf_text)

            exam_issues = []

            # Check for each question
            for q in questions:
                q_id = q.get('id')
                q_text = q.get("text", "")

                # Check Question Text
                if not check_match(q_text, pdf_text_norm, pdf_text_nospace):
                    exam_issues.append(f"  [Q{q_id}] Question Text Mismatch:\n    JSON: '{q_text[:100]}...'")

                # Check Options (Answers)
                opts = q.get("options", [])
                for idx, opt in enumerate(opts):
                    if not check_match(opt, pdf_text_norm, pdf_text_nospace):
                        exam_issues.append(f"  [Q{q_id}] Option {idx+1} Mismatch:\n    JSON: '{opt[:100]}...'")

                # Check Statements (Aussagen)
                stmts = q.get("statements", [])
                for idx, stmt in enumerate(stmts):
                    if not check_match(stmt, pdf_text_norm, pdf_text_nospace):
                        exam_issues.append(f"  [Q{q_id}] Statement {idx+1} Mismatch:\n    JSON: '{stmt[:100]}...'")

            if exam_issues:
                exams_with_issues += 1
                for issue in exam_issues:
                    report.write(issue + "\n")
                report.write("\n")
            else:
                report.write("  All questions, options, and statements verified.\n\n")

        report.write(f"SUMMARY: {exams_with_issues} exams with issues out of {total_exams} exams checked.\n")
        print(f"Verification complete. Report saved to {REPORT_PATH}")

if __name__ == "__main__":
    verify()
