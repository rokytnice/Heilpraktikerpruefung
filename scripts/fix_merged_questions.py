#!/usr/bin/env python3
"""Fix exams with merged questions (10+ options) by splitting them
and adding missing questions from PDF extraction."""

import json
import re
import fitz

EXAMS_JSON = "app/src/main/assets/exams.json"

def get_full_text(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text() + "\n"
    doc.close()
    return text.replace('\xa0', ' ').replace('\x01', '').replace('\x02', '')

def extract_questions(text):
    """Extract questions from text."""
    questions = {}

    q_starts = list(re.finditer(
        r'(?:^|\n)\s*(\d{1,2})\s+(Einfachauswahl|Aussagenkombination|Mehrfachauswahl(?:aufgabe)?)',
        text
    ))
    q_starts2 = list(re.finditer(
        r'(?:^|\n)\s*(\d{1,2})\s*\n\s*(Einfachauswahl|Aussagenkombination|Mehrfachauswahl(?:aufgabe)?)',
        text
    ))

    all_starts = {}
    for m in q_starts + q_starts2:
        num = int(m.group(1))
        if 1 <= num <= 28:
            if num not in all_starts or m.start() < all_starts[num][0]:
                all_starts[num] = (m.start(), m.end(), m.group(2))

    sorted_nums = sorted(all_starts.keys())

    for i, qnum in enumerate(sorted_nums):
        start, end, qtype = all_starts[qnum]

        if i + 1 < len(sorted_nums):
            next_start = all_starts[sorted_nums[i+1]][0]
        else:
            next_start = min(start + 5000, len(text))

        q_region = text[end:next_start]

        if 'Mehrfach' in qtype:
            qtype = 'Mehrfachauswahl'

        # Extract options
        options = []
        for fmt in [r'([A-E])\)\s', r'([A-E])\.\s']:
            opt_matches = list(re.finditer(fmt, q_region))
            if len(opt_matches) >= 5:
                for j in range(len(opt_matches) - 4):
                    letters = [m.group(1) for m in opt_matches[j:j+5]]
                    if letters == ['A', 'B', 'C', 'D', 'E']:
                        for k in range(5):
                            m = opt_matches[j+k]
                            if k + 1 < 5:
                                opt_end = opt_matches[j+k+1].start()
                            else:
                                remaining = q_region[m.end():m.end()+500]
                                end_m = re.search(r'\n\s*\n', remaining)
                                opt_end = m.end() + (end_m.start() if end_m else min(300, len(remaining)))

                            opt_text = q_region[m.end():opt_end].strip()
                            opt_text = re.sub(r'\s*\n\s*', ' ', opt_text)
                            opt_text = re.sub(r'\s+', ' ', opt_text)
                            opt_text = re.sub(r'Heilpraktiker.*?Gruppe [AB]\s*\d*', '', opt_text).strip()
                            options.append(opt_text)
                        break
                if options:
                    break

        # Extract statements and question text
        statements = []
        q_text = ""

        first_opt = None
        for fmt in [r'[A-E]\)\s', r'[A-E]\.\s']:
            m = re.search(fmt, q_region)
            if m:
                if first_opt is None or m.start() < first_opt:
                    first_opt = m.start()

        pre_opts = q_region[:first_opt] if first_opt else q_region

        if qtype == 'Aussagenkombination':
            stmt_matches = list(re.finditer(r'(?:^|\n)\s*(\d)\.\s*(.*?)(?=\n\s*\d\.\s|\n\s*[A-E][.)]\s|\Z)',
                                           pre_opts, re.DOTALL))
            if stmt_matches:
                q_text = pre_opts[:stmt_matches[0].start()].strip()
                for sm in stmt_matches:
                    stmt = re.sub(r'\s+', ' ', sm.group(2).strip())
                    statements.append(stmt)
            else:
                q_text = pre_opts.strip()
        else:
            q_text = pre_opts.strip()

        q_text = re.sub(r'\s*\n\s*', ' ', q_text)
        q_text = re.sub(r'\s+', ' ', q_text)
        q_text = re.sub(r'Heilpraktiker.*?Gruppe [AB]\s*\d*', '', q_text).strip()
        q_text = re.sub(r'\s*W.hlen Sie.*?Antwort.*?!?\s*$', '', q_text).strip()

        questions[qnum] = {
            'type': qtype,
            'text': q_text,
            'statements': statements,
            'options': options
        }

    return questions


def fix_exam(exam, pdf_questions):
    """Fix an exam by splitting merged questions and adding missing ones."""
    existing = {q['id']: q for q in exam['questions']}
    all_q_ids = set(existing.keys()) | set(pdf_questions.keys())

    new_questions = []
    fixed = 0
    added = 0

    for qid in sorted(all_q_ids):
        if qid in existing:
            q = existing[qid]
            opts = q.get('options', [])

            if len(opts) >= 10:
                # Split: keep first 5 options for this question
                q['options'] = opts[:5]

                # Check if the statements belong to the NEXT question
                next_id = qid + 1
                if next_id in pdf_questions:
                    pdf_q = pdf_questions[next_id]

                    # If current question has statements that match the next question's topic,
                    # they were merged from the next question
                    if q.get('statements') and pdf_q['type'] == 'Aussagenkombination':
                        # Statements belong to next question, not this one
                        pass  # Will handle below
                    elif q['type'] != 'Aussagenkombination' and q.get('statements'):
                        # This non-Aussagenkombination question shouldn't have statements
                        q['statements'] = []

                fixed += 1
                new_questions.append(q)

                # Add the next question if it's missing
                next_id = qid + 1
                if next_id not in existing and next_id in pdf_questions:
                    pdf_q = pdf_questions[next_id]
                    new_q = {
                        'id': next_id,
                        'type': pdf_q['type'],
                        'text': pdf_q['text'],
                        'options': pdf_q['options'] if pdf_q['options'] else opts[5:10],
                        'statements': pdf_q['statements'],
                        'correctIndices': [],
                        'explanation': ''
                    }
                    new_questions.append(new_q)
                    added += 1

            elif len(opts) == 15:
                # Triple merge (Q7 in 2017-october) - keep first 5
                q['options'] = opts[:5]
                fixed += 1
                new_questions.append(q)

                # Add next two questions
                for offset in [1, 2]:
                    next_id = qid + offset
                    if next_id not in existing and next_id in pdf_questions:
                        pdf_q = pdf_questions[next_id]
                        new_q = {
                            'id': next_id,
                            'type': pdf_q['type'],
                            'text': pdf_q['text'],
                            'options': pdf_q['options'] if pdf_q['options'] else opts[5*offset:5*(offset+1)],
                            'statements': pdf_q['statements'],
                            'correctIndices': [],
                            'explanation': ''
                        }
                        new_questions.append(new_q)
                        added += 1
            else:
                new_questions.append(q)
        elif qid in pdf_questions and qid not in existing:
            # Missing question - add from PDF
            pdf_q = pdf_questions[qid]
            new_q = {
                'id': qid,
                'type': pdf_q['type'],
                'text': pdf_q['text'],
                'options': pdf_q['options'],
                'statements': pdf_q['statements'],
                'correctIndices': [],
                'explanation': ''
            }
            new_questions.append(new_q)
            added += 1

    # Sort by question ID
    new_questions.sort(key=lambda q: q['id'])

    # Fix statements: for merged questions, the existing question's statements
    # may belong to the next question
    for i, q in enumerate(new_questions):
        qid = q['id']
        if qid in pdf_questions:
            pdf_q = pdf_questions[qid]

            # If the PDF has statements for this question but the JSON doesn't,
            # and the JSON has a different type, update from PDF
            if pdf_q['statements'] and not q.get('statements'):
                if pdf_q['type'] == 'Aussagenkombination':
                    q['statements'] = pdf_q['statements']

            # Update type if wrong
            if q['type'] != pdf_q['type']:
                q['type'] = pdf_q['type']

            # Update text if it seems wrong or truncated
            if pdf_q['text'] and (not q['text'] or len(q['text']) < len(pdf_q['text']) * 0.5):
                q['text'] = pdf_q['text']

    # Clear statements from non-Aussagenkombination questions
    for q in new_questions:
        if q['type'] != 'Aussagenkombination':
            q['statements'] = []

    exam['questions'] = new_questions
    return fixed, added


def main():
    with open(EXAMS_JSON, 'r') as f:
        exams = json.load(f)

    pdfs = {
        '2010-october': 'fragen/Oktober-2010.pdf',
        '2016-march': 'fragen/Maerz-2016.pdf',
        '2016-october': 'fragen/Oktober-2016.pdf',
        '2017-march': 'fragen/Maerz-2017.pdf',
        '2017-october': 'fragen/Oktober-2017.pdf',
    }

    total_fixed = 0
    total_added = 0

    for exam in exams:
        eid = exam['id']
        if eid not in pdfs:
            continue

        # Check if this exam has merged questions
        has_merged = any(len(q.get('options', [])) >= 10 for q in exam['questions'])
        if not has_merged:
            continue

        text = get_full_text(pdfs[eid])
        pdf_questions = extract_questions(text)

        if not pdf_questions:
            print(f"  {eid}: Could not extract from PDF")
            continue

        fixed, added = fix_exam(exam, pdf_questions)
        total_fixed += fixed
        total_added += added

        print(f"  {eid}: fixed {fixed} merged, added {added} missing -> {len(exam['questions'])} total")

    # Save
    with open(EXAMS_JSON, 'w') as f:
        json.dump(exams, f, ensure_ascii=False, indent=2)

    print(f"\nTotal: {total_fixed} split, {total_added} added")


if __name__ == '__main__':
    main()
