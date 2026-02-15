# Anforderungsdokument: Quiz-App "Heilpraktiker für Psychotherapie" (HPP)

## 1. Projektübersicht
Ziel des Projekts ist die Entwicklung einer Android-App zur gezielten Vorbereitung auf die schriftliche Prüfung zum Heilpraktiker für Psychotherapie. [cite_start]Die App basiert auf einem interaktiven Multiple-Choice-System und bietet eine strukturierte Erfolgskontrolle. [cite: 20]

## 2. Funktionale Anforderungen (Phasenmodell)

### Phase 1: Kernfunktionen (MVP)
* [cite_start]**Datenbasis**: Integration von MC-Fragen (28 Fragen pro Prüfung), inklusive der korrekten Lösungen. [cite: 20]
* [cite_start]**Prüfungsmodus**: Auswahl der Übungseinheiten nach Jahr und Monat. [cite: 20]
* [cite_start]**Interaktion**: Beantwortung der Fragen per Klick. [cite: 20]
* [cite_start]**Auswertung & Statistik**: [cite: 20]
    * [cite_start]Anzeige der Ergebnisse in Prozent nach Abschluss einer Prüfung. [cite: 20]
    * [cite_start]Gezielte Identifikation falscher Antworten. [cite: 20]
    * [cite_start]Statistik, wie viel Prozent aller Prüfungen bereits absolviert wurden und Quote Falsch/Richtig. [cite: 20]
    * [cite_start]Optional: Wie viele Prüfungen mehrfach geübt wurden. [cite: 20]
* [cite_start]**Fehlermanagement**: [cite: 20]
    * [cite_start]Funktion zur exklusiven Wiederholung falsch beantworteter Fragen einer Session. [cite: 20]
    * [cite_start]Funktion, alle falschen Prüfungsfragen aus dem Gesamtpool wiederholen zu können. [cite: 20]
* [cite_start]**Lernfortschritt**: Speicherung des individuellen Fortschritts  [cite: 20]

### Phase 2: Wissensvertiefung
* [cite_start]Bereitstellung von Hintergrundinformationen und fachlichen Erklärungen zu jeder einzelnen Frage. [cite: 20]

### Phase 3: Themen-Kategorisierung
* [cite_start]Erstellung zusätzlicher Lernkategorien nach Schwerpunkten: [cite: 20]
    * [cite_start]Krankheitsbilder [cite: 20]
    * [cite_start]Geschichtliche Hintergründe [cite: 20]
    * [cite_start]Therapieverfahren [cite: 20]

### Phase 4: Gamification & Didaktik
* [cite_start]Erweiterung um Lernspiele und spezielle Anwendungen zur langfristigen Wissensverankerung. [cite: 20]

## 3. Technische Spezifikationen
* [cite_start]**Betriebssystem**: Android [cite: 20] 

## 4. Datenstruktur (für den Import)
[cite_start]Um einen reibungslosen Import der Inhalte zu gewährleisten, werden die Daten in einem strukturierten Format (z. B. CSV oder JSON) bereitgestellt, welches Felder für Jahr, Monat, Frage, Antwortoptionen (A-E), korrekte Lösung, Kategorie und Hintergrundinfos enthält. [cite: 20]

_________________
[cite_start]Stand 10.02.2026, Lisa [cite: 20]
_________________