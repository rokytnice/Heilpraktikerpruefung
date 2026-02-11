#!/usr/bin/env python3
"""Comprehensive fix script for exams.json:
1. Remove duplicate exams
2. Fix correctIndices (from fix_exams.py answer keys)
3. Strip A)/B) prefixes from existing options
4. Extract options from PDFs for empty questions
5. Fix manually identified missing options
6. Split merged 10-option questions and add missing questions from PDFs
7. Fix 4-option questions missing 5th option
"""

import json
import re
import fitz
import os
import sys

EXAMS_JSON = "app/src/main/assets/exams.json"
FRAGEN_DIR = "fragen"


# ===== ANSWER KEYS (from fix_exams.py) =====
def letter_to_index(letter):
    return ord(letter.upper()) - ord('A')

def parse_answer_key(answer_str):
    letters = answer_str.strip().split('+')
    return sorted([letter_to_index(l) for l in letters])

ANSWER_KEYS_RAW = {
    "2003-march": {1:"A",2:"B",3:"D",4:"C",5:"C",6:"E",7:"E",8:"D",9:"C",10:"E",11:"D",12:"B",13:"B",14:"E",15:"E",16:"C",17:"E",18:"D",19:"B",20:"D",21:"C",22:"B",23:"D",24:"E",25:"A+D+E",26:"A+B+C",27:"C",28:"B"},
    "2004-march": {1:"E",2:"D",3:"D",4:"E",5:"B",6:"E",7:"E",8:"A",9:"B",10:"C",11:"B",12:"B",13:"D",14:"A+B+C+E",15:"B+C+D+E",16:"C",17:"D",18:"D",19:"E",20:"E",21:"B+D",22:"D",23:"C",24:"D",25:"C",26:"C",27:"C",28:"B"},
    "2006-march": {1:"B",2:"C",3:"D",4:"A",5:"E",6:"A",7:"B",8:"A",9:"A",10:"D",11:"E",12:"A+E",13:"C",14:"D",15:"C",16:"E",17:"E",18:"A",19:"C",20:"A",21:"B",22:"B",23:"E",24:"C",25:"A",26:"C",27:"A",28:"E"},
    "2007-march": {1:"C",2:"A",3:"E",4:"B",5:"A",6:"D",7:"D",8:"D",9:"A+D",10:"B",11:"B+E",12:"D",13:"C",14:"B+E",15:"B",16:"C",17:"A",18:"B",19:"D+E",20:"C",21:"B+D",22:"B",23:"D",24:"D",25:"B+D",26:"B",27:"A+E",28:"E"},
    "2008-march": {1:"E",2:"C",3:"A",4:"D",5:"E",6:"A+C",7:"B+C",8:"B",9:"B",10:"E",11:"A+D",12:"D",13:"B",14:"B",15:"C+E",16:"C",17:"A",18:"C",19:"B",20:"B",21:"D",22:"C",23:"E",24:"B+C",25:"B",26:"D",27:"C+D",28:"D"},
    "2009-march": {1:"C",2:"B",3:"C",4:"C+E",5:"C",6:"B",7:"D",8:"C",9:"E",10:"A+D",11:"D",12:"C",13:"C",14:"E",15:"C",16:"B",17:"C+E",18:"D",19:"D",20:"D",21:"D",22:"C",23:"E",24:"D",25:"A+D",26:"A",27:"B",28:"D"},
    "2010-march": {1:"D",2:"C",3:"A",4:"E",5:"C",6:"D",7:"A",8:"B",9:"D",10:"C",11:"A+D",12:"B+E",13:"B+D",14:"C",15:"A+D",16:"E",17:"E",18:"D",19:"A",20:"B+D",21:"C+D",22:"D",23:"B",24:"E",25:"D",26:"B",27:"A+E",28:"C"},
    "2011-march": {1:"C",2:"E",3:"B",4:"C",5:"C+D",6:"C",7:"C",8:"D",9:"D",10:"B+D",11:"D+E",12:"D",13:"A+C",14:"D",15:"C",16:"C",17:"D",18:"C",19:"B+C",20:"C+E",21:"C",22:"D",23:"A+D",24:"C",25:"C",26:"A",27:"D",28:"D"},
    "2012-march": {1:"B",2:"A+B",3:"D",4:"B+E",5:"B",6:"C",7:"E",8:"A+D",9:"D+E",10:"B",11:"B+C",12:"D",13:"D+E",14:"C",15:"B",16:"D",17:"D",18:"A+C",19:"A+D",20:"A",21:"D",22:"A+C",23:"A",24:"A+B",25:"D",26:"B",27:"A",28:"B+E"},
    "2013-march": {1:"A+C",2:"D",3:"E",4:"D",5:"A",6:"A+E",7:"C+E",8:"D",9:"E",10:"C",11:"D",12:"B+C",13:"B+E",14:"D",15:"B+E",16:"E",17:"D",18:"D",19:"C",20:"B+C",21:"D",22:"C",23:"C",24:"C",25:"A+E",26:"D",27:"C",28:"B"},
    "2014-march": {1:"A+D",2:"D",3:"D+E",4:"B",5:"C+D",6:"E",7:"D+E",8:"D",9:"D",10:"D",11:"C+D",12:"E",13:"B+C",14:"C",15:"A+B",16:"A+D",17:"A",18:"D",19:"A+D",20:"E",21:"E",22:"D+E",23:"E",24:"C",25:"D",26:"A",27:"B",28:"A"},
    "2015-march": {1:"C",2:"B+E",3:"E",4:"B",5:"E",6:"B",7:"A+B",8:"A+E",9:"C",10:"B+D",11:"C+D",12:"A",13:"A+C",14:"A",15:"D",16:"E",17:"E",18:"A",19:"A+D",20:"A+B",21:"B+E",22:"C",23:"C",24:"C+D",25:"D",26:"B",27:"E",28:"C"},
    "2016-march": {1:"A+C",2:"D",3:"A",4:"D",5:"A",6:"A+C",7:"C+E",8:"B+C",9:"B+E",10:"A+D",11:"B+D",12:"B+C",13:"C",14:"B+C",15:"B",16:"D",17:"B+D",18:"C",19:"E",20:"A+E",21:"A",22:"D",23:"E",24:"C",25:"C",26:"C+D",27:"A+B",28:"B+C"},
    "2017-march": {1:"B",2:"A+D",3:"B",4:"C+D",5:"A",6:"B",7:"C",8:"A",9:"D",10:"B",11:"D",12:"B+E",13:"D",14:"D",15:"B",16:"E",17:"A",18:"C+D",19:"B",20:"E",21:"D",22:"D",23:"C",24:"C",25:"B",26:"E",27:"A+B",28:"B"},
    "2019-march": {1:"D",2:"C",3:"C",4:"E",5:"B+E",6:"E",7:"B",8:"E",9:"C",10:"A+D",11:"C",12:"D",13:"A",14:"B+E",15:"E",16:"B",17:"A",18:"E",19:"A+C",20:"D",21:"C",22:"B+D",23:"C",24:"B+D",25:"C",26:"A+E",27:"C",28:"B"},
    "2022-march": {1:"B",2:"C",3:"A+E",4:"B",5:"A+D",6:"E",7:"A+B",8:"D",9:"C",10:"E",11:"A",12:"A+C",13:"D",14:"B",15:"B+E",16:"D",17:"D",18:"E",19:"C+E",20:"A",21:"C",22:"A+C",23:"B+C",24:"D",25:"E",26:"D",27:"D",28:"C+E"},
    "2023-march": {1:"D",2:"C",3:"C",4:"A",5:"D",6:"C",7:"A",8:"D",9:"E",10:"A+D",11:"B",12:"C+E",13:"C",14:"C",15:"D",16:"A+C",17:"B",18:"B",19:"E",20:"D",21:"D",22:"D",23:"E",24:"D",25:"E",26:"E",27:"C",28:"D"},
    "2024-march": {1:"C",2:"A",3:"D+E",4:"C",5:"A+B",6:"E",7:"A",8:"D",9:"D",10:"D",11:"C+D",12:"E",13:"A",14:"D",15:"B",16:"E",17:"C",18:"E",19:"D",20:"D",21:"C",22:"B",23:"B",24:"B",25:"A",26:"B+E",27:"B",28:"C"},
    "2025-march": {1:"A+B",2:"A",3:"C",4:"C+E",5:"B",6:"B",7:"D",8:"D",9:"C",10:"D+E",11:"D",12:"B+C",13:"B+C",14:"D",15:"C",16:"A+C",17:"A",18:"A+E",19:"A",20:"B+E",21:"C+E",22:"C",23:"A+D",24:"D",25:"A+E",26:"B+C",27:"D+E",28:"B"},
    "2002-october": {1:"B",2:"E",3:"A",4:"B",5:"C",6:"A",7:"D",8:"E",9:"E",10:"D",11:"D",12:"D",13:"D",14:"E",15:"D",16:"C",17:"B",18:"D",19:"C",20:"B",21:"C",22:"B",23:"D",24:"A",25:"A",26:"A",27:"D",28:"D"},
    "2003-october": {1:"B",2:"B",3:"D",4:"D",5:"C",6:"B+C+E",7:"D",8:"B+C+E",9:"A+B+D",10:"B",11:"C",12:"B",13:"C",14:"D",15:"A",16:"B+D+E",17:"D",18:"B",19:"B+C+E",20:"A+C+E",21:"A+B+E",22:"C",23:"A+D+E",24:"A",25:"D",26:"B",27:"B",28:"A+B+E"},
    "2005-october": {1:"C",2:"D",3:"C",4:"C",5:"C",6:"C",7:"D",8:"E",9:"B+E",10:"C",11:"D",12:"B",13:"C",14:"D",15:"D",16:"C",17:"A",18:"A",19:"D",20:"D",21:"B",22:"A",23:"C",24:"C",25:"C",26:"E",27:"A",28:"C"},
    "2006-october": {1:"A",2:"C",3:"E",4:"B",5:"D",6:"C",7:"A",8:"B",9:"A",10:"B",11:"A",12:"D",13:"C",14:"C",15:"B",16:"C",17:"C",18:"B",19:"D",20:"B",21:"C",22:"C",23:"D",24:"A",25:"B+D",26:"E",27:"B",28:"C"},
    "2008-october": {1:"D+E",2:"C",3:"E",4:"E",5:"B+C",6:"C+D",7:"D",8:"E",9:"C",10:"E",11:"A",12:"C",13:"D",14:"C",15:"D",16:"B",17:"D",18:"E",19:"D",20:"E",21:"D",22:"B",23:"A+D",24:"B",25:"C",26:"C",27:"D",28:"E"},
    "2009-october": {1:"D",2:"A",3:"A+C",4:"B+C",5:"D",6:"D+E",7:"A",8:"E",9:"A+C",10:"E",11:"B+D",12:"E",13:"A+C",14:"D",15:"B",16:"B",17:"A",18:"C",19:"C",20:"D+E",21:"A",22:"A+D",23:"D",24:"B",25:"D+E",26:"E",27:"B",28:"B"},
    "2010-october": {1:"A+D",2:"D",3:"D",4:"A",5:"B",6:"E",7:"D+E",8:"A",9:"B+D",10:"D+E",11:"B",12:"D",13:"A",14:"B+D",15:"E",16:"D",17:"D+E",18:"D",19:"B",20:"D",21:"B+E",22:"B",23:"A+D",24:"B+D",25:"D",26:"E",27:"D+E",28:"C"},
    "2011-october": {1:"C",2:"D+E",3:"B",4:"B",5:"B",6:"A+C",7:"B",8:"A",9:"D",10:"A+B",11:"B",12:"E",13:"E",14:"A",15:"C",16:"B+C",17:"E",18:"A+E",19:"E",20:"B+D",21:"C",22:"C+D",23:"C+D",24:"C",25:"B",26:"A+E",27:"D",28:"B"},
    "2012-october": {1:"B",2:"B",3:"E",4:"A+C",5:"D+E",6:"B",7:"D",8:"D",9:"C+E",10:"B",11:"C+E",12:"A",13:"E",14:"C",15:"D",16:"A",17:"C",18:"D",19:"C",20:"C",21:"C",22:"D",23:"C",24:"B+E",25:"C",26:"D",27:"B",28:"A+D"},
    "2013-october": {1:"B",2:"D",3:"E",4:"C",5:"C+D",6:"D",7:"E",8:"D",9:"A+C",10:"D",11:"B+C",12:"D",13:"A+D",14:"C",15:"B",16:"C",17:"B+E",18:"D",19:"C+D",20:"C",21:"B",22:"E",23:"D",24:"D",25:"D",26:"B",27:"C+E",28:"D+E"},
    "2016-october": {1:"C",2:"D",3:"A+C",4:"C",5:"D",6:"C",7:"D",8:"B+D",9:"A+E",10:"B+C",11:"B",12:"D",13:"A+E",14:"E",15:"C",16:"C+D",17:"D",18:"C",19:"C",20:"D",21:"C",22:"C+E",23:"A+D",24:"C+E",25:"D",26:"C+E",27:"A+D",28:"B+C"},
    "2017-october": {1:"E",2:"C",3:"D",4:"D",5:"D",6:"D",7:"C+E",8:"D",9:"B",10:"B",11:"B+E",12:"B",13:"C",14:"D",15:"A+E",16:"D",17:"C",18:"D",19:"C",20:"B+D",21:"B",22:"A+C",23:"D",24:"B",25:"A+E",26:"A+E",27:"A+D",28:"A"},
    "2020-october": {1:"E",2:"B+E",3:"B+C",4:"D",5:"A+C",6:"A+D",7:"B",8:"A",9:"E",10:"E",11:"D",12:"B",13:"E",14:"E",15:"D",16:"A+B",17:"C",18:"D",19:"B+E",20:"A+C",21:"D",22:"A+D",23:"D+E",24:"C",25:"A+B",26:"B+D",27:"A",28:"C+E"},
    "2022-october": {1:"D",2:"B+E",3:"B+C",4:"B",5:"A+E",6:"B",7:"A",8:"C+E",9:"C+D",10:"D",11:"A",12:"C",13:"A+D",14:"A+B",15:"C+E",16:"C",17:"A+D",18:"B",19:"B",20:"D+E",21:"B+C",22:"E",23:"A+D",24:"B+E",25:"B",26:"D",27:"D",28:"A"},
    "2023-october": {1:"A",2:"D",3:"C",4:"E",5:"D",6:"C+E",7:"D",8:"C",9:"A+C",10:"C",11:"D",12:"B",13:"D",14:"E",15:"C",16:"D",17:"D",18:"A",19:"A",20:"C",21:"E",22:"D",23:"C+E",24:"B+C",25:"A+E",26:"B+D",27:"B",28:"D"},
    "2024-october": {1:"D",2:"E",3:"A",4:"B",5:"A",6:"B",7:"B+C",8:"D",9:"D",10:"B",11:"C+D",12:"E",13:"B",14:"B+D",15:"D",16:"C",17:"A+D",18:"E",19:"C",20:"A+C",21:"E",22:"E",23:"A+E",24:"A",25:"B",26:"B+C",27:"D",28:"A+D"},
    "2025-october": {1:"D",2:"E",3:"C+D",4:"C",5:"B",6:"A",7:"D",8:"A+E",9:"C",10:"E",11:"B",12:"B+E",13:"E",14:"A+C",15:"B",16:"C",17:"B+E",18:"B",19:"D",20:"A",21:"A",22:"B+C",23:"A+E",24:"C",25:"C+E",26:"B+E",27:"C",28:"D"},
}

def build_answer_keys():
    keys = {}
    for eid, qs in ANSWER_KEYS_RAW.items():
        keys[eid] = {qid: parse_answer_key(ans) for qid, ans in qs.items()}
    return keys


# ===== PDF TEXT EXTRACTION =====
def get_pdf_text(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text() + "\n"
    doc.close()
    return text.replace('\xa0', ' ').replace('\x01', '').replace('\x02', '')


def extract_questions_from_pdf(text):
    """Extract all questions from PDF text."""
    questions = {}
    q_starts = list(re.finditer(
        r'(?:^|\n)\s*(\d{1,2})\s+(Einfachauswahl|Aussagenkombination|Mehrfachauswahl(?:aufgabe)?)', text))
    q_starts2 = list(re.finditer(
        r'(?:^|\n)\s*(\d{1,2})\s*\n\s*(Einfachauswahl|Aussagenkombination|Mehrfachauswahl(?:aufgabe)?)', text))

    all_starts = {}
    for m in q_starts + q_starts2:
        num = int(m.group(1))
        if 1 <= num <= 28:
            if num not in all_starts or m.start() < all_starts[num][0]:
                all_starts[num] = (m.start(), m.end(), m.group(2))

    sorted_nums = sorted(all_starts.keys())
    for i, qnum in enumerate(sorted_nums):
        start, end, qtype = all_starts[qnum]
        next_start = all_starts[sorted_nums[i+1]][0] if i+1 < len(sorted_nums) else min(start+5000, len(text))
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
                            if k+1 < 5:
                                opt_end = opt_matches[j+k+1].start()
                            else:
                                remaining = q_region[m.end():m.end()+500]
                                skip = 0
                                while skip < len(remaining) and remaining[skip] in ' \n\t\r':
                                    skip += 1
                                end_m = re.search(r'\n\s*\n', remaining[skip:])
                                opt_end = m.end() + skip + (end_m.start() if end_m else min(300, len(remaining) - skip))
                            opt_text = q_region[m.end():opt_end].strip()
                            opt_text = re.sub(r'\s*\n\s*', ' ', opt_text)
                            opt_text = re.sub(r'\s+', ' ', opt_text)
                            opt_text = re.sub(r'Heilpraktiker.*?Gruppe [AB]\s*\d*', '', opt_text).strip()
                            options.append(opt_text)
                        break
                if options:
                    break

        # Extract statements and text
        first_opt = None
        for fmt in [r'[A-E]\)\s', r'[A-E]\.\s']:
            m = re.search(fmt, q_region)
            if m and (first_opt is None or m.start() < first_opt):
                first_opt = m.start()
        pre_opts = q_region[:first_opt] if first_opt else q_region

        statements = []
        q_text = ""
        if qtype == 'Aussagenkombination':
            stmt_matches = list(re.finditer(r'(?:^|\n)\s*(\d)\.\s*(.*?)(?=\n\s*\d\.\s|\n\s*[A-E][.)]\s|\Z)',
                                           pre_opts, re.DOTALL))
            if stmt_matches:
                q_text = pre_opts[:stmt_matches[0].start()].strip()
                for sm in stmt_matches:
                    statements.append(re.sub(r'\s+', ' ', sm.group(2).strip()))
            else:
                q_text = pre_opts.strip()
        else:
            q_text = pre_opts.strip()

        q_text = re.sub(r'\s*\n\s*', ' ', q_text)
        q_text = re.sub(r'\s+', ' ', q_text)
        q_text = re.sub(r'Heilpraktiker.*?Gruppe [AB]\s*\d*', '', q_text).strip()
        q_text = re.sub(r'\s*W.hlen Sie.*?Antwort.*?!?\s*$', '', q_text).strip()

        questions[qnum] = {'type': qtype, 'text': q_text, 'statements': statements, 'options': options}

    return questions


def find_option_blocks(text):
    """Find A-E option blocks for bulk extraction."""
    blocks = []
    a_paren = len(re.findall(r'\bA\)\s', text))
    a_dot = len(re.findall(r'\bA\.\s', text))
    if a_paren >= a_dot:
        marker_re = lambda l: re.compile(r'\b' + l + r'\)\s')
    else:
        marker_re = lambda l: re.compile(r'\b' + l + r'\.\s')

    for a_start, a_end in [(m.start(), m.end()) for m in marker_re('A').finditer(text)]:
        search = text[a_start:a_start+4000]
        markers = [('A', 0, a_end-a_start)]
        pos = a_end-a_start
        ok = True
        for letter in 'BCDE':
            m = marker_re(letter).search(search, pos)
            if m:
                markers.append((letter, m.start(), m.end()))
                pos = m.end()
            else:
                ok = False
                break
        if not ok:
            continue
        if any(markers[i+1][1]-markers[i][1] > 800 for i in range(4)):
            continue

        options = []
        for k, (_, ms, me) in enumerate(markers):
            if k+1 < 5:
                oe = markers[k+1][1]
            else:
                remaining = search[me:me+500]
                # Skip initial whitespace to avoid matching immediately
                skip = 0
                while skip < len(remaining) and remaining[skip] in ' \n\t\r':
                    skip += 1
                end_m = re.search(r'\n\s*\n', remaining[skip:])
                oe = me + skip + (end_m.start() if end_m else min(300, len(remaining) - skip))
            ot = search[me:oe].strip()
            ot = re.sub(r'\s*\n\s*', ' ', ot)
            ot = re.sub(r'\s+', ' ', ot)
            ot = re.sub(r'Heilpraktiker.*?Gruppe [AB]\s*\d*', '', ot).strip()
            options.append(ot)

        if all(o.strip() for o in options) and len(options) == 5:
            blocks.append({'start': a_start, 'options': options})
    return blocks


def associate_blocks(text, blocks):
    """Associate option blocks with question numbers."""
    questions = {}
    for block in blocks:
        lb = text[max(0, block['start']-2500):block['start']]
        candidates = []
        for m in re.finditer(r'(?:^|\n)\s*(\d{1,2})\s+(?:Einfachauswahl|Aussagenkombination|Mehrfachauswahl)', lb):
            n = int(m.group(1))
            if 1 <= n <= 28:
                candidates.append((n, m.start()))
        for m in re.finditer(r'(?:^|\n)\s*(\d{1,2})\s*\n\s*(?:Einfachauswahl|Aussagenkombination|Mehrfachauswahl)', lb):
            n = int(m.group(1))
            if 1 <= n <= 28 and not any(c[0]==n for c in candidates):
                candidates.append((n, m.start()))
        if not candidates:
            for m in re.finditer(r'(?:^|\n)\s*(\d{1,2})\s*\n', lb):
                n = int(m.group(1))
                if 1 <= n <= 28:
                    candidates.append((n, m.start()))
        if candidates:
            candidates.sort(key=lambda x: x[1])
            qn = candidates[-1][0]
            if qn not in questions or sum(len(o) for o in block['options']) > sum(len(o) for o in questions[qn]):
                questions[qn] = block['options']
    return questions


def get_pdf_for_exam(year, month):
    month_de = "Maerz" if month == "March" else "Oktober"
    for pattern in [
        f"{month_de}-{year}.pdf",
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


def get_gruppe_section(text, gruppe):
    if gruppe == 'A':
        # Return text before Gruppe B starts (if any)
        b_matches = list(re.finditer(r'Gruppe\s*B', text))
        for m in b_matches:
            if m.start() > len(text) * 0.3:
                return text[:m.start()]
        return text
    else:
        # Return text from Gruppe B start
        b_matches = list(re.finditer(r'Gruppe\s*B', text))
        for m in b_matches:
            if m.start() > len(text) * 0.3:
                return text[m.start():]
        return text


def has_empty_options(q):
    opts = q.get('options', [])
    return not opts or all(o == '' for o in opts)


# ===== MAIN =====
def main():
    with open(EXAMS_JSON, 'r') as f:
        exams = json.load(f)
    print(f"Loaded {len(exams)} exams")

    # 1. Remove duplicate exams
    seen = set()
    to_remove = []
    for i, e in enumerate(exams):
        if e['id'] in seen:
            to_remove.append(i)
        seen.add(e['id'])
    for idx in sorted(to_remove, reverse=True):
        print(f"  Removing duplicate: {exams[idx]['id']}")
        exams.pop(idx)
    print(f"Step 1: Removed {len(to_remove)} duplicates -> {len(exams)} exams")

    # 2. Fix correctIndices
    answer_keys = build_answer_keys()
    ci_changes = 0
    for exam in exams:
        if exam['id'] in answer_keys:
            key = answer_keys[exam['id']]
            for q in exam['questions']:
                if q['id'] in key:
                    expected = key[q['id']]
                    if q.get('correctIndices') != expected:
                        q['correctIndices'] = expected
                        ci_changes += 1
    print(f"Step 2: Fixed {ci_changes} correctIndices")

    # 3. Strip A)/B)/A./B. prefixes from existing options
    prefix_stripped = 0
    for exam in exams:
        for q in exam['questions']:
            opts = q.get('options', [])
            if opts:
                new_opts = []
                changed = False
                for opt in opts:
                    m = re.match(r'^[A-E][.)]\s*', opt)
                    if m:
                        new_opts.append(opt[m.end():])
                        changed = True
                    else:
                        new_opts.append(opt)
                if changed:
                    q['options'] = new_opts
                    prefix_stripped += 1
    print(f"Step 3: Stripped prefixes from {prefix_stripped} questions")

    # 4. Split merged 10-option questions and add missing from PDFs
    merged_pdfs = {
        '2010-october': 'fragen/Oktober-2010.pdf',
        '2016-march': 'fragen/Maerz-2016.pdf',
        '2016-october': 'fragen/Oktober-2016.pdf',
        '2017-march': 'fragen/Maerz-2017.pdf',
        '2017-october': 'fragen/Oktober-2017.pdf',
    }

    total_split = 0
    total_added = 0
    for exam in exams:
        eid = exam['id']
        if eid not in merged_pdfs:
            continue

        has_merged = any(len(q.get('options', [])) >= 10 for q in exam['questions'])
        if not has_merged:
            continue

        text = get_pdf_text(merged_pdfs[eid])
        pdf_qs = extract_questions_from_pdf(text)
        if not pdf_qs:
            continue

        existing = {q['id']: q for q in exam['questions']}
        added_ids = set()
        new_questions = []

        for qid in sorted(existing.keys()):
            q = existing[qid]
            opts = q.get('options', [])

            if len(opts) >= 10:
                # Split: keep first 5 for this question
                q['options'] = opts[:5]
                total_split += 1

                # Clear wrongly-merged statements
                if q['type'] != 'Aussagenkombination':
                    q['statements'] = []

                new_questions.append(q)

                # Add missing next question(s)
                num_merged = len(opts) // 5
                for offset in range(1, num_merged):
                    next_id = qid + offset
                    if next_id not in existing and next_id in pdf_qs:
                        pq = pdf_qs[next_id]
                        new_q = {
                            'id': next_id,
                            'type': pq['type'],
                            'text': pq['text'],
                            'options': pq['options'] if pq['options'] else opts[5*offset:5*(offset+1)],
                            'statements': pq['statements'],
                            'correctIndices': answer_keys.get(eid, {}).get(next_id, []),
                            'explanation': ''
                        }
                        new_questions.append(new_q)
                        added_ids.add(next_id)
                        total_added += 1
            else:
                new_questions.append(q)

        # Also add any questions that are in PDF but not in JSON and weren't added above
        for qid in sorted(pdf_qs.keys()):
            if qid not in existing and qid not in added_ids:
                pq = pdf_qs[qid]
                if pq['options']:
                    new_q = {
                        'id': qid,
                        'type': pq['type'],
                        'text': pq['text'],
                        'options': pq['options'],
                        'statements': pq['statements'],
                        'correctIndices': answer_keys.get(eid, {}).get(qid, []),
                        'explanation': ''
                    }
                    new_questions.append(new_q)
                    total_added += 1

        new_questions.sort(key=lambda q: q['id'])

        # Update types/text from PDF where the existing data was wrong
        for q in new_questions:
            if q['id'] in pdf_qs:
                pq = pdf_qs[q['id']]
                if pq['type'] and q['type'] != pq['type']:
                    q['type'] = pq['type']
                if pq['statements'] and q['type'] == 'Aussagenkombination' and not q.get('statements'):
                    q['statements'] = pq['statements']
                if q['type'] != 'Aussagenkombination':
                    q['statements'] = []

        exam['questions'] = new_questions
        print(f"  {eid}: split {sum(1 for q in existing.values() if len(q.get('options',[])) >= 10)}, now {len(new_questions)} questions")

    print(f"Step 4: Split {total_split}, added {total_added}")

    # 5. Extract options from PDFs for remaining empty questions
    extract_count = 0
    for exam in exams:
        empty_qs = [q for q in exam['questions'] if has_empty_options(q)]
        if not empty_qs:
            continue

        pdf_path = get_pdf_for_exam(exam['year'], exam['month'])
        if not pdf_path:
            continue

        text = get_pdf_text(pdf_path)
        if not text.strip():
            continue

        # Handle Gruppe - only split if there's a real section divider (count=1-2),
        # not when Gruppe appears in page headers (count>3)
        count_b = len(re.findall(r'Gruppe\s*B', text))
        count_a = len(re.findall(r'Gruppe\s*A', text))
        parse_text = text
        if 1 <= count_b <= 3 and count_a > 3:
            # "Gruppe B" is a real section divider; PDF is primarily Gruppe A
            # Find where Gruppe B section starts
            for m in re.finditer(r'Gruppe\s*B', text):
                if m.start() > len(text) * 0.2:
                    parse_text = text[:m.start()]
                    break
        elif 1 <= count_a <= 3 and count_b > 3:
            # "Gruppe A" is a section divider; PDF is primarily Gruppe B
            # Check if exam questions match Gruppe A section
            for m in re.finditer(r'Gruppe\s*A', text):
                if m.start() > len(text) * 0.2:
                    q1_text = exam['questions'][0].get('text', '')[:40] if exam['questions'] else ''
                    text_from_a = text[m.start():]
                    if q1_text and q1_text in text_from_a:
                        parse_text = text_from_a
                    break

        parse_text = re.sub(r'Heilpraktiker(?:\u00fc|ü)berpr\u00fcfung[^\n]*\n', '\n', parse_text)
        parse_text = re.sub(r'Heilpraktikerüberprüfung[^\n]*\n', '\n', parse_text)
        parse_text = re.sub(r'Heilpraktikerprüfung[^\n]*\n', '\n', parse_text)

        blocks = find_option_blocks(parse_text)
        extracted = associate_blocks(parse_text, blocks)

        for q in exam['questions']:
            if has_empty_options(q) and q['id'] in extracted:
                opts = extracted[q['id']]
                if opts and len(opts) == 5 and all(o.strip() for o in opts):
                    q['options'] = opts
                    extract_count += 1

    print(f"Step 5: Extracted options for {extract_count} questions")

    # 5b. Extract missing statements for Aussagenkombination questions from PDFs
    stmt_count = 0
    for exam in exams:
        missing_stmts = [q for q in exam['questions']
                         if q['type'] == 'Aussagenkombination' and not q.get('statements')]
        if not missing_stmts:
            continue

        pdf_path = get_pdf_for_exam(exam['year'], exam['month'])
        if not pdf_path:
            continue

        text = get_pdf_text(pdf_path)
        if not text.strip():
            continue

        # Handle Gruppe
        count_b = len(re.findall(r'Gruppe\s*B', text))
        count_a = len(re.findall(r'Gruppe\s*A', text))
        parse_text = text
        if 1 <= count_b <= 3 and count_a > 3:
            for m in re.finditer(r'Gruppe\s*B', text):
                if m.start() > len(text) * 0.2:
                    parse_text = text[:m.start()]
                    break
        elif 1 <= count_a <= 3 and count_b > 3:
            for m in re.finditer(r'Gruppe\s*A', text):
                if m.start() > len(text) * 0.2:
                    q1_text = exam['questions'][0].get('text', '')[:40] if exam['questions'] else ''
                    text_from_a = text[m.start():]
                    if q1_text and q1_text in text_from_a:
                        parse_text = text_from_a
                    break

        pdf_qs = extract_questions_from_pdf(parse_text)
        for q in missing_stmts:
            if q['id'] in pdf_qs and pdf_qs[q['id']]['statements']:
                q['statements'] = pdf_qs[q['id']]['statements']
                stmt_count += 1

    print(f"Step 5b: Extracted statements for {stmt_count} questions")

    # 6. Manual fixes for specific questions
    manual_fixes = 0

    def fix_q(eid, qid, options=None, add_option=None, insert_option=None):
        nonlocal manual_fixes
        for e in exams:
            if e['id'] == eid:
                for q in e['questions']:
                    if q['id'] == qid:
                        if options:
                            q['options'] = options
                            manual_fixes += 1
                        if add_option and len(q.get('options', [])) < 5:
                            q['options'].append(add_option)
                            manual_fixes += 1
                        if insert_option is not None and len(q.get('options', [])) < 5:
                            q['options'].insert(0, insert_option)
                            manual_fixes += 1
                        return

    # Fix 2019-March Q1 (missing E option)
    fix_q('2019-march', 1, add_option="Die Blutwerte zeigen bei Demenz spezifische Ver\u00e4nderungen")
    # Fix 2019-March Q2 (missing A option)
    fix_q('2019-march', 2, insert_option="Nur die Aussage 5 ist richtig")
    # Fix 2024-March Q7, Q8, Q9 (missing E option)
    for qid in [7, 8, 9]:
        fix_q('2024-march', qid, add_option="Alle Aussagen sind richtig.")
    # Fix 2024-October Q1 (missing E option)
    fix_q('2024-october', 1, add_option="Nur die Aussagen 1, 2, 4 und 5 sind richtig")

    # Fix 2022-March Q23
    fix_q('2022-march', 23, options=[
        "Bei der Depression besteht meist eine deutliche St\u00f6rung des Orientierungsverm\u00f6gens und der Ged\u00e4chtnisfunktionen",
        "Ein korrekt ausgef\u00fchrter Uhren-Zeichen-Test spricht gegen eine schwere Demenz",
        "Ein Mini-Mental-Status-Test (MMST) wird bei der Diagnose und Verlaufskontrolle der Demenz verwendet",
        "Der \u201etypische\u201c depressive Patient \u00fcberspielt seine Unsicherheiten um kompetent zu wirken",
        "Der \u201etypische\u201c demente Patient im Fr\u00fchstadium klagt \u00fcber Vergesslichkeit und aggraviert seine Leistungseinbu\u00dfen"
    ])
    # Fix 2024-March Q26
    fix_q('2024-march', 26, options=[
        "Die Verhaltenstherapie basiert auf den Erkenntnissen der modernen Lerntheorie",
        "Der Begriff \u201eVerhalten\u201c umfasst dabei nur das von au\u00dfen beobachtbare Verhalten und die k\u00f6rperlichen Reaktionen.",
        "Die kognitive Verhaltenstherapie umfasst auch Denkmuster und die gedankliche Bewertung des Erlebten",
        "Eine Verhaltenstherapie kann bei Suchtkranken indiziert sein.",
        "Die Verhaltenstherapie ist stets direktiv ausgerichtet, das zugrunde liegende Problem wird vom Behandler erarbeitet und von ihm gesteuert bearbeitet."
    ])
    # Fix 2020-October Q18
    fix_q('2020-october', 18, options=[
        "Geschlechtsinkongruenz", "Fetischismus", "Sadismus", "P\u00e4dophilie", "Anorgasmie"])
    # Fix 2025-March Q1, Q15
    fix_q('2025-march', 1, options=[
        "Zu den Symptomen einer Alkoholintoxikation geh\u00f6ren unter anderem Atemdepression und Unterk\u00fchlung",
        "Die Diagnose einer Alkoholintoxikation ist auch bei einem Blutalkoholspiegel von unter 1,0 Promille m\u00f6glich",
        "Der Konsum von 3 oder mehreren Gl\u00e4sern eines alkoholischen Getr\u00e4nks definiert das sogenannte Binge-Drinking bzw. Rauschtrinken.",
        "Ein riskanter Gebrauch ist nicht definiert \u00fcber die Menge des konsumierten Alkohols.",
        "Ein Standardglas in Deutschland entspricht 500 ml Bier bzw. 40 g reinem Alkohol."])
    fix_q('2025-march', 15, options=[
        "Nur die Aussagen 1 und 4 sind richtig", "Nur die Aussagen 4 und 5 sind richtig",
        "Nur die Aussagen 1, 2 und 4 sind richtig", "Nur die Aussagen 1, 4 und 5 sind richtig",
        "Nur die Aussagen 1, 2, 3 und 5 sind richtig"])
    # Fix 2025-March Q4 (options merged into 1 string)
    for e in exams:
        if e['id'] == '2025-march':
            for q in e['questions']:
                if q['id'] == 4 and len(q.get('options', [])) == 1:
                    raw = q['options'][0]
                    parts = re.split(r'\s*[B-E]\)\s*', raw)
                    if len(parts) >= 5:
                        q['options'] = [p.strip() for p in parts[:5]]
                        manual_fixes += 1
                if q['id'] == 24 and len(q.get('options', [])) == 1:
                    raw = q['options'][0]
                    parts = re.split(r'\s*[B-E]\)\s*', raw)
                    if len(parts) >= 5:
                        q['options'] = [p.strip().replace('\xa0', ' ') for p in parts[:5]]
                        manual_fixes += 1

    # Fix 2011-March Q2, 2013-March Q19, 2013-October Q6, 2017-March Q1, 2005-March extras
    fix_q('2011-march', 2, options=["9 Jahren","61 Jahren","43 Jahren","55 Jahren","22 Jahren"])
    fix_q('2013-march', 19, options=["1 Tag","1 Woche","1 Monat","1 Jahr","2 Jahre"])
    fix_q('2013-october', 6, options=["1 Monat","6 Monate","1 Jahr","2 Jahre","5 Jahre"])

    # 2013-October Q3 - missing statements
    for e in exams:
        if e['id'] == '2013-october':
            for q in e['questions']:
                if q['id'] == 3 and not q.get('statements'):
                    q['statements'] = ["Ataxie", "Desorientierung", "Konfabulationen",
                                       "Bewusstseinsst\u00f6rungen", "Ged\u00e4chtnisst\u00f6rungen"]
                    manual_fixes += 1

    # 2017-March Q1 - clean embedded options from text
    for e in exams:
        if e['id'] == '2017-march':
            for q in e['questions']:
                if q['id'] == 1:
                    m = re.search(r'\n\s*A[.)]\s', q.get('text', ''))
                    if m:
                        q['text'] = q['text'][:m.start()].strip()
                    q['options'] = [
                        "Eine Migr\u00e4neerkrankung", "Eine akute paranoide Psychose",
                        "Eine Bluthochdruckerkrankung", "Ein Schlafapnoesyndrom",
                        "Eine psychosomatische Erkrankung"]
                    manual_fixes += 1

    # 2005-March missing options
    fix_q('2005-march', 5, options=["Nur die Aussage 1 ist richtig","Nur die Aussagen 1, 2 und 3 sind richtig","Nur die Aussagen 1, 3 und 5 sind richtig","Nur die Aussagen 1, 2, 3 und 4 sind richtig","Nur die Aussagen 1, 2, 3 und 5 sind richtig"])
    fix_q('2005-march', 9, options=["In der Balint-Gruppe spricht der Patient \u00fcber seine Probleme","Flooding (Reiz\u00fcberflutung) wird bei der Behandlung isolierter Phobien (z. B. Spinnenphobie) angewandt","Die klassische Psychoanalyse wird bei neurotischen St\u00f6rungen eingesetzt","Eine therapeutische tiefe Regression ist Therapieziel der Verhaltenstherapie","Das Standardverfahren der klassischen Psychoanalyse ist die Kurzzeittherapie"])
    fix_q('2005-march', 12, options=["Nur die Aussagen 1 und 2 sind richtig","Nur die Aussagen 2 und 3 sind richtig","Nur die Aussagen 2, 4 und 5 sind richtig","Nur die Aussagen 1, 2, 3 und 4 sind richtig","Alle Aussagen sind richtig"])
    fix_q('2005-march', 15, options=["Nur die Aussage 1 ist richtig","Nur die Aussagen 1 und 4 sind richtig","Nur die Aussagen 1, 2 und 4 sind richtig","Nur die Aussagen 1, 3, 4 und 5 sind richtig","Nur die Aussagen 2, 3, 4 und 5 sind richtig"])
    fix_q('2005-march', 19, options=["\u00dcberm\u00e4\u00dfiger Zweifel und Vorsicht","Suggestibilit\u00e4t","Altruistisches Verhalten","\u00dcberm\u00e4\u00dfige Befolgung von Konventionen","Andauerndes Verlangen nach Anerkennung"])
    fix_q('2005-march', 23, options=["Nur die Aussagen 1 und 2 sind richtig","Nur die Aussagen 2 und 4 sind richtig","Nur die Aussagen 2, 3 und 5 sind richtig","Nur die Aussagen 2, 4 und 5 sind richtig","Alle Aussagen sind richtig"])

    # 2022-March Q11, Q14, Q26 manual
    fix_q('2022-march', 11, options=[
        "Eine auf das Gebiet der Psychotherapie beschr\u00e4nkte Heilpraktikererlaubnis berechtigt grunds\u00e4tzlich auch zur Durchf\u00fchrung einer Gruppentherapie",
        "Gruppentherapien sind bei depressiven St\u00f6rungen kontraindiziert",
        "Gruppentherapie kommen nur bei der Behandlung zwischenmenschlicher Probleme in Frage",
        "Die Wirkfaktoren sind in der Einzel- und Gruppentherapie v\u00f6llig identisch",
        "In methodenorientierten Psychotherapiegruppen geht es vor allem um die Bearbeitung gruppendynamischer Konflikte"])
    fix_q('2022-march', 14, options=[
        "Einge\u00fcbt wird die Achtsamkeit f\u00fcr vergangene Gef\u00fchle",
        "Der Patient soll bef\u00e4higt werden, mit seinen Gef\u00fchlen umzugehen",
        "Gefordert wird, sich st\u00e4rker mit seinem Gef\u00fchl zu identifizieren",
        "Der Patient wird best\u00e4rkt, die Wahrnehmung negativer Gef\u00fchle zu vermeiden und diese zu unterdr\u00fccken",
        "Der Therapeut hilft dem Patienten dabei, problematische Gef\u00fchle (z.B. be\u00e4ngstigende Gedanken) zu verst\u00e4rken"])

    print(f"Step 6: {manual_fixes} manual fixes")

    # 7. Add missing questions extracted from PDFs
    added_missing = 0

    def add_q(eid, qid, qtype, text, options, statements=None):
        nonlocal added_missing
        for e in exams:
            if e['id'] == eid:
                if any(q['id'] == qid for q in e['questions']):
                    return  # Already exists
                ci = answer_keys.get(eid, {}).get(qid, [])
                e['questions'].append({
                    'id': qid, 'type': qtype, 'text': text,
                    'options': options, 'statements': statements or [],
                    'correctIndices': ci, 'explanation': ''
                })
                e['questions'].sort(key=lambda q: q['id'])
                added_missing += 1
                return

    # 2003-march Q24
    add_q('2003-march', 24, 'Aussagenkombination',
        'Kennzeichen f\u00fcr eine Alkoholkrankheit k\u00f6nnen sein:',
        ["Nur die Aussagen 1 und 2 sind richtig",
         "Nur die Aussagen 1 und 4 sind richtig",
         "Nur die Aussagen 3 und 4 sind richtig",
         "Nur die Aussagen 1, 2 und 4 sind richtig",
         "Alle Aussagen sind richtig"],
        ["Pers\u00f6nlichkeitsver\u00e4nderungen und sozialer Abstieg",
         "Libidoverlust und Eifersuchtswahn",
         "Palmarerythem (ger\u00f6tete Handinnenflächen) und Spider naevi (Gef\u00e4\u00dfsternchen der Haut)",
         "Ataxie (Gangunsicherheit) aufgrund von Polyneuropathie"])

    # 2003-october Q25
    add_q('2003-october', 25, 'Einfachauswahl',
        'Typisch f\u00fcr die senile Demenz vom Alzheimer-Typ ist eines der folgenden Merkmale:',
        ["Die senile Demenz vom Alzheimer-Typ beginnt akut, meist nach einem Schlaganfall.",
         "Meist wird \u00fcber Sehst\u00f6rungen und fl\u00fcchtige Paresen (= L\u00e4hmungserscheinungen) in der Vorgeschichte berichtet.",
         "Die senile Demenz vom Alzheimer-Typ verl\u00e4uft schubweise und unregelm\u00e4\u00dfig.",
         "Zu Beginn kommt es bei der senilen Demenz vom Alzheimer-Typ haupts\u00e4chlich zu Merkf\u00e4higkeits- und Wortfindungsst\u00f6rungen, au\u00dferdem zur Einschr\u00e4nkung von Alltagsaktivit\u00e4ten und Interessen.",
         "Die Krankheit ist meistens mit einem Hypertonus verbunden."])

    # 2003-october Q26
    add_q('2003-october', 26, 'Aussagenkombination',
        'Welche der folgenden Aussagen zur Suizidalit\u00e4t trifft (treffen) zu?',
        ["Nur die Aussage 1 ist richtig",
         "Nur die Aussage 2 ist richtig",
         "Nur die Aussage 3 ist richtig",
         "Nur die Aussagen 1 und 2 sind richtig",
         "Nur die Aussagen 1 und 3 sind richtig"],
        ["Nur selten (in weniger als 10 %) geben Suizidanten vor der Suizidalhandlung Signale (z.B. Ank\u00fcndigung, verbale Andeutungen, etc.).",
         "Bei angek\u00fcndigter Selbstt\u00f6tung oder bei Verdacht auf Suizidneigung muss der Behandler dieses Thema mit dem Betreffenden ansprechen.",
         "Der Versuch abzusch\u00e4tzen, ob bei einem Patienten Suizidgefahr vorliegt, ist grunds\u00e4tzlich ein vergebliches Unterfangen."])

    print(f"Step 7: Added {added_missing} missing questions")

    # SAVE
    with open(EXAMS_JSON, 'w') as f:
        json.dump(exams, f, ensure_ascii=False, indent=2)

    # FINAL AUDIT
    print(f"\n=== FINAL AUDIT ===")
    total_q = 0
    issues = 0
    for e in exams:
        qs = e['questions']
        total_q += len(qs)
        exam_issues = []
        for q in qs:
            opts = q.get('options', [])
            ci = q.get('correctIndices', [])
            if len(opts) != 5:
                exam_issues.append(f"Q{q['id']}:{len(opts)}opts")
            if not ci:
                pass  # Don't count - some exams legitimately missing keys
            if opts and any(o.strip() == '' for o in opts):
                exam_issues.append(f"Q{q['id']}:empty_opt")
        if exam_issues:
            print(f"  {e['id']} ({len(qs)}q): {', '.join(exam_issues[:5])}")
            issues += len(exam_issues)

    no_ci_exams = []
    for e in exams:
        no_ci = sum(1 for q in e['questions'] if not q.get('correctIndices'))
        if no_ci > 0:
            no_ci_exams.append(f"{e['id']}({no_ci})")
    print(f"\n  Exams missing correctIndices: {', '.join(no_ci_exams)}")
    print(f"\n  Total: {len(exams)} exams, {total_q} questions, {issues} option issues")


if __name__ == '__main__':
    main()
