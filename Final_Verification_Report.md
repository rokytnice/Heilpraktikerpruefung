# Final Verification Report: App Data vs PDF Originals

## 1. Methodology
To ensure complete accuracy and that no text is missing, I developed a custom verification tool (`verify_script.py`) that performs the following steps for each exam:
1.  **Extracts Text**: Automatically reads the text from the original PDF files located in the `fragen/` directory using `pdftotext` (layout-preserving mode).
2.  **Loads App Data**: Reads the `exams.json` file used by the Android application.
3.  **Comparision**:
    - Normalizes text (removes excess whitespace and special characters like bullets/checkboxes).
    - Compares each Question Text, Option, and Statement from the App against the PDF text.
    - Matches are verified locally. If an exact match is not found, the script attempts to find the text using fuzzy matching logic to account for minor OCR differences.
    - Checks the number of questions to ensure no questions are missing.

## 2. Executive Summary of Findings
The verification process has identified **significant discrepancies** between the App data and the original PDFs.

### critical Issues:
*   **Missing Questions**: Several exams have fewer questions in the App than in the PDF (typically 28). This is likely due to parsing errors wherequestions were merged into previous options.
    *   **2012-October**: 21 questions found (7 missing/merged).
    *   **2005-March**: 24 questions found (4 missing/merged).
    *   **2011-March**: 25 questions found.
    *   **2012-March**: 25 questions found.
    *   **2017-March**: 27 questions found.
    *   **2010-October**: 27 questions found.
*   **Merged Content**: For newer exams (2019-2025), the Question Text in the App often includes the first option or instructions (e.g., "A) ..."), which creates a mismatch with the clean Question Text in the PDF. This suggests the import script failed to separate the question body from the options correctly.
*   **Missing Options**: The report details specific options that could not be found in the PDF text, often due to formatting issues or truncation.

### Recommendation
The `exams.json` file needs to be regenerated or manually fixed. The current parser (`import_exams.py` or similar) likely struggles with:
1.  Distinguishing the end of a question from the start of the next (leading to merged questions).
2.  Separating the question text from the first option (leading to "A) ..." inside the question).

## 3. Detailed Mismatches (Excerpt)
Below is a summary of specific issues found. See `verification_report.md` for the full technical log.

### Examples of Merged Text (2019+ Exams)
*   **2019-March Q2**: App text contains `...ist/sind:  ‚A) Nur die Aussage 5 ist richtig...`. The PDF separates this.
*   **2023-March Q2**: App text includes part of the answer key structure.

### Examples of Missing/Merged Questions (Older Exams)
*   **2012-October**: Questions 3, 4, etc. appear to be merged into the options of previous questions (e.g., Question 2's Option D contains the text of Question 3).

## 4. Visual Verification
I have manually inspected a sample (2012-October) and confirmed that the JSON structure is indeed malformed, containing multiple questions merged into single fields.

Here is a screenshot of the quiz screen for verification:
![Quiz Screen Sample](quiz_q1_verification.png)

## 5. Next Steps
To resolve these issues, we need to:
1.  Fix the parsing logic in `import_exams.py` to better handle the PDF layouts (especially for 2012 and 2019+ variations).
2.  Re-run the import.
3.  Re-run this verification script to confirm the fix.

---
**Full Technical Log**: See [Detailed_Verification_Log.md](Detailed_Verification_Log.md) for the complete list of mismatches.
