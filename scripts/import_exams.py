import os
import re
import json
import subprocess
from bs4 import BeautifulSoup

FRAGEN_DIR = "/home/aroc/projects/Heilpraktikerpruefung/fragen"
OUTPUT_JSON = "/home/aroc/projects/Heilpraktikerpruefung/app/src/main/assets/exams.json"

def get_exams_list():
    files = [f for f in os.listdir(FRAGEN_DIR) if f.endswith(".pdf")]
    return sorted(files)

def parse_questions_from_html(main_html):
    with open(main_html, 'r') as f:
        soup = BeautifulSoup(f, 'html.parser')
    
    questions = []
    # Identify question blocks. Usually start with a number followed by a type.
    # Ex: "1 Einfachauswahl", "2 Aussagenkombination"
    ps = soup.find_all('p')
    current_q = None
    
    for i, p in enumerate(ps):
        text = p.get_text().strip()
        # Regex for question start: "1 Einfachauswahl" or similar
        match = re.search(r'^(\d+)\s+(Einfachauswahl|Aussagenkombination|Mehrfachauswahl)', text)
        if match:
            if current_q:
                questions.append(current_q)
            current_q = {
                "id": int(match.group(1)),
                "type": match.group(2).strip(),
                "text": "",
                "options": [],
                "statements": [], # For Aussagenkombination
                "correctIndices": [],
                "explanation": ""
            }
            continue
            
        if current_q:
            # Check for statements (1. ..., 2. ...)
            statement_match = re.match(r'^(\d+)\.\s+(.*)', text)
            if statement_match and current_q["type"] == "Aussagenkombination":
                current_q["statements"].append(statement_match.group(2).strip())
                continue
                
            # Check for options (A) ..., B) ...)
            option_match = re.match(r'^([A-E])\)\s*(.*)', text)
            if option_match:
                current_q["options"].append(f"{option_match.group(1)}) {option_match.group(2).strip()}")
                continue
            
            # If it's not a statement or option, it's part of the question text
            if text and not text.startswith("Wählen Sie"):
                if current_q["options"]: # Already in options, maybe multi-line?
                     # Handle multi-line options if needed
                     pass
                else:
                     current_q["text"] += " " + text
                     current_q["text"] = current_q["text"].strip()
                     
    if current_q:
        questions.append(current_q)
    return questions

def parse_solutions_from_html(main_html):
    with open(main_html, 'r') as f:
        soup = BeautifulSoup(f, 'html.parser')
    
    ps = soup.find_all('p')
    
    # 1. Collect all elements in the solution area
    grid_elements = []
    found_key = False
    for p in ps:
        text = p.get_text().strip()
        if "Lösungsschlüssel" in text or "Lösungsschluessel" in text:
            found_key = True
        if not found_key: continue
        
        style = p.get('style', '')
        left_match = re.search(r'left:(\d+)px', style)
        top_match = re.search(r'top:(\d+)px', style)
        if not left_match or not top_match: continue
        left = int(left_match.group(1))
        top = int(top_match.group(1))
        
        grid_elements.append({
            "text": text,
            "left": left,
            "top": top,
            "class": p.get('class', [None])[0]
        })

    if not grid_elements: return {}

    # 2. Group into rows by 'top'
    rows = []
    for el in sorted(grid_elements, key=lambda x: x["top"]):
        if not rows or abs(el["top"] - rows[-1][0]["top"]) > 10:
            rows.append([el])
        else:
            rows[-1].append(el)
            
    for row in rows:
        row.sort(key=lambda x: x["left"])

    # 3. Identify rows and detect correct class globally
    letter_rows = []
    
    for row in rows:
        row_text = " ".join([el["text"] for el in row])
        if any(re.match(r'^[A-E](\s+[A-E])*$', el["text"].strip()) for el in row) or "A B C D E" in row_text.replace(" ", ""):
            letter_rows.append(row)

    # 4. Dynamically detect 'correct' class
    class_counts = {}
    for row in letter_rows:
        for el in row:
            letters = [c for c in el["text"] if c in "ABCDE"]
            if letters:
                cls = el["class"]
                class_counts[cls] = class_counts.get(cls, 0) + len(letters)
    
    # Filter classes with too few occurrences (noise)
    # A generic exam has ~60 questions. Correct class should have > 10 hits at least.
    valid_classes = [c for c, count in class_counts.items() if count > 10]
    
    if not valid_classes: 
        if class_counts:
             valid_classes = list(class_counts.keys())
        else:
             return {}

    # Sort valid classes by count
    sorted_valid = sorted(valid_classes, key=lambda x: class_counts[x])
    correct_class = sorted_valid[0] # Pick the valid class with the lowest count

    # 5. Extract solutions (Stateful Pass)
    solutions = {}
    current_q_centers = {}
    
    for row in rows:
        row_text = " ".join([el["text"] for el in row])
        nums = re.findall(r'\d+', row_text)
        
        # Check if Header Row (heuristic: at least 5 numbers)
        if len(nums) >= 5: 
            # Reset current centers for new block to avoid mixing with previous block
            current_q_centers = {} 
            
            for el in row:
                parts = el["text"].split()
                current_left = el["left"]
                for p in parts:
                    if p.isdigit():
                         q_id = int(p)
                         current_q_centers[current_left + 10] = q_id
                         current_left += 48

        # Check if Letter Row (and extract if we have active centers)
        elif any(re.match(r'^[A-E](\s+[A-E])*$', el["text"].strip()) for el in row) or "A B C D E" in row_text.replace(" ", ""):
            if not current_q_centers: continue # No header seen yet?
            
            for el in row:
                if el["class"] == correct_class:
                    parts = el["text"].split()
                    txt = el["text"].strip()
                    clean_txt = "".join([c for c in txt if c in "ABCDE"])
                    
                    if not clean_txt: continue
                    
                    x = el["left"] + 10 # Center bias
                    
                    best_q = None
                    min_dist = 20
                    for cx, q_id in current_q_centers.items():
                        if abs(cx - x) < min_dist:
                            min_dist = abs(cx - x)
                            best_q = q_id
                    
                    if best_q:
                        print(f"DEBUG: MATCH Q{best_q} -> {clean_txt} at x={x} (center={cx}, dist={min_dist})")
                        if best_q not in solutions: solutions[best_q] = []
                        for char in clean_txt:
                            if char not in solutions[best_q]:
                                solutions[best_q].append(char)
                                
    return solutions

def parse_text_exam(text):
    # Split text into questions and solution key
    parts = re.split(r'Lösungsschlüssel', text, flags=re.I)
    q_text = parts[0]
    s_text = parts[1] if len(parts) > 1 else ""
    
    # 1. Parse questions
    questions = []
    # Pattern: "1 Einfachauswahl" or "1 Aussagenkombination"
    q_blocks = re.split(r'\n(\d+)\s+(Einfachauswahl|Aussagenkombination|Mehrfachauswahl)', q_text)
    # The split results in [preamble, id1, type1, content1, id2, type2, content2, ...]
    for i in range(1, len(q_blocks), 3):
        q_id = int(q_blocks[i])
        q_type = q_blocks[i+1]
        content = q_blocks[i+2]
        
        # Split content into text, statements, and options
        # Statements are "1. ... 2. ..."
        # Options are "A) ... B) ..."
        statements = re.findall(r'\n(\d+)\.\s+(.*?)(?=\n\d+\.|\n[A-E]\)|$)', content, re.S)
        options = re.findall(r'\n([A-E])\)\s+(.*?)(?=\n[A-E]\)|$)', content, re.S)
        
        # Remove statements/options from content to get the main question text
        cleaned_text = re.sub(r'(\d+\.\s+.*?)(?=\n\d+\.|\n[A-E]\)|$)', '', content, flags=re.S)
        cleaned_text = re.sub(r'([A-E]\)\s+.*?)(?=\n[A-E]\)|$)', '', cleaned_text, flags=re.S)
        cleaned_text = cleaned_text.strip()
        
        questions.append({
            "id": q_id,
            "type": q_type,
            "text": cleaned_text,
            "statements": [s[1].strip() for s in statements],
            "options": [f"{o[0]}) {o[1].strip()}" for o in options],
            "correctIndices": [],
            "explanation": ""
        })
        
    # 2. Parse solutions
    sol_matches = re.findall(r'(\d+)\s+([A-E](?:,\s*[A-E])*)', s_text)
    solutions = {int(m[0]): [l.strip() for l in m[1].split(',')] for m in sol_matches}
    
    # Apply solutions
    for q in questions:
        if q["id"] in solutions:
            q["correctIndices"] = [ord(l) - ord('A') for l in solutions[q["id"]]]
            
    return questions

def parse_pdf_old(pdf_path):
    result = subprocess.run(["pdftotext", "-layout", pdf_path, "-"], capture_output=True, text=True)
    if result.returncode != 0:
        return []
    return parse_text_exam(result.stdout)

def parse_pdf_modern(pdf_path):
    temp_dir = "temp_html"
    os.makedirs(temp_dir, exist_ok=True)
    base_name = os.path.basename(pdf_path).replace(".pdf", "")
    html_file = os.path.join(temp_dir, f"{base_name}.html")
    
    try:
        subprocess.run(["pdftohtml", "-s", "-c", pdf_path, html_file], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        main_html = html_file.replace(".html", "-html.html")
        if not os.path.exists(main_html):
            # Fallback to text for modern PDFs if HTML fails
            return parse_pdf_old(pdf_path)
            
        questions = parse_questions_from_html(main_html)
        solutions = parse_solutions_from_html(main_html)
        
        # Merge solutions into questions
        for q in questions:
             q_id = q["id"]
             if q_id in solutions:
                 correct_letters = solutions[q_id]
                 q["correctIndices"] = [ord(l) - ord('A') for l in correct_letters]
             
        return questions
    finally:
        subprocess.run(["rm", "-rf", temp_dir])

def run_import():
    all_exams = []
    pdf_files = get_exams_list()
    
    for pdf in pdf_files:
        if "Oktober_2024_mit_Loesungen_A_B" not in pdf: continue
        print(f"Processing {pdf}...")
        match = re.search(r'(Maerz|Oktober).*?(\d{4})', pdf, re.I)
        if match:
            month_de = match.group(1).lower()
            month = "March" if "maerz" in month_de else "October"
            year = int(match.group(2))
            exam_id = f"{year}-{month.lower()}"
            
            questions = []
            full_path = os.path.join(FRAGEN_DIR, pdf)
            if year >= 2019:
                 questions = parse_pdf_modern(full_path)
            else:
                 questions = parse_pdf_old(full_path)
            
            all_exams.append({
                "id": exam_id,
                "year": year,
                "month": month,
                "questions": questions
            })
            
    with open(OUTPUT_JSON, 'w') as f:
        json.dump(all_exams, f, indent=2, ensure_ascii=False)
    print(f"Import complete. Generated {len(all_exams)} exam entries.")

if __name__ == "__main__":
    run_import()
