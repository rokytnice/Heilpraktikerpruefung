from difflib import SequenceMatcher
import re

def normalize_text(text):
    """Normalize text by removing extra whitespace and special characters."""
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def verify_text_match(app_text, pdf_text, threshold=0.85):
    """
    Verifies if app_text is present in pdf_text.
    Returns: (is_match, score)
    """
    norm_app = normalize_text(app_text)
    # pdf_text might be huge, so we don't always normalize the whole thing if passed repeatedly, 
    # but here we assume caller manages it or we do it.
    # ideally pdf_text is already normalized.
    
    if not norm_app:
        return True, 1.0 # Empty text is "found" (or irrelevant)

    # 1. Direct substring match (fastest)
    if norm_app in pdf_text:
        return True, 1.0

    # 2. Fuzzy substring match
    # SequenceMatcher is slow for large text. 
    # We can try to split app_text into chunks overlap?
    # Or just use find_longest_match logic
    
    s = SequenceMatcher(None, norm_app, pdf_text)
    match = s.find_longest_match(0, len(norm_app), 0, len(pdf_text))
    
    # If the longest match covers most of the app_text, it's a match.
    if match.size > len(norm_app) * threshold:
        return True, match.size / len(norm_app)
        
    return False, match.size / len(norm_app) if len(norm_app) > 0 else 0
