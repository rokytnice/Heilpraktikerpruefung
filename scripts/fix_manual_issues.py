#!/usr/bin/env python3
"""Fix specific remaining verification mismatches manually."""
import json

EXAMS_JSON = "app/src/main/assets/exams.json"

with open(EXAMS_JSON, 'r') as f:
    exams = json.load(f)

def get_q(eid, qid):
    exam = [e for e in exams if e['id'] == eid][0]
    return [q for q in exam['questions'] if q['id'] == qid][0]

# === Fix 1: 2022-march Q14 - extract options from text ===
q = get_q('2022-march', 14)
q['text'] = (
    "Ein Patient mit emotional instabiler Persönlichkeitsstörung vom Borderline-Typ "
    "spricht auf eine kognitive Umstrukturierung nicht an. Sie denken daher als Alternative "
    "zur Veränderung dysfunktionaler Kognitionen an ein Emotionsregulationstraining als "
    "Teil der Dialektisch-Behavioralen Therapie (DBT). "
    "Welche Aussage zum Emotionsregulationstraining trifft zu?"
)
q['options'] = [
    "Eingeübt wird die Achtsamkeit für vergangene Gefühle",
    "Der Patient soll befähigt werden, mit seinen Gefühlen umzugehen",
    "Gefördert wird, sich stärker mit seinem Gefühl zu identifizieren",
    "Der Patient wird bestärkt, die Wahrnehmung negativer Gefühle zu vermeiden und diese zu unterdrücken",
    "Der Therapeut hilft dem Patienten dabei, problematische Gefühle (z.B. beängstigende Gedanken) zu verstärken"
]
print("Fixed 2022-march Q14: options extracted")

# === Fix 2: 2020-october Q18 - fix statements and options (numbered 1-5 format) ===
q = get_q('2020-october', 18)
q['statements'] = [
    "Parkinsonoid",
    "Sitzunruhe (Akathisie)",
    "Herzkreislaufstörungen",
    "Gewichtszunahme",
    "Abhängigkeitsentwicklung"
]
q['options'] = [
    "Nur die Aussagen 2 und 3 sind richtig",
    "Nur die Aussagen 1, 3 und 4 sind richtig",
    "Nur die Aussagen 2, 4 und 5 sind richtig",
    "Nur die Aussagen 1, 2, 3 und 4 sind richtig",
    "Nur die Aussagen 1, 2, 4 und 5 sind richtig"
]
print("Fixed 2020-october Q18: statements/options separated")

# === Fix 3: 2025-october Q16 - strip instruction from statement 5, clean text ===
q = get_q('2025-october', 16)
q['text'] = (
    "Sie möchten eine Raucherentwöhnung als Heilpraktikerin/Heilpraktiker, "
    "beschränkt auf das Gebiet der Psychotherapie, anbieten. Welche/s der "
    "folgenden Therapien \u2013 nach entsprechender Ausbildung \u2013 "
    "darf/dürfen Sie unterstützend anbieten?"
)
q['statements'] = [
    "Einzelhypnose",
    "Gruppenhypnose in Ihrer Praxis",
    "Verordnung einer Medikation wie z.B. Buprion, Varencelin oder Cystin",
    "Akupunktur",
    "Kognitive Verhaltenstherapie"
]
print("Fixed 2025-october Q16: stripped instruction from stmt 5")

# === Fix 4a: 2004-october Q7 - fix garbled word order ===
q = get_q('2004-october', 7)
q['text'] = "Zu den Methoden/Techniken der Verhaltenstherapie zählen üblicherweise:"
print("Fixed 2004-october Q7: corrected word order")

# === Fix 4b: 2004-october Q9 - fix garbled text + option E ===
q = get_q('2004-october', 9)
q['text'] = (
    "In der psychoanalytischen Theorie werden verschiedene Abwehrmechanismen "
    "postuliert. Welcher dieser Abwehrmechanismen kommt in der folgenden "
    "Beschreibung am besten zum Ausdruck? "
    "\u201eUneingestandene Impulse werden in die Au\u00dfenwelt verlagert, "
    "so dass sie als von au\u00dfen kommend wahrgenommen werden.\u201c"
)
q['options'][4] = "Verschiebung"
print("Fixed 2004-october Q9: corrected text order, cleaned option E")

# === Fix 5: 2012-october Q2 - fix option D/E (duplicate D label in PDF) ===
q = get_q('2012-october', 2)
q['options'] = [
    "Verlust der Integration bestimmter Ich-Funktionen oder bestimmter körperlicher Funktionen",
    "Verhalten, das den geltenden sozialen Normen erheblich widerspricht",
    "Rückzug von sozialen Kontakten in eine abgeschirmte Phantasiewelt",
    "Vorhandensein von zwei oder mehr Persönlichkeiten in einem Individuum",
    "Verhalten ist manieriert, flapsig und oberflächlich"
]
print("Fixed 2012-october Q2: separated option D/E")

# === Fix 6: 2005-march Q17 - fix options (all fused into opt A) ===
q = get_q('2005-march', 17)
q['text'] = (
    "Ein seelischer (für diesen Menschen unerträglicher) Konflikt wird von einem "
    "Menschen unbewusst so in körperliche Symptome umgesetzt, dass die Symptome "
    "eine symbolhafte Darstellung des Konflikts bilden. "
    "Diesen Abwehrmechanismus bezeichnet man als:"
)
q['options'] = [
    "Projektion",
    "Konversion",
    "Regression",
    "Narzissmus",
    "Psychosoziale Abwehr"
]
print("Fixed 2005-march Q17: separated options")

# === Fix 7: 2005-march Q25 - fix missing statement 1 and options ===
q = get_q('2005-march', 25)
q['statements'] = [
    "Verhaltenstherapeutische Maßnahmen",
    "Selbsthilfegruppe",
    "Analytische Psychotherapie",
    "Personenzentrierte Gesprächstherapie",
    "Familientherapie"
]
q['options'] = [
    "Nur die Aussagen 1, 2 und 4 sind richtig",
    "Nur die Aussagen 1, 3 und 5 sind richtig",
    "Nur die Aussagen 2, 3 und 5 sind richtig",
    "Nur die Aussagen 1, 2, 3 und 5 sind richtig",
    "Alle Aussagen sind richtig"
]
print("Fixed 2005-march Q25: added statement 1, cleaned options")

# === Fix 8: 2005-march Q27 - clean trailing "0" and OCR artifacts ===
q = get_q('2005-march', 27)
q['text'] = (
    'Welche der folgenden Aussagen treffen zu? '
    'Merkmale der sog. \u201evoll funktionsfähigen Person\u201c '
    '(\u201efully functioning person\u201c) nach Rogers sind:'
)
print("Fixed 2005-march Q27: cleaned text")

with open(EXAMS_JSON, 'w') as f:
    json.dump(exams, f, ensure_ascii=False, indent=2)
print("\nAll fixes saved.")
