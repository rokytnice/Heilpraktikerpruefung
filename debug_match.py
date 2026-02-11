from scripts import text_utils
import re

def main():
    # Load PDF text
    with open("pdf_debug.txt", "r") as f:
        pdf_raw = f.read()
    
    norm_pdf = text_utils.normalize_text(pdf_raw)
    
    # App text from report (approximate)
    app_raw = "Welche Aussage zu Demenzerkrankungen trifft zu? "
    norm_app = text_utils.normalize_text(app_raw)
    
    print(f"App Norm: '{norm_app}'")
    # print(f"PDF Norm: '{norm_pdf}'") # Too long
    
    if norm_app in norm_pdf:
        print("MATCH FOUND!")
    else:
        print("NO MATCH.")
        # Find where it *should* reflect
        idx = norm_pdf.find("Welche Aussage")
        if idx != -1:
            print(f"Found context: '{norm_pdf[idx:idx+100]}'")
            
            # Compare char by char
            snippet = norm_pdf[idx:idx+len(norm_app)]
            print(f"Snippet:  '{snippet}'")
            print(f"App Norm: '{norm_app}'")
            
            for i, (c1, c2) in enumerate(zip(snippet, norm_app)):
                if c1 != c2:
                    print(f"Diff at {i}: PDF='{c1}'({ord(c1)}) vs App='{c2}'({ord(c2)})")
        else:
            print("Context not found in PDF.")

if __name__ == "__main__":
    main()
