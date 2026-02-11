# Report: Exams JSON Verification Against PDF Sources

This report details the comparison between `app/src/main/assets/exams.json` and the PDF files in `fragen/`.

## Summary
The verification process has identified several issues in the JSON content compared to the source PDFs.
*   **Verified Exams**: 26 exams (content matches or acceptable minor variations).
*   **Missing Questions in JSON**: 2 exams (October 2009, October 2014).
*   **Unverifiable (PDF Content Missing)**: 4 exams (March 2008, March 2009, March 2010 - solution keys only; October 2007 - unreadable scan).
*   **Correction Required**: 4 specific questions with significant text errors or formatting issues.

## Detailed Findings

### 1. Missing Questions in JSON
The following exams exist in the database but contain no questions:
*   **October 2009**
*   **October 2014**

### 2. Unverifiable Source PDFs
The following exams could not be verified because the source PDF contains only solutions or is unreadable:
*   **March 2008** (Solution key only)
*   **March 2009** (Solution key only)
*   **March 2010** (Solution key only)
*   **October 2007** (Scanned image, unreadable by script)

### 3. Corrections Required in JSON

#### March 2024 (2024-march) - Q7 Statement 2
*   **Issue**: Missing critical text in the statement.
*   **Current JSON**: `Das Führen der Berufsbezeichnung „wird durch das Psychotherapeutengesetz (PsychThG) geregelt.`
*   **PDF Source**: `Das Führen der Berufsbezeichnung „Heilpraktiker/in“ beschränkt auf das Gebiet der Psychotherapie wird durch das Psychotherapeutengesetz (PsychThG) geregelt.`
*   **Correction**: Insert missing phrase `Heilpraktiker/in“ beschränkt auf das Gebiet der Psychotherapie`.

#### October 2024 (2024-october) - Q18 Text
*   **Issue**: Medication dosage formatting is merged and confusing.
*   **Current JSON**: `...Man hat ihm Risperdon 2 mg Filmtablette Olanzapin 2,5 mg Tablette 1-0-0-0 / Tag 1-0-0-0 / Tag verordnet...`
*   **PDF Source**: `Man hat ihm Risperdon 2 mg Filmtablette 1-0-0-0 / Tag Olanzapin 2,5 mg Tablette 1-0-0-0 / Tag verordnet.`
*   **Correction**: Reformat to `Man hat ihm Risperdon 2 mg Filmtablette 1-0-0-0 / Tag, Olanzapin 2,5 mg Tablette 1-0-0-0 / Tag verordnet.`

#### October 2004 (2004-october) - Q9 Text
*   **Issue**: Quoted description differs slightly from PDF source.
*   **Current JSON**: `...„Uneingestandene Impulse werden in die Außenwelt verlagert, so dass sie als von außen kommend wahrgenommen werden.“`
*   **PDF Source**: `...„Uneingestandene Impulse werden in die Außenwelt verlagert, in einer anderen Person wahrgenommen und dort bekämpft.“`
*   **Correction**: Update quote to match PDF: `„Uneingestandene Impulse werden in die Außenwelt verlagert, in einer anderen Person wahrgenommen und dort bekämpft.“`

#### October 2025 (2025-october) - Q10 Statement 3
*   **Issue**: Typo / Missing text "Heilpraktiker (Psychotherapie)".
*   **Current JSON**: `Ein Gericht fordert einen ) im Rahmen eines Strafverfahrens auf...`
*   **PDF Source**: `Ein Gericht fordert einen Heilpraktiker (Psychotherapie) im Rahmen eines Strafverfahrens auf...`
*   **Correction**: Replace `einen ) im` with `einen Heilpraktiker (Psychotherapie) im`.

### 4. Note on Other Differences
*   **March 2005 - Q17**: The JSON text is a summarized version of the PDF text. The core question remains "Which defense mechanism is described?", but the wording is significantly different.
    *   *JSON*: `Ein seelischer (für diesen Menschen unerträglicher) Konflikt wird von einem Menschen unbewusst so in körperliche Symptome umgesetzt, dass die Symptome eine symbolhafte Darstellung des Konflikts bilden. Diesen Abwehrmechanismus bezeichnet man als:`
    *   *PDF*: `Ein seelischer (für diesen Menschen unerträglicher) Konflikt wird von einem Menschen unbewusst so in körperliche Symptome umgesetzt, dass die Symptome den Konflikt in symbolischer Form zum Ausdruck bringen und die Psyche dieser Person dadurch zugleich Entlastung von dieser inneren Anspannung erfährt. Welche Aussage bezeichnet diesen Vorgang aus psychoanalytischer Sicht (Sigmund Freud) am genauesten?`
    *   *Action*: Review if simplification is intended. If not, update to match PDF.
*   **October 2002**: Several typos found in the **PDF** source (e.g., `Leibmissempfndungen`, `Weiche`, `seiten` instead of `selten`). The JSON has the correct spellings, so no action is needed for these.
