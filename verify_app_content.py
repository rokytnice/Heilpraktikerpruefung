import argparse
import os
import sys
import json
import time
import subprocess
import re
from scripts import adb_utils, text_utils

# Configuration
EXAMS_JSON_PATH = "app/src/main/assets/exams.json"
PDF_DIR = "fragen"

def main():
    parser = argparse.ArgumentParser(description="Verify app content against PDF")
    parser.add_argument("--exam_id", help="Verify a specific exam ID")
    args = parser.parse_args()

    # Load known exams to iterate
    if not os.path.exists(EXAMS_JSON_PATH):
        print(f"Error: {EXAMS_JSON_PATH} not found.")
        return

    with open(EXAMS_JSON_PATH, 'r') as f:
        exams = json.load(f)

    # Filter if specific exam requested
    if args.exam_id:
        exams = [e for e in exams if e.get('id') == args.exam_id]

    # 1. Initialize Report
    report_lines = []
    report_lines.append("# App Content Verification Report")
    report_lines.append(f"Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")

    total_issues = 0
    
    # 2. Iterate through exams
    for exam in exams:
        exam_id = exam.get('id')
        print(f"Verifying Exam: {exam_id}")
        
        # A. Extract PDF Text
        pdf_path = get_pdf_filename(exam_id)
        if not pdf_path:
            report_lines.append(f"## {exam_id}")
            report_lines.append(f"- **ERROR**: PDF not found for {exam_id}")
            continue

        try:
            # -layout for better text flow
            result = subprocess.run(['pdftotext', '-layout', pdf_path, '-'], stdout=subprocess.PIPE, text=True)
            pdf_text = result.stdout
            norm_pdf_text = text_utils.normalize_text(pdf_text)
        except Exception as e:
            report_lines.append(f"## {exam_id}")
            report_lines.append(f"- **ERROR**: PDF extraction failed: {e}")
            continue

        exam_issues = []
        questions = exam.get('questions', [])

        # B. Compare JSON Content vs PDF Text
        for q in questions:
            q_id = q.get('id')
            q_text = q.get('text', '')
            
            # Check Question Text
            match, ratio = text_utils.verify_text_match(q_text, norm_pdf_text)
            if not match:
                # Try finding it with relaxed constraints or check if it's a known artifact
                # e.g. "A)" being part of the text
                cleaned_text = re.sub(r'^[A-Z]\)\s*', '', q_text) # Remove leading "A) "
                match_cleaned, ratio_cleaned = text_utils.verify_text_match(cleaned_text, norm_pdf_text)
                
                if not match_cleaned and ratio < 0.6: # Only report if it's a bad match
                    exam_issues.append(f"Q{q_id}: Text mismatch (Similarity: {ratio:.2f})")
                    exam_issues.append(f"  App: {q_text[:100]}...")
            
            # Check Options
            for idx, opt in enumerate(q.get('options', [])):
                match_opt, ratio_opt = text_utils.verify_text_match(opt, norm_pdf_text)
                if not match_opt and ratio_opt < 0.6:
                     exam_issues.append(f"Q{q_id} Opt {idx+1}: Option mismatch (Similarity: {ratio_opt:.2f})")
                     exam_issues.append(f"  App: {opt[:50]}...")

        if exam_issues:
            total_issues += len(exam_issues)
            report_lines.append(f"## {exam_id} ({pdf_path})")
            report_lines.append(f"Questions in App: {len(questions)}")
            for issue in exam_issues:
                report_lines.append(f"- {issue}")
            report_lines.append("")
        else:
            report_lines.append(f"## {exam_id} - OK ({len(questions)} Qs)")

    # 3. Save Report
    with open("app_verification_report.md", "w") as f:
        f.write("\n".join(report_lines))

    print(f"Verification complete. Total issues found: {total_issues}")
    print("Report saved to app_verification_report.md")

def get_pdf_filename(exam_id):
    # Reuse logic to find PDF
    year, month = exam_id.split('-')
    month_german = "Maerz" if month == "march" else "Oktober"
    patterns = [
        f"HPP_Pruefung_{month_german}_{year}",
        f"{month_german}-{year}",
        f"Oktober-{year}" if month == "october" else f"Maerz-{year}"
    ]
    for f in os.listdir(PDF_DIR):
        if not f.endswith(".pdf"): continue
        for p in patterns:
            if f.startswith(p):
                return os.path.join(PDF_DIR, f)
    return None


if __name__ == "__main__":
    main()
