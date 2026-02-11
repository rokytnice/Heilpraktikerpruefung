#!/usr/bin/env python3
"""Extract answer options from PDF exam files and apply to exams.json.

Two operations:
1. Extract options from PDFs for questions with empty options arrays
2. Strip A)/B)/C)/D)/E) or A./B./C./D./E. prefixes from existing options
"""

import json
import re
import fitz  # PyMuPDF
import os

FRAGEN_DIR = "fragen"
EXAMS_JSON = "app/src/main/assets/exams.json"


def extract_text_from_pdf(pdf_path):
    """Extract all text from a PDF file."""
    doc = fitz.open(pdf_path)
    full_text = ""
    for page in doc:
        full_text += page.get_text() + "\n"
    doc.close()
    return full_text


def clean_text(text):
    """Remove special characters and normalize."""
    text = text.replace('\xa0', ' ')
    text = text.replace('\x01', '')
    text = text.replace('\x02', '')
    return text


def find_option_blocks(text):
    """Find all complete A...B...C...D...E option blocks.

    Handles both "X)" and "X." format markers.
    Returns list of dicts: {'start', 'options': [5 strings]}
    """
    blocks = []

    # Detect which format this text uses: "A)" vs "A."
    # Count occurrences of each
    a_paren_count = len(re.findall(r'\bA\)\s', text))
    a_dot_count = len(re.findall(r'\bA\.\s', text))

    if a_paren_count >= a_dot_count:
        marker_pattern = r'[A-E]\)\s'
        marker_re = lambda letter: re.compile(r'\b' + letter + r'\)\s')
        strip_len = 2  # "X)"
    else:
        marker_pattern = r'[A-E]\.\s'
        marker_re = lambda letter: re.compile(r'\b' + letter + r'\.\s')
        strip_len = 2  # "X."

    # Find all A positions
    a_re = marker_re('A')
    a_positions = [(m.start(), m.end()) for m in a_re.finditer(text)]

    for a_start, a_end in a_positions:
        search_region = text[a_start:a_start + 4000]

        # Find B, C, D, E in order after A
        option_markers = [('A', 0, a_end - a_start)]
        current_pos = a_end - a_start

        found_all = True
        for letter in ['B', 'C', 'D', 'E']:
            lre = marker_re(letter)
            m = lre.search(search_region, current_pos)
            if m:
                option_markers.append((letter, m.start(), m.end()))
                current_pos = m.end()
            else:
                found_all = False
                break

        if not found_all:
            continue

        # Check gaps aren't too large (max 800 chars between options)
        valid = True
        for i in range(1, len(option_markers)):
            gap = option_markers[i][1] - option_markers[i-1][1]
            if gap > 800:
                valid = False
                break
        if not valid:
            continue

        # Extract option texts
        options = []
        for i, (letter, mark_start, mark_end) in enumerate(option_markers):
            if i + 1 < len(option_markers):
                text_end = option_markers[i + 1][1]
            else:
                # For E), find end
                remaining = search_region[mark_end:mark_end + 500]
                end_match = re.search(r'\n\s*\n\s*\d{1,2}\s', remaining)
                if end_match:
                    text_end = mark_end + end_match.start()
                else:
                    end_match2 = re.search(r'\n\s*\n\s*\n', remaining)
                    if end_match2:
                        text_end = mark_end + end_match2.start()
                    else:
                        text_end = mark_end + min(300, len(remaining))

            opt_text = search_region[mark_end:text_end].strip()
            # Clean multiline
            opt_text = re.sub(r'\s*\n\s*', ' ', opt_text)
            opt_text = re.sub(r'\s+', ' ', opt_text)
            # Remove page headers
            opt_text = re.sub(r'Heilpraktiker(?:über)?prüfung.*?(?:Gruppe [AB]|$)', '', opt_text).strip()
            options.append(opt_text)

        # Validate: all options should have some text
        if all(o.strip() for o in options) and len(options) == 5:
            blocks.append({
                'start': a_start,
                'options': options
            })

    return blocks


def associate_blocks_with_questions(text, blocks):
    """Associate option blocks with question numbers.
    Returns dict: {q_num: [5 option strings]}
    """
    questions = {}

    for block in blocks:
        # Look backward from this block to find the question number
        look_back_start = max(0, block['start'] - 2500)
        look_back = text[look_back_start:block['start']]

        # Find question number candidates
        candidates = []

        # Pattern 1: "N Einfachauswahl/Aussagenkombination/Mehrfachauswahl"
        for m in re.finditer(r'(?:^|\n)\s*(\d{1,2})\s+(?:Einfachauswahl|Aussagenkombination|Mehrfachauswahl)', look_back):
            num = int(m.group(1))
            if 1 <= num <= 28:
                candidates.append((num, m.start()))

        # Pattern 2: "N\nEinfachauswahl/Aussagenkombination/Mehrfachauswahl"
        for m in re.finditer(r'(?:^|\n)\s*(\d{1,2})\s*\n\s*(?:Einfachauswahl|Aussagenkombination|Mehrfachauswahl)', look_back):
            num = int(m.group(1))
            if 1 <= num <= 28:
                if not any(c[0] == num and abs(c[1] - m.start()) < 20 for c in candidates):
                    candidates.append((num, m.start()))

        # Pattern 3: standalone number (less reliable, use as fallback)
        if not candidates:
            for m in re.finditer(r'(?:^|\n)\s*(\d{1,2})\s*\n', look_back):
                num = int(m.group(1))
                if 1 <= num <= 28:
                    candidates.append((num, m.start()))

        # Pattern 4: Some older PDFs have question text directly after number without type
        if not candidates:
            for m in re.finditer(r'(?:^|\n)\s*(\d{1,2})\s*$', look_back, re.MULTILINE):
                num = int(m.group(1))
                if 1 <= num <= 28:
                    candidates.append((num, m.start()))

        if not candidates:
            continue

        # Take the closest candidate (last in look_back = closest to option block)
        candidates.sort(key=lambda x: x[1])
        q_num = candidates[-1][0]

        # Store (prefer longer options if duplicate)
        if q_num not in questions:
            questions[q_num] = block['options']
        else:
            old_len = sum(len(o) for o in questions[q_num])
            new_len = sum(len(o) for o in block['options'])
            if new_len > old_len:
                questions[q_num] = block['options']

    return questions


def get_gruppe_sections(text):
    """Split text into Gruppe A and B sections."""
    has_a = bool(re.search(r'Gruppe\s*A', text))
    has_b = bool(re.search(r'Gruppe\s*B', text))

    if not (has_a and has_b):
        return text, None

    # Find where Gruppe B section starts
    b_matches = list(re.finditer(r'Gruppe\s*B', text))
    text_len = len(text)

    for m in b_matches:
        if m.start() > text_len * 0.3:
            # Check if question 1 follows nearby
            nearby = text[m.start():m.start() + 800]
            if re.search(r'\b1\s+(?:Einfachauswahl|Aussagenkombination|Mehrfachauswahl)', nearby) or \
               re.search(r'\n\s*1\s*\n', nearby):
                return text[:m.start()], text[m.start():]

    # Fallback: split at midpoint-ish Gruppe B occurrence
    for m in b_matches:
        if m.start() > text_len * 0.4:
            return text[:m.start()], text[m.start():]

    return text, None


def match_exam_to_gruppe(exam, text_a, text_b):
    """Determine which Gruppe matches the exam questions."""
    if not text_b or not exam['questions']:
        return 'A'

    q1 = exam['questions'][0].get('text', '')[:80]
    q2 = exam['questions'][1].get('text', '')[:80] if len(exam['questions']) > 1 else ''

    score_a = sum(1 for qt in [q1, q2] if qt and qt[:40] in text_a)
    score_b = sum(1 for qt in [q1, q2] if qt and qt[:40] in text_b)

    return 'B' if score_b > score_a else 'A'


def get_pdf_for_exam(year, month_str):
    """Find PDF file for exam."""
    month_de = "Maerz" if month_str == "March" else "Oktober"

    # Old format
    old_path = os.path.join(FRAGEN_DIR, f"{month_de}-{year}.pdf")
    if os.path.exists(old_path):
        return old_path

    # New format variants
    for pattern in [
        f"HPP_Pruefung_{month_de}_{year}_mit_Loesungen_.pdf",
        f"HPP_Pruefung_{month_de}_{year}_mit_Loesungen.pdf",
        f"HPP_Pruefung_{month_de}_{year}_.pdf",
        f"HPP_Pruefung_{month_de}_{year}_mit_Loesungen_A_B.pdf",
        f"HPP_Pruefung_{month_de}_{year}_Gruppe_A_mit_Loesungen.pdf",
    ]:
        path = os.path.join(FRAGEN_DIR, pattern)
        if os.path.exists(path):
            return path
    return None


def has_empty_options(q):
    """Check if question has empty options."""
    opts = q.get('options', [])
    return not opts or len(opts) == 0 or all(o == '' for o in opts)


def strip_option_prefix(opt_text):
    """Remove A)/B)/C)/D)/E) or A./B./C./D./E. prefix from option text."""
    # Match patterns like "A) text", "A. text", "B) text", etc.
    m = re.match(r'^[A-E][.)]\s*', opt_text)
    if m:
        return opt_text[m.end():]
    return opt_text


def main():
    with open(EXAMS_JSON, 'r', encoding='utf-8') as f:
        exams = json.load(f)

    # Phase 1: Strip A)/B) prefixes from existing options
    prefix_stripped = 0
    for exam in exams:
        for q in exam['questions']:
            opts = q.get('options', [])
            if opts:
                new_opts = []
                changed = False
                for opt in opts:
                    stripped = strip_option_prefix(opt)
                    if stripped != opt:
                        changed = True
                    new_opts.append(stripped)
                if changed:
                    q['options'] = new_opts
                    prefix_stripped += 1

    print(f"Phase 1: Stripped option prefixes from {prefix_stripped} questions")

    # Phase 2: Extract options from PDFs for questions with empty options
    total_extracted = 0
    results = []

    for exam in exams:
        year = exam['year']
        month = exam['month']
        exam_id = f"{year}-{month}"

        empty_count = sum(1 for q in exam['questions'] if has_empty_options(q))
        if empty_count == 0:
            continue

        pdf_path = get_pdf_for_exam(year, month)
        if not pdf_path:
            results.append(f"  {exam_id}: NO PDF ({empty_count} need options)")
            continue

        text = extract_text_from_pdf(pdf_path)
        if not text.strip():
            results.append(f"  {exam_id}: No extractable text ({empty_count} need)")
            continue

        text = clean_text(text)

        # Handle Gruppe splitting
        text_a, text_b = get_gruppe_sections(text)
        if text_b:
            gruppe = match_exam_to_gruppe(exam, text_a, text_b)
            parse_text = text_b if gruppe == 'B' else text_a
        else:
            parse_text = text

        # Remove page headers
        parse_text_clean = re.sub(r'Heilpraktiker(?:über)?prüfung[^\n]*\n', '\n', parse_text)

        # Find and associate option blocks
        blocks = find_option_blocks(parse_text_clean)
        extracted = associate_blocks_with_questions(parse_text_clean, blocks)

        if not extracted:
            results.append(f"  {exam_id}: No options extracted ({empty_count} need)")
            continue

        # Apply to questions
        updated = 0
        for q in exam['questions']:
            if has_empty_options(q) and q['id'] in extracted:
                opts = extracted[q['id']]
                if opts and len(opts) == 5 and all(o.strip() for o in opts):
                    q['options'] = opts
                    updated += 1

        total_extracted += updated
        still_empty = sum(1 for q in exam['questions'] if has_empty_options(q))

        if still_empty > 0:
            missing = [str(q['id']) for q in exam['questions'] if has_empty_options(q)]
            results.append(f"  {exam_id}: {updated}/{empty_count} done ({still_empty} left: Q{', Q'.join(missing)})")
        else:
            results.append(f"  {exam_id}: All {updated} questions OK")

    # Save
    with open(EXAMS_JSON, 'w', encoding='utf-8') as f:
        json.dump(exams, f, ensure_ascii=False, indent=2)

    print(f"Phase 2: Extracted options for {total_extracted} questions from PDFs")
    print(f"\nPer-exam results:")
    for r in results:
        print(r)


if __name__ == '__main__':
    main()
