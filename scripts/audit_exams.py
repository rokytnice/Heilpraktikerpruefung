#!/usr/bin/env python3
"""
Comprehensive quality audit of exams.json.
Checks all questions for every possible error, grouped by category.
"""

import json
import re
import sys
from collections import defaultdict

EXAMS_PATH = "app/src/main/assets/exams.json"

def load_exams():
    with open(EXAMS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def audit():
    exams = load_exams()
    findings = []  # list of (exam_id, question_id, category, detail)
    
    total_questions = 0
    total_exams = len(exams)
    
    # Category counters
    categories = defaultdict(int)
    
    def add(exam_id, qid, category, detail):
        findings.append((exam_id, qid, category, detail))
        categories[category] += 1

    # Text artifact patterns to check in options, text, and statements
    artifact_patterns = [
        (r"Korrekturrand", "Contains 'Korrekturrand'"),
        (r"Gruppe\s*A", "Contains 'Gruppe A'"),
        (r"Gruppe\s*B", "Contains 'Gruppe B'"),
        (r"Heilpraktikerüberprüfung", "Contains 'Heilpraktikerueberprüfung'"),
        (r"Institut\s+Ehlert", "Contains 'Institut Ehlert'"),
    ]
    
    # Question type markers that should not appear in option/statement text
    type_markers = [
        (r"(?<![a-zäöü])Einfachauswahl(?![a-zäöü])", "Contains type marker 'Einfachauswahl'"),
        (r"(?<![a-zäöü])Aussagenkombination(?![a-zäöü])", "Contains type marker 'Aussagenkombination'"),
        (r"(?<![a-zäöü])Mehrfachauswahl(?![a-zäöü])", "Contains type marker 'Mehrfachauswahl'"),
    ]
    
    # Control character pattern (excluding normal whitespace)
    control_char_re = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
    
    # Garbled text patterns
    garbled_patterns = [
        (re.compile(r"\d\s*[A-E]\)"), "Merged option label pattern (e.g. '0 B)')"),
        (re.compile(r"[A-E]\)\s*[A-E]\)"), "Consecutive option labels"),
    ]
    
    # Consecutive uppercase (5+ uppercase letters not typical German words)
    consec_upper_re = re.compile(r"[A-ZÄÖÜ]{5,}")
    # Known acceptable uppercase sequences
    acceptable_upper = {
        "ADHS", "AIDS", "PTBS", "SSRI", "SNRI", "MAOI", "MAOH", "NSAR",
        "PTSD", "EEG", "EKG", "MRT", "WHO", "EMDR", "GAF",
        "AMDP", "HAMD", "CGI", "PANSS", "MMPI", "WAIS", "HAWIK",
        "COMT", "GABA", "NMDA", "ACTH", "HPA", "ZNS", "MAO",
        "DGPPN", "DIMDI", "AWMF", "NICE", "SKID",
        "THADA", "RECHT", "NICHT", "DURCH", "GEGEN", "UNTER",
        "EINER", "KEINE", "DIESE", "JEDER", "IMMER", "NACH",
    }

    for exam in exams:
        exam_id = exam.get("id", "UNKNOWN")
        questions = exam.get("questions", [])
        
        if not questions:
            continue  # skip empty exams
        
        total_questions += len(questions)
        
        # ---- Category 9: Question numbering ----
        seen_ids = set()
        for q in questions:
            qid = q.get("id")
            if qid is None:
                add(exam_id, "?", "9-NUMBERING", "Question missing 'id' field")
                continue
            if qid in seen_ids:
                add(exam_id, qid, "9-NUMBERING", f"Duplicate question id {qid}")
            seen_ids.add(qid)
        
        # Check for non-sequential IDs
        sorted_ids = sorted(seen_ids)
        for i in range(len(sorted_ids) - 1):
            if sorted_ids[i+1] != sorted_ids[i] + 1:
                gap_start = sorted_ids[i] + 1
                gap_end = sorted_ids[i+1] - 1
                if gap_start == gap_end:
                    add(exam_id, gap_start, "9-NUMBERING", f"Missing question id {gap_start}")
                else:
                    add(exam_id, gap_start, "9-NUMBERING", f"Missing question ids {gap_start}-{gap_end}")
        
        for q in questions:
            qid = q.get("id", "?")
            text = q.get("text", "")
            options = q.get("options", [])
            statements = q.get("statements", [])
            correct = q.get("correctIndices", [])
            qtype = q.get("type", "")
            explanation = q.get("explanation", "")
            
            # ---- Category 2: Empty/missing fields ----
            if not text or text.strip() == "":
                add(exam_id, qid, "2-EMPTY_FIELDS", "Empty question text")
            if not options:
                add(exam_id, qid, "2-EMPTY_FIELDS", "Empty options array")
            for i, opt in enumerate(options):
                if opt is None or (isinstance(opt, str) and opt.strip() == ""):
                    add(exam_id, qid, "2-EMPTY_FIELDS", f"Empty option at index {i}")
            if correct is None:
                add(exam_id, qid, "2-EMPTY_FIELDS", "Missing correctIndices field")
            elif len(correct) == 0:
                add(exam_id, qid, "2-EMPTY_FIELDS", "Empty correctIndices array")
            if not qtype or qtype.strip() == "":
                add(exam_id, qid, "2-EMPTY_FIELDS", "Empty/missing type field")
            
            # ---- Category 10: Option count ----
            if options and len(options) != 5:
                add(exam_id, qid, "10-OPTION_COUNT", f"Has {len(options)} options instead of 5")
            
            # ---- Category 1: Option length issues ----
            for i, opt in enumerate(options):
                if isinstance(opt, str):
                    if len(opt) > 120:
                        add(exam_id, qid, "1-OPTION_LENGTH", 
                            f"Option {chr(65+i)} too long ({len(opt)} chars): '{opt[:80]}...'")
                    if 0 < len(opt.strip()) < 3:
                        add(exam_id, qid, "1-OPTION_LENGTH", 
                            f"Option {chr(65+i)} too short ({len(opt.strip())} chars): '{opt.strip()}'")
            
            # ---- Category 3: correctIndices issues ----
            if correct is not None and len(correct) > 0:
                for idx in correct:
                    if not isinstance(idx, int):
                        add(exam_id, qid, "3-CORRECT_INDICES", f"Non-integer correctIndex: {idx}")
                    elif idx < 0 or idx > 4:
                        add(exam_id, qid, "3-CORRECT_INDICES", f"correctIndex {idx} not in range 0-4")
                    if isinstance(idx, int) and options and idx >= len(options):
                        add(exam_id, qid, "3-CORRECT_INDICES", 
                            f"correctIndex {idx} out of range (only {len(options)} options)")
            
            # ---- Category 4: Type/content mismatch ----
            is_aussagen = qtype == "Aussagenkombination"
            has_statements = statements and len(statements) > 0
            
            if is_aussagen and not has_statements:
                add(exam_id, qid, "4-TYPE_MISMATCH", 
                    "Type is 'Aussagenkombination' but no statements")
            if has_statements and not is_aussagen:
                add(exam_id, qid, "4-TYPE_MISMATCH", 
                    f"Has {len(statements)} statements but type is '{qtype}'")
            if is_aussagen and has_statements and len(statements) != 5:
                add(exam_id, qid, "4-TYPE_MISMATCH", 
                    f"Aussagenkombination has {len(statements)} statements (expected 5)")
            
            # ---- Category 5: Duplicate options ----
            if options:
                seen_opts = {}
                for i, opt in enumerate(options):
                    if isinstance(opt, str):
                        normalized = opt.strip().lower()
                        if normalized in seen_opts and normalized:
                            add(exam_id, qid, "5-DUPLICATE_OPTIONS", 
                                f"Option {chr(65+i)} duplicates option {chr(65+seen_opts[normalized])}: '{opt[:60]}'")
                        seen_opts[normalized] = i
            
            # ---- Category 6: Text artifacts ----
            # Check in options
            for i, opt in enumerate(options):
                if isinstance(opt, str):
                    for pattern, desc in artifact_patterns:
                        if re.search(pattern, opt):
                            add(exam_id, qid, "6-TEXT_ARTIFACTS", 
                                f"Option {chr(65+i)}: {desc} -> '{opt[:80]}'")
                    for pattern, desc in type_markers:
                        if re.search(pattern, opt):
                            add(exam_id, qid, "6-TEXT_ARTIFACTS", 
                                f"Option {chr(65+i)}: {desc} -> '{opt[:80]}'")
                    if control_char_re.search(opt):
                        chars = control_char_re.findall(opt)
                        add(exam_id, qid, "6-TEXT_ARTIFACTS", 
                            f"Option {chr(65+i)}: Control characters {[hex(ord(c)) for c in chars]}")
            
            # Check in question text
            if isinstance(text, str):
                for pattern, desc in artifact_patterns:
                    if re.search(pattern, text):
                        add(exam_id, qid, "6-TEXT_ARTIFACTS", f"Text: {desc}")
                if control_char_re.search(text):
                    chars = control_char_re.findall(text)
                    add(exam_id, qid, "6-TEXT_ARTIFACTS", 
                        f"Text: Control characters {[hex(ord(c)) for c in chars]}")
            
            # Check in statements
            for i, stmt in enumerate(statements):
                if isinstance(stmt, str):
                    for pattern, desc in artifact_patterns:
                        if re.search(pattern, stmt):
                            add(exam_id, qid, "6-TEXT_ARTIFACTS", 
                                f"Statement {i+1}: {desc} -> '{stmt[:80]}'")
                    for pattern, desc in type_markers:
                        if re.search(pattern, stmt):
                            add(exam_id, qid, "6-TEXT_ARTIFACTS", 
                                f"Statement {i+1}: {desc} -> '{stmt[:80]}'")
                    if control_char_re.search(stmt):
                        chars = control_char_re.findall(stmt)
                        add(exam_id, qid, "6-TEXT_ARTIFACTS", 
                            f"Statement {i+1}: Control characters {[hex(ord(c)) for c in chars]}")
            
            # ---- Category 7: Garbled text ----
            all_text_fields = []
            for i, opt in enumerate(options):
                if isinstance(opt, str):
                    all_text_fields.append((f"Option {chr(65+i)}", opt))
            if isinstance(text, str):
                all_text_fields.append(("Text", text))
            for i, stmt in enumerate(statements):
                if isinstance(stmt, str):
                    all_text_fields.append((f"Statement {i+1}", stmt))
            
            for field_name, field_text in all_text_fields:
                for pattern, desc in garbled_patterns:
                    matches = pattern.findall(field_text)
                    if matches:
                        add(exam_id, qid, "7-GARBLED_TEXT", 
                            f"{field_name}: {desc} - found '{matches[0]}' in '{field_text[:80]}'")
                
                # Check for suspicious consecutive uppercase (skip known abbreviations)
                for match in consec_upper_re.finditer(field_text):
                    word = match.group()
                    if word not in acceptable_upper and len(word) >= 5:
                        # Check if it's part of a larger word context
                        start = max(0, match.start() - 5)
                        end = min(len(field_text), match.end() + 5)
                        context = field_text[start:end]
                        add(exam_id, qid, "7-GARBLED_TEXT", 
                            f"{field_name}: Suspicious consecutive uppercase '{word}' in '...{context}...'")
            
            # ---- Category 8: Statement issues ----
            for i, stmt in enumerate(statements):
                if isinstance(stmt, str):
                    stripped = stmt.strip()
                    if len(stripped) > 200:
                        add(exam_id, qid, "8-STATEMENT_ISSUES", 
                            f"Statement {i+1} too long ({len(stripped)} chars): '{stripped[:80]}...'")
                    if 0 < len(stripped) < 3:
                        add(exam_id, qid, "8-STATEMENT_ISSUES", 
                            f"Statement {i+1} too short ({len(stripped)} chars): '{stripped}'")
                    # Check for option-like content in statements
                    if re.search(r"(?i)Nur\s+die\s+Aussagen?", stripped):
                        add(exam_id, qid, "8-STATEMENT_ISSUES", 
                            f"Statement {i+1} contains option-like text 'Nur die Aussage(n)': '{stripped[:80]}'")
                    if re.search(r"(?i)Alle\s+Aussagen\s+sind\s+richtig", stripped):
                        add(exam_id, qid, "8-STATEMENT_ISSUES", 
                            f"Statement {i+1} contains option-like text 'Alle Aussagen sind richtig': '{stripped[:80]}'")
                    if re.search(r"(?i)Keine\s+der\s+Aussagen", stripped):
                        add(exam_id, qid, "8-STATEMENT_ISSUES", 
                            f"Statement {i+1} contains option-like text 'Keine der Aussagen': '{stripped[:80]}'")
                    # Check for embedded numbering that suggests merged statements
                    if re.search(r"^\d+\.\s", stripped):
                        add(exam_id, qid, "8-STATEMENT_ISSUES",
                            f"Statement {i+1} starts with numbering: '{stripped[:60]}'")
                elif stmt is None or (isinstance(stmt, str) and stmt.strip() == ""):
                    add(exam_id, qid, "8-STATEMENT_ISSUES", f"Statement {i+1} is empty")

    # ===== PRINT RESULTS =====
    print("=" * 100)
    print(f"EXAMS.JSON QUALITY AUDIT REPORT")
    print(f"Total exams: {total_exams}, Total questions audited: {total_questions}")
    print(f"Total findings: {len(findings)}")
    print("=" * 100)
    
    # Group by category
    by_category = defaultdict(list)
    for exam_id, qid, cat, detail in findings:
        by_category[cat].append((exam_id, qid, detail))
    
    for cat in sorted(by_category.keys()):
        items = by_category[cat]
        print(f"\n{'─' * 100}")
        print(f"CATEGORY: {cat} ({len(items)} findings)")
        print(f"{'─' * 100}")
        for exam_id, qid, detail in items:
            print(f"  [{exam_id}] Q{qid}: {detail}")
    
    # Summary
    print(f"\n{'=' * 100}")
    print("SUMMARY BY CATEGORY")
    print(f"{'=' * 100}")
    for cat in sorted(categories.keys()):
        print(f"  {cat}: {categories[cat]} findings")
    print(f"\n  TOTAL: {len(findings)} findings across {len(categories)} categories")
    print(f"{'=' * 100}")

if __name__ == "__main__":
    audit()
