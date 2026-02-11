import json
import os
import subprocess
import re
from difflib import SequenceMatcher

# CONFIG
EXAMS_JSON_PATH = "app/src/main/assets/exams.json"
PDF_DIR = "fragen"

def normalize_text(text):
    # Standardize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    # Remove common OCR artifacts or specific allowed differences
    # Remove checkbox chars often found in these PDFs
    text = text.replace('', '').replace('☐', '').replace('□', '')
    return text

def get_similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()

def find_best_match(query, large_text):
    # This is a bit expensive for large text, but we can optimize
    # by finding the first few words 
    if not query: return 0.0, ""
    
    # Simple check first
    if query in large_text:
        return 1.0, query
        
    s = SequenceMatcher(None, query, large_text)
    match = s.find_longest_match(0, len(query), 0, len(large_text))
    
    # If we found a significant chunk
    if match.size > 10:
        # Check the region around it in large_text
        start = max(0, match.b - match.a)
        end = min(len(large_text), start + len(query) + 50)
        candidate = large_text[start:end]
        
        # Refine candidate to match length roughly
        # This is a heuristic. 
        # Better: just use the ratio of the query against the best matching block
        pass
        
    return s.ratio(), "" # precise location is hard without more complex logic

def get_pdf_filename(exam_id):
    year, month = exam_id.split('-')
    month_german = "Maerz" if month == "march" else "Oktober"
    
    # Pattern matching for filenames
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

def main():
    if not os.path.exists(EXAMS_JSON_PATH):
        print(f"Error: {EXAMS_JSON_PATH} not found.")
        return

    with open(EXAMS_JSON_PATH, 'r') as f:
        exams = json.load(f)

    report_lines = []
    report_lines.append("# Exam Verification Report")
    report_lines.append(f"Generated on: {os.popen('date').read().strip()}")
    report_lines.append("")

    total_issues = 0
    
    for exam in exams:
        exam_id = exam.get('id')
        print(f"Checking Exam: {exam_id}")
        pdf_path = get_pdf_filename(exam_id)
        
        if not pdf_path:
            report_lines.append(f"## {exam_id}")
            report_lines.append(f"- **ERROR**: PDF not found.")
            continue

        try:
            # -layout for better text flow
            result = subprocess.run(['pdftotext', '-layout', pdf_path, '-'], stdout=subprocess.PIPE, text=True)
            pdf_text = result.stdout
            norm_pdf_text = normalize_text(pdf_text)
        except Exception as e:
            report_lines.append(f"## {exam_id}")
            report_lines.append(f"- **ERROR**: PDF extraction failed: {e}")
            continue

        questions = exam.get('questions', [])
        
        # 1. Count check
        # Heuristic: Count occurrences of "1" followed by typ (Einfachauswahl etc) or numbered questions
        # This is hard to do reliably on raw text, but we can try to find number of expected questions (usually 28 or 60)
        # 2018+ usually 28 questions. Before 2018 usually 28 or 60?
        # Let's just compare JSON count to expectation if we knew it. 
        # Instead, verify if JSON questions cover the content.
        
        exam_issues = []
        
        for q in questions:
            q_id = q.get('id')
            q_text = q.get('text', '')
            
            # Remove potential artifacts from JSON text like appended options
            # e.g. "A) ... "
            # But we want to VERIFY if they are correct. If JSON has "A) ..." in text, and PDF does too, then it's "correct" regarding fidelity, 
            # though maybe semantically wrong. User asked to compare with original.
            # If original PDF has "1. Question... A) Option", and JSON has text="1. Question... A) Option", it is a match.
            # So normalize and check containment.
            
            norm_q_text = normalize_text(q_text)
            
            # Check if this text exists in PDF
            if norm_q_text not in norm_pdf_text:
                # Basic fuzzy check logic: split into chunks or check similarity
                # We can try to find the question number and ensuring text follows.
                
                # Check if it's a near match
                # Use a sliding window or just manual check indicator
                exam_issues.append(f"Q{q_id}: Text mismatch")
                exam_issues.append(f"  JSON: {norm_q_text[:100]}...")
                
                # Attempt to find what IS in the PDF for this question ID if possible?
                # Hard without parsing.
                
                # Double check if removing the artifact helps
                cleaned = re.sub(r'.*', '', q_text).strip()
                norm_cleaned = normalize_text(cleaned)
                if norm_cleaned in norm_pdf_text:
                     exam_issues.append(f"  -> Match found after stripping trailing chars. JSON has metadata in text?")
                
            # Check Options
            for idx, opt in enumerate(q.get('options', [])):
                norm_opt = normalize_text(opt)
                if norm_opt not in norm_pdf_text:
                     exam_issues.append(f"Q{q_id} Opt {idx+1}: Not found")
                     exam_issues.append(f"  JSON: {norm_opt[:100]}...")

        if exam_issues:
            total_issues += len(exam_issues)
            report_lines.append(f"## {exam_id} ({pdf_path})")
            report_lines.append(f"Questions in JSON: {len(questions)}")
            for issue in exam_issues:
                report_lines.append(f"- {issue}")
            report_lines.append("")
        else:
            report_lines.append(f"## {exam_id} - OK ({len(questions)} Qs)")

    with open("verification_report.md", "w") as f:
        f.write("\n".join(report_lines))

    print(f"Done. Issues: {total_issues}")

if __name__ == "__main__":
    main()
