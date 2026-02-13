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
    "2007-october": {1:"A+D",2:"D",3:"E",4:"D",5:"A+D",6:"D",7:"C",8:"C",9:"D",10:"D",11:"C",12:"B",13:"C",14:"E",15:"A",16:"C",17:"C",18:"A+B",19:"E",20:"A+C",21:"C",22:"E",23:"B+D",24:"A",25:"B",26:"E",27:"C+D",28:"E"},
    "2008-october": {1:"D+E",2:"C",3:"E",4:"E",5:"B+C",6:"C+D",7:"D",8:"E",9:"C",10:"E",11:"A",12:"C",13:"D",14:"C",15:"D",16:"B",17:"D",18:"E",19:"D",20:"E",21:"D",22:"B",23:"A+D",24:"B",25:"C",26:"C",27:"D",28:"E"},
    "2009-october": {1:"D",2:"A",3:"A+C",4:"B+C",5:"D",6:"D+E",7:"A",8:"E",9:"A+C",10:"E",11:"B+D",12:"E",13:"A+C",14:"D",15:"B",16:"B",17:"A",18:"C",19:"C",20:"D+E",21:"A",22:"A+D",23:"D",24:"B",25:"D+E",26:"E",27:"B",28:"B"},
    "2010-october": {1:"A+D",2:"D",3:"D",4:"A",5:"B",6:"E",7:"D+E",8:"A",9:"B+D",10:"D+E",11:"B",12:"D",13:"A",14:"B+D",15:"E",16:"D",17:"D+E",18:"D",19:"B",20:"D",21:"B+E",22:"B",23:"A+D",24:"B+D",25:"D",26:"E",27:"D+E",28:"C"},
    "2011-october": {1:"C",2:"D+E",3:"B",4:"B",5:"B",6:"A+C",7:"B",8:"A",9:"D",10:"A+B",11:"B",12:"E",13:"E",14:"A",15:"C",16:"B+C",17:"E",18:"A+E",19:"E",20:"B+D",21:"C",22:"C+D",23:"C+D",24:"C",25:"B",26:"A+E",27:"D",28:"B"},
    "2012-october": {1:"B",2:"B",3:"E",4:"A+C",5:"D+E",6:"B",7:"D",8:"D",9:"C+E",10:"B",11:"C+E",12:"A",13:"E",14:"C",15:"D",16:"A",17:"C",18:"D",19:"C",20:"C",21:"C",22:"D",23:"C",24:"B+E",25:"C",26:"D",27:"B",28:"A+D"},
    "2013-october": {1:"B",2:"D",3:"E",4:"C",5:"C+D",6:"D",7:"E",8:"D",9:"A+C",10:"D",11:"B+C",12:"D",13:"A+D",14:"C",15:"B",16:"C",17:"B+E",18:"D",19:"C+D",20:"C",21:"B",22:"E",23:"D",24:"D",25:"D",26:"B",27:"C+E",28:"D+E"},
    "2014-october": {1:"C+D",2:"E",3:"A+D",4:"B",5:"B+E",6:"A",7:"D",8:"C+E",9:"B+E",10:"B",11:"C",12:"C",13:"C",14:"A+C",15:"A+C",16:"A+D",17:"D",18:"C+E",19:"B+D",20:"B",21:"A+D",22:"C+D",23:"B",24:"E",25:"A+D",26:"A+B",27:"E",28:"C"},
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
        r'(?:^|\n)\s*(\d{1,2})\s+(Einfachauswahl|Aussage\s*n?\s*kombination|Mehrfachauswahl(?:aufgabe)?)', text))
    q_starts2 = list(re.finditer(
        r'(?:^|\n)\s*(\d{1,2})\s*\n\s*(Einfachauswahl|Aussage\s*n?\s*kombination|Mehrfachauswahl(?:aufgabe)?)', text))

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
        if 'ombination' in qtype and qtype != 'Aussagenkombination':
            qtype = 'Aussagenkombination'

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
            stmt_matches = list(re.finditer(r'(?:^|\n)\s*(\d)[.)]\s*(.*?)(?=\n\s*\d[.)]\s|\n\s*[A-E][.)]\s|\Z)',
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
        for m in re.finditer(r'(?:^|\n)\s*(\d{1,2})\s+(?:Einfachauswahl|Aussage\s*n?\s*kombination|Mehrfachauswahl)', lb):
            n = int(m.group(1))
            if 1 <= n <= 28:
                candidates.append((n, m.start()))
        for m in re.finditer(r'(?:^|\n)\s*(\d{1,2})\s*\n\s*(?:Einfachauswahl|Aussage\s*n?\s*kombination|Mehrfachauswahl)', lb):
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

    # 5c. Add missing questions from PDFs (for exams that have gaps)
    added_from_pdf = 0
    for exam in exams:
        existing_ids = {q['id'] for q in exam['questions']}
        if len(existing_ids) >= 28:
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

        # Also try finding questions via option blocks (catches unlabeled questions)
        blocks = find_option_blocks(parse_text)
        block_qs = associate_blocks(parse_text, blocks)

        for qid in range(1, 29):
            if qid in existing_ids:
                continue
            pq = pdf_qs.get(qid)
            if pq and pq['options']:
                new_q = {
                    'id': qid,
                    'type': pq['type'],
                    'text': pq['text'],
                    'options': pq['options'],
                    'statements': pq['statements'],
                    'correctIndices': answer_keys.get(exam['id'], {}).get(qid, []),
                    'explanation': ''
                }
                exam['questions'].append(new_q)
                added_from_pdf += 1
                print(f"  Added Q{qid} to {exam['id']} (from PDF extraction)")
            elif qid in block_qs:
                # Question found via option blocks but not via header regex
                opts = block_qs[qid]
                ci = answer_keys.get(exam['id'], {}).get(qid, [])
                qtype = 'Aussagenkombination' if ci and max(ci) < 5 and all(
                    'Aussage' in o for o in opts) else 'Einfachauswahl'
                new_q = {
                    'id': qid,
                    'type': qtype,
                    'text': '',
                    'options': opts,
                    'statements': [],
                    'correctIndices': ci,
                    'explanation': ''
                }
                exam['questions'].append(new_q)
                added_from_pdf += 1
                print(f"  Added Q{qid} to {exam['id']} (from option blocks)")

        exam['questions'].sort(key=lambda q: q['id'])

    print(f"Step 5c: Added {added_from_pdf} missing questions from PDFs")

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
    # Fix 2019-March Q2 (garbled text with embedded option, merged statements)
    for e in exams:
        if e['id'] == '2019-march':
            for q in e['questions']:
                if q['id'] == 2:
                    q['text'] = "Welche der folgenden Aussagen trifft (treffen) zu? Negativsymptome eines schizophrenen Residuums ist/sind:"
                    q['statements'] = [
                        "Psychomotorische Verlangsamung",
                        "Affektverflachung",
                        u"Passivit\u00e4t und Initiativemangel",
                        "Akustische und optische Halluzinationen",
                        "Negativismus"
                    ]
                    q['options'] = [
                        "Nur die Aussage 5 ist richtig",
                        "Nur die Aussagen 1 und 4 sind richtig",
                        "Nur die Aussagen 1, 2 und 3 sind richtig",
                        "Nur die Aussagen 1, 2, 3 und 5 sind richtig",
                        "Alle Aussagen sind richtig"
                    ]
                    manual_fixes += 1
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
    # Fix 2024-March Q12 (garbled text, truncated statements)
    for e in exams:
        if e['id'] == '2024-march':
            for q in e['questions']:
                if q['id'] == 12:
                    q['text'] = "Welche Aussagen zu organisch bedingten psychischen St\u00f6rungen sind richtig?"
                    q['statements'] = [
                        "Bei den organisch bedingten psychischen St\u00f6rungen unterscheiden wir akute von chronischen Erkrankungen",
                        "Nur die chronisch organisch bedingten psychischen St\u00f6rungen gehen mit einer Bewusstseinsst\u00f6rung einher",
                        "Akute organisch bedingte psychische St\u00f6rungen k\u00f6nnen durch Drogen oder Arzneimittel ausgel\u00f6st werden",
                        "Bei einer akuten organisch bedingten psychischen St\u00f6rung handelt es sich immer um einen Notfall",
                        "Krankheitszeichen einer auf Dauer bestehenden organisch bedingten psychischen St\u00f6rung sind z.B. Ged\u00e4chtnis- und Orientierungsst\u00f6rungen"
                    ]
                    manual_fixes += 1
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
        "Stimuluskontrolle",
        "Negative Bestrafung (Entzugsbestrafung)",
        "Negative Verstärkung",
        "Generalisierter Strafreiz",
        "Positive Vermeidung"])
    # Fix 2025-March Q20 (truncated option B)
    for e in exams:
        if e['id'] == '2025-march':
            for q in e['questions']:
                if q['id'] == 20:
                    opts = q.get('options', [])
                    if len(opts) >= 2 and opts[1].endswith(' und ein'):
                        opts[1] = "Leichtere Gesichtsanomalien wie z.B. eine schmale Oberlippe und ein glattes Philtrum"
                        manual_fixes += 1
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

    # 2011-March Q26 - statements use 1) format, PDF extraction may miss them
    for e in exams:
        if e['id'] == '2011-march':
            for q in e['questions']:
                if q['id'] == 26 and not q.get('statements'):
                    q['statements'] = [
                        "St\u00f6rungen im Neurotransmittersystem wirken entscheidend bei der Entstehung affektiver Erkrankungen mit",
                        "Wichtige Transmitter hei\u00dfen Adrenalin, Noradrenalin und Serotonin",
                        "Synapse nennt man den Bereich, in dem ein Reiz mittels Neurotransmittern von einer Nervenzelle auf eine andere \u00fcbertragen wird",
                        "Johanniskraut hat als pflanzliches Medikament keine Wirkung auf das Neurotransmittersystem",
                        "Ein \u00dcberangebot von Neurotransmittern f\u00fchrt h\u00e4ufig zu vaskul\u00e4rer Demenz"]
                    manual_fixes += 1

    # 2005-March Q5 - garbled OCR, reconstructed from context (bipolare affektive St\u00f6rung)
    for e in exams:
        if e['id'] == '2005-march':
            for q in e['questions']:
                if q['id'] == 5 and not q.get('statements'):
                    q['statements'] = [
                        "Es handelt sich um eine St\u00f6rung, die durch wenigstens zwei Episoden charakterisiert ist, in denen Stimmung und Aktivit\u00e4tsniveau des Betroffenen deutlich gest\u00f6rt sind",
                        "Es besteht manchmal angehobene Stimmung, vermehrter Antrieb und Aktivit\u00e4t",
                        "Es besteht manchmal Stimmungssenkung, verminderter Antrieb und verminderte Aktivit\u00e4t",
                        "Depressive Episoden kommen nicht vor",
                        "Depressiver Wahn kann auftreten"]
                    manual_fixes += 1
                if q['id'] == 12 and not q.get('statements'):
                    q['statements'] = [
                        "Es gibt erfolglose Versuche oder den bleibenden Wunsch, den Substanzgebrauch zu regulieren oder zu reduzieren",
                        "Intoxikations- oder Entzugssymptome k\u00f6nnen auftreten",
                        "Es findet sich eine deutliche Toleranzentwicklung",
                        "F\u00fcr die Beschaffung der Substanz, die Einnahme oder die notwendige Erholung nach Gebrauch der Substanz wird viel Zeit aufgewendet",
                        "Wichtige Aktivit\u00e4ten in Beruf und/oder Freizeit leiden nicht unter einem Suchtverhalten"]
                    manual_fixes += 1
                if q['id'] == 15 and not q.get('statements'):
                    q['statements'] = [
                        "Die Betreuung kann ggf. auch nur einen Aufgabenkreis betreffen",
                        "Das Vormundschaftsgericht kann anordnen, dass bei dem Betreuten zwei Betreuer einzelne der festgelegten Aufgabenkreise \u00fcbernehmen",
                        "Beim Einwilligungsvorbehalt handelt es sich um ein Vetorecht in allen Angelegenheiten, das jedem Betreuten zusteht",
                        "Das Gesetz regelt u.a. die Betreuung k\u00f6rperlich Behinderter",
                        "Beim Betreuungsgesetz handelt es sich um eine l\u00e4ndergesetzliche Regelung"]
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

    # 2005-March Q27 - garbled text/statements/options (page number "28" merged into text)
    for e in exams:
        if e['id'] == '2005-march':
            for q in e['questions']:
                if q['id'] == 27:
                    q['text'] = "Welche der folgenden Aussagen treffen zu? Merkmale der sog. voll funktionsf\u00e4higen Person (fully functioning person) nach Rogers sind:"
                    q['statements'] = [
                        "Unverzerrte Realit\u00e4tswahrnehmung und reife, befriedigende soziale Interaktionen",
                        "Offenheit gegen\u00fcber Erfahrungen",
                        "Totale \u00dcbereinstimmung von Selbstbild und Idealbild",
                        "Wertsch\u00e4tzung des eigenen Selbst",
                        "\u00dcbereinstimmung von Selbstbild und Erfahrung"
                    ]
                    q['options'] = [
                        "Nur die Aussagen 1 und 4 sind richtig",
                        "Nur die Aussagen 1, 2 und 4 sind richtig",
                        "Nur die Aussagen 1, 3 und 5 sind richtig",
                        "Nur die Aussagen 1, 2, 4 und 5 sind richtig",
                        "Alle Aussagen sind richtig"
                    ]
                    manual_fixes += 1

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

    # 2012-October Q18 (no type label in PDF, missed by extraction)
    add_q('2012-october', 18, 'Aussagenkombination',
        'Welche der folgenden Aussagen zu den organischen psychischen St\u00f6rungen (nach ICD-10) treffen zu?',
        ["Nur die Aussagen 1 und 3 sind richtig",
         "Nur die Aussagen 1 und 4 sind richtig",
         "Nur die Aussagen 1, 2 und 3 sind richtig",
         "Nur die Aussagen 1, 3 und 5 sind richtig",
         "Alle Aussagen sind richtig"],
        ["Verfolgungswahn kann ein Symptom einer organischen psychischen St\u00f6rung sein",
         "Die Alkoholabh\u00e4ngigkeit z\u00e4hlt zu den organischen psychischen St\u00f6rungen",
         "Die Demenz bei HIV-Krankheit z\u00e4hlt zu den organischen psychischen St\u00f6rungen",
         "Eine internistische Abkl\u00e4rung ist nicht notwendig",
         "Unterschiedliche k\u00f6rperliche Erkrankungen k\u00f6nnen die gleichen psychischen Symptome hervorrufen, d. h. die Symptome sind nicht spezifisch f\u00fcr die Ursache der Erkrankung"])

    # 2003-october Q19 (stray 'r' in PDF between number and type label)
    add_q('2003-october', 19, 'Mehrfachauswahl',
        'Was ist f\u00fcr die katatone Form der Schizophrenie charakteristisch? W\u00e4hlen Sie drei Antworten!',
        ["Rededrang",
         "Bewegungsstereotypien",
         "Psychomotorische Unruhe",
         "Konfabulation",
         "Mutismus"])

    # 2005-march Q1 (no type label in PDF, starts directly with statements)
    add_q('2005-march', 1, 'Aussagenkombination',
        'Welche der folgenden Ver\u00e4nderungen kann (k\u00f6nnen) auch durch eine Alkoholkrankheit bedingt sein?',
        ["Nur die Aussage 3 ist richtig",
         "Nur die Aussagen 3 und 4 sind richtig",
         "Nur die Aussagen 3 und 5 sind richtig",
         "Nur die Aussagen 1, 2, 3 und 4 sind richtig",
         "Alle Aussagen sind richtig"],
        ["Vorgealtertes Erscheinungsbild",
         "\u00dcbergewicht",
         "Zittern der H\u00e4nde",
         "Undeutliche Aussprache",
         "Schlechter allgemeiner K\u00f6rpflegezustand"])

    # 2006-october Q19 (no type label in PDF)
    add_q('2006-october', 19, 'Aussagenkombination',
        'Welcher der folgenden Aussagen zu Inhalten der Verhaltenstherapie trifft (treffen) zu?',
        ["Nur die Aussage 1 ist richtig",
         "Nur die Aussagen 2 und 3 sind richtig",
         "Nur die Aussagen 1, 4 und 5 sind richtig",
         "Nur die Aussagen 1, 2, 4 und 5 sind richtig",
         "Alle Aussagen sind richtig"],
        ["Intermittierende Verst\u00e4rker (mal wird verst\u00e4rkt, mal nicht) erwiesen sich \u2013 was den langzeitigen Behandlungserfolg (L\u00f6schungsresistenz) betrifft \u2013 wirksamer als kontinuierliche Verst\u00e4rker",
         "Verschieben einer Pr\u00fcfung bei starker Pr\u00fcfungsangst (Vermeidungsverhalten) ist ein Beispiel f\u00fcr negative Verst\u00e4rkung",
         "K\u00f6rperliche Z\u00fcchtigung bei einem Kind, das immer nicht richtig aufisst, ist ein Beispiel f\u00fcr positive Verst\u00e4rkung",
         "Wichtig bei operanten Verfahren ist die zeitliche N\u00e4he zwischen problematischem Verhalten und den folgenden Konsequenzen",
         "Die apparative Enuresis-Behandlung basiert \u00fcberwiegend auf einer klassischen Konditionierung"])

    # 2006-october Q20 (no type label in PDF)
    add_q('2006-october', 20, 'Aussagenkombination',
        'Welcher der folgenden Aussagen trifft (treffen) zu? Zu den Negativsymptomen einer Schizophrenie z\u00e4hlt (z\u00e4hlen):',
        ["Nur die Aussage 1 ist richtig",
         "Nur die Aussagen 2 und 4 sind richtig",
         "Nur die Aussagen 2, 3 und 4 sind richtig",
         "Nur die Aussagen 1, 2, 4 und 5 sind richtig",
         "Alle Aussagen sind richtig"],
        ["Inhaltliche Denkst\u00f6rungen",
         "Emotionale Verarmung",
         "Gedankenausbreitung",
         "Sozialer R\u00fcckzug",
         "Manie"])

    # 2006-october Q21 (no type label in PDF)
    add_q('2006-october', 21, 'Aussagenkombination',
        'Welcher der folgenden Aussagen treffen zu? Zu den typischen Symptomen einer Manie z\u00e4hlen:',
        ["Nur die Aussagen 1 und 2 sind richtig",
         "Nur die Aussagen 3 und 4 sind richtig",
         "Nur die Aussagen 1, 2 und 4 sind richtig",
         "Nur die Aussagen 1, 2, 3 und 4 sind richtig",
         "Alle Aussagen sind richtig"],
        ["Ein deutlich vermehrtes Redebed\u00fcrfnis",
         "Man h\u00e4lt sich f\u00fcr deutlich qualifizierter und intelligenter als man tats\u00e4chlich ist",
         "Ein deutlich erh\u00f6htes Schlafbed\u00fcrfnis",
         "Formale Denkst\u00f6rungen",
         "Vermindertes Selbstwertgef\u00fchl mit Zweifel an sich selbst"])

    # 2005-march Q8 (scanned page, manually transcribed)
    add_q('2005-march', 8, 'Mehrfachauswahl',
        'Verhaltenstherapeutische Methoden und Techniken sind: W\u00e4hlen Sie zwei Antworten!',
        ["Probleml\u00f6setraining",
         "Unbedingte Wertsch\u00e4tzung des Klienten durch den Therapeuten",
         "Liegende Position des Patienten mit fehlendem Blickkontakt zum Therapeuten",
         "Shaping (schrittweise Ausformung des Verhaltens)",
         "Aufforderung an den Patienten, frei zu assoziieren"])

    # 2005-march Q11 (scanned page, manually transcribed)
    add_q('2005-march', 11, 'Einfachauswahl',
        'Welche Aussage trifft zu? Ein Patient gibt an, dass seine eigenen Gedanken laut w\u00fcrden. Die Angabe spricht am ehesten f\u00fcr eine',
        ["organische Wesens\u00e4nderung",
         "Schizophrenie",
         "endogene Manie",
         "endogene Depression",
         "symptomatische Psychose"])

    # 2005-march Q28 (scanned page, manually transcribed)
    add_q('2005-march', 28, 'Einfachauswahl',
        'Welche Aussage trifft f\u00fcr eine Hebephrenie (hebephrene Schizophrenie) zu?',
        ["Die Krankheit beginnt meist nach dem 45. Lebensjahr",
         "Wahnvorstellungen und Halluzinationen stehen im Vordergrund des Krankheitsbildes",
         "Die Stimmung ist flach und unpassend",
         "Ursache ist ein chronischer Alkoholmissbrauch",
         "Das Verhalten ist zielgerichtet und vorhersehbar"])

    # === 2008-march (scanned PDF - all 28 questions manually transcribed) ===
    add_q('2008-march', 1, 'Aussagenkombination',
        'Welche der im Folgenden genannten Begriffe kommen als Differentialdiagnose zu Tic-St\u00f6rungen in Frage?',
        ["Nur die Aussagen 1 und 4 sind richtig",
         "Nur die Aussagen 2 und 3 sind richtig",
         "Nur die Aussagen 1, 3 und 5 sind richtig",
         "Nur die Aussagen 3, 4 und 5 sind richtig",
         "Alle Aussagen sind richtig"],
        ["Sp\u00e4tdyskinesien nach Neuroleptika-Behandlung",
         "Aufmerksamkeitsdefizit-Hyperaktivit\u00e4tsst\u00f6rung (ADHS)",
         "Zwangsst\u00f6rungen",
         "Hyperkinesen durch Medikamente",
         "Folgen bestimmter Infektionskrankheiten"])

    add_q('2008-march', 2, 'Aussagenkombination',
        'Welche der folgenden Aussagen treffen zu? Ursachen f\u00fcr eine Demenz k\u00f6nnen sein:',
        ["Nur die Aussagen 1, 2 und 3 sind richtig",
         "Nur die Aussagen 1, 3 und 5 sind richtig",
         "Nur die Aussagen 1, 2, 3 und 4 sind richtig",
         "Nur die Aussagen 1, 2, 4 und 5 sind richtig",
         "Nur die Aussagen 2, 3, 4 und 5 sind richtig"],
        ["HIV-Infektion",
         "Fehlern\u00e4hrung (Nikotins\u00e4uremangel)",
         "Schilddr\u00fcsenunterfunktion",
         "Wiederholte Schlaganf\u00e4lle",
         "Kurzfristiger Alkoholgenuss unter 15 g Alkohol/Tag bei einem gesunden Erwachsenen"])

    add_q('2008-march', 3, 'Aussagenkombination',
        'Welche der folgenden Aussagen passen zur Manie?',
        ["Nur die Aussagen 1 und 3 sind richtig",
         "Nur die Aussagen 1, 3 und 4 sind richtig",
         "Nur die Aussagen 2, 4 und 5 sind richtig",
         "Nur die Aussagen 1, 3, 4 und 5 sind richtig",
         "Alle Aussagen sind richtig"],
        ["Der Betroffene \u00fcbersch\u00e4tzt sich selbst",
         "Es bestehen hypochondrische Z\u00fcge",
         "Es kommt zu Assoziationslockerungen",
         "Es besteht ein erh\u00f6htes Schlafbed\u00fcrfnis",
         "Es kommt zu Minderwertigkeitsgef\u00fchlen"])

    add_q('2008-march', 4, 'Einfachauswahl',
        'Eine \u201eanankastische (zwanghafte) Pers\u00f6nlichkeit\u201c (nach ICD-10) ist unter anderem durch folgende Begriffe definiert:',
        ["Deutliche und andauernde Verantwortungslosigkeit und Missachtung sozialer Normen, Regeln und Verpflichtungen",
         "\u00dcberm\u00e4\u00dfige Inanspruchnahme durch Phantasie und Introspektion",
         "Ausgepr\u00e4gte Sorge, in sozialen Situationen kritisiert oder abgelehnt zu werden",
         "Rigidit\u00e4t und Eigensinn",
         "Dramatisierung bez\u00fcglich der eigenen Person, theatralisches Verhalten, \u00fcbertriebener Ausdruck von Gef\u00fchlen"])

    add_q('2008-march', 5, 'Einfachauswahl',
        'Unter einer Verhaltenstherapie versteht man',
        ["eine klientenzentrierte Gespr\u00e4chspsychotherapie (nach Rogers)",
         "eine psychoanalytische Psychotherapie",
         "eine psychoanalytische Fokaltherapie",
         "eine \u00fcbertragungsfokussierte Psychotherapie",
         "ein Behandlungsverfahren, das auf Erkenntnissen der empirischen Psychologie (z.B. Lerntheorie) basiert"])

    add_q('2008-march', 6, 'Mehrfachauswahl',
        'Welche der folgenden Aussagen treffen zu? W\u00e4hlen Sie zwei Antworten! An chronischen Opiatkonsum (Drogenkonsument) ist zu denken bei:',
        ["Engen Pupillen",
         "Weiten Pupillen",
         "Schlechten Z\u00e4hnen",
         "Deutlicher Gewichtszunahme",
         "Diarrh\u00f6"])

    add_q('2008-march', 7, 'Mehrfachauswahl',
        'Welche der folgenden Aussagen treffen zu? W\u00e4hlen Sie zwei Antworten! In der klientenzentrierten Psychotherapie (nach Rogers)',
        ["wird die Technik der freien Assoziation angewendet",
         "k\u00f6nnen Anpassungsst\u00f6rungen bearbeitet werden",
         "wiederholt der Therapeut die Aussagen des Patienten",
         "ber\u00e4t der Therapeut den Patienten in Lebenskrisen",
         "muss der Patient so lange in der Angstsituation verbleiben, bis die Angst abnimmt"])

    add_q('2008-march', 8, 'Aussagenkombination',
        'Bei welchen der folgenden Medikamentengruppen ist bei regelm\u00e4\u00dfiger Einnahme mit einer Abh\u00e4ngigkeitsentwicklung zu rechnen?',
        ["Nur die Aussagen 1, 2 und 4 sind richtig",
         "Nur die Aussagen 1, 3 und 4 sind richtig",
         "Nur die Aussagen 1, 3 und 5 sind richtig",
         "Nur die Aussagen 3, 4 und 5 sind richtig",
         "Alle Aussagen sind richtig"],
        ["Bei Morphinpr\u00e4paraten",
         "Bei Antidepressiva",
         "Bei Codeinpr\u00e4paraten",
         "Bei Tranquilizern",
         "Bei Neuroleptika"])

    add_q('2008-march', 9, 'Einfachauswahl',
        'Welche Aussage trifft zu? Typisch f\u00fcr die hebephrene Schizophrenie ist:',
        ["Im Vordergrund stehen akustische Halluzinationen (Stimmenh\u00f6ren)",
         "Im Vordergrund stehen affektive Ver\u00e4nderungen",
         "Im Vordergrund steht vor allem eine allgemeine Antriebssteigerung",
         "Sie tritt vor allem im h\u00f6heren Lebensalter auf (typischerweise nach dem 60. Lebensjahr)",
         "Denkst\u00f6rungen treten sehr selten auf"])

    add_q('2008-march', 10, 'Aussagenkombination',
        'Welche Komplikationen bzw. Symptome k\u00f6nnen bei einer Anorexia nervosa auftreten?',
        ["Nur die Aussagen 1 und 3 sind richtig",
         "Nur die Aussagen 2, 4 und 5 sind richtig",
         "Nur die Aussagen 1, 2, 3 und 4 sind richtig",
         "Nur die Aussagen 2, 3, 4 und 5 sind richtig",
         "Alle Aussagen sind richtig"],
        ["Abf\u00fchrmittelmissbrauch",
         "Suizidalit\u00e4t",
         "Natrium- und Kaliummangel",
         "Selbst induziertes Erbrechen",
         "Deutliche Verminderung der Libido bei M\u00e4nnern"])

    add_q('2008-march', 11, 'Mehrfachauswahl',
        'Welche der folgenden St\u00f6rungen des Denkens gelten als Ich-St\u00f6rungen? W\u00e4hlen Sie zwei Antworten!',
        ["Gedankenentzug",
         "Stimmungslabilit\u00e4t",
         "Gesteigertes Selbstwertgef\u00fchl",
         "Gedankeneingebung",
         "Innere Unruhe"])

    add_q('2008-march', 12, 'Aussagenkombination',
        'Welche der folgenden Aussagen zur Depression treffen zu?',
        ["Nur die Aussagen 1, 2 und 3 sind richtig",
         "Nur die Aussagen 1, 3 und 5 sind richtig",
         "Nur die Aussagen 2, 4 und 5 sind richtig",
         "Nur die Aussagen 1, 2, 3 und 5 sind richtig",
         "Alle Aussagen sind richtig"],
        ["Depressive St\u00f6rungen k\u00f6nnen in jedem Lebensalter \u2013 auch in der Kindheit \u2013 auftreten.",
         "Die Lichttherapie wird bei der sog. Winterdepression als Behandlungsform eingesetzt.",
         "Typische Symptome sind Verminderung des Antriebs und Aktivit\u00e4tseinschr\u00e4nkung.",
         "Wahnideen wie z. B. Vers\u00fcndigungs- oder Verarmungsideen schlie\u00dfen eine schwere depressive St\u00f6rung aus.",
         "In der depressiven Phase kann es zu St\u00f6rungen des Vegetativums kommen (z. B. der Libido)."])

    add_q('2008-march', 13, 'Einfachauswahl',
        'Welche Aussage trifft zu? Die Panikst\u00f6rung, auch als \u201eepisodisch paroxysmale Angst\u201c bezeichnet,',
        ["ist gekennzeichnet durch wiederkehrende schwere Angstattacken, die vorhersagbar sind, da sie im Zusammenhang mit spezifischen Ausl\u00f6sern auftreten, z.B. beim Betreten eines Aufzuges",
         "\u00e4u\u00dfert sich oft mit pl\u00f6tzlich auftretendem Herzklopfen, Brustschmerz, Erstickungsgef\u00fchlen, Schwindel und Entfremdungsgef\u00fchlen (Depersonalisation oder Derealisation)",
         "l\u00e4sst sich medikament\u00f6s problemlos beseitigen",
         "l\u00e4sst sich durch das Auftreten optischer Halluzinationen diagnostizieren",
         "ist Ursache einer paranoiden Schizophrenie"])

    add_q('2008-march', 14, 'Aussagenkombination',
        'Welche der folgenden Aussagen zur geistigen Behinderung treffen zu?',
        ["Nur die Aussagen 1 und 3 sind richtig",
         "Nur die Aussagen 1, 4 und 5 sind richtig",
         "Nur die Aussagen 2, 3 und 5 sind richtig",
         "Nur die Aussagen 2, 4 und 5 sind richtig",
         "Alle Aussagen sind richtig"],
        ["Menschen mit geistiger Behinderung haben oft eine Mehrfachbehinderung.",
         "Von einer mittelgradigen Intelligenzminderung (Imbezillit\u00e4t) spricht man bei einem IQ von 85.",
         "Bei Kindern mit geistiger Behinderung gelingt es heute in \u00fcber 90 % der F\u00e4lle die Ursachen zu kl\u00e4ren.",
         "Je schwerer der Grad der geistigen Behinderung, desto h\u00e4ufiger bestehen psychische St\u00f6rungen und Symptome.",
         "Zu den pr\u00e4ventiven Ma\u00dfnahmen gegen bestimmte angeborene Intelligenzminderungen geh\u00f6ren Schutzimpfungen der Mutter vor Eintritt der Schwangerschaft."])

    add_q('2008-march', 15, 'Mehrfachauswahl',
        'Welche der folgenden Begriffe sind typisch f\u00fcr die Aufmerksamkeitsdefizit-Hyperaktivit\u00e4tsst\u00f6rung (ADHS) bei Kindern? W\u00e4hlen Sie zwei Antworten!',
        ["Gute Schulnoten",
         "Beginn ab dem 9. Lebensjahr",
         "Regelverletzungen",
         "Gro\u00dfer Freundeskreis",
         "Niedrige Frustrationstoleranz"])

    add_q('2008-march', 16, 'Einfachauswahl',
        'Sie machen einen Hausbesuch bei einem Patienten, der st\u00e4ndig nestelnde Bewegungen mit den H\u00e4nden ausf\u00fchrt. Er ist scheinbar orientierungslos, redet ohne erkennbaren Zusammenhang und hat scheinbar optische Halluzinationen. Welche der genannten Erkrankungen kommt am ehesten in Betracht?',
        ["Manische Phase",
         "Demenz",
         "Delirium tremens",
         "SHT (Sch\u00e4del-Hirn-Trauma)",
         "Schizophrenie"])

    add_q('2008-march', 17, 'Aussagenkombination',
        'Welche der folgenden Aussagen zum Suizid trifft (treffen) zu?',
        ["Nur die Aussage 3 ist richtig",
         "Nur die Aussagen 1 und 4 sind richtig",
         "Nur die Aussagen 2 und 3 sind richtig",
         "Nur die Aussagen 4 und 5 sind richtig",
         "Alle Aussagen sind richtig"],
        ["Der Betroffene sollte nicht auf einen geplanten Suizid angesprochen werden",
         "In Deutschland liegt der Suizid an Rang 2 der Todesursachen",
         "Zu den Risikogruppen z\u00e4hlen alleinlebende Patienten ohne enge famili\u00e4re Bindung",
         "Wer einmal einen Suizidversuch unternommen hat wird dies nie wieder tun",
         "Lehnt ein Suizidgef\u00e4hrdeter eine Behandlung ab, so muss dies akzeptiert werden"])

    add_q('2008-march', 18, 'Einfachauswahl',
        'Welche der genannten Krankheiten kann Ursache eines endokrinen (hormonell bedingten) Psychosyndroms sein?',
        ["Gehirnersch\u00fctterung",
         "Alkoholmissbrauch",
         "Hypothyreose",
         "Alzheimer-Erkrankung",
         "Drogensucht"])

    add_q('2008-march', 19, 'Aussagenkombination',
        'Zu den formalen Denkst\u00f6rungen geh\u00f6ren:',
        ["Nur die Aussagen 1, 3 und 4 sind richtig",
         "Nur die Aussagen 1, 2, 3 und 5 sind richtig",
         "Nur die Aussagen 1, 2, 4 und 5 sind richtig",
         "Nur die Aussagen 2, 3, 4 und 5 sind richtig",
         "Alle Aussagen sind richtig"],
        ["Perseveration bei hirnorganischen Erkrankungen",
         "Denkhemmung bei depressiven Zust\u00e4nden",
         "Ideenflucht bei manischen Erkrankungen",
         "Wahnhaftes Denken bei paranoiden Psychosen",
         "Zerfahrenes Denken bei Schizophrenie"])

    add_q('2008-march', 20, 'Einfachauswahl',
        'Welche Aussage trifft zu? Typisch f\u00fcr eine organische Halluzinose ist:',
        ["Im Vordergrund steht eine getr\u00fcbte Bewusstseinseinslage",
         "Die Halluzinationen k\u00f6nnen vom Patienten manchmal als solche erkannt werden",
         "Sie ist mit Verhaltenstherapie gut therapierbar",
         "Sie tritt bevorzugt zu Beginn der Pubert\u00e4t auf",
         "Wahn dominiert das klinische Bild"])

    add_q('2008-march', 21, 'Einfachauswahl',
        'Sie werden zu einem Hausbesuch zu einer Patientin gebeten und erfahren, dass sie an einer Depression leidet, die vom Arzt medikament\u00f6s behandelt wird. Seit 5 Tagen nimmt sie schon die (trizyklischen) Antidepressiva ein, und es zeigt sich keinerlei Besserung der Stimmung. (Eine Suizidgef\u00e4hrdung ist nicht gegeben). Wie ist Ihr weiteres Vorgehen?',
        ["Da sich nach 5 Tagen noch keinerlei Besserung zeigt, setzen Sie das Medikament ab und raten einen Psychiater aufzusuchen.",
         "Sie setzen das bisher verordnete Medikament ab und verordnen Johanniskraut.",
         "Da sich bisher keinerlei Besserung eingestellt hat, schlagen Sie vor, die Dosis des verschriebenen Medikaments zu erh\u00f6hen.",
         "Nachdem Sie sich \u00fcberzeugt haben, dass die Patientin gut betreut wird, raten Sie ihr weiter abzuwarten, da die Medikamente meist l\u00e4ngere Zeit brauchen, bis sich eine Wirkung einstellt.",
         "Da das Medikament keine Wirkung zeigt, muss die Ursache der Depression herausgefunden werden, am besten durch eine analytische Vorgehensweise."])

    add_q('2008-march', 22, 'Aussagenkombination',
        'Welche der folgenden Aussagen zum Korsakow-Syndrom treffen zu?',
        ["Nur die Aussagen 3 und 5 sind richtig",
         "Nur die Aussagen 1, 2 und 4 sind richtig",
         "Nur die Aussagen 1, 4 und 5 sind richtig",
         "Nur die Aussagen 1, 2, 4 und 5 sind richtig",
         "Alle Aussagen sind richtig"],
        ["Typisch hierf\u00fcr sind Desorientiertheit und Konfabulieren",
         "Prim\u00e4re Ursache ist ein Mangel an Vitamin C",
         "St\u00f6rungen des Zeitgef\u00fchls und des Zeitgitters treten nicht auf",
         "Irreversible Verl\u00e4ufe werden beobachtet",
         "Pers\u00f6nlichkeitsver\u00e4nderungen treten auf"])

    add_q('2008-march', 23, 'Einfachauswahl',
        'Welche Aussage trifft zu? Als \u00dcbertragung (im engeren Sinne) bezeichnet man in der Psychoanalyse:',
        ["Den Vorgang, durch den ein Psychisches in ein k\u00f6rperliches Symptom umgewandelt wird.",
         "Einen psychodynamischen Vorgang, durch den ein Angstimpuls in psychotisches Erlebnis \u00fcbertragen wird.",
         "Den Vorgang, durch den ein \u2013 z.B. optisch wahrgenommenes \u2013 Geschehen in die subjektive, f\u00fcr andere unverst\u00e4ndliche Logik eines psychotischen Erlebens \u00fcbertragen wird.",
         "Den Vorgang des \u00dcbergehens depressiver Erlebnisweisen in manisches Erleben.",
         "Fr\u00fchere Beziehungs- und Interaktionsmuster werden auf die therapeutische Beziehung \u00fcbertragen."])

    add_q('2008-march', 24, 'Mehrfachauswahl',
        'Welche der folgenden Aussagen zur Demenz treffen zu? W\u00e4hlen Sie zwei Antworten!',
        ["Bei der Demenz vom Alzheimer Typ f\u00e4llt ein akuter Beginn eines amnestischen Syndroms auf.",
         "Die vaskul\u00e4re Demenz ist h\u00e4ufig mit einem Bluthochdruck verbunden.",
         "Im Rahmen einer AIDS-Erkrankung kann im sp\u00e4teren Verlauf eine Demenz beobachtet werden.",
         "Die Alzheimer-Krankheit ist mit Medikamenten heilbar.",
         "Bei der Diagnose von Demenzerkrankungen spielen bildgebende Verfahren (z.B. kraniale Computertomographie) keine Rolle."])

    add_q('2008-march', 25, 'Einfachauswahl',
        'Sie sehen sich einem Patienten gegen\u00fcber, der Ihrer Meinung nach ernsthaft ank\u00fcndigt, sich das Leben zu nehmen. Unter welchen Voraussetzungen m\u00fcssen Sie auch gegen seinen Willen die Unterbringung in einem psychiatrischen Krankenhaus einleiten?',
        ["In keinem Fall, auch ein Selbstt\u00f6tungskandidat sollte nicht gegen seinen Willen station\u00e4r untergebracht werden.",
         "In jedem Fall, wenn Sie von der Ernsthaftigkeit der Ank\u00fcndigung und einer unmittelbar drohenden Gef\u00e4hrdung \u00fcberzeugt sind.",
         "In keinem Fall, da die Einschr\u00e4nkung des Rechts auf freie Entfaltung der Pers\u00f6nlichkeit entgegensteht.",
         "In keinem Fall, da bei ausreichend intensiver Zuwendung eine station\u00e4re Einweisung vermeidbar ist.",
         "In keinem Fall, da es sich nicht um eine St\u00f6rung der \u00f6ffentlichen Sicherheit und Ordnung handelt."])

    add_q('2008-march', 26, 'Aussagenkombination',
        'Welche der folgenden Aussagen treffen zu? Zu den diagnostischen Leitlinien der Alkoholabh\u00e4ngigkeit nach ICD-10 z\u00e4hlen:',
        ["Nur die Aussagen 1 und 2 sind richtig",
         "Nur die Aussagen 3 und 4 sind richtig",
         "Nur die Aussagen 1, 2 und 3 sind richtig",
         "Nur die Aussagen 1, 3, 4 und 5 sind richtig",
         "Alle Aussagen sind richtig"],
        ["Verminderte Kontrollf\u00e4higkeit bez\u00fcglich des Beginns, der Beendigung und der Menge des Konsums",
         "Dauerhafte Organsch\u00e4den, beispielsweise der Leber",
         "Ein k\u00f6rperliches Entzugssyndrom bei Beendigung oder Reduktion des Konsums",
         "Nachweis einer Toleranz",
         "Fortschreitende Vernachl\u00e4ssigung anderer Vergn\u00fcgen oder Interessen zugunsten des Substanzkonsums"])

    add_q('2008-march', 27, 'Mehrfachauswahl',
        'Welche der folgenden Aussagen zur prim\u00e4ren Enuresis treffen zu? W\u00e4hlen Sie zwei Antworten!',
        ["Nach bereits erworbener Blasenkontrolle \u00fcber 6 Monate tritt wieder Einn\u00e4ssen auf",
         "Famili\u00e4re H\u00e4ufung wird nur selten beobachtet",
         "Prim\u00e4re Enuresis ist definiert als unwillk\u00fcrliches Einn\u00e4ssen ohne somatischen Befund \u00fcber das 5. Lebensjahr hinaus",
         "Der Verlauf zeigt eine hohe Spontanheilungsrate",
         "Am h\u00e4ufigsten tritt sie tags\u00fcber auf (Enuresis diurna)"])

    add_q('2008-march', 28, 'Aussagenkombination',
        'Welche der folgenden Aussagen trifft (treffen) f\u00fcr die bipolare affektive St\u00f6rung nach ICD-10 (manisch-depressive Krankheit) zu?',
        ["Nur die Aussage 1 ist richtig",
         "Nur die Aussagen 2 und 3 sind richtig",
         "Nur die Aussagen 2, 3 und 4 sind richtig",
         "Nur die Aussagen 1, 2, 4 und 5 sind richtig",
         "Alle Aussagen sind richtig"],
        ["Bei der Entwicklung affektiver St\u00f6rungen k\u00f6nnen fr\u00fchere Umwelteinfl\u00fcsse eine Rolle spielen.",
         "Charakteristisch bei der bipolaren affektiven Erkrankung ist eine weitgehende bis vollst\u00e4ndige Besserung zwischen den Episoden.",
         "Von der Erkrankung sind fast nur M\u00e4nner betroffen.",
         "Manische Episoden beginnen in der Regel abrupt (rasch, innerhalb weniger Tage) und dauern zwischen zwei Wochen und vier bis f\u00fcnf Monaten.",
         "Depressive Phasen der bipolaren St\u00f6rung tendieren zu l\u00e4ngerer Dauer, selten allerdings l\u00e4nger als ein Jahr."])

    # === 2007-october (scanned PDF - all 28 questions manually transcribed) ===
    add_q('2007-october', 1, 'Mehrfachauswahl',
        'Welche der folgenden Aussagen treffen zu? W\u00e4hlen Sie zwei Antworten! Typische Symptome der Manie sind:',
        ["Ideenflucht",
         "Depersonalisation",
         "Zwangsgedanken",
         "Vermindertes Schlafbed\u00fcrfnis",
         "Somatisierungsst\u00f6rung"])

    add_q('2007-october', 2, 'Einfachauswahl',
        'Der fr\u00fchkindliche Autismus ist eine Erkrankung mit meist chronischem Verlauf. Welche Aussage zum fr\u00fchkindlichen Autismus trifft zu?',
        ["Autismus kommt bei M\u00e4dchen wesentlich h\u00e4ufiger vor als bei Knaben (etwa drei- bis viermal h\u00e4ufiger)",
         "Ein autistisches Kind bedarf keiner Therapie, da die Symptome in der Pubert\u00e4t (sp\u00e4testens in der Adoleszenz) eine Spontanheilung erfahren",
         "Autistische Kinder kapseln sich zwar von ihrer Umgebung ab, entwickeln aber ein hohes Ma\u00df an Empathie, Mitleid und Wunsch nach emotionaler Zuwendung",
         "Die Kommunikation ist von klein auf gest\u00f6rt, die aktive Sprache bleibt wenig produktiv, sie ist unmoduliert, affektarm und wird kaum von Mimik und Gestik begleitet",
         "Hirnorganische St\u00f6rungen, insbesondere eine Epilepsie oder Intelligenzminderungen werden bei autistischen Kindern in der Regel nicht beobachtet"])

    add_q('2007-october', 3, 'Aussagenkombination',
        'Welche der folgenden Aussagen zur Akathisie treffen zu?',
        ["Nur die Aussagen 1 und 2 sind richtig",
         "Nur die Aussagen 1, 2 und 5 sind richtig",
         "Nur die Aussagen 2, 3 und 4 sind richtig",
         "Nur die Aussagen 3, 4 und 5 sind richtig",
         "Alle Aussagen sind richtig"],
        ["Die Akathisie kommt im Verlauf einer Neuroleptikatherapie vor",
         "Die Akathisie hat einen hohen subjektiven Beschwerdecharakter",
         "Die Akathisie ist ein wesentlicher Grund f\u00fcr medikament\u00f6se Non-Compliance",
         "Die Akathisie bereitet nicht selten erhebliche differenzialdiagnostische Probleme, vor allem kann sie als psychosebedingte Unruhesymptomatik fehlgedeutet werden",
         "Charakteristisch f\u00fcr Akathisie ist innere Unruhe und Bewegungsdrang"])

    add_q('2007-october', 4, 'Aussagenkombination',
        'Welche der folgenden Aussagen zum Einn\u00e4ssen oder Einkoten bei Kindern trifft (treffen) zu?',
        ["Nur die Aussage 4 ist richtig",
         "Nur die Aussagen 1 und 4 sind richtig",
         "Nur die Aussagen 2, 3 und 5 sind richtig",
         "Nur die Aussagen 1, 2, 4 und 5 sind richtig",
         "Alle Aussagen sind richtig"],
        ["Die Anwendung von Verst\u00e4rkerpl\u00e4nen ist eine Therapieoption",
         "F\u00fcr das Toilettentraining beim Einkoten werden feste Uhrzeiten f\u00fcr den Toilettengang vereinbart",
         "Einkoten ist bei Kleinkindern (unter 2 Jahren) i. d. R. psychisch bedingt",
         "Eine genaue Dokumentation der H\u00e4ufigkeit von Einn\u00e4ssen oder Einkoten ist unerl\u00e4sslich",
         "Ein Blasentraining wird oft mit gesteigerter Fl\u00fcssigkeitszufuhr gekoppelt"])

    add_q('2007-october', 5, 'Mehrfachauswahl',
        'Ein Therapeut besitzt eine auf das Gebiet der heilkundlichen Psychotherapie beschr\u00e4nkte Erlaubnis nach dem Heilpraktikergesetz. Welche der folgenden Verfahren oder Techniken darf dieser Therapeut anwenden? W\u00e4hlen Sie zwei Antworten!',
        ["Entspannungstraining",
         "Chirotherapie",
         "Akupressur",
         "Testpsychologische Untersuchungen",
         "Sauerstoff-Mehrschritt-Therapie zur Krebsbehandlung"])

    add_q('2007-october', 6, 'Aussagenkombination',
        'Welche der folgenden Symptome/Erkrankungen sind typisch f\u00fcr chronischen Alkoholismus?',
        ["Nur die Aussagen 1 und 3 sind richtig",
         "Nur die Aussagen 1 und 5 sind richtig",
         "Nur die Aussagen 2 und 4 sind richtig",
         "Nur die Aussagen 1, 2, 4 und 5 sind richtig",
         "Nur die Aussagen 2, 3, 4 und 5 sind richtig"],
        ["Mangelern\u00e4hrung",
         "Gerinnungsst\u00f6rung",
         "Erh\u00f6hte Kreativit\u00e4t",
         "Potenzst\u00f6rung",
         "Wernicke-Syndrom"])

    add_q('2007-october', 7, 'Einfachauswahl',
        'Welche Aussage trifft zu? Eine Negativsymptomatik',
        ["tritt im Rahmen des \u00dcbertragungswiderstands bei der Psychoanalyse auf",
         "wird oft bei dissozialen Pers\u00f6nlichkeitsst\u00f6rungen beobachtet",
         "ist ein h\u00e4ufiges Symptom bei chronischen Schizophrenien",
         "charakterisiert den Verlauf therapieresistenter Depressionen",
         "bezeichnet die Krankheitsuneinsichtigkeit bei Manikern"])

    add_q('2007-october', 8, 'Einfachauswahl',
        'Eine Ihrer Patientinnen berichtet von ihrem Mann. Dieser sei seit seiner Pensionierung vor 6 Jahren reizbar und depressiv. Er verhalte sich teilweise wie ein kleines Kind und sie m\u00fcsse ihm die Schuhe zubinden, weil er mit offenen Schuhen herumlaufen w\u00fcrde. Wichtige Telefonnummern vergesse er immer wieder und sie m\u00fcsse sie ihm aufschreiben. Welche Verdachtsdiagnose haben Sie?',
        ["Schizophrenie",
         "Multiple Sklerose",
         "Demenz",
         "Parkinson-Syndrom",
         "Depression"])

    add_q('2007-october', 9, 'Einfachauswahl',
        'Ideenflucht ist ein Symptom bei psychiatrischen Erkrankungen. Darunter ist zu verstehen:',
        ["Eine besondere \u00dcberlastungsreaktion",
         "Eine Zerstreutheit bei k\u00f6rperlicher Erm\u00fcdung",
         "Eine Zerfahrenheit",
         "Ein krankhaft beschleunigter Denkablauf",
         "Eine Wahnvorstellung"])

    add_q('2007-october', 10, 'Einfachauswahl',
        'Hypochondrische Bef\u00fcrchtungen sind am wenigsten zu erwarten bei:',
        ["Somatisierungsst\u00f6rung",
         "Herzangstneurose",
         "Dysmorphophobie",
         "Manische Episode im Rahmen der bipolaren affektiven St\u00f6rung",
         "Anhaltende somatoforme Schmerzst\u00f6rung"])

    add_q('2007-october', 11, 'Aussagenkombination',
        'Eine Ihrer Patientinnen ist vom Psychiater mit Antidepressiva eingestellt worden. Der Psychiater ist zur Zeit im Urlaub und sie m\u00f6chte nicht zu dessen Vertreter gehen. Mit welchen der folgenden Nebenwirkungen von (trizyklischen) Antidepressiva ist am ehesten zu rechnen?',
        ["Nur die Aussagen 1, 2, 3 und 4 sind richtig",
         "Nur die Aussagen 1, 2, 3 und 5 sind richtig",
         "Nur die Aussagen 1, 2, 4 und 5 sind richtig",
         "Nur die Aussagen 1, 3, 4 und 5 sind richtig",
         "Nur die Aussagen 2, 3, 4 und 5 sind richtig"],
        ["Mundtrockenheit",
         "Schwitzen",
         "Durchfall",
         "Hypotonie",
         "Gewichtszunahme"])

    add_q('2007-october', 12, 'Aussagenkombination',
        'Welche der folgenden Aussagen trifft (treffen) zu?',
        ["Nur die Aussage 1 ist richtig",
         "Nur die Aussagen 1 und 3 sind richtig",
         "Nur die Aussagen 1, 2 und 5 sind richtig",
         "Nur die Aussagen 2, 3 und 5 sind richtig",
         "Alle Aussagen sind richtig"],
        ["Die operante Konditionierung kann bei chronisch Schizophrenen eingesetzt werden.",
         "Bei akuten Psychosen kann durch kognitive Restrukturierung eine anhaltende Distanzierung von Wahninhalten erreicht werden.",
         "Die operante Konditionierung darf auch von ausgebildeten Helfern ausgef\u00fchrt werden (nach Verordnung durch befugte Personen, z.B. Arzt, Heilpraktiker).",
         "In der Behandlung von Kindern bevorzugt man die klassische Konditionierung.",
         "Beim operanten Konditionieren wird durch systematische Reizreduktion eine Verhaltens\u00e4nderung bewirkt."])

    add_q('2007-october', 13, 'Aussagenkombination',
        'Welche der folgenden Aussagen treffen zu? In bestimmten Phasen des Kindes- und Jugendalters finden sich jeweils f\u00fcr diese Phase typische entwicklungsabh\u00e4ngige emotionale Ph\u00e4nomene bzw. St\u00f6rungen. Hierzu z\u00e4hlen:',
        ["Nur die Aussagen 1 und 4 sind richtig",
         "Nur die Aussagen 2 und 3 sind richtig",
         "Nur die Aussagen 2 und 4 sind richtig",
         "Nur die Aussagen 1, 2 und 3 sind richtig",
         "Nur die Aussagen 2, 3 und 5 sind richtig"],
        ["Dunkelangst in der Adoleszenz",
         "Trennungsangst im Kindesalter",
         "Agoraphobie im Kleinkindalter",
         "Passagere zwangs\u00e4hnliche Rituale bei jungen Kindern",
         "Artikulationsst\u00f6rungen im S\u00e4uglingsalter"])

    add_q('2007-october', 14, 'Aussagenkombination',
        'Bei welchen der folgenden Erkrankungen kann es zur Entwicklung einer Demenz kommen?',
        ["Nur die Aussagen 1 und 2 sind richtig",
         "Nur die Aussagen 3 und 4 sind richtig",
         "Nur die Aussagen 1, 2 und 3 sind richtig",
         "Nur die Aussagen 1, 2, 4 und 5 sind richtig",
         "Alle Aussagen sind richtig"],
        ["Rezidivierende zerebrale Insulte",
         "M. Parkinson",
         "Creutzfeldt-Jakob-Krankheit",
         "Multiple Sklerose",
         "Epilepsie"])

    add_q('2007-october', 15, 'Aussagenkombination',
        'Welche der folgenden Aussagen zur Anorexia nervosa treffen zu?',
        ["Nur die Aussagen 2 und 4 sind richtig",
         "Nur die Aussagen 1, 2 und 3 sind richtig",
         "Nur die Aussagen 1, 3 und 4 sind richtig",
         "Nur die Aussagen 2, 3 und 4 sind richtig",
         "Alle Aussagen sind richtig"],
        ["Alle Anorexia nervosa-Kranken sind Frauen",
         "Anorexia nervosa-Kranke sind in Schule oder Beruf ehrgeizig und leistungsf\u00e4hig",
         "Ein Body-Mass-Index (BMI) von 25 ist typisch",
         "Bei starker Abmagerung anorektischer Patienten/Patientinnen k\u00f6nnen Zwangsma\u00dfnahmen (z.B. Zwangseinweisung in ein psychiatrisches Krankenhaus) notwendig werden",
         "Anorexia nervosa-Kranke haben ein stabiles Selbstbewusstsein"])

    add_q('2007-october', 16, 'Aussagenkombination',
        'Welche der folgenden Aussagen \u00fcber das Aufmerksamkeitsdefizitsyndrom (ADS) trifft (treffen) zu?',
        ["Nur die Aussage 1 ist richtig",
         "Nur die Aussagen 1 und 2 sind richtig",
         "Nur die Aussagen 2 und 5 sind richtig",
         "Nur die Aussagen 1, 2, 3 und 5 sind richtig",
         "Alle Aussagen sind richtig"],
        ["Bei der Behandlung von ADS sollten nicht gleichzeitig Medikamente und psychotherapeutische Techniken eingesetzt werden.",
         "Bei der Aufmerksamkeitsdefizitst\u00f6rung des Kindesalters (ADS) kann eine motorisch hyperaktive Symptomatik v\u00f6llig fehlen.",
         "St\u00f6rungen der Fein- oder Grobmotorik sind ein Ausschlusskriterium f\u00fcr die Diagnose ADS.",
         "Mit Flooding-Techniken erreicht man bei ADS-Patienten oft ein rascheres Verschwinden der Symptomatik als bei anderen Indikationen.",
         "Symptome wie z. B. Distanzlosigkeit oder Impulsivit\u00e4t st\u00fctzen die Diagnose."])

    add_q('2007-october', 17, 'Aussagenkombination',
        'Welche der folgenden Aussagen \u00fcber Autogenes Training treffen zu?',
        ["Nur die Aussagen 1 und 2 sind richtig",
         "Nur die Aussagen 2 und 3 sind richtig",
         "Nur die Aussagen 2, 3 und 5 sind richtig",
         "Nur die Aussagen 3, 4 und 5 sind richtig",
         "Alle Aussagen sind richtig"],
        ["Das Erlernen des Autogenen Trainings kann nur im Gruppensetting erfolgen",
         "Das vegetative Nervensystem wird beeinflusst",
         "Nach Anleitung kann das Autogene Training schon von 8 bis 10-j\u00e4hrigen Kindern selbstst\u00e4ndig ausge\u00fcbt werden",
         "Das Autogene Training ist bei psychotischen Erkrankungen immer gut zur L\u00f6sung von \u00c4ngsten und Spannungen geeignet",
         "Die Wirksamkeit des Autogenen Trainings bei Neurodermitis wurde nachgewiesen"])

    add_q('2007-october', 18, 'Mehrfachauswahl',
        'Welche der folgenden Symptome lassen Sie in erster Linie an eine k\u00f6rperlich verursachte Erkrankung denken? W\u00e4hlen Sie zwei Antworten!',
        ["\u201eAnf\u00e4lle\u201c kurzdauernder Bewusstlosigkeit",
         "St\u00f6rungen der Orientiertheit",
         "Gedankenentzug",
         "Kommentierende Stimmen",
         "Kontrollwahn"])

    add_q('2007-october', 19, 'Aussagenkombination',
        'Welche der folgenden Aussagen treffen zu? Die Differenzialdiagnose der Schizophrenie umfasst u.a. folgende Krankheiten:',
        ["Nur die Aussagen 2 und 3 sind richtig",
         "Nur die Aussagen 1, 2 und 5 sind richtig",
         "Nur die Aussagen 1, 3 und 5 sind richtig",
         "Nur die Aussagen 2, 3 und 4 sind richtig",
         "Alle Aussagen sind richtig"],
        ["Zustand nach Sch\u00e4del-Hirn-Trauma",
         "Schizoaffektive St\u00f6rung",
         "Depression",
         "Substanzmittelmissbrauch",
         "Substanzmittelentzug"])

    add_q('2007-october', 20, 'Mehrfachauswahl',
        'Welche der folgenden Aussagen zur Suizidalit\u00e4t treffen zu? W\u00e4hlen Sie zwei Antworten!',
        ["Die Mehrzahl der in Folge eines Suizids Verstorbenen hat ihren Suizid vorher angek\u00fcndigt",
         "Menschen, die an einer Psychose leiden, ver\u00fcben selten Suizid",
         "Bei einem Patienten mit Suizidversuch in der Vorgeschichte besteht besonders im ersten Jahr Wiederholungsgefahr",
         "Bei der Zahl der Suizidversuche \u00fcberwiegt die Zahl der M\u00e4nner",
         "Bei Verdacht auf Suizidalit\u00e4t sollte dieses Thema im Rahmen der Untersuchung nicht direkt angesprochen werden"])

    add_q('2007-october', 21, 'Aussagenkombination',
        'Welche der folgenden Begriffe geh\u00f6ren zu den Abwehrmechanismen im psychoanalytischen Sinne?',
        ["Nur die Aussagen 1 und 4 sind richtig",
         "Nur die Aussagen 1, 2 und 3 sind richtig",
         "Nur die Aussagen 1, 3 und 4 sind richtig",
         "Nur die Aussagen 2, 3 und 4 sind richtig",
         "Nur die Aussagen 3, 4 und 5 sind richtig"],
        ["Introjektion",
         "Dyslalie",
         "Reaktionsbildung",
         "Intellektualisierung",
         "Internalisierung"])

    add_q('2007-october', 22, 'Einfachauswahl',
        'Ein 45-j\u00e4hriger Mann hatte vor einem Jahr einen Unfall mit seinem Wagen. Seit dieser Zeit hat er nicht nur Angst vor dem Autofahren, sondern auch Angst, mit \u00f6ffentlichen Verkehrsmitteln zu fahren. F\u00fcr die Ausweitung der Angst kommt aus lerntheoretischer Sicht am ehesten in Betracht?',
        ["Diskriminationslernen",
         "Modelllernen",
         "Verst\u00e4rkung",
         "Konditionierung",
         "Reizgeneralisierung"])

    add_q('2007-october', 23, 'Mehrfachauswahl',
        'Welche der folgenden Begriffe geh\u00f6ren zu den formalen Denkst\u00f6rungen? W\u00e4hlen Sie zwei Antworten!',
        ["Projektion",
         "Gedankenabreißen",
         "Residualwahn",
         "Zerfahrenheit",
         "Mutismus"])

    add_q('2007-october', 24, 'Einfachauswahl',
        'Welche Aussage zum Alkoholdelir trifft zu?',
        ["Ein Delirium tremens kann auch w\u00e4hrend fortgesetzten Trinkens auftreten",
         "Ein Vorbote des Delirium tremens ist vermehrter Schlaf",
         "Ein Alkoholentzugsdelir tritt fr\u00fchestens 5 Tage nach Beginn des Entzugs auf",
         "Typisch ist die Symptomtrias: Bewusstseinsklarheit, ungest\u00f6rte Orientierung und akustische Halluzinationen",
         "Bei einem Delir treten folgende vegetativen St\u00f6rungen auf: Hypotonie, Bradykardie, Fr\u00f6steln"])

    add_q('2007-october', 25, 'Aussagenkombination',
        'Welche der folgenden Aussagen treffen zu? Kennzeichen der narzisstischen Pers\u00f6nlichkeitsst\u00f6rung sind:',
        ["Nur die Aussagen 1 und 3 sind richtig",
         "Nur die Aussagen 1 und 4 sind richtig",
         "Nur die Aussagen 3 und 5 sind richtig",
         "Nur die Aussagen 1, 2 und 5 sind richtig",
         "Nur die Aussagen 2, 4 und 5 sind richtig"],
        ["Arrogantes, \u00fcberhebliches Verhalten",
         "Theatralischer Ausdruck von Gef\u00fchlen",
         "Die St\u00f6rung beginnt bei Frauen nach der Menopause",
         "Erwartung, durch andere bevorzugt behandelt zu werden",
         "\u00dcbertriebene Gewissenhaftigkeit und Perfektionismus"])

    add_q('2007-october', 26, 'Aussagenkombination',
        'Welche der folgenden Aussagen trifft (treffen) zu? Die Borderline-Pers\u00f6nlichkeitsst\u00f6rung umfasst:',
        ["Nur die Aussage 1 ist richtig",
         "Nur die Aussagen 1 und 5 sind richtig",
         "Nur die Aussagen 1, 2 und 5 sind richtig",
         "Nur die Aussagen 2, 3 und 5 sind richtig",
         "Alle Aussagen sind richtig"],
        ["Impulsive, h\u00e4ufig selbstsch\u00e4digende Verhaltensweisen",
         "Instabile und wechselhafte Stimmung",
         "Identit\u00e4tsunsicherheit",
         "Dissoziative und paranoide Symptome",
         "Inkonstante und krisenhafte Beziehungen"])

    add_q('2007-october', 27, 'Mehrfachauswahl',
        'Welche der folgenden Aussagen treffen f\u00fcr Cannabiskonsum zu? W\u00e4hlen Sie zwei Antworten!',
        ["Regelm\u00e4\u00dfiger Cannabiskonsum f\u00fchrt zu ausgepr\u00e4gter k\u00f6rperlicher Abh\u00e4ngigkeit",
         "Cannabiskonsum verursacht eine Pupillenverengung (Miosis)",
         "Durch regelm\u00e4\u00dfigen Cannabiskonsum k\u00f6nnen Psychosen ausgel\u00f6st werden",
         "L\u00e4ngerdauernder Cannabiskonsum kann zu psychischer Abh\u00e4ngigkeit f\u00fchren",
         "Bei chronischem Cannabiskonsum kommt es h\u00e4ufig zu einer starken Antriebssteigerung"])

    add_q('2007-october', 28, 'Aussagenkombination',
        'Welche der folgenden Aussagen treffen zu? M\u00f6gliche Hinweise auf Suizidgef\u00e4hrdung bei Verdacht auf Suizidalit\u00e4t sind:',
        ["Nur die Aussagen 1, 2 und 3 sind richtig",
         "Nur die Aussagen 1, 3 und 4 sind richtig",
         "Nur die Aussagen 2, 4 und 5 sind richtig",
         "Nur die Aussagen 1, 2, 3 und 4 sind richtig",
         "Alle Aussagen sind richtig"],
        ["Aggressionsstau und Wendung der Aggression gegen sich selbst",
         "Einengung (sozial, kognitiv) der Wertewelt",
         "Anbehandelte Depression",
         "Suizidphantasien",
         "Vorkommen von Suiziden in der Familie oder Umgebung"])


    # === 2009-march (scanned PDF - all 28 questions manually transcribed) ===
    add_q('2009-march', 1, 'Aussagenkombination',
        'Zu den charakteristischen Symptomen bei der Manie z\u00e4hlen:',
        ["Nur die Aussagen 1 und 3 sind richtig",
         "Nur die Aussagen 2 und 4 sind richtig",
         "Nur die Aussagen 3 und 4 sind richtig",
         "Nur die Aussagen 1, 3 und 5 sind richtig",
         "Nur die Aussagen 2, 3 und 4 sind richtig"],
        ["Hypersomnie",
         "Perseveration",
         "Gr\u00f6\u00dfenideen",
         "Psychomotorische Enthemmung",
         "Ambivalenz"])

    add_q('2009-march', 2, 'Aussagenkombination',
        'Welche der folgenden Aussagen \u00fcber die Somatisierungsst\u00f6rung trifft (treffen) zu?',
        ["Nur die Aussage 4 ist richtig",
         "Nur die Aussagen 2 und 4 sind richtig",
         "Nur die Aussagen 1, 2 und 3 sind richtig",
         "Nur die Aussagen 1, 2, 3 und 4 sind richtig",
         "Alle Aussagen sind richtig"],
        ["Die Symptome sind nur auf einen K\u00f6rperteil bezogen",
         "\u00c4ngste und Depressionen sind h\u00e4ufige Begleiterscheinungen",
         "Die psychophysische Konstitution spielt bei der Entstehung keine Rolle",
         "Medikamentenmissbrauch bis hin zur Abh\u00e4ngigkeit entsteht h\u00e4ufig",
         "Eine l\u00e4ngere Psychotherapie ist in jedem Fall die alleinige Behandlungsmethode"])

    add_q('2009-march', 3, 'Einfachauswahl',
        'Welche Aussage zur Demenz trifft zu?',
        ["Kennzeichen der vaskul\u00e4ren Demenz (arteriosklerotische Demenz) ist der schleichende Beginn bei Fehlen k\u00f6rperlicher Begleitbefunde",
         "Charakteristisch f\u00fcr die Demenz bei Alzheimer-Krankheit ist der pl\u00f6tzliche Beginn der Erkrankung mit rascher Verschlechterung",
         "Die Alzheimer-Krankheit mit fr\u00fchem Beginn (vor dem 65. Lebensjahr) zeigt gew\u00f6hnlich eine rasche Progredienz der Symptome",
         "Eine vorbestehende Intelligenzminderung (z.B. bei Down-Syndrom) schlie\u00dft die Entwicklung einer Demenz aus",
         "Die Demenz bei Creutzfeldt-Jakob-Krankheit ist durch einen besonders langsamen Verlauf gekennzeichnet"])

    add_q('2009-march', 4, 'Mehrfachauswahl',
        'Welche der folgenden Aussagen zu Drogen- und Alkoholmissbrauch treffen zu? W\u00e4hlen Sie zwei Antworten!',
        ["Regelm\u00e4\u00dfiger Amphetamin-Konsum f\u00fchrt prim\u00e4r zu k\u00f6rperlicher Abh\u00e4ngigkeit",
         "Ein Alkoholdelir tritt nur nach abruptem Alkoholentzug auf, nicht w\u00e4hrend fortgesetztem Trinken",
         "Im Rahmen eines Cannabis-Missbrauchs kann eine akute Psychose auftreten",
         "Ein Benzodiazepin-Entzug kann problemlos ambulant erfolgen, da keinerlei k\u00f6rperliche Symptomatik oder Gef\u00e4hrdung zu erwarten ist",
         "Bei einer Opiat-Intoxikation besteht die Gefahr einer Atemdepression"])

    add_q('2009-march', 5, 'Aussagenkombination',
        'Welche der folgenden Aussagen trifft (treffen) zu? Zu den phobischen St\u00f6rungen nach ICD-10 geh\u00f6rt (geh\u00f6ren):',
        ["Nur die Aussage 2 ist richtig",
         "Nur die Aussagen 1 und 3 sind richtig",
         "Nur die Aussagen 2, 4 und 5 sind richtig",
         "Nur die Aussagen 1, 2, 4 und 5 sind richtig",
         "Alle Aussagen sind richtig"],
        ["Panikst\u00f6rung",
         "Agoraphobie",
         "Herzneurose",
         "Spinnenphobie",
         "Soziale Phobie"])

    add_q('2009-march', 6, 'Einfachauswahl',
        'Bei chronischem Alkoholismus kann als Sp\u00e4tfolge das sog. Korsakow-Syndrom auftreten. Leitsymptome sind:',
        ["Optische Halluzinationen, Verwirrtheit, illusion\u00e4re Verkennung",
         "St\u00f6rungen des Kurzzeitged\u00e4chtnisses, des Zeitgef\u00fchls, fehlende St\u00f6rung des Immediatged\u00e4chtnisses",
         "Akustische Halluzinationen, Wahnwahrnehmungen",
         "Antriebsschw\u00e4che, Depressionen",
         "Eifersuchtswahn, Bewusstseinseintr\u00fcbung"])

    add_q('2009-march', 7, 'Einfachauswahl',
        'Die Einsch\u00e4tzung der Introspektionsf\u00e4higkeit des Patienten durch den Therapeuten ist f\u00fcr die Beurteilung der Therapief\u00e4higkeit des Patienten von Bedeutung. F\u00fcr welches der folgenden Psychotherapieverfahren trifft dies vor allem zu?',
        ["Gespr\u00e4chspsychotherapie nach Rogers",
         "Verhaltenstherapie",
         "Hypnosetherapie",
         "Psychoanalyse",
         "Katathymes Bilderleben"])

    add_q('2009-march', 8, 'Einfachauswahl',
        'Welche Aussage zur Schizophrenie trifft zu?',
        ["Der Krankheitsbeginn ist meist nach dem 40. Lebensjahr",
         "Die Prognose der Erkrankung ist bei schleichendem Beginn besser als bei akut einsetzenden psychotischen Symptomen",
         "Die Wahrscheinlichkeit, im Laufe des Lebens an Schizophrenie zu erkranken, liegt bei ca. 1 %",
         "M\u00e4nner erkranken in einem sp\u00e4teren Alter als Frauen",
         "Der Verwandtschaftsgrad zu einem an Schizophrenie Erkrankten spielt f\u00fcr das Erkrankungsrisiko keine Rolle"])

    add_q('2009-march', 9, 'Einfachauswahl',
        'W\u00e4hrend einer Psychotherapie \u00fcbt eine Patientin mit Bulimie alternative Strategien, die sie zur Impulskontrolle und Unterdr\u00fcckung eines Essanfalls einsetzen kann. Welcher psychotherapeutischen Richtung ist diese Vorgehensweise am ehesten zuzuordnen?',
        ["Gespr\u00e4chspsychotherapie",
         "Psychoanalyse",
         "Systemische Psychotherapie",
         "Tiefenpsychologisch fundierte Psychotherapie",
         "Verhaltenstherapie"])

    add_q('2009-march', 10, 'Mehrfachauswahl',
        'Was sind diagnostische Kriterien (nach ICD-10) f\u00fcr eine depressive Episode? W\u00e4hlen Sie zwei Antworten!',
        ["Dauer von mind. 2 Wochen",
         "Dauer von mind. 6 Monaten",
         "\u00c4ngstlich vermeidende Pers\u00f6nlichkeit",
         "Antriebsminderung",
         "Gewichtszunahme"])

    add_q('2009-march', 11, 'Aussagenkombination',
        'Welche der folgenden Aussagen zum elektiven Mutismus trifft (treffen) zu?',
        ["Nur die Aussage 3 ist richtig",
         "Nur die Aussagen 2 und 4 sind richtig",
         "Nur die Aussagen 1, 2 und 3 sind richtig",
         "Nur die Aussagen 2, 3 und 4 sind richtig",
         "Alle Aussagen sind richtig"],
        ["Die St\u00f6rung tritt fast ausschlie\u00dflich bei Jungen auf",
         "Es besteht ein normales oder nahezu normales Niveau des Sprachverst\u00e4ndnisses",
         "Es besteht eine Voraussagbarkeit f\u00fcr Situationen, in denen gesprochen und nicht gesprochen wird",
         "Andere sozial-emotionale St\u00f6rungen sind oft ebenfalls vorhanden",
         "In der Vorgeschichte findet sich meist eine Sprachentwicklungsverz\u00f6gerung"])

    add_q('2009-march', 12, 'Aussagenkombination',
        'Welche der folgenden Aussagen zu Zwangsst\u00f6rungen treffen zu?',
        ["Nur die Aussagen 1, 2 und 3 sind richtig",
         "Nur die Aussagen 1, 4 und 5 sind richtig",
         "Nur die Aussagen 2, 3 und 4 sind richtig",
         "Nur die Aussagen 2, 4 und 5 sind richtig",
         "Alle Aussagen sind richtig"],
        ["Zwangsst\u00f6rungen treten deutlich h\u00e4ufiger bei Frauen auf",
         "Der Patient empfindet die Zwangshandlungen/Zwangsgedanken als qu\u00e4lend",
         "Verhaltenstherapeutisch lassen sich Zwangsst\u00f6rungen g\u00fcnstig beeinflussen",
         "H\u00e4ufig treten Zwangsst\u00f6rungen in Verbindung mit Depressionen auf",
         "Bei der Zwangsst\u00f6rung finden sich st\u00e4ndig wechselnde Zwangshandlungen und Zwangsgedanken"])

    add_q('2009-march', 13, 'Aussagenkombination',
        'Welche der folgenden Aussagen trifft (treffen) zu? Was sind wichtige Elemente bei der kognitiv-verhaltenstherapeutischen Behandlung einer Angstst\u00f6rung, wenn identifizierbare Angstausl\u00f6ser vorhanden sind und der Patient Vermeidungsverhalten zeigt?',
        ["Nur die Aussage 1 ist richtig",
         "Nur die Aussagen 4 und 5 sind richtig",
         "Nur die Aussagen 1, 2 und 3 sind richtig",
         "Nur die Aussagen 1, 2, 4 und 5 sind richtig",
         "Alle Aussagen sind richtig"],
        ["Reizkonfrontation",
         "Vermittlung eines Erkl\u00e4rungsmodells",
         "Psychoedukation",
         "Vermeidung der Angstausl\u00f6ser",
         "Ermutigung des Patienten, sich in der Angst ausl\u00f6senden Situation durch Aktivit\u00e4ten abzulenken"])

    add_q('2009-march', 14, 'Aussagenkombination',
        'Welche der folgenden Aussagen zur Agoraphobie trifft (treffen) zu?',
        ["Nur die Aussage 3 ist richtig",
         "Nur die Aussagen 2 und 4 sind richtig",
         "Nur die Aussagen 1, 3 und 4 sind richtig",
         "Nur die Aussagen 3, 4 und 5 sind richtig",
         "Alle Aussagen sind richtig"],
        ["\u00dcberwiegend sind Frauen betroffen",
         "Depressive und zwanghafte Symptome sowie soziale Phobien k\u00f6nnen zus\u00e4tzlich vorhanden sein",
         "Aufenthalt auf gro\u00dfen Pl\u00e4tzen oder in Menschenmengen sind typisch angstausl\u00f6sende Momente",
         "Vermeidung der phobischen Situation ist ein typisches Symptom",
         "Ohne effektive Behandlung wird die Agoraphobie h\u00e4ufig chronisch"])

    add_q('2009-march', 15, 'Einfachauswahl',
        'Eine 25-j\u00e4hrige Frau bekommt pl\u00f6tzlich Angstgef\u00fchle, \u201epf\u00f6tchenartige\u201c Verkrampfungen der H\u00e4nde und atmet schnell und flach. Es handelt sich am ehesten um eine/einen',
        ["Klaustrophobie",
         "Soziophobie",
         "Hyperventilationstetanie",
         "Herzanfall",
         "Lungenembolie"])

    add_q('2009-march', 16, 'Aussagenkombination',
        'Welche der folgenden Aussagen trifft (treffen) zu? Was ist kennzeichnend f\u00fcr eine k\u00f6rperliche Abh\u00e4ngigkeit von psychotropen Substanzen?',
        ["Nur die Aussage 1 ist richtig",
         "Nur die Aussagen 1 und 2 sind richtig",
         "Nur die Aussagen 3 und 4 sind richtig",
         "Nur die Aussagen 1, 2, 3 und 5 sind richtig",
         "Alle Aussagen sind richtig"],
        ["Entzugssymptome beim Absetzen der Substanz",
         "Toleranzentwicklung",
         "Akute Bauchspeicheldr\u00fcsenentz\u00fcndung",
         "Vermehrtes Schlafbed\u00fcrfnis",
         "Konflikte im Familienkreis"])

    add_q('2009-march', 17, 'Mehrfachauswahl',
        'Was sind diagnostische Kriterien (nach ICD-10) f\u00fcr eine Anorexia nervosa? W\u00e4hlen Sie zwei Antworten!',
        ["Aktivit\u00e4tseinschr\u00e4nkung",
         "Alkoholmissbrauch",
         "Amenorrh\u00f6",
         "Vergiftungs\u00e4ngste",
         "K\u00f6rperschemast\u00f6rung"])

    add_q('2009-march', 18, 'Einfachauswahl',
        'Welche Aussage trifft zu? Der Gedankenentzug bei schizophrenen Patienten geh\u00f6rt zu welcher Gruppe von St\u00f6rungen?',
        ["Antriebsst\u00f6rungen",
         "Formale Denkst\u00f6rungen",
         "Wahnwahrnehmungen",
         "Ichst\u00f6rungen",
         "Ged\u00e4chtnisst\u00f6rungen"])

    add_q('2009-march', 19, 'Aussagenkombination',
        'Welche der folgenden Aussagen treffen zu? Ein Patient klagt \u00fcber Schlafst\u00f6rungen. Welche Ma\u00dfnahmen sollten ergriffen werden?',
        ["Nur die Aussagen 1 und 2 sind richtig",
         "Nur die Aussagen 2 und 3 sind richtig",
         "Nur die Aussagen 4 und 5 sind richtig",
         "Nur die Aussagen 1, 2, 3 und 5 sind richtig",
         "Alle Aussagen sind richtig"],
        ["F\u00fchren eines Schlaftagebuches",
         "Exploration der Schlafbedingungen",
         "Veranlassung einer k\u00f6rperlichen Untersuchung",
         "Verordnung eines Schlafmittels als Erstma\u00dfnahme",
         "Erhebung eines psychopathologischen Befundes"])

    add_q('2009-march', 20, 'Aussagenkombination',
        'Welche der folgenden Aussagen zu ADHS treffen zu?',
        ["Nur die Aussagen 1, 2 und 4 sind richtig",
         "Nur die Aussagen 2, 3 und 5 sind richtig",
         "Nur die Aussagen 3, 4 und 5 sind richtig",
         "Nur die Aussagen 1, 2, 3 und 5 sind richtig",
         "Alle Aussagen sind richtig"],
        ["Bei ADHS-Patienten besteht ein erh\u00f6htes Risiko f\u00fcr die Ausbildung einer Sucht",
         "Als Differentialdiagnose zum ADHS ist an Minderbegabung zu denken",
         "Organische Erkrankungen wie z.B. eine Schilddr\u00fcsen\u00fcberfunktion k\u00f6nnen \u00e4hnliche Symptome wie ein ADHS bewirken",
         "Wegen des erh\u00f6hten Suchtrisikos sollten bei ADHS-Patienten Stimulantien, bei denen die Gefahr einer Abh\u00e4ngigkeitsentwicklung besteht, nicht eingesetzt werden",
         "Eine maniforme Psychose kann eine \u00e4hnliche Symptomatik zeigen wie ein ADHS"])

    add_q('2009-march', 21, 'Einfachauswahl',
        'Welche Aussage zum Suizid bzw. zur Suizidgefahr bei einem depressiven Patienten trifft am ehesten zu?',
        ["Wer nicht \u00fcber Suizid redet, wird ihn nicht begehen",
         "Wer eine Suizidhandlung begeht, will sich unbedingt das Leben nehmen",
         "Eine Schwangerschaft sch\u00fctzt zuverl\u00e4ssig vor suizidalen Handlungen",
         "Versteckte Suiziddrohungen sprechen f\u00fcr ein erh\u00f6htes Suizidrisiko",
         "Fehlende suizidale Handlungen in der Verwandtschaft schlie\u00dfen ein Suizidrisiko nahezu aus"])

    add_q('2009-march', 22, 'Aussagenkombination',
        'Welche der folgenden Aussagen treffen zu? Zu den formalen Denkst\u00f6rungen z\u00e4hlen:',
        ["Nur die Aussagen 1 und 2 sind richtig",
         "Nur die Aussagen 2 und 3 sind richtig",
         "Nur die Aussagen 1, 2 und 3 sind richtig",
         "Nur die Aussagen 1, 3 und 5 sind richtig",
         "Alle Aussagen sind richtig"],
        ["Denkhemmung",
         "Zerfahrenheit",
         "Gedankenabrei\u00dfen",
         "Konfabulation",
         "Gedankenentzug"])

    add_q('2009-march', 23, 'Einfachauswahl',
        '\u00dcberpr\u00fcfen Sie folgende Beschreibungen des Begriffes der Konfabulation. Welche Aussage trifft am besten daf\u00fcr zu?',
        ["Bestehen bleiben sog. Ged\u00e4chtnisinseln im Rahmen einer umschriebenen Amnesie",
         "Z\u00e4hfl\u00fcssiges Haften an umschriebenen Erinnerungsresten aus dem Langzeitged\u00e4chtnis",
         "Hyperamnestisches (abnorm gesteigertes) Erinnerungsverm\u00f6gen",
         "Allgemeines Gef\u00fchl der Bekanntheit ohne realen Bezug",
         "Mit Phantasien ausgef\u00fcllte Erinnerungsl\u00fccken"])

    add_q('2009-march', 24, 'Aussagenkombination',
        'Welche der folgenden Aussagen in Bezug auf die medikament\u00f6se Behandlung von Patienten mit Schizophrenie treffen zu?',
        ["Nur die Aussagen 1 und 2 sind richtig",
         "Nur die Aussagen 2, 3 und 5 sind richtig",
         "Nur die Aussagen 3, 4 und 5 sind richtig",
         "Nur die Aussagen 2, 3, 4 und 5 sind richtig",
         "Alle Aussagen sind richtig"],
        ["Wegen der guten Vertr\u00e4glichkeit sind Neuroleptika problemlos in der Therapie einsetzbar",
         "Die Gabe von neuroleptischen Medikamenten kann den psychotischen Leidensdruck erheblich vermindern",
         "Die beste Rezidivprophylaxe ist eine l\u00e4ngerfristige medikament\u00f6se Therapie",
         "Die medikament\u00f6se Abschw\u00e4chung der Psychosesymptome macht die Patienten f\u00fcr aktivierende und st\u00fctzende Therapie zug\u00e4nglich",
         "Aktivierende und psychotherapeutische Ma\u00dfnahmen k\u00f6nnen das Ergebnis der medikament\u00f6sen Therapie und das subjektive Befinden der Patienten erheblich verbessern"])

    add_q('2009-march', 25, 'Mehrfachauswahl',
        'Welche der folgenden Aussagen treffen zu? W\u00e4hlen Sie zwei Antworten! Verhaltenstherapeutische Methoden und Techniken sind:',
        ["Probleml\u00f6setraining",
         "Unbedingte Wertsch\u00e4tzung des Klienten durch den Therapeuten",
         "Liegende Position des Patienten mit fehlendem Blickkontakt zum Therapeuten",
         "Selbstsicherheitstraining",
         "Aufforderung an den Patienten, frei zu assoziieren"])

    add_q('2009-march', 26, 'Aussagenkombination',
        'Welche der folgenden Aussagen treffen zu? Typische k\u00f6rperliche Symptome einer depressiven Episode sind:',
        ["Nur die Aussagen 1, 2 und 4 sind richtig",
         "Nur die Aussagen 1, 3 und 5 sind richtig",
         "Nur die Aussagen 2, 3 und 4 sind richtig",
         "Nur die Aussagen 1, 2, 3 und 4 sind richtig",
         "Alle Aussagen sind richtig"],
        ["Libidoverlust",
         "Schlafst\u00f6rungen",
         "Suizidgedanken",
         "Appetitlosigkeit",
         "Fieber"])

    add_q('2009-march', 27, 'Aussagenkombination',
        'Welche der folgenden Aussagen zur zwanghaften (anankastischen) Pers\u00f6nlichkeitsst\u00f6rung (nach ICD-10) treffen zu?',
        ["Nur die Aussagen 1 und 3 sind richtig",
         "Nur die Aussagen 2 und 4 sind richtig",
         "Nur die Aussagen 2, 3 und 5 sind richtig",
         "Nur die Aussagen 1, 2, 4 und 5 sind richtig",
         "Alle Aussagen sind richtig"],
        ["Es besteht eine Neigung, sich auf intensive, aber instabile Beziehungen einzulassen, oft mit der Folge von emotionalen Krisen",
         "Sie ist gekennzeichnet von Gef\u00fchlen von Zweifel, Perfektionismus und von \u00fcbertriebener Gewissenhaftigkeit",
         "Typisch sind wiederholte Drohungen oder Handlungen mit Selbstbesch\u00e4digung",
         "Damit verbunden sind st\u00e4ndige Kontrollen, Halsstarrigkeit, Vorsicht und Rigidit\u00e4t",
         "Aus einer zwanghaften Pers\u00f6nlichkeitsst\u00f6rung entwickelt sich h\u00e4ufig eine Zwangsst\u00f6rung"])

    add_q('2009-march', 28, 'Einfachauswahl',
        'Welche Aussage zum Delirium tremens (Alkoholentzugsdelir) trifft zu?',
        ["Zittern stellt ein seltenes Symptom der Erkrankung dar",
         "Das Delirium tremens tritt nur bei einem Blutalkoholspiegel von mehr als 3 Promille auf",
         "Unbehandelt f\u00fchrt ein Delirium tremens in unter 1 % zum Tode",
         "Krampfanf\u00e4lle k\u00f6nnen Vorboten eines nahenden Delirs sein",
         "Wahnvorstellungen schlie\u00dfen ein Delirium tremens aus"])

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
