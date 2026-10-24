# Heilpraktikerprüfung

Android-App zur Vorbereitung auf die schriftliche Prüfung „Heilpraktiker für Psychotherapie" (HPP). Die App arbeitet mit Multiple-Choice-Fragen aus früheren Prüfungen und wertet die Antworten aus.

## Funktionen

- Übungseinheiten nach Prüfungsjahr und -monat (jeweils 28 Fragen)
- Fragetypen: Einfachauswahl, Mehrfachauswahl, Aussagenkombination
- Ergebnis in Prozent nach jeder Prüfung, mit Anzeige der falsch beantworteten Fragen
- Wiederholung der falschen Fragen einer Sitzung
- Lernfortschritt und Statistik (Quote richtig/falsch) in einer lokalen Datenbank
- Erklärungen zu den Fragen und Bildanzeige, soweit vorhanden

Die Anforderungen und die geplanten Ausbaustufen stehen in [`req.md`](req.md).

## Technik

- Kotlin, Jetpack Compose, Room
- Fragen als JSON in `app/src/main/assets/exams.json`
- minSdk 24, targetSdk 34
- Hilfsskripte: `generate_verification_report.py` und `gap_analysis.py` prüfen die Fragendaten gegen die Prüfungs-PDFs unter `fragen/`

## Bauen und installieren

```bash
./build_apk.sh   # Debug-APK nach app/build/outputs/apk/debug/
./deploy.sh      # bauen und auf ein per adb verbundenes Gerät installieren
```
