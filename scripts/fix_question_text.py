#!/usr/bin/env python3
"""Fix corrupted question text and statements in exams.json by re-extracting from PDFs.

Fixes three corruption patterns:
1. Statement fragments leaked into question text after "?"
2. "aufgabe" prefix from old PDF layout
3. Merged/mis-split statements with embedded number markers

Usage: python3 scripts/fix_question_text.py [--dry-run]
Run from project root.
"""

import json
import re
import subprocess
import os
import sys

EXAMS_JSON = "app/src/main/assets/exams.json"
FRAGEN_DIR = "fragen"

# Exams to skip (scanned/no text, answer-key-only, or empty)
SKIP_EXAMS = {
    "2007-october",  # scanned PDF
    "2014-october",  # scanned PDF
    "2009-october",  # empty exam
    "2010-march",    # empty exam / answer-key-only
}


def get_pdf_for_exam(exam_id):
    """Find PDF file for an exam ID."""
    parts = exam_id.split('-')
    year = parts[0]
    month_eng = parts[1]
    month_de = "Maerz" if month_eng == "march" else "Oktober"
    for pattern in [
        f"{month_de}-{year}.pdf",
        f"HPP_Pruefung_{month_de}_{year}_mit_Loesungen_.pdf",
        f"HPP_Pruefung_{month_de}_{year}_mit_Loesungen.pdf",
        f"HPP_Pruefung_{month_de}_{year}_.pdf",
        f"HPP_Pruefung_{month_de}_{year}_mit_Loesungen_A_B.pdf",
        f"HPP_Pruefung_{month_de}_{year}_Gruppe_A_mit_Loesungen.pdf",
        f"HPP_Pruefung_{month_de}_{year}_mit_Loesungen_Gruppe_A.pdf",
    ]:
        path = os.path.join(FRAGEN_DIR, pattern)
        if os.path.exists(path):
            return path
    return None


def extract_pdf_text(pdf_path):
    """Extract text from PDF using pdftotext."""
    result = subprocess.run(['pdftotext', pdf_path, '-'],
                            capture_output=True, text=True)
    return result.stdout


def get_gruppe_a_section(text):
    """Get Gruppe A section from PDF text (skip Gruppe B if present)."""
    # Count Gruppe B occurrences
    b_matches = list(re.finditer(r'Gruppe\s*B', text))
    if len(b_matches) >= 17:
        # "Gruppe B" is a page header, the whole PDF is Gruppe B - use all text
        return text
    for m in b_matches:
        # If Gruppe B appears after 30% of text, it's a section divider
        if m.start() > len(text) * 0.3:
            return text[:m.start()]
    return text


def extract_questions_from_pdf(text):
    """Extract questions with clean text and statements from PDF text."""
    questions = {}

    # Find question start markers
    q_pattern1 = re.compile(
        r'(?:^|\n)\s*(\d{1,2})\s+(Einfachauswahl|Aussage\s*n?\s*kombination|Mehrfachauswahl(?:aufgabe)?)',
        re.MULTILINE)
    q_pattern2 = re.compile(
        r'(?:^|\n)\s*(\d{1,2})\s*\n\s*(Einfachauswahl|Aussage\s*n?\s*kombination|Mehrfachauswahl(?:aufgabe)?)',
        re.MULTILINE)

    all_starts = {}
    for m in list(q_pattern1.finditer(text)) + list(q_pattern2.finditer(text)):
        num = int(m.group(1))
        if 1 <= num <= 28:
            if num not in all_starts or m.start() < all_starts[num][0]:
                all_starts[num] = (m.start(), m.end(), m.group(2))

    sorted_nums = sorted(all_starts.keys())

    for i, qnum in enumerate(sorted_nums):
        start, end, qtype = all_starts[qnum]
        next_start = (all_starts[sorted_nums[i + 1]][0]
                      if i + 1 < len(sorted_nums)
                      else min(start + 5000, len(text)))
        q_region = text[end:next_start]

        # Normalize type
        if 'Mehrfach' in qtype:
            qtype = 'Mehrfachauswahl'
        if 'ombination' in qtype and qtype != 'Aussagenkombination':
            qtype = 'Aussagenkombination'

        # Find first A option marker to delimit question+statements region
        first_opt = None
        for fmt in [r'(?:^|\n)\s*A\)\s', r'(?:^|\n)\s*A\.\s',
                     r'(?:^|\n)\s*\u201aA\)\s', r'(?:^|\n)\s*\u201eA\)\s']:
            m = re.search(fmt, q_region)
            if m and (first_opt is None or m.start() < first_opt):
                first_opt = m.start()

        # Also look for "Nur die Aussage" as option start indicator (A. or 1. format)
        for fmt in [r'(?:^|\n)\s*(?:\u201a)?A[.)]\s*Nur\s+die\s+Aussage',
                     r'(?:^|\n)\s*1[.)]\s*Nur\s+die\s+Aussage']:
            m = re.search(fmt, q_region)
            if m and (first_opt is None or m.start() < first_opt):
                first_opt = m.start()
        # Also look for "Alle Aussagen sind richtig" without A-E prefix
        m = re.search(r'(?:^|\n)\s*\d[.)]\s*Alle\s+Aussagen\s+sind\s+richtig', q_region)
        if m and first_opt is not None and m.start() > first_opt:
            pass  # already found earlier option start
        elif m and (first_opt is None or m.start() < first_opt):
            # Search backwards for the first numbered option
            search_before = q_region[:m.start()]
            num_opt = re.search(r'(?:^|\n)\s*1[.)]\s*Nur\s+die\s+Aussage', search_before)
            if num_opt:
                first_opt = num_opt.start()

        pre_opts = q_region[:first_opt] if first_opt else q_region

        # Clean header junk from pre_opts
        pre_opts = re.sub(
            r'Heilpraktiker.*?(?:Gruppe\s+[AB]|Psychotherapie)\s*(?:\d+\s*)?(?:\n|$)',
            '\n', pre_opts)

        # Parse statements for Aussagenkombination
        statements = []
        q_text = ""

        if qtype == 'Aussagenkombination':
            # Find numbered statement markers (1. or 1))
            # Only match digits 1-9 at start of line or after newline
            # Allow zero or more spaces after delimiter (some PDFs have "1.Text")
            stmt_matches = list(re.finditer(
                r'(?:^|\n)\s*(\d)[.)]\s*', pre_opts))

            # Filter: only keep matches with sequential or near-sequential numbers
            # to avoid false positives like "6. Lebensjahr" in running text
            if stmt_matches:
                filtered = [stmt_matches[0]]
                for sm in stmt_matches[1:]:
                    prev_num = int(filtered[-1].group(1))
                    curr_num = int(sm.group(1))
                    # Accept if number is sequential or close
                    if curr_num == prev_num + 1:
                        filtered.append(sm)
                    elif curr_num > prev_num and curr_num <= prev_num + 2:
                        # Allow small gap (e.g., skipped number)
                        filtered.append(sm)
                stmt_matches = filtered

            if stmt_matches and int(stmt_matches[0].group(1)) == 1:
                # Question text is everything before first statement
                q_text = pre_opts[:stmt_matches[0].start()].strip()

                # Extract each statement's full text
                for j, sm in enumerate(stmt_matches):
                    stmt_start = sm.end()
                    if j + 1 < len(stmt_matches):
                        stmt_end = stmt_matches[j + 1].start()
                    else:
                        stmt_end = len(pre_opts)
                    stmt_text = pre_opts[stmt_start:stmt_end].strip()
                    # Normalize whitespace (join multi-line)
                    stmt_text = re.sub(r'\s*\n\s*', ' ', stmt_text)
                    stmt_text = re.sub(r'\s+', ' ', stmt_text)
                    # Remove header artifacts
                    stmt_text = re.sub(
                        r'Heilpraktiker.*?(?:Gruppe\s+[AB]|Psychotherapie)\s*(?:\d+\s*)?',
                        '', stmt_text).strip()
                    if stmt_text:
                        statements.append(stmt_text)
            else:
                q_text = pre_opts.strip()
        else:
            q_text = pre_opts.strip()

        # Clean question text
        q_text = re.sub(r'\s*\n\s*', ' ', q_text)
        q_text = re.sub(r'\s+', ' ', q_text)
        q_text = re.sub(
            r'Heilpraktiker.*?(?:Gruppe\s+[AB]|Psychotherapie)\s*(?:\d+\s*)?',
            '', q_text).strip()
        # Remove "aufgabe" prefix
        q_text = re.sub(r'^[Aa]ufgabe\s*', '', q_text).strip()
        # Remove "Wählen Sie..." instructions (can appear before or after text)
        # First remove leading "Wählen Sie..." (before question text)
        q_text = re.sub(r'^Wählen Sie[^?!]*[?!]\s*', '', q_text).strip()
        # Then remove trailing "Wählen Sie..." (after question mark)
        q_text = re.sub(r'\s*Wählen Sie[^?]*$', '', q_text).strip()
        # Remove page numbers that crept in
        q_text = re.sub(r'^\d+\s+', '', q_text).strip()

        questions[qnum] = {
            'type': qtype,
            'text': q_text,
            'statements': statements,
        }

    return questions


def is_text_corrupted(json_text):
    """Check if a question's text field shows corruption patterns."""
    # Pattern 1: statement fragments after "?"
    qmark_pos = json_text.find('?')
    if qmark_pos > 0 and qmark_pos < len(json_text) - 5:
        after = json_text[qmark_pos + 1:].strip()
        if len(after) > 10 and not after.startswith('Wählen'):
            return True

    # Pattern 2: "aufgabe" prefix
    if json_text.lower().startswith('aufgabe'):
        return True

    return False


def are_statements_corrupted(json_stmts):
    """Check if statements show corruption (truncated or merged)."""
    for s in json_stmts:
        # Merged statements: embedded "2." or "3." etc inside a statement
        if re.search(r'\s+\d\.\s+[A-Z]', s):
            return True
    return False


def normalize_text(text):
    """Normalize text for comparison."""
    t = re.sub(r'\s+', ' ', text).strip()
    t = re.sub(r'[""„‟»«\u201a\u201e\u201c\u201d]', '"', t)
    t = re.sub(r'[''‛`\u2018\u2019]', "'", t)
    return t


def text_similarity(a, b):
    """Check how similar two texts are (word overlap ratio)."""
    if not a or not b:
        return 0.0
    words_a = set(normalize_text(a).lower().split())
    words_b = set(normalize_text(b).lower().split())
    if not words_a or not words_b:
        return 0.0
    intersection = words_a & words_b
    return len(intersection) / max(len(words_a), len(words_b))


def main():
    dry_run = '--dry-run' in sys.argv

    with open(EXAMS_JSON, 'r') as f:
        exams = json.load(f)
    print(f"Loaded {len(exams)} exams")

    total_text_fixes = 0
    total_stmt_fixes = 0
    total_aufgabe_fixes = 0
    exam_fixes = {}

    for exam in exams:
        eid = exam['id']
        if eid in SKIP_EXAMS:
            continue
        if not exam['questions']:
            continue

        pdf_path = get_pdf_for_exam(eid)
        if not pdf_path:
            continue

        # Extract text from PDF
        pdf_text = extract_pdf_text(pdf_path)
        if not pdf_text or len(pdf_text) < 500:
            print(f"  {eid}: PDF text too short, skipping")
            continue

        # Handle Gruppe A/B
        pdf_text = get_gruppe_a_section(pdf_text)

        # Extract questions from PDF
        pdf_questions = extract_questions_from_pdf(pdf_text)
        if not pdf_questions:
            print(f"  {eid}: No questions extracted from PDF, skipping")
            continue

        fixes_in_exam = 0

        for q in exam['questions']:
            qid = q['id']
            if qid not in pdf_questions:
                continue

            pq = pdf_questions[qid]
            changed = False

            # Check and fix question text
            json_text = q.get('text', '')
            pdf_q_text = pq['text']

            if not pdf_q_text:
                continue

            # Fix "aufgabe" prefix
            if json_text.lower().startswith('aufgabe'):
                q['text'] = pdf_q_text
                total_aufgabe_fixes += 1
                changed = True

            # Fix statement-leaked text
            elif is_text_corrupted(json_text):
                # Verify the PDF text is reasonable (similar topic)
                sim = text_similarity(json_text, pdf_q_text)
                if sim > 0.3 or pdf_q_text.split('?')[0] in json_text:
                    q['text'] = pdf_q_text
                    total_text_fixes += 1
                    changed = True

            # Fix statements
            json_stmts = q.get('statements', [])
            pdf_stmts = pq.get('statements', [])

            if pdf_stmts and q.get('type') == 'Aussagenkombination':
                needs_stmt_fix = False

                # Check if JSON statements are truncated/merged
                if are_statements_corrupted(json_stmts):
                    needs_stmt_fix = True
                elif len(json_stmts) < len(pdf_stmts) and len(json_stmts) <= 3:
                    # Too few statements compared to PDF
                    needs_stmt_fix = True
                elif json_stmts and pdf_stmts:
                    # Check if any JSON statement is a proper prefix of PDF
                    # statement (truncated)
                    for js, ps in zip(json_stmts, pdf_stmts):
                        js_norm = normalize_text(js)
                        ps_norm = normalize_text(ps)
                        if (len(js_norm) < len(ps_norm) - 5 and
                                ps_norm.startswith(js_norm[:min(30, len(js_norm))])):
                            needs_stmt_fix = True
                            break

                if needs_stmt_fix:
                    q['statements'] = pdf_stmts
                    total_stmt_fixes += 1
                    changed = True
                    # Also fix the text if it wasn't already fixed
                    # (the leaked fragments are in the text)
                    if not is_text_corrupted(json_text) and pdf_q_text:
                        # Check if current text has extra content that shouldn't
                        # be there
                        json_norm = normalize_text(json_text)
                        pdf_norm = normalize_text(pdf_q_text)
                        if len(json_norm) > len(pdf_norm) + 20:
                            q['text'] = pdf_q_text
                            total_text_fixes += 1

            if changed:
                fixes_in_exam += 1

        if fixes_in_exam > 0:
            exam_fixes[eid] = fixes_in_exam

    # Summary
    print(f"\n{'DRY RUN - ' if dry_run else ''}Summary:")
    print(f"  Text fixes (statement leaks): {total_text_fixes}")
    print(f"  Statement fixes (truncated/merged): {total_stmt_fixes}")
    print(f"  Aufgabe prefix removals: {total_aufgabe_fixes}")
    print(f"  Total questions fixed: {sum(exam_fixes.values())}")
    print(f"  Exams affected: {len(exam_fixes)}")

    if exam_fixes:
        print(f"\nFixes per exam:")
        for eid in sorted(exam_fixes.keys()):
            print(f"  {eid}: {exam_fixes[eid]}")

    if not dry_run:
        with open(EXAMS_JSON, 'w') as f:
            json.dump(exams, f, ensure_ascii=False, indent=2)
        print(f"\nSaved to {EXAMS_JSON}")
    else:
        print(f"\nDry run - no changes written")


if __name__ == '__main__':
    main()
