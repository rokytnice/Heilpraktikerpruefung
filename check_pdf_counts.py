import os
import re
import subprocess

FRAGEN_DIR = "fragen"

def get_pdf_question_count(pdf_path):
    try:
        # pdftotext -layout <pdf> -
        result = subprocess.run(["pdftotext", "-layout", pdf_path, "-"], capture_output=True, text=True, check=True)
        text = result.stdout
        
        # Heuristics for question counting
        # Pattern 1: "Frage 1", "Frage 2"
        # Pattern 2: "1.", "2." at start of line (more risky)
        
        # Method 1: Count "Frage X"
        frage_matches = re.findall(r'Frage\s+(\d+)', text)
        if frage_matches:
            # Get max number
            nums = [int(n) for n in frage_matches]
            method1_max = max(nums) if nums else 0
        else:
            method1_max = 0
            
        method1_max = 0
            
        lines = text.split('\n')
        
        # Method 2: Count lines starting with number
        # Pattern seen: "1 Einfachauswahl", "2 Aussagenkombination"
        # Also just "1 " sometimes?
        
        found_nums = []
        for line in lines:
            line = line.strip()
            # Match number followed by space and text, or number and dot
            # e.g. "1 Einfachauswahl", "1. Frage", "1 "
            m = re.match(r'^(\d+)\s+([A-Z]|Einfach|Mehrfach|Aussagen)', line)
            if not m:
                m = re.match(r'^(\d+)\.\s', line)
            
            if m:
                num = int(m.group(1))
                if 0 < num < 100: # Sanity check for question numbers
                    found_nums.append(num)
        
        # Filter for sequential-ish
        found_nums = sorted(list(set(found_nums)))
        # valid sequence should likely end near the max
        if found_nums:
            # Check for a reasonable sequence length or max value
            # If we have 1, 2, 3 ... 28 -> max is 28.
            # If we have 1, 5, 10 -> risky.
            # Just take the max for now as an estimate.
            method2_max = found_nums[-1] 
        else:
            method2_max = 0
        
        return max(method1_max, method2_max)

    except subprocess.CalledProcessError:
        return -1
    except Exception as e:
        print(f"Error processing {pdf_path}: {e}")
        return -1

def check_pdfs():
    print(f"{'PDF Filename':<60} | {'Est. Questions':<15}")
    print("-" * 80)
    
    files = sorted([f for f in os.listdir(FRAGEN_DIR) if f.endswith('.pdf')])
    for f in files:
        path = os.path.join(FRAGEN_DIR, f)
        count = get_pdf_question_count(path)
        print(f"{f:<60} | {count:<15}")

if __name__ == "__main__":
    check_pdfs()
