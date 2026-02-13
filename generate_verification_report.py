import json
import os
import re
from pypdf import PdfReader

JSON_PATH = "app/src/main/assets/exams.json"
PDF_DIR = "fragen/"
REPORT_PATH = "verification_report.txt"

MONTH_MAP = {
    "March": "Maerz",
    "October": "Oktober"
}

# Known limitations that cannot be fixed
KNOWN_SCANNED = {"2007-october", "2014-october"}  # Fully scanned PDFs
KNOWN_ANSWER_KEY_ONLY = {"2008-march", "2009-march"}  # Only answer key extractable
KNOWN_EMPTY = {"2009-october", "2010-march"}  # No questions in JSON (no source)
KNOWN_TEXT_MISMATCHES = {
    # (exam_id, question_id): reason
    ("2005-march", 5): "PDF OCR typo 'Weiche' vs correct 'Welche'",
    ("2005-march", 8): "Scanned page, no extractable text",
    ("2005-march", 17): "Manually corrected from PDF image",
    ("2002-october", 7): "Manually corrected garbled OCR text",
    ("2004-october", 9): "Manually corrected garbled OCR text",
}


def normalize_text(text):
    text = text.lower()
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def normalize_text_nospace(text):
    text = text.lower()
    text = re.sub(r'[^a-zäöüß0-9]', '', text)
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
    except Exception:
        return ""


def find_pdf_file(year, month_en):
    month_de = MONTH_MAP.get(month_en, month_en)
    files = os.listdir(PDF_DIR)
    candidates = []
    for f in files:
        if str(year) in f and month_de in f and f.lower().endswith(".pdf"):
            candidates.append(os.path.join(PDF_DIR, f))
    return candidates


def check_match(needle, haystack_norm, haystack_nospace):
    if not needle.strip():
        return True

    n_norm = normalize_text(needle)
    if n_norm in haystack_norm:
        return True

    n_nospace = normalize_text_nospace(needle)
    if len(n_nospace) > 10 and n_nospace in haystack_nospace:
        return True

    if len(n_norm) > 40:
        half_len = len(n_norm) // 2
        if n_norm[:half_len] in haystack_norm:
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

    # Sort exams chronologically
    exams.sort(key=lambda e: (e.get("year", 0), 0 if e.get("month") == "March" else 1))

    # Tracking
    verified_full = []
    verified_known = []
    unverifiable = []
    real_issues = []

    total_questions = 0
    total_answers = 0
    matched_questions = 0
    matched_answers = 0

    with open(REPORT_PATH, 'w', encoding='utf-8') as report:
        report.write("VERIFICATION REPORT: exams.json vs Source PDFs\n")
        report.write("=" * 50 + "\n\n")

        for exam in exams:
            exam_id = exam.get("id")
            year = exam.get("year")
            month = exam.get("month")
            questions = exam.get("questions", [])
            label = f"{month} {year}"

            # Empty exams
            if not questions:
                if exam_id in KNOWN_EMPTY:
                    unverifiable.append(f"  {label:20s} Empty exam (no source PDF with questions)")
                else:
                    unverifiable.append(f"  {label:20s} No questions in JSON")
                continue

            # Find PDF
            pdf_files = find_pdf_file(year, month)
            if not pdf_files:
                unverifiable.append(f"  {label:20s} No PDF found")
                continue

            pdf_path = pdf_files[0]
            raw_pdf_text = extract_text_from_pdf(pdf_path)

            # Scanned/answer-key-only PDFs
            if len(raw_pdf_text) < 500:
                reason = "scanned PDF" if exam_id in KNOWN_SCANNED else "answer-key-only PDF"
                unverifiable.append(f"  {label:20s} {len(questions):2d} questions ({reason})")
                continue

            pdf_text_norm = normalize_text(raw_pdf_text)
            pdf_text_nospace = normalize_text_nospace(raw_pdf_text)

            q_match = 0
            a_match = 0
            q_total = len(questions)
            a_total = 0
            text_mismatches = []

            for q in questions:
                q_text = q.get("text", "")
                qid = q.get("id")

                if check_match(q_text, pdf_text_norm, pdf_text_nospace):
                    q_match += 1
                else:
                    known_key = (exam_id, qid)
                    reason = KNOWN_TEXT_MISMATCHES.get(known_key)
                    text_mismatches.append((qid, reason))

                opts = q.get("options", [])
                for opt in opts:
                    a_total += 1
                    if check_match(opt, pdf_text_norm, pdf_text_nospace):
                        a_match += 1

            total_questions += q_total
            total_answers += a_total
            matched_questions += q_match
            matched_answers += a_match

            if q_match == q_total and a_match == a_total:
                verified_full.append(f"  {label:20s} {q_match:2d}/{q_total:2d} questions, {a_match:3d}/{a_total:3d} answers")
            elif a_match == a_total and all(r is not None for _, r in text_mismatches):
                # All answer options match, text mismatches are all known/explained
                details = "; ".join(f"Q{qid}: {r}" for qid, r in text_mismatches)
                verified_known.append(f"  {label:20s} {q_match:2d}/{q_total:2d} questions, {a_match:3d}/{a_total:3d} answers  [{details}]")
            else:
                unknown_text = [f"Q{qid}" for qid, r in text_mismatches if r is None]
                opt_miss = a_total - a_match
                detail = f"{q_match}/{q_total} questions, {a_match}/{a_total} answers"
                if unknown_text:
                    detail += f"  [text: {', '.join(unknown_text)}]"
                if opt_miss > 0:
                    detail += f"  [{opt_miss} option mismatches]"
                real_issues.append(f"  {label:20s} {detail}")

        # Write summary report
        report.write(f"Fully verified ({len(verified_full)} exams):\n")
        for line in verified_full:
            report.write(line + "\n")

        if verified_known:
            report.write(f"\nVerified with known text differences ({len(verified_known)} exams):\n")
            for line in verified_known:
                report.write(line + "\n")

        if real_issues:
            report.write(f"\nIssues found ({len(real_issues)} exams):\n")
            for line in real_issues:
                report.write(line + "\n")

        report.write(f"\nNot verifiable ({len(unverifiable)} exams):\n")
        for line in unverifiable:
            report.write(line + "\n")

        report.write(f"\n{'=' * 50}\n")
        report.write(f"Total: {len(exams)} exams, {total_questions} questions checked\n")
        report.write(f"Questions matched: {matched_questions}/{total_questions}\n")
        report.write(f"Answers matched:   {matched_answers}/{total_answers}\n")
        report.write(f"Fully verified:    {len(verified_full)} exams\n")
        report.write(f"Known diffs:       {len(verified_known)} exams\n")
        report.write(f"Unverifiable:      {len(unverifiable)} exams\n")
        if real_issues:
            report.write(f"Real issues:       {len(real_issues)} exams\n")

        # Print summary
        print(f"\nFully verified: {len(verified_full)} exams")
        print(f"Known diffs:    {len(verified_known)} exams")
        print(f"Unverifiable:   {len(unverifiable)} exams")
        print(f"Real issues:    {len(real_issues)} exams")
        print(f"Questions: {matched_questions}/{total_questions}, Answers: {matched_answers}/{total_answers}")


if __name__ == "__main__":
    verify()
