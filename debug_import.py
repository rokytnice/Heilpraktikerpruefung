
import os
import re
import subprocess
from bs4 import BeautifulSoup

def debug_solutions(pdf_path):
    print(f"DEBUG: Processing {pdf_path}")
    temp_dir = "temp_debug_html"
    os.makedirs(temp_dir, exist_ok=True)
    base_name = os.path.basename(pdf_path).replace(".pdf", "")
    html_file = os.path.join(temp_dir, f"{base_name}.html")
    
    # Run pdftohtml
    subprocess.run(["pdftohtml", "-s", "-c", pdf_path, html_file], check=True)
    
    main_html = html_file.replace(".html", "-html.html")
    if not os.path.exists(main_html):
        print(f"ERROR: {main_html} not found. pdftohtml might have failed.")
        return

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
            print("DEBUG: Found 'Lösungsschlüssel' marker")
        if not found_key: continue
        
        style = p.get('style', '')
        left_match = re.search(r'left:(\d+)px', style)
        top_match = re.search(r'top:(\d+)px', style)
        if not left_match or not top_match: continue
        left = int(left_match.group(1))
        top = int(top_match.group(1))
        
        # Filter out obvious noise (too far left/right or top/bottom relative to first match if implemented)
        # For now, just keep everything after the key marker
        
        grid_elements.append({
            "text": text,
            "left": left,
            "top": top,
            "class": p.get('class', [None])[0]
        })

    print(f"DEBUG: Found {len(grid_elements)} potential grid elements")

    if not grid_elements: 
        print("DEBUG: No grid elements found.")
        return 

    # 2. Group into rows by 'top'
    rows = []
    for el in sorted(grid_elements, key=lambda x: x["top"]):
        if not rows or abs(el["top"] - rows[-1][0]["top"]) > 10:
            rows.append([el])
        else:
            rows[-1].append(el)
            
    for row in rows:
        row.sort(key=lambda x: x["left"])

    print(f"DEBUG: Grouped into {len(rows)} rows")

    # 3. Identify header rows and data rows
    q_centers = {}
    letter_rows = []
    
    for row in rows:
        row_text = " ".join([el["text"] for el in row])
        # print(f"DEBUG ROW: {row_text}")
        
        nums = re.findall(r'\d+', row_text)
        # Heuristic: Header row usually has question numbers like 1 2 3 4 ... 
        # But specifically we look for the header row with question numbers to map x-coordinates
        if len(nums) >= 5: # Header row candidate
            # Refine check: are they sequential or close? 
            # For now, trust the count.
            print(f"DEBUG: Potential header row: {row_text}")
            for el in row:
                parts = el["text"].split()
                current_left = el["left"] # This is rough, pdftohtml puts text in one block sometimes?
                # Actually, pdftohtml with -c splits fairly well usually, but sometimes chunks.
                # Let's assume discrete elements for numbers if possible.
                
                if el["text"].isdigit():
                     q_id = int(el["text"])
                     q_centers[el["left"] + 5] = q_id # Center approx
                     print(f"  -> Mapped Q{q_id} to x={el['left']}")
                else:
                    # Mixed text/numbers?
                    pass

        # Check for letter rows (the solutions)
        # Rows containing A, B, C, D, E
        if any(re.match(r'^[ABCDE]$', el["text"].strip()) for el in row):
             letter_rows.append(row)
             # print(f"DEBUG: Added letter row: {row_text}")

    print(f"DEBUG: Found {len(q_centers)} question centers and {len(letter_rows)} letter rows")

    # 4. Dynamically detect 'correct' class
    # We look for the class that appears exactly once per question column ideally?
    # Or simply the class used for the solution letters. 
    # In many exams, the correct answer is BOLD or Colored. pdftohtml converts this to a CSS class.
    
    class_counts = {}
    for row in letter_rows:
        for el in row:
            if el["text"] in "ABCDE":
                cls = el["class"]
                class_counts[cls] = class_counts.get(cls, 0) + 1
    
    print("DEBUG: Class counts for letters:", class_counts)
    
    # The 'correct' class should be significantly less frequent than the 'wrong' class (1 correct vs 4 wrong options)
    # BUT wait, the solution grid usually ONLY shows the correct letter? 
    # OR it shows A B C D E and the correct one is marked?
    # Let's check a sample PDF to know the TRUTH.
    
    # If the grid shows ALL letters and highlights one: One class ~4x count of other.
    # If the grid shows ONLY correct letters: Only one class usually?
    
    # Let's infer from counts.
    sorted_classes = sorted([c for c in class_counts if c], key=lambda x: class_counts[x])
    if not sorted_classes: 
        print("DEBUG: No classes found.")
        return

    # In "Lösungsschlüssel" usually it lists question numbers and the CORRECT letter next to it.
    # It might NOT be a grid of A B C D E where one is marked. 
    # It might just be:  1  A   2  C   3  B
    
    # Hypothesis: If it's a list of correct answers, we just need to associate the letter to the column (Question ID).
    
    # Let's dump the structure of letter_rows to understand better.
    for i, row in enumerate(letter_rows[:3]):
        print(f"DEBUG Row {i}: " + " | ".join([f"{el['text']}({el['left']})" for el in row]))
        
debug_solutions("/home/aroc/projects/Heilpraktikerpruefung/fragen/HPP_Pruefung_Oktober_2024_mit_Loesungen_A_B.pdf")
if not os.path.exists("/home/aroc/projects/Heilpraktikerpruefung/fragen/Lösungsschlüssel_HPP_Okt_2024.pdf"):
     # Try to find a valid PDF to test
     print("DEBUG: Specific solution file not found. Listing dir:")
     print(os.listdir("/home/aroc/projects/Heilpraktikerpruefung/fragen")[:5])
