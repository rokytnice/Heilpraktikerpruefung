import json
import os
import re
import subprocess
import sys

# Config
PDF_DIR = "fragen"
OUTPUT_JSON = "app/src/main/assets/exams_v2.json" # Temporary output
ORIGINAL_JSON = "app/src/main/assets/exams.json"

def normalize_text(text):
    """
    Cleans up text:
    - Replaces newlines with spaces
    - Collapses multiple spaces
    - Removes checkbox characters
    """
    if not text: return ""
    text = text.replace('\n', ' ')
    text = re.sub(r'\s+', ' ', text)
    text = text.replace('', '').replace('☐', '').replace('□', '')
    return text.strip()

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

def parse_solutions(lines):
    """
    Parses the solution key at the end of the PDF.
    Expected format: Grid of numbers and letters.
    """
    solutions = {}
    
    # Heuristic: look for lines with many "A B C D E" or "A C D ..."
    # And lines with numbers "1 2 3 ..."
    
    # Simple approach: Join all lines after "Lösungsschlüssel"
    # Find patterns like "1 A" (vertical) or columns.
    
    # In the 2019-March debug text, it is:
    # 1 2 3 ...
    # A B C ...
    
    # This is hard to parse generically without more complex logic.
    # Let's try to detect lines that look like a row of answers.
    
    # Regex for a row of answers: (A|B|C|D|E) repeated >= 5 times
    re_answer_row = re.compile(r'(?:[ABCDE]\s+){5,}')
    re_number_row = re.compile(r'(?:\d+\s+){5,}')
    
    # Regex for single line solution "1b" or "4 a, c"
    # Matches start of line, number, space(opt), letters(comma separated)
    re_solution_line = re.compile(r'^\s*(\d+)\s*([a-e](?:\s*,\s*[a-e])*)\s*$', re.IGNORECASE)
    
    found_numbers = []
    found_answers = []
    
    start_parsing = False
    
    for line in lines:
        if "Lösungsschlüssel" in line or "Institut Ehlert" in line or "Lösungen" in line:
            start_parsing = True
            print("DEBUG: Found start of solutions")
            
        if not start_parsing: 
            continue
            
        # Check for "1b" style
        sol_match = re_solution_line.match(line)
        if sol_match:
            q_idx = int(sol_match.group(1))
            ans_str = sol_match.group(2).lower()
            # Split by comma
            ans_chars = re.split(r'[\s,]+', ans_str)
            indices = []
            for char in ans_chars:
                if char:
                    idx = ord(char) - ord('a')
                    if 0 <= idx <= 4:
                        indices.append(idx)
            if indices:
                solutions[q_idx] = sorted(indices)
            continue

        print(f"DEBUG SOLUTION LINE: '{line.strip()}'")
        
        # Parse potential number row
        if re_number_row.search(line):
             # Extract all numbers
             nums = [int(n) for n in re.findall(r'\d+', line)]
             found_numbers.append(nums)
             
        # Parse potential answer row
        elif re_answer_row.search(line):
             # Extract all letters
             ans = re.findall(r'[ABCDE]', line)
             found_answers.append(ans)

    # Now try to align them
    # If we have a row of numbers followed by a row of answers (or vice versa, usually nums then answers)
    
    # Flat lists
    all_nums = [n for row in found_numbers for n in row]
    all_ans = [a for row in found_answers for a in row]
    
    # This is risky if layout is complex (e.g. multiple columns).
    # But usually it's Question 1..14, then Answers 1..14.
    
    # Let's verify lengths
    if len(all_ans) == len(all_nums):
        for i in range(len(all_nums)):
            q_idx = all_nums[i]
            ans_char = all_ans[i]
            # Convert char to index (A=0, B=1...)
            # Note: Sometimes multiple answers? "A, B". The regex above only finds single chars.
            # If multiple, it might be "A+B".
            
            idx = ord(ans_char) - ord('A')
            if 0 <= idx <= 4:
                solutions[q_idx] = [idx]
                
    return solutions

def parse_pdf(pdf_path, debug=False):
    """
    Parses a PDF file and returns a list of question objects.
    """
    try:
        # Use simple pdftotext first (layout mode often helps but can split lines weirdly)
        # -layout is crucial for the table-like structure of some options
        result = subprocess.run(['pdftotext', '-layout', pdf_path, '-'], stdout=subprocess.PIPE, text=True)
        content = result.stdout
    except Exception as e:
        print(f"Error extracting PDF {pdf_path}: {e}")
        return []

    lines = content.split('\n')
    questions = []
    
    current_q = None
    state = "FIND_START" 
    
    # Regex patterns
    # Start of a question: "1 Einfachauswahl", "28 Aussagenkombination"
    # Added Aussagen?kombination for 2012-October singular case
    re_q_start_combined = re.compile(r'^\s*(\d+)\s+(Einfachauswahl|Mehrfachauswahl|Aussage(?:n)?kombination)')
    re_q_type_only = re.compile(r'^\s*(Einfachauswahl|Mehrfachauswahl|Aussage(?:n)?kombination)')
    re_q_num_only = re.compile(r'^\s*(\d+)\s*$')
    
    re_statement = re.compile(r'^\s*(\d+)\.\s+(.*)') 
    # Options: "A) Text", "B) Text", "A. Text" (2025)
    re_option = re.compile(r'^\s*(?:|☐|□)?\s*([A-E])(?:\)|\.)\s+(.*)')
    re_exam_end = re.compile(r'Lösungsschlüssel|Institut Ehlert|^\s*Gesundheitsamt', re.IGNORECASE)

    potential_q_num = None

    # 1. Parse Questions
    for line in lines:
        if re_exam_end.search(line):
             # We reached end of questions.
             break 
            
        stripped = line.strip()
        if not stripped: continue
        
        # Check for Combined start "1 Einfachauswahl"
        q_match = re_q_start_combined.match(line)
        if q_match:
            if debug: print(f"DEBUG: Found Q {q_match.group(1)} Type {q_match.group(2)}")
            if current_q: questions.append(finalize_question(current_q))
            q_num = int(q_match.group(1))
            q_type = q_match.group(2)
            current_q = init_question(q_num, q_type)
            state = "IN_QUESTION_TEXT"
            potential_q_num = None
            continue
            
        # Check for Split start: Number then Type
        # Case 1: We found a number previously, check if this line is Type
        if potential_q_num:
            type_match = re_q_type_only.match(line)
            if type_match:
                if current_q: questions.append(finalize_question(current_q))
                q_type = type_match.group(1)
                current_q = init_question(potential_q_num, q_type)
                state = "IN_QUESTION_TEXT"
                potential_q_num = None
                continue
            else:
                # The previous number was NOT a question starter (maybe just a page number?)
                # But wait, if it was "2", and this line is NOT type, was "2" text?
                # In strict PDF layout, a standalone number is rare unless it's a pagination or question.
                # Let's drop the potential_q_num state if we don't match type immediately.
                # But we might need to process the *previous* line as text? 
                # Actually, usually page numbers are at bottom/top.
                # Let's ignore standalone numbers if they don't start a question.
                potential_q_num = None
        
        # Case 2: This line is just a number?
        num_match = re_q_num_only.match(line)
        if num_match:
            potential_q_num = int(num_match.group(1))
            continue # Skip processing this line as text until we verify next line
            
        # ... Rest of logic
        
        if not current_q:
            continue

        # Processing based on state/content
        
        # Check for Option start "A) ..."
        opt_match = re_option.match(line)
        if opt_match:
            if debug: print(f"DEBUG: Found Option {opt_match.group(1)}")
            opt_char = opt_match.group(1)
            opt_text = opt_match.group(2)
            current_q["current_part"] = "OPTIONS"
            current_q["current_option_key"] = opt_char
            current_q["options"][opt_char].append(opt_text)
            state = "IN_OPTIONS"
            continue
            
        # Check for Statements "1. ..."
        stmt_match = re_statement.match(line)
        if stmt_match and current_q["current_part"] != "OPTIONS":
            stmt_num = int(stmt_match.group(1))
            stmt_text = stmt_match.group(2)
            current_q["current_part"] = "STATEMENTS"
            while len(current_q["statements"]) < stmt_num:
                current_q["statements"].append([])
            current_q["statements"][stmt_num-1].append(stmt_text)
            state = "IN_STATEMENTS"
            continue
            
        if current_q["current_part"] == "TEXT":
            current_q["text_lines"].append(stripped)
        elif current_q["current_part"] == "STATEMENTS":
             if current_q["statements"]: current_q["statements"][-1].append(stripped)
        elif current_q["current_part"] == "OPTIONS":
             if current_q["current_option_key"]: current_q["options"][current_q["current_option_key"]].append(stripped)

    if current_q:
        questions.append(finalize_question(current_q))
        
    # 2. Parse Solutions
    extracted_solutions = parse_solutions(lines)
    print(f"  Extracted Solutions: {len(extracted_solutions)} found.")
    # print(extracted_solutions)
    
    # 3. Merge Solutions
    for q in questions:
        if q['id'] in extracted_solutions:
            q['correctIndices'] = extracted_solutions[q['id']]
            
    return questions

def init_question(q_num, q_type):
    return {
        "id": q_num,
        "type": q_type,
        "text_lines": [],
        "statements": [], 
        "options": {'A': [], 'B': [], 'C': [], 'D': [], 'E': []},
        "current_part": "TEXT",
        "current_option_key": None
    }

def finalize_question(q_data):
    """
    Converts raw line buffers into final strings.
    """
    final_q = {
        "id": q_data["id"],
        "type": q_data["type"],
        "text": normalize_text(" ".join(q_data["text_lines"])),
        "statements": [normalize_text(" ".join(lines)) for lines in q_data["statements"]],
        "options": [],
        "correctIndices": [], # We will fetch this separately or later
        "explanation": ""
    }
    
    # Convert options dict to list
    # Ensure order A, B, C, D, E
    for char in ['A', 'B', 'C', 'D', 'E']:
        lines = q_data["options"].get(char, [])
        if lines:
            final_q["options"].append(normalize_text(" ".join(lines)))
    
    return final_q

def main():
    if not os.path.exists(ORIGINAL_JSON):
        print("Original exams.json not found.")
        return

    with open(ORIGINAL_JSON, 'r') as f:
        exams = json.load(f)
        
    new_exams = []
    
    for exam in exams:
        exam_id = exam.get('id')
        # print(f"Reprocessing {exam_id}...")
        
        pdf_path = get_pdf_filename(exam_id)
        if not pdf_path:
            print(f"  Warning: PDF not found for {exam_id}. Keeping original questions.")
            new_exams.append(exam)
            continue
            
        new_questions = parse_pdf(pdf_path)
        
        if not new_questions:
             print(f"  Warning: No questions parsed for {exam_id}. Parser failure? Keeping original.")
             new_exams.append(exam)
             continue
             
        # Merge logic:
        # We probably want to keep 'correctIndices' from the old JSON if possible, 
        # OR verify if we can re-extract them.
        # The user's main complaint was missing questions and bad text. 
        # Verification of answers is another step, but we can try to map old answers to new questions by ID.
        
        # Mapping old correctIndices
        old_questions_map = {q['id']: q.get('correctIndices', []) for q in exam.get('questions', [])}
        
        for nq in new_questions:
            nq["correctIndices"] = old_questions_map.get(nq['id'], [])
            
        # Update exam object
        exam['questions'] = new_questions
        new_exams.append(exam)
        print(f"  -> Extracted {len(new_questions)} questions.")

    with open(OUTPUT_JSON, 'w') as f:
        json.dump(new_exams, f, indent=2, ensure_ascii=False)
        
    print(f"Saved new data to {OUTPUT_JSON}")

if __name__ == "__main__":
    main()
