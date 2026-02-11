# Gap Analysis Report: App Content vs Original PDFs

## 1. Executive Summary
This report analyzes the completeness and accuracy of the exam data in the Heilpraktiker App compared to the original PDF sources.

**Validation Status**: **FAILED**

*   **Total Missing Questions**: ~140 questions are missing entirely from the App.
*   **Empty Exams**: 4 exams exist in the database but contain **0 questions**.
*   **Incomplete Exams**: 11 exams have fewer questions than the original PDF (e.g., 21 instead of 28).
*   **Data Integrity**: Newer exams (2018-2025) often contain parsing errors where answer choices are merged into the question text.

## 2. Detailed Gap Analysis
The following table summarizes the status of each exam. The "Gap" column indicates the number of missing questions.

| Exam ID | App Questions | PDF Questions (Est) | Gap (Missing) | Status | Issue |
| :--- | :---: | :---: | :---: | :--- | :--- |
| **2002-October** | **0** | **28** | **28** | **CRITICAL** | **Exam Empty** |
| 2003-March | 28 | 28 | 0 | OK |  |
| **2003-October** | **26** | **28** | **2** | **MISSING** | 2 Questions Missing |
| 2004-March | 28 | 28 | 0 | OK |  |
| 2004-October | 28 | 28 | 0 | OK |  |
| **2005-March** | **24** | **28** | **4** | **MISSING** | 4 Questions Missing |
| 2005-October | 28 | 28 | 0 | OK |  |
| 2006-March | 28 | 28 | 0 | OK |  |
| **2006-October** | **25** | **28** | **3** | **MISSING** | 3 Questions Missing |
| 2007-March | 28 | 28 | 0 | OK |  |
| **2007-October** | **0** | **0** | **0** | **ERROR** | **PDF Unreadable?** |
| **2008-March** | **0** | **20** | **20** | **CRITICAL** | **Exam Empty** |
| 2008-October | 28 | 28 | 0 | OK |  |
| **2009-March** | **0** | **10** | **10** | **CRITICAL** | **Exam Empty** |
| **2009-October** | **0** | **28** | **28** | **CRITICAL** | **Exam Empty** |
| 2010-March | 28 | 28 | 0 | OK |  |
| **2010-October** | **27** | **28** | **1** | **MISSING** | 1 Question Missing |
| 2011-March | 25 | 25 | 0 | OK |  |
| **2011-October** | **27** | **28** | **1** | **MISSING** | 1 Question Missing |
| **2012-March** | **25** | **28** | **3** | **MISSING** | 3 Questions Missing |
| **2012-October** | **21** | **28** | **7** | **MISSING** | 7 Questions Missing (!) |
| **2013-March** | **27** | **28** | **1** | **MISSING** | 1 Question Missing |
| 2013-October | 28 | 28 | 0 | OK |  |
| 2014-March | 28 | 28 | 0 | OK |  |
| **2014-October** | **0** | **0** | **0** | **ERROR** | **PDF Unreadable/Empty** |
| 2015-March | 28 | 28 | 0 | OK |  |
| 2016-March | 28 | 28 | 0 | OK |  |
| 2016-October | 28 | 28 | 0 | OK |  |
| **2017-March** | **27** | **28** | **1** | **MISSING** | 1 Question Missing |
| 2017-October | 28 | 28 | 0 | OK |  |
| 2019-March | 28 | 28 | 0 | WARN | Merged Text Issues |
| 2020-October | 28 | 28 | 0 | OK |  |
| 2022-March | 28 | 28 | 0 | OK |  |
| 2022-October | 28 | 28 | 0 | OK |  |
| 2023-March | 28 | 28 | 0 | OK |  |
| 2023-October | 28 | 28 | 0 | OK |  |
| 2024-March | 28 | 28 | 0 | OK |  |
| 2024-October | 28 | 28 | 0 | WARN | Merged Text Issues |
| 2025-March | 28 | 28 | 0 | OK |  |
| 2025-October | 28 | 28 | 0 | OK |  |

## 3. Structural & Content Issues
Beyond the missing questions, verified content issues include:

### A. Merged Answer Choices (Newer Exams)
In exams from **2019 onward**, the import script often fails to separate the first option from the question body.
*   **Example**: "Welche Aussage trifft zu? A) Die Lewy-Körperchen-Demenz..." is stored as the Question Text.
*   **Impact**: The first option is removed from the list of choices and displayed as part of the question. The user cannot select the correct answer if it's option A, or sees strange formatting.

### B. Missing Question Text (Older Exams)
In older exams (e.g., **2012-October**), questions are often merged.
*   **Example**: Question 4's text might be appended to Question 3's options, causing Question 4 to disappear entirely from the list. This explains why an exam has 21 questions instead of 28.

## 4. Recommendations
1.  **Stop Using the App for Study**: The current data is unreliable.
2.  **Fix Import Script**: The `import_exams.py` (or parser logic) needs a major overhaul to handle:
    *   Different PDF layouts (old vs new).
    *   Separating Question Text from Options (regex logic needs improvement).
    *   Detecting end-of-question markers.
3.  **Regenerate Data**: Once fixed, the entire `exams.json` must be rebuilt.
