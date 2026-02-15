#!/usr/bin/env python3
"""Extract question images and answer key images from exam PDFs.

Output structure:
  app/src/main/assets/images/{exam_id}/
    q{N}.webp           - Question N image (cropped from PDF)
    a{N}.webp           - Answer matrix column for question N (grid PDFs)
    answer_key.webp     - Full answer key page (fallback)
"""

import fitz
import json
import os
import re
import sys
from PIL import Image
import io
from collections import defaultdict

FRAGEN_DIR = "fragen"
EXAMS_JSON = "app/src/main/assets/exams.json"
OUTPUT_DIR = "app/src/main/assets/images"
DPI = 96
WEBP_QUALITY = 60

QUESTION_TYPE_WORDS = {
    "Einfachauswahl", "Aussagenkombination", "Mehrfachauswahl",
    "Mehrfachauswahlaufgabe", "Aussagekombination"
}


def get_pdf_for_exam(year, month):
    """Find PDF file for an exam."""
    month_de = "Maerz" if month == "March" else "Oktober"
    for pattern in [
        f"{month_de}-{year}.pdf",
        f"HPP_Pruefung_{month_de}_{year}_mit_Loesungen_.pdf",
        f"HPP_Pruefung_{month_de}_{year}_mit_Loesungen.pdf",
        f"HPP_Pruefung_{month_de}_{year}_.pdf",
        f"HPP_Pruefung_{month_de}_{year}_mit_Loesungen_A_B.pdf",
        f"HPP_Pruefung_{month_de}_{year}_Gruppe_A_mit_Loesungen.pdf",
        f"HPP_Pruefung_{month_de}_{year}_mit_Loesungen_Gruppe_A.pdf",
    ]:
        path = os.path.join(FRAGEN_DIR, pattern)
        if os.path.exists(path):
            return path
    return None


def is_scanned_pdf(doc):
    """Check if PDF has no extractable text (scanned)."""
    total_text = 0
    for i in range(min(5, doc.page_count)):
        total_text += len(doc[i].get_text().strip())
    return total_text < 100


def find_answer_key_page(doc):
    """Find the Gruppe A answer key page. Returns (page_idx, is_gruppe_b_only).

    Prefers Gruppe A answer keys. Returns is_gruppe_b_only=True if only
    Gruppe B answer key was found (should not be used for answer grid images).
    """
    candidates = []  # [(page_idx, has_gruppe_a, has_gruppe_b_only)]

    for i in range(doc.page_count - 1, max(doc.page_count // 2 - 1, -1), -1):
        text = doc[i].get_text()
        is_answer_page = False
        if "Lösungsschlüssel" in text or "Lösungschlüssel" in text:
            is_answer_page = True
        elif "Lösungen" in text and i >= doc.page_count - 4:
            is_answer_page = True

        if is_answer_page:
            first_400 = text[:400]
            has_gruppe_a = bool(re.search(r'Gruppe\s*A', first_400))
            has_gruppe_b = bool(re.search(r'Gruppe\s*B', first_400))
            candidates.append((i, has_gruppe_a, has_gruppe_b))

    if not candidates:
        return None, False

    # Prefer pages explicitly labeled Gruppe A
    for page_idx, has_a, has_b in candidates:
        if has_a and not has_b:
            return page_idx, False
        if has_a:
            return page_idx, False

    # If no explicit Gruppe A, check if pages are Gruppe B only
    for page_idx, has_a, has_b in candidates:
        if not has_b:
            return page_idx, False  # No Gruppe marker = assume A

    # Only Gruppe B answer key found
    return candidates[0][0], True


def find_gruppe_b_page(doc):
    """Find the page where Gruppe B section starts (if applicable)."""
    full_text = ""
    for page in doc:
        full_text += page.get_text() + "\n"

    b_count = len(re.findall(r'Gruppe\s*B', full_text))

    if b_count == 0 or b_count >= 15:
        return None  # No Gruppe B section, or it's just page headers

    # Find the page where Gruppe B section starts (after first third of doc)
    text_len = 0
    threshold = len(full_text) * 0.25
    for i in range(doc.page_count):
        page_text = doc[i].get_text()
        text_len += len(page_text)
        if text_len > threshold and re.search(r'Gruppe\s*B', page_text):
            # Verify this is a section header, not just a mention
            # Check if "Gruppe B" appears near the top of the page
            lines = page_text.strip().split('\n')
            for line in lines[:5]:
                if re.search(r'Gruppe\s*B', line):
                    return i
    return None


def find_questions_on_pages(doc, end_page):
    """Find question positions using word-based search.
    Returns: {question_num: (page_idx, y_top)}
    """
    questions = {}

    for page_idx in range(end_page):
        page = doc[page_idx]
        words = page.get_text("words")

        for i, w in enumerate(words):
            word = w[4].strip()

            is_type = word in QUESTION_TYPE_WORDS

            # Handle split "Aussagen kombination" / "Aussage kombination"
            if not is_type and word in ("Aussagen", "Aussage"):
                if i + 1 < len(words):
                    next_w = words[i + 1][4].strip().lower()
                    if next_w.startswith("kombination"):
                        is_type = True

            if is_type and i > 0:
                prev = words[i - 1]
                try:
                    n = int(prev[4].strip())
                    if 1 <= n <= 28 and n not in questions:
                        questions[n] = (page_idx, prev[1] - 2)
                except ValueError:
                    pass

    return questions


def extract_question_image(doc, questions, qnum, output_path):
    """Extract and save image for a single question."""
    if qnum not in questions:
        return False

    page_idx, y_top = questions[qnum]
    page = doc[page_idx]
    page_rect = page.rect
    mat = fitz.Matrix(DPI / 72, DPI / 72)

    # Find where this question ends
    next_q_page = None
    next_q_y = None
    for nq in range(qnum + 1, 30):
        if nq in questions:
            next_q_page, next_q_y = questions[nq]
            break

    if next_q_page is not None and next_q_page == page_idx:
        # Next question on same page
        clip = fitz.Rect(0, max(0, y_top), page_rect.width, next_q_y - 3)
        pix = page.get_pixmap(matrix=mat, clip=clip)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
    elif next_q_page is not None and next_q_page > page_idx:
        # Question spans multiple pages - stitch
        images = []

        # Current page from y_top to bottom
        clip1 = fitz.Rect(0, max(0, y_top), page_rect.width, page_rect.height)
        pix1 = page.get_pixmap(matrix=mat, clip=clip1)
        images.append(Image.open(io.BytesIO(pix1.tobytes("png"))))

        # Intermediate full pages (rare)
        for mid_idx in range(page_idx + 1, next_q_page):
            mid_page = doc[mid_idx]
            pix_mid = mid_page.get_pixmap(matrix=mat)
            images.append(Image.open(io.BytesIO(pix_mid.tobytes("png"))))

        # Next question's page from top to its y_top
        next_page = doc[next_q_page]
        clip2 = fitz.Rect(0, 0, next_page.rect.width, next_q_y - 3)
        pix2 = next_page.get_pixmap(matrix=mat, clip=clip2)
        images.append(Image.open(io.BytesIO(pix2.tobytes("png"))))

        # Stitch vertically
        total_height = sum(im.height for im in images)
        max_width = max(im.width for im in images)
        img = Image.new("RGB", (max_width, total_height), (255, 255, 255))
        y_offset = 0
        for im in images:
            img.paste(im, (0, y_offset))
            y_offset += im.height
    else:
        # Last question or no next found - take rest of page
        clip = fitz.Rect(0, max(0, y_top), page_rect.width, page_rect.height)
        pix = page.get_pixmap(matrix=mat, clip=clip)
        img = Image.open(io.BytesIO(pix.tobytes("png")))

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path, "WebP", quality=WEBP_QUALITY)
    return True


def detect_grid_sections(page):
    """Detect answer grid sections on the answer key page.
    Returns list of sections: [{items: [...], y_top, y_bottom, ...}]
    """
    words = page.get_text("words")

    # Find all standalone number words
    num_words = []
    for w in words:
        txt = w[4].strip()
        try:
            n = int(txt)
            if 1 <= n <= 28:
                num_words.append({
                    'x0': w[0], 'y0': w[1], 'x1': w[2], 'y1': w[3], 'num': n
                })
        except ValueError:
            pass

    # Group by approximate y position
    y_groups = defaultdict(list)
    for nw in num_words:
        y_key = round(nw['y0'] / 8) * 8
        y_groups[y_key].append(nw)

    # Find header rows (groups with 8+ numbers in a horizontal line)
    header_rows = []
    for y_key in sorted(y_groups.keys()):
        group = y_groups[y_key]
        if len(group) >= 8:
            group.sort(key=lambda x: x['x0'])
            header_rows.append(group)

    if len(header_rows) < 2:
        return None

    # Determine which rows are Q1-14 and Q15-28
    # Check the numbers in each row
    sections = []
    for row in header_rows[:2]:
        nums = [item['num'] for item in row]
        col_width = (row[-1]['x1'] - row[0]['x0']) / len(row) if len(row) > 1 else 30
        sections.append({
            'items': row,
            'nums': nums,
            'col_width': col_width,
            'y_top': row[0]['y0'] - 5,
        })

    # Find y_bottom for each section
    # Section 1 ends where section 2 begins (with some margin)
    sections[0]['y_bottom'] = sections[1]['y_top'] - 3

    # Section 2 ends at the last E row
    # Find all 'E' letter words below the second header
    e_y_max = sections[1]['y_top'] + 150  # default
    for w in words:
        if w[4].strip() == 'E' and w[1] > sections[1]['y_top']:
            if w[3] > e_y_max:
                e_y_max = w[3]
    sections[1]['y_bottom'] = e_y_max + 8

    # Limit y_bottom to Gruppe B answer section if present below grid
    gruppe_b = page.search_for("Gruppe B")
    if gruppe_b:
        # Only use Gruppe B position if it's below the grid sections
        for gb in gruppe_b:
            if gb.y0 > sections[-1]['y_top'] + 50:
                for section in sections:
                    section['y_bottom'] = min(section['y_bottom'], gb.y0 - 5)
                break

    # Validate: ensure y_bottom > y_top for all sections
    for section in sections:
        if section['y_bottom'] <= section['y_top'] + 10:
            return None  # Invalid grid, fallback

    return sections


def extract_answer_grid_images(doc, answer_page_idx, output_dir):
    """Extract per-question answer images from grid-format answer key."""
    page = doc[answer_page_idx]
    mat = fitz.Matrix(DPI / 72, DPI / 72)
    page_rect = page.rect

    sections = detect_grid_sections(page)
    if sections is None:
        return False

    count = 0
    for section in sections:
        items = section['items']
        col_width = section['col_width']
        y_top = section['y_top']
        y_bottom = section['y_bottom']

        for item in items:
            n = item['num']
            x_center = (item['x0'] + item['x1']) / 2

            # Column boundaries: include ~2 neighbor columns for context
            x0 = x_center - col_width * 2.5
            x1 = x_center + col_width * 2.5

            clip = fitz.Rect(
                max(0, x0), max(0, y_top),
                min(page_rect.width, x1), min(page_rect.height, y_bottom)
            )
            if clip.width < 5 or clip.height < 5:
                continue
            pix = page.get_pixmap(matrix=mat, clip=clip)
            img = Image.open(io.BytesIO(pix.tobytes("png")))

            path = os.path.join(output_dir, f"a{n}.webp")
            img.save(path, "WebP", quality=WEBP_QUALITY)
            count += 1

    return count > 0


def extract_answer_key_full_page(doc, answer_page_idx, output_dir):
    """Save the full answer key page as a single image."""
    page = doc[answer_page_idx]
    mat = fitz.Matrix(DPI / 72, DPI / 72)

    # Try to crop to just the Gruppe A section (only if Gruppe B is a real section, not header)
    gruppe_b = page.search_for("Gruppe B")
    clip = None
    if gruppe_b:
        # Only crop if "Gruppe B" appears below the top quarter of the page
        # (not a page header)
        for gb in gruppe_b:
            if gb.y0 > page.rect.height * 0.25:
                clip = fitz.Rect(0, 0, page.rect.width, gb.y0 - 5)
                break

    if clip and clip.height > 50:
        pix = page.get_pixmap(matrix=mat, clip=clip)
    else:
        pix = page.get_pixmap(matrix=mat)

    img = Image.open(io.BytesIO(pix.tobytes("png")))
    path = os.path.join(output_dir, "answer_key.webp")
    img.save(path, "WebP", quality=WEBP_QUALITY)
    return True


def process_exam(exam):
    """Process a single exam: extract question and answer images."""
    exam_id = exam['id']
    year = exam['year']
    month = exam['month']

    pdf_path = get_pdf_for_exam(year, month)
    if not pdf_path:
        print(f"  No PDF found")
        return 0

    output_dir = os.path.join(OUTPUT_DIR, exam_id)
    os.makedirs(output_dir, exist_ok=True)

    doc = fitz.open(pdf_path)
    print(f"  PDF: {os.path.basename(pdf_path)} ({doc.page_count} pages)")

    if is_scanned_pdf(doc):
        print(f"  Scanned PDF - saving page images")
        mat = fitz.Matrix(DPI / 72, DPI / 72)
        count = doc.page_count
        for page_idx in range(count):
            pix = doc[page_idx].get_pixmap(matrix=mat)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            path = os.path.join(output_dir, f"page{page_idx + 1}.webp")
            img.save(path, "WebP", quality=WEBP_QUALITY)
        doc.close()
        return count

    # Determine page ranges
    answer_page, is_gruppe_b_only = find_answer_key_page(doc)
    gruppe_b_page = find_gruppe_b_page(doc)

    questions_end = doc.page_count
    if answer_page is not None:
        questions_end = min(questions_end, answer_page)
    if gruppe_b_page is not None:
        questions_end = min(questions_end, gruppe_b_page)

    answer_info = ""
    if answer_page is not None:
        answer_info = f", answer key: page {answer_page}"
        if is_gruppe_b_only:
            answer_info += " (GRUPPE B - skipping!)"
    print(f"  Question pages: 0-{questions_end - 1}" + answer_info +
          (f", Gruppe B starts: page {gruppe_b_page}" if gruppe_b_page else ""))

    # Find and extract question images
    questions = find_questions_on_pages(doc, questions_end)
    print(f"  Found {len(questions)} questions: {sorted(questions.keys())}")

    q_count = 0
    for n in range(1, 29):
        path = os.path.join(output_dir, f"q{n}.webp")
        if extract_question_image(doc, questions, n, path):
            q_count += 1

    # Extract answer key - always save full page
    if answer_page is not None:
        extract_answer_key_full_page(doc, answer_page, output_dir)
        print(f"  Saved full answer key page")
    else:
        print(f"  No answer key page found")

    print(f"  Result: {q_count} question images")
    doc.close()
    return q_count


def main():
    with open(EXAMS_JSON) as f:
        exams = json.load(f)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    total_images = 0
    for exam in exams:
        print(f"\n{'='*50}")
        print(f"Processing {exam['id']}...")
        total_images += process_exam(exam)

    # Summary
    total_size = 0
    exam_stats = []
    for exam_dir in sorted(os.listdir(OUTPUT_DIR)):
        dir_path = os.path.join(OUTPUT_DIR, exam_dir)
        if os.path.isdir(dir_path):
            files = [f for f in os.listdir(dir_path) if f.endswith('.webp')]
            q_files = [f for f in files if f.startswith('q')]
            a_files = [f for f in files if re.match(r'a\d+\.webp$', f)]
            dir_size = sum(os.path.getsize(os.path.join(dir_path, f)) for f in files)
            total_size += dir_size
            exam_stats.append((exam_dir, len(q_files), len(a_files), dir_size))

    print(f"\n{'='*60}")
    print(f"{'Exam':<20} {'Questions':>10} {'Answers':>10} {'Size':>10}")
    print(f"{'-'*60}")
    for eid, qc, ac, sz in exam_stats:
        print(f"{eid:<20} {qc:>10} {ac:>10} {sz/1024:>9.0f}K")
    print(f"{'-'*60}")
    print(f"{'TOTAL':<20} {sum(s[1] for s in exam_stats):>10} {sum(s[2] for s in exam_stats):>10} {total_size/1024/1024:>8.1f}M")


if __name__ == "__main__":
    main()
