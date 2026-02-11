import json
import os
import subprocess
import re

# CONFIG
EXAMS_JSON_PATH = "app/src/main/assets/exams.json"
PDF_DIR = "fragen"

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

def estimate_pdf_question_count(pdf_path):
    try:
        # Extract text using pdftotext -layout
        result = subprocess.run(['pdftotext', '-layout', pdf_path, '-'], stdout=subprocess.PIPE, text=True)
        text = result.stdout
        
        # Heuristic: Find lines starting with a number and look for the max number <= 60
        # Typical patterns: "1 Einfachauswahl", "28 Aussagenkombination", "60 ..."
        # Also check for "1.", "28." at start of line
        matches = re.findall(r'^\s*(\d+)\s+', text, re.MULTILINE)
        
        # Convert to ints, filter legitimate range (1-60)
        nums = [int(m) for m in matches if 1 <= int(m) <= 60]
        
        if not nums:
            return 0
            
        # Filter for likely max
        # usually 28 or 60.
        max_num = max(nums)
        
        # Specific check for 28 vs 60
        if 28 in nums and 60 not in nums:
             # Likely 28 questions
             return 28
        if 60 in nums:
             return 60
             
        return max_num
        
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")
        return 0

def check_text_quality(text):
    # Check for common merged artifacts
    issues = []
    if "A)" in text and len(text) < 200: # Short text with A) might be merged option
         issues.append("Contains 'A)' inside text")
    if "1." in text and "2." in text: # Numbered list inside text
         issues.append("Contains numbered list inside text")
    return issues

def main():
    if not os.path.exists(EXAMS_JSON_PATH):
        print(f"Error: {EXAMS_JSON_PATH} not found.")
        return

    with open(EXAMS_JSON_PATH, 'r') as f:
        exams = json.load(f)

    # Sort exams by Year/Month
    exams.sort(key=lambda x: (x.get('year'), x.get('month')))

    print("| Exam ID | App Qs | PDF Qs (Est) | Gap | Status | Issues |")
    print("| :--- | :---: | :---: | :---: | :--- | :--- |")

    overall_gap_count = 0

    for exam in exams:
        exam_id = exam.get('id')
        questions = exam.get('questions', [])
        app_count = len(questions)
        
        pdf_path = get_pdf_filename(exam_id)
        pdf_est = 0
        if pdf_path:
            pdf_est = estimate_pdf_question_count(pdf_path)
        else:
            pdf_est = "N/A"

        gap = 0
        if isinstance(pdf_est, int):
            gap = pdf_est - app_count
        
        status = "OK"
        if gap > 0:
            status = "**MISSING**"
            overall_gap_count += gap
        elif gap < 0:
             status = "EXTRA?"
        
        # Content checks
        issue_flags = []
        if gap > 0:
            issue_flags.append(f"Missing {gap} Qs")
        
        # Check first question for text quality
        if questions:
            q1_text = questions[0].get('text', '')
            quality_issues = check_text_quality(q1_text)
            if quality_issues:
                issue_flags.extend(quality_issues)

        issues_str = ", ".join(issue_flags) if issue_flags else ""
        
        print(f"| {exam_id} | {app_count} | {pdf_est} | {gap if isinstance(gap, int) else '-'} | {status} | {issues_str} |")

    print(f"\nTotal Missing Questions (Est): {overall_gap_count}")

if __name__ == "__main__":
    main()
