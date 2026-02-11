# Heilpraktiker Psychotherapie Prüfungsfragen Verification

This repository contains tools to verify the contents of the examination questions in `app/src/main/assets/exams.json` against the original PDF files located in `fragen/`.

## Prerequisites

The verification script requires Python 3 and the `pypdf` library for extracting text from PDF files.

```bash
pip install pypdf
```

## How to Run

To run the verification script, execute the following command from the root of the repository:

```bash
python3 verify_exams_content.py
```

## Output

The script generates a report file named `Final_Verification_Report.md`. This report details:

1.  **Status per Exam**: Whether the exam content was fully verified, had mismatches, or if the source PDF was missing/unreadable.
2.  **Issues Found**: Specific discrepancies between the JSON data and the PDF text, including:
    *   Missing questions.
    *   Text mismatches in questions, options, or statements (often due to typos or OCR errors).
    *   "Potential Typo/OCR Error" warnings where the start and end of a text match but the middle differs.
3.  **Summary**: A count of exams with issues versus total exams checked.

## Directory Structure

*   `app/src/main/assets/exams.json`: The source JSON file containing the exam questions used by the app.
*   `fragen/`: Directory containing the original PDF exam files.
*   `verify_exams_content.py`: The Python script that performs the verification.
*   `Final_Verification_Report.md`: The generated report file.
