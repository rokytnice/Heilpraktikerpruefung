#!/usr/bin/env python3
"""
Fix exams.json - correct answer indices, fix structural issues.
"""
import json
import copy
import sys

JSON_PATH = "app/src/main/assets/exams.json"

def letter_to_index(letter):
    """Convert answer letter to 0-based index: A=0, B=1, C=2, D=3, E=4"""
    return ord(letter.upper()) - ord('A')

def parse_answer_key(answer_str):
    """Parse answer string like 'A' or 'A+D' or 'B+C+E' into sorted index list"""
    letters = answer_str.strip().split('+')
    return sorted([letter_to_index(l) for l in letters])

def build_answer_keys():
    """Build dict of exam_id -> {question_id: [correctIndices]}"""
    raw_keys = {
        # === MARCH EXAMS ===

        # 2003-march (Gruppe A) - text-based extraction
        "2003-march": {
            1: "A", 2: "B", 3: "D", 4: "C", 5: "C", 6: "E", 7: "E",
            8: "D", 9: "C", 10: "E", 11: "D", 12: "B", 13: "B", 14: "E",
            15: "E", 16: "C", 17: "E", 18: "D", 19: "B", 20: "D",
            21: "C", 22: "B", 23: "D", 24: "E", 25: "A+D+E", 26: "A+B+C",
            27: "C", 28: "B"
        },
        # 2004-march (Gruppe A) - text-based extraction
        "2004-march": {
            1: "E", 2: "D", 3: "D", 4: "E", 5: "B", 6: "E", 7: "E",
            8: "A", 9: "B", 10: "C", 11: "B", 12: "B", 13: "D", 14: "A+B+C+E",
            15: "B+C+D+E", 16: "C", 17: "D", 18: "D", 19: "E", 20: "E",
            21: "B+D", 22: "D", 23: "C", 24: "D", 25: "C", 26: "C",
            27: "C", 28: "B"
        },
        # 2006-march (Grid) - bold/black grid extraction
        "2006-march": {
            1: "B", 2: "C", 3: "D", 4: "A", 5: "E", 6: "A", 7: "B",
            8: "A", 9: "A", 10: "D", 11: "E", 12: "A+E", 13: "C", 14: "D",
            15: "C", 16: "E", 17: "E", 18: "A", 19: "C", 20: "A",
            21: "B", 22: "B", 23: "E", 24: "C", 25: "A", 26: "C",
            27: "A", 28: "E"
        },
        # 2007-march (Grid) - bold/black grid extraction
        "2007-march": {
            1: "C", 2: "A", 3: "E", 4: "B", 5: "A", 6: "D", 7: "D",
            8: "D", 9: "A+D", 10: "B", 11: "B+E", 12: "D", 13: "C", 14: "B+E",
            15: "B", 16: "C", 17: "A", 18: "B", 19: "D+E", 20: "C",
            21: "B+D", 22: "B", 23: "D", 24: "D", 25: "B+D", 26: "B",
            27: "A+E", 28: "E"
        },
        # 2008-march (Gruppe A) - text-based extraction
        "2008-march": {
            1: "E", 2: "C", 3: "A", 4: "D", 5: "E", 6: "A+C", 7: "B+C",
            8: "B", 9: "B", 10: "E", 11: "A+D", 12: "D", 13: "B", 14: "B",
            15: "C+E", 16: "C", 17: "A", 18: "C", 19: "B", 20: "B",
            21: "D", 22: "C", 23: "E", 24: "B+C", 25: "B", 26: "D",
            27: "C+D", 28: "D"
        },
        # 2009-march (Gruppe A) - text-based extraction
        "2009-march": {
            1: "C", 2: "B", 3: "C", 4: "C+E", 5: "C", 6: "B", 7: "D",
            8: "C", 9: "E", 10: "A+D", 11: "D", 12: "C", 13: "C", 14: "E",
            15: "C", 16: "B", 17: "C+E", 18: "D", 19: "D", 20: "D",
            21: "D", 22: "C", 23: "E", 24: "D", 25: "A+D", 26: "A",
            27: "B", 28: "D"
        },
        # 2011-march (Gruppe B) - bold/black grid extraction
        "2011-march": {
            1: "C", 2: "E", 3: "B", 4: "C", 5: "C+D", 6: "C", 7: "C",
            8: "D", 9: "D", 10: "B+D", 11: "D+E", 12: "D", 13: "A+C", 14: "D",
            15: "C", 16: "C", 17: "D", 18: "C", 19: "B+C", 20: "C+E",
            21: "C", 22: "D", 23: "A+D", 24: "C", 25: "C", 26: "A",
            27: "D", 28: "D"
        },
        # 2019-march (Gruppe A) - programmatic grid extraction
        "2019-march": {
            1: "D", 2: "C", 3: "C", 4: "E", 5: "B+E", 6: "E", 7: "B",
            8: "E", 9: "C", 10: "A+D", 11: "C", 12: "D", 13: "A", 14: "B+E",
            15: "E", 16: "B", 17: "A", 18: "E", 19: "A+C", 20: "D",
            21: "C", 22: "B+D", 23: "C", 24: "B+D", 25: "C", 26: "A+E",
            27: "C", 28: "B"
        },
        # 2022-march (Gruppe B) - from agent analysis
        "2022-march": {
            1: "B", 2: "C", 3: "A+E", 4: "B", 5: "A+D", 6: "E", 7: "A+B",
            8: "D", 9: "C", 10: "E", 11: "A", 12: "A+C", 13: "D", 14: "B",
            15: "B+E", 16: "D", 17: "D", 18: "E", 19: "C+E", 20: "A",
            21: "C", 22: "A+C", 23: "B+C", 24: "D", 25: "E", 26: "D",
            27: "D", 28: "C+E"
        },
        # 2023-march (Gruppe A) - verified via programmatic grid extraction
        "2023-march": {
            1: "D", 2: "C", 3: "C", 4: "A", 5: "D", 6: "C", 7: "A",
            8: "D", 9: "E", 10: "A+D", 11: "B", 12: "C+E", 13: "C", 14: "C",
            15: "D", 16: "A+C", 17: "B", 18: "B", 19: "E", 20: "D",
            21: "D", 22: "D", 23: "E", 24: "D", 25: "E", 26: "E",
            27: "C", 28: "D"
        },
        # 2024-march (Gruppe A)
        "2024-march": {
            1: "C", 2: "A", 3: "D+E", 4: "C", 5: "A+B", 6: "E", 7: "A",
            8: "D", 9: "D", 10: "D", 11: "C+D", 12: "E", 13: "A", 14: "D",
            15: "B", 16: "E", 17: "C", 18: "E", 19: "D", 20: "D",
            21: "C", 22: "B", 23: "B", 24: "B", 25: "A", 26: "B+E",
            27: "B", 28: "C"
        },
        # 2025-march (Gruppe A) - verified via programmatic grid extraction
        "2025-march": {
            1: "A+B", 2: "A", 3: "C", 4: "C+E", 5: "B", 6: "B", 7: "D",
            8: "D", 9: "C", 10: "D+E", 11: "D", 12: "B+C", 13: "B+C", 14: "D",
            15: "C", 16: "A+C", 17: "A", 18: "A+E", 19: "A", 20: "B+E",
            21: "C+E", 22: "C", 23: "A+D", 24: "D", 25: "A+E", 26: "B+C",
            27: "D+E", 28: "B"
        },
        # 2010-march (Gruppe B)
        "2010-march": {
            1: "D", 2: "C", 3: "A", 4: "E", 5: "C", 6: "D", 7: "A",
            8: "B", 9: "D", 10: "C", 11: "A+D", 12: "B+E", 13: "B+D", 14: "C",
            15: "A+D", 16: "E", 17: "E", 18: "D", 19: "A", 20: "B+D",
            21: "C+D", 22: "D", 23: "B", 24: "E", 25: "D", 26: "B",
            27: "A+E", 28: "C"
        },
        # 2012-march (Gruppe A)
        "2012-march": {
            1: "B", 2: "A+B", 3: "D", 4: "B+E", 5: "B", 6: "C", 7: "E",
            8: "A+D", 9: "D+E", 10: "B", 11: "B+C", 12: "D", 13: "D+E", 14: "C",
            15: "B", 16: "D", 17: "D", 18: "A+C", 19: "A+D", 20: "A",
            21: "D", 22: "A+C", 23: "A", 24: "A+B", 25: "D", 26: "B",
            27: "A", 28: "B+E"
        },
        # 2013-march (Gruppe B)
        "2013-march": {
            1: "A+C", 2: "D", 3: "E", 4: "D", 5: "A", 6: "A+E", 7: "C+E",
            8: "D", 9: "E", 10: "C", 11: "D", 12: "B+C", 13: "B+E", 14: "D",
            15: "B+E", 16: "E", 17: "D", 18: "D", 19: "C", 20: "B+C",
            21: "D", 22: "C", 23: "C", 24: "C", 25: "A+E", 26: "D",
            27: "C", 28: "B"
        },
        # 2014-march (Gruppe B)
        "2014-march": {
            1: "A+D", 2: "D", 3: "D+E", 4: "B", 5: "C+D", 6: "E", 7: "D+E",
            8: "D", 9: "D", 10: "D", 11: "C+D", 12: "E", 13: "B+C", 14: "C",
            15: "A+B", 16: "A+D", 17: "A", 18: "D", 19: "A+D", 20: "E",
            21: "E", 22: "D+E", 23: "E", 24: "C", 25: "D", 26: "A",
            27: "B", 28: "A"
        },
        # 2015-march (Gruppe A)
        "2015-march": {
            1: "C", 2: "B+E", 3: "E", 4: "B", 5: "E", 6: "B", 7: "A+B",
            8: "A+E", 9: "C", 10: "B+D", 11: "C+D", 12: "A", 13: "A+C", 14: "A",
            15: "D", 16: "E", 17: "E", 18: "A", 19: "A+D", 20: "A+B",
            21: "B+E", 22: "C", 23: "C", 24: "C+D", 25: "D", 26: "B",
            27: "E", 28: "C"
        },
        # 2016-march (Gruppe B)
        "2016-march": {
            1: "A+C", 2: "D", 3: "C", 4: "D", 5: "A", 6: "A+C", 7: "C+E",
            8: "B+D", 9: "B+E", 10: "A+D", 11: "B+D", 12: "C+E", 13: "C", 14: "B+C",
            15: "B", 16: "D", 17: "B+D", 18: "A", 19: "E", 20: "A+E",
            21: "D", 22: "D", 23: "C", 24: "C", 25: "B", 26: "C+D",
            27: "A+B", 28: "B+C"
        },
        # 2017-march (Gruppe B)
        "2017-march": {
            1: "B", 2: "A+D", 3: "B", 4: "C+D", 5: "A", 6: "B", 7: "C",
            8: "A", 9: "D", 10: "B", 11: "D", 12: "B+E", 13: "D", 14: "D",
            15: "B", 16: "E", 17: "A", 18: "C+D", 19: "B", 20: "E",
            21: "D", 22: "D", 23: "C", 24: "C", 25: "B", 26: "E",
            27: "A+B", 28: "B"
        },

        # === OCTOBER EXAMS ===

        # 2002-october
        "2002-october": {
            1: "B", 2: "E", 3: "A", 4: "B", 5: "C", 6: "A", 7: "D",
            8: "E", 9: "E", 10: "D", 11: "D", 12: "D", 13: "D", 14: "E",
            15: "D", 16: "C", 17: "B", 18: "D", 19: "C", 20: "B",
            21: "C", 22: "B", 23: "D", 24: "A", 25: "A", 26: "A",
            27: "D", 28: "D"
        },
        # 2003-october (old format - Mehrfachauswahlaufgabe has multiple correct)
        "2003-october": {
            1: "B", 2: "B", 3: "D", 4: "D", 5: "C", 6: "B+C+E", 7: "D",
            8: "B+C+E", 9: "A+B+D", 11: "C", 12: "B", 13: "C", 14: "D",
            15: "A", 16: "B+D+E", 17: "D", 18: "B",
            20: "A+C+E", 21: "A+B+E", 22: "C", 23: "A+D+E", 24: "A",
            27: "B", 28: "A+B+E"
        },
        # 2005-october
        "2005-october": {
            1: "C", 2: "D", 3: "C", 4: "C", 5: "C", 6: "C", 7: "D",
            8: "E", 9: "B+E", 10: "C", 11: "D", 12: "B", 13: "C", 14: "D",
            15: "D", 16: "C", 17: "A", 18: "A", 19: "D", 20: "D",
            21: "B", 22: "A", 23: "C", 24: "C", 25: "C", 26: "E",
            27: "A", 28: "C"
        },
        # 2006-october (Grid) - bold/black grid extraction
        "2006-october": {
            1: "A", 2: "C", 3: "E", 4: "B", 5: "D", 6: "C", 7: "A",
            8: "B", 9: "A", 10: "B", 11: "A", 12: "D", 13: "C", 14: "C",
            15: "B", 16: "C", 17: "C", 18: "B", 19: "D", 20: "B",
            21: "C", 22: "C", 23: "D", 24: "A", 25: "B+D", 26: "E",
            27: "B", 28: "C"
        },
        # 2008-october (Gruppe A) - color grid extraction
        "2008-october": {
            1: "D+E", 2: "C", 3: "E", 4: "E", 5: "B+C", 6: "C+D", 7: "D",
            8: "E", 9: "C", 10: "E", 11: "A", 12: "C", 13: "D", 14: "C",
            15: "D", 16: "B", 17: "D", 18: "E", 19: "D", 20: "E",
            21: "D", 22: "B", 23: "A+D", 24: "B", 25: "C", 26: "C",
            27: "D", 28: "E"
        },
        # 2009-october (Gruppe A) - text-based extraction
        "2009-october": {
            1: "D", 2: "A", 3: "A+C", 4: "B+C", 5: "D", 6: "D+E", 7: "A",
            8: "E", 9: "A+C", 10: "E", 11: "B+D", 12: "E", 13: "A+C", 14: "D",
            15: "B", 16: "B", 17: "A", 18: "C", 19: "C", 20: "D+E",
            21: "A", 22: "A+D", 23: "D", 24: "B", 25: "D+E", 26: "E",
            27: "B", 28: "B"
        },
        # 2010-october (Gruppe B - matches JSON questions)
        "2010-october": {
            1: "A+D", 2: "D", 3: "D", 4: "A", 5: "B", 6: "E", 7: "D+E",
            8: "A", 9: "B+D", 10: "D+E", 11: "B", 12: "D", 13: "A", 14: "B+D",
            15: "E", 16: "D", 17: "D+E", 18: "D", 19: "B", 20: "D",
            21: "B+E", 22: "B", 23: "A+D", 24: "B+D", 25: "D", 26: "E",
            27: "D+E", 28: "C"
        },
        # 2011-october (Gruppe B) - text-based extraction
        "2011-october": {
            1: "C", 2: "D+E", 3: "B", 4: "B", 5: "B", 6: "A+C", 7: "B",
            8: "A", 9: "D", 10: "A+B", 11: "B", 12: "E", 13: "E", 14: "A",
            15: "C", 16: "B+C", 17: "E", 18: "A+E", 19: "E", 20: "B+D",
            21: "C", 22: "C+D", 23: "C+D", 24: "C", 25: "B", 26: "A+E",
            27: "D", 28: "B"
        },
        # 2012-october (Gruppe B) - text-based extraction
        "2012-october": {
            1: "B", 2: "B", 3: "E", 4: "A+C", 5: "D+E", 6: "B", 7: "D",
            8: "D", 9: "C+E", 10: "B", 11: "C+E", 12: "A", 13: "E", 14: "C",
            15: "D", 16: "A", 17: "C", 18: "D", 19: "C", 20: "C",
            21: "C", 22: "D", 23: "C", 24: "B+E", 25: "C", 26: "D",
            27: "B", 28: "A+D"
        },
        # 2013-october (Gruppe A) - bold/black grid extraction
        "2013-october": {
            1: "B", 2: "D", 3: "E", 4: "C", 5: "C+D", 6: "D", 7: "E",
            8: "D", 9: "A+C", 10: "D", 11: "B+C", 12: "D", 13: "A+D", 14: "C",
            15: "B", 16: "C", 17: "B+E", 18: "D", 19: "C+D", 20: "C",
            21: "B", 22: "E", 23: "D", 24: "D", 25: "D", 26: "B",
            27: "C+E", 28: "D+E"
        },
        # 2016-october (Gruppe B) - color grid extraction
        "2016-october": {
            1: "C", 2: "D", 3: "A+C", 4: "C", 5: "D", 6: "C", 7: "D",
            8: "B+D", 9: "A+E", 10: "B+C", 11: "B", 12: "D", 13: "A+E", 14: "E",
            15: "C", 16: "C+D", 17: "D", 18: "C", 19: "C", 20: "D",
            21: "C", 22: "C+E", 23: "A+D", 24: "C+E", 25: "D", 26: "C+E",
            27: "A+D", 28: "B+C"
        },
        # 2017-october (Gruppe B) - color grid extraction
        "2017-october": {
            1: "E", 2: "C", 3: "D", 4: "D", 5: "D", 6: "D", 7: "C+E",
            8: "D", 9: "B", 10: "B", 11: "B+E", 12: "B", 13: "C", 14: "D",
            15: "A+E", 16: "D", 17: "C", 18: "D", 19: "C", 20: "B+D",
            21: "B", 22: "A+C", 23: "D", 24: "B", 25: "A+E", 26: "A+E",
            27: "A+D", 28: "A"
        },
        # 2020-october (Gruppe A)
        "2020-october": {
            1: "E", 2: "B+E", 3: "B+C", 4: "D", 5: "A+C", 6: "A+D", 7: "B",
            8: "A", 9: "E", 10: "E", 11: "D", 12: "B", 13: "E", 14: "E",
            15: "D", 16: "A+B", 17: "C", 18: "D", 19: "B+E", 20: "A+C",
            21: "D", 22: "A+D", 23: "D+E", 24: "C", 25: "A+B", 26: "B+D",
            27: "A", 28: "C+E"
        },
        # 2022-october (Gruppe B - matches JSON questions)
        "2022-october": {
            1: "D", 2: "B+E", 3: "B+C", 4: "B", 5: "A+E", 6: "B", 7: "A",
            8: "C+E", 9: "C+D", 10: "D", 11: "A", 12: "C", 13: "A+D", 14: "A+B",
            15: "C+E", 16: "C", 17: "A+D", 18: "B", 19: "B", 20: "D+E",
            21: "B+C", 22: "E", 23: "A+D", 24: "B+E", 25: "B", 26: "D",
            27: "D", 28: "A"
        },
        # 2023-october (Gruppe B - matches JSON questions)
        "2023-october": {
            1: "A", 2: "D", 3: "C", 4: "E", 5: "D", 6: "C+E", 7: "D",
            8: "C", 9: "A+C", 10: "C", 11: "D", 12: "B", 13: "D", 14: "E",
            15: "C", 16: "D", 17: "D", 18: "A", 19: "A", 20: "C",
            21: "E", 22: "D", 23: "C+E", 24: "B+C", 25: "A+E", 26: "B+D",
            27: "B", 28: "D"
        },
        # 2024-october (Gruppe A - matches JSON questions)
        "2024-october": {
            1: "D", 2: "E", 3: "A", 4: "B", 5: "A", 6: "B", 7: "B+C",
            8: "D", 9: "D", 10: "B", 11: "C+D", 12: "E", 13: "B", 14: "B+D",
            15: "D", 16: "C", 17: "A+D", 18: "E", 19: "C", 20: "A+C",
            21: "E", 22: "E", 23: "A+E", 24: "A", 25: "B", 26: "B+C",
            27: "D", 28: "A+D"
        },
        # 2025-october (Gruppe A)
        "2025-october": {
            1: "D", 2: "E", 3: "C+D", 4: "C", 5: "B", 6: "A", 7: "D",
            8: "A+E", 9: "C", 10: "E", 11: "B", 12: "B+E", 13: "E", 14: "A+C",
            15: "B", 16: "C", 17: "B+E", 18: "B", 19: "D", 20: "A",
            21: "A", 22: "B+C", 23: "A+E", 24: "C", 25: "C+E", 26: "B+E",
            27: "C", 28: "D"
        },
    }

    # Convert to index format
    answer_keys = {}
    for exam_id, questions in raw_keys.items():
        answer_keys[exam_id] = {}
        for qid, answer in questions.items():
            answer_keys[exam_id][qid] = parse_answer_key(answer)

    return answer_keys

def fix_correct_indices(exams, answer_keys):
    """Fix correctIndices for all exams where we have answer keys"""
    changes = 0
    for exam in exams:
        eid = exam['id']
        if eid not in answer_keys:
            continue

        key = answer_keys[eid]
        for q in exam['questions']:
            qid = q['id']
            if qid not in key:
                continue

            expected = key[qid]
            current = q.get('correctIndices', [])

            if current != expected:
                q['correctIndices'] = expected
                changes += 1

    return changes

def fix_duplicate_ids(exams):
    """Remove duplicate 2014-october entries"""
    seen = set()
    to_remove = []
    for i, exam in enumerate(exams):
        eid = exam['id']
        if eid in seen:
            # Keep the one with more questions
            # Find the first one
            for j, e2 in enumerate(exams):
                if e2['id'] == eid and j != i:
                    if len(e2['questions']) >= len(exam['questions']):
                        to_remove.append(i)
                    else:
                        to_remove.append(j)
                    break
        seen.add(eid)

    for idx in sorted(to_remove, reverse=True):
        print(f"  Removing duplicate exam at index {idx}: {exams[idx]['id']}")
        exams.pop(idx)

    return len(to_remove)

def main():
    # Read JSON
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        exams = json.load(f)

    print(f"Loaded {len(exams)} exams")

    # Build answer keys
    answer_keys = build_answer_keys()
    print(f"Have answer keys for {len(answer_keys)} exams")

    # Fix correctIndices
    print("\n--- Fixing correctIndices ---")
    ci_changes = fix_correct_indices(exams, answer_keys)
    print(f"Fixed {ci_changes} correctIndices")

    # Fix duplicate IDs
    print("\n--- Fixing duplicate IDs ---")
    dup_changes = fix_duplicate_ids(exams)
    print(f"Removed {dup_changes} duplicate(s)")

    # Verify
    print("\n--- Verification ---")
    for exam in exams:
        eid = exam['id']
        qs = exam['questions']
        num_q = len(qs)
        empty_correct = sum(1 for q in qs if not q.get('correctIndices'))
        empty_opts = sum(1 for q in qs if not q.get('options'))

        if eid in answer_keys:
            status = "KEYS_APPLIED"
            missing = num_q - len(answer_keys[eid])
            if missing > 0:
                status += f" ({missing} questions without key)"
        elif num_q == 0:
            status = "EMPTY"
        else:
            status = "NO_KEY_AVAILABLE"

        if empty_correct > 0 or empty_opts > 0:
            status += f" [empty_correct={empty_correct}, empty_opts={empty_opts}]"

        print(f"  {eid}: {num_q}q - {status}")

    # Write output
    with open(JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(exams, f, ensure_ascii=False, indent=2)

    print(f"\nWrote corrected JSON to {JSON_PATH}")
    print(f"Total changes: {ci_changes} correctIndices + {dup_changes} duplicates removed")

if __name__ == "__main__":
    main()
