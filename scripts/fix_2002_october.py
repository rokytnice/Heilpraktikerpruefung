#!/usr/bin/env python3
"""Fix the 2002-october exam: add question texts, statements, and fix corrupted options."""

import json

EXAMS_PATH = "app/src/main/assets/exams.json"

# Full questions transcribed from Oktober-2002.pdf
QUESTIONS_2002_OCT = [
    {
        "id": 1,
        "type": "Aussagenkombination",
        "text": "Hinsichtlich der Verbreitung des Alkoholismus in der Bundesrepublik Deutschland gilt:",
        "statements": [
            "Die Prävalenz (Erkrankungshäufigkeit) in der Bundesrepublik liegt bei mehreren Prozent (ca. drei bis fünf Prozent).",
            "Bei Männern kommt Alkoholismus häufiger vor als bei Frauen",
            "Bei Kindern von Alkoholikern ist das Risiko eine Alkoholkrankheit zu entwickeln deutlich vermindert"
        ],
        "options": [
            "Nur die Aussage 2 ist richtig",
            "Nur die Aussagen 1 und 2 sind richtig",
            "Nur die Aussagen 1 und 3 sind richtig",
            "Nur die Aussagen 2 und 3 sind richtig",
            "Alle Aussagen sind richtig"
        ],
        "correctIndices": [1],
        "explanation": ""
    },
    {
        "id": 2,
        "type": "Aussagenkombination",
        "text": "Bei einer drogeninduzierten Psychose können folgende Symptome auftreten:",
        "statements": [
            "Starke Angst",
            "Leibmissempfindungen",
            "Verworrenheit",
            "Ekstase",
            "Dranghafte Geschäftigkeit"
        ],
        "options": [
            "Nur die Aussagen 1 und 2 sind richtig",
            "Nur die Aussagen 1 und 4 sind richtig",
            "Nur die Aussagen 1, 2 und 3 sind richtig",
            "Nur die Aussagen 3, 4 und 5 sind richtig",
            "Alle Aussagen sind richtig"
        ],
        "correctIndices": [4],
        "explanation": ""
    },
    {
        "id": 3,
        "type": "Einfachauswahl",
        "text": "Was ist bei der Alkoholhalluzinose am häufigsten das kennzeichnende Merkmal?",
        "statements": [],
        "options": [
            "Akustische Halluzinationen",
            "Extreme Bewegungsunruhe mit unaufhörlichen Nestelbewegungen",
            "Gustatorische (geschmackliche) Halluzinationen",
            "Beim Einschlafen auftretende optische Sinnestäuschungen",
            "Schwere Bewusstseinsstörung"
        ],
        "correctIndices": [0],
        "explanation": ""
    },
    {
        "id": 4,
        "type": "Aussagenkombination",
        "text": "Zur Anorexia nervosa gehören folgende Symptome:",
        "statements": [
            "Verstärkte Monatsblutung bei Frauen",
            "Übertriebene körperliche Aktivitäten",
            "Hoher Leidensdruck",
            "Selbst induziertes Erbrechen",
            "Eingeschränkte Nahrungsauswahl"
        ],
        "options": [
            "Nur die Aussagen 2 und 4 sind richtig",
            "Nur die Aussagen 2, 4 und 5 sind richtig",
            "Nur die Aussagen 1, 2, 4 und 5 sind richtig",
            "Nur die Aussagen 2, 3, 4 und 5 sind richtig",
            "Alle Aussagen sind richtig"
        ],
        "correctIndices": [1],
        "explanation": ""
    },
    {
        "id": 5,
        "type": "Aussagenkombination",
        "text": "Für die Bulimia nervosa gilt:",
        "statements": [
            "Die Bulimia nervosa tritt meist zwischen dem 12. und 30. Lebensjahr auf",
            "Frauen erkranken ungefähr zehnmal häufiger als Männer an Bulimia nervosa",
            "Ein BMI (Body-Maß-Index) über 30 spricht immer für eine Bulimia nervosa",
            "Die Bulimia nervosa ist in der Regel eine harmlose, spontan ausheilende Störung im Essverhalten",
            "Typisch sind Heißhungerattacken mit Aufnahme großer Mengen von Nahrungsmitteln in kurzer Zeit"
        ],
        "options": [
            "Nur die Aussagen 3 und 4 sind richtig",
            "Nur die Aussagen 1, 2 und 3 sind richtig",
            "Nur die Aussagen 1, 2 und 5 sind richtig",
            "Nur die Aussagen 3, 4 und 5 sind richtig",
            "Alle Aussagen sind richtig"
        ],
        "correctIndices": [2],
        "explanation": ""
    },
    {
        "id": 6,
        "type": "Einfachauswahl",
        "text": "Ein Patient, der gerade vom Heilpraktiker die Mitteilung einer ungünstigen Prognose seiner Erkrankung bekommen hat, äußert gegenüber der Praxismitarbeiterin: \u201eIch werde wohl nicht mehr lange leben, aber es ist so merkwürdig: Ich weiß nicht, wie es mir geht. Ich komme mir vor, wie in Watte eingepackt.\u201c\nDas beobachtete Erleben lässt sich psychoanalytisch beschreiben als",
        "statements": [],
        "options": [
            "Isolierung",
            "Projektion",
            "Rationalisierung",
            "Ungeschehen-Machen",
            "Sublimierung"
        ],
        "correctIndices": [0],
        "explanation": ""
    },
    {
        "id": 7,
        "type": "Aussagenkombination",
        "text": "Welche der folgenden Aussagen treffen auf Grundannahmen, Ziele und Vorgehensweisen der klientenzentrierten Psychotherapie nach Carl Rogers zu?",
        "statements": [
            "Der Therapeut verbalisiert die emotionalen Erlebnisinhalte des Klienten",
            "Der Therapeut vermittelt dem Klienten emotionale Wertschätzung",
            "Der Klient wird in seinem Bemühen nach Selbstverwirklichung und Selbstaktualisierung unterstützt",
            "Die Dynamik der Entwicklung des Selbst wird durch biologisch determinierte Vorgänge gesteuert",
            "Psychische Störungen sind die Folge einer Diskrepanz zwischen dem Bedürfnis nach uneingeschränkter Wertschätzung und negativen Erfahrungen der Ablehnung von Teilen des Selbst"
        ],
        "options": [
            "Nur die Aussagen 1, 2 und 3 sind richtig",
            "Nur die Aussagen 3, 4 und 5 sind richtig",
            "Nur die Aussagen 1, 2, 3 und 4 sind richtig",
            "Nur die Aussagen 1, 2, 3 und 5 sind richtig",
            "Alle Aussagen sind richtig"
        ],
        "correctIndices": [3],
        "explanation": ""
    },
    {
        "id": 8,
        "type": "Aussagenkombination",
        "text": "Stützende (supportive) Psychotherapie kann angewandt werden bei:",
        "statements": [
            "Chronischer Psychose, auch mit Residualsymptomatik",
            "Psychosomatischer Erkrankung",
            "Suchtkrankheit",
            "Anhaltender seelischer Belastung",
            "Chronischer körperlicher Erkrankung"
        ],
        "options": [
            "Nur die Aussage 1 ist richtig",
            "Nur die Aussagen 1 und 2 sind richtig",
            "Nur die Aussagen 3 und 5 sind richtig",
            "Nur die Aussagen 2, 3 und 4 sind richtig",
            "Alle Aussagen sind richtig"
        ],
        "correctIndices": [4],
        "explanation": ""
    },
    {
        "id": 9,
        "type": "Aussagenkombination",
        "text": "Als Form der Gruppentherapie finden Anwendung:",
        "statements": [
            "Rollenspiel",
            "Psychodrama",
            "Themenzentrierte Interaktion",
            "Systemische Therapie",
            "Tiefenpsychologisch orientierte Gruppe"
        ],
        "options": [
            "Nur die Aussagen 1 und 2 sind richtig",
            "Nur die Aussagen 3 und 4 sind richtig",
            "Nur die Aussagen 4 und 5 sind richtig",
            "Nur die Aussagen 1, 2 und 3 sind richtig",
            "Alle Aussagen sind richtig"
        ],
        "correctIndices": [4],
        "explanation": ""
    },
    {
        "id": 10,
        "type": "Aussagenkombination",
        "text": "Welche der folgenden Aussagen zur manischen Episode treffen zu?",
        "statements": [
            "Die gehobene Stimmung ist manchmal durch Heiterkeit, Ausgelassenheit und Ähnliches gekennzeichnet",
            "Die Antriebssteigerung kann sich in starkem Bewegungsdrang und unermüdlicher Betriebsamkeit äußern",
            "Während einer manischen Episode kann es auch zu Gereiztheit, Aggressivität und Streitsucht kommen",
            "Während einer manischen Episode sind die Patienten meist klagsam und stark ermüdet",
            "Ideenflucht ist typisch bei der Manie"
        ],
        "options": [
            "Nur die Aussagen 1 und 2 sind richtig",
            "Nur die Aussagen 3 und 4 sind richtig",
            "Nur die Aussagen 3, 4 und 5 sind richtig",
            "Nur die Aussagen 1, 2, 3 und 5 sind richtig",
            "Alle Aussagen sind richtig"
        ],
        "correctIndices": [3],
        "explanation": ""
    },
    {
        "id": 11,
        "type": "Aussagenkombination",
        "text": "Welche der folgenden Aussagen eines schizophrenen Patienten entsprechen einem Symptom 1. Ranges der Schizophrenie (nach Kurt Schneider)?",
        "statements": [
            "Unbekannte Personen zwingen mir Gedanken auf, arbeiten diese in Wellen in meinem Kopf hinein, wollen mir damit übel.",
            "Ich merke, wie man mir meine Gedanken aus dem Kopf zieht, was einen unmäßigen Druck verursacht.",
            "Ich werde von Ultraschall angepeilt, moderne Apparate verursachen in meinem Körper elektrische, in Wellen kommende Ströme.",
            "Mein Partner beeinflusst mich, er lenkt mich genau wie einen Roboter, vielleicht durch Hypnose.",
            "Seit längerer Zeit weiß ich schon, dass meine Frau mich vergiften will."
        ],
        "options": [
            "Nur die Aussagen 1 und 4 sind richtig",
            "Nur die Aussagen 1, 2 und 3 sind richtig",
            "Nur die Aussagen 2, 3 und 5 sind richtig",
            "Nur die Aussagen 1, 2, 3 und 4 sind richtig",
            "Alle Aussagen sind richtig"
        ],
        "correctIndices": [3],
        "explanation": ""
    },
    {
        "id": 12,
        "type": "Einfachauswahl",
        "text": "Hinsichtlich der Symptomatik der Schizophrenie wird in der Psychiatrie psychopathologisch zwischen Minus-Symptomatik einerseits und Plus-Symptomatik andererseits unterschieden.\nWelches der psychopathologischen Symptome wird üblicherweise zur schizophrenen Minus-Symptomatik gerechnet?",
        "statements": [],
        "options": [
            "Größenwahn",
            "Akustische Halluzinationen in Form dialogisierender Stimmen",
            "Nihilistischer Wahn",
            "Affektverflachung",
            "Akustische Halluzinationen in Form aggressiver imperativer Stimmen"
        ],
        "correctIndices": [3],
        "explanation": ""
    },
    {
        "id": 13,
        "type": "Aussagenkombination",
        "text": "Welche der folgenden Aussagen zur Demenz bei Alzheimer-Krankheit treffen zu?",
        "statements": [
            "Es ist eine primär degenerative, zerebrale Krankheit mit weitgehend unbekannter Entstehungsursache",
            "Ab dem 70. Lebensjahr beginnt die Alzheimer-Krankheit gewöhnlich abrupt und verläuft rasch fortschreitend",
            "Es können Koordinationsstörungen und Bewegungsautomatismen auftreten",
            "Die Demenz bei Alzheimer-Krankheit mit spätem Beginn (ab 65. Lebensjahr) weist meist als Hauptsymptom eine Gedächtnisstörung auf",
            "Eine Demenz bei Alzheimer-Krankheit muss gegenwärtig als irreversibel angesehen werden"
        ],
        "options": [
            "Nur die Aussagen 1 und 2 sind richtig",
            "Nur die Aussagen 2, 3 und 5 sind richtig",
            "Nur die Aussagen 1, 2, 4 und 5 sind richtig",
            "Nur die Aussagen 1, 3, 4 und 5 sind richtig",
            "Alle Aussagen sind richtig"
        ],
        "correctIndices": [3],
        "explanation": ""
    },
    {
        "id": 14,
        "type": "Aussagenkombination",
        "text": "Welche der folgenden Aussagen zum organischen Psychosyndrom nach Schädelhirntrauma treffen zu?",
        "statements": [
            "Das Syndrom folgt einem Schädeltrauma, das gewöhnlich schwer genug ist, um zu Bewusstlosigkeit zu führen",
            "Es kann zu Erschöpftheit und Störungen des geistigen Leistungsvermögens kommen",
            "Es können Depressivität und Angst auftreten",
            "Eine verminderte Belastungsfähigkeit bei emotionalen Reizen oder nach Alkoholgenuss kann nach einem Schädelhirntrauma auftreten",
            "Manche Patienten mit organischem Psychosyndrom nach einem Schädelhirntrauma entwickeln hypochondrische Züge"
        ],
        "options": [
            "Nur die Aussagen 1 und 2 sind richtig",
            "Nur die Aussagen 2 und 4 sind richtig",
            "Nur die Aussagen 1, 3 und 5 sind richtig",
            "Nur die Aussagen 2, 3, 4 und 5 sind richtig",
            "Alle Aussagen sind richtig"
        ],
        "correctIndices": [4],
        "explanation": ""
    },
    {
        "id": 15,
        "type": "Aussagenkombination",
        "text": "Welche der folgenden Aussagen treffen hinsichtlich der hypochondrischen Störung zu?",
        "statements": [
            "Hinwendung der Aufmerksamkeit des Betroffenen auf bestimmte Organe bzw. Organsysteme ist ein charakteristisches Phänomen.",
            "Normale Empfindungen werden als krankhaft und belastend interpretiert.",
            "Ein charakteristisches Phänomen ist die Weigerung, zu akzeptieren, dass den Symptomen keine körperliche Erkrankung zugrunde liegt.",
            "Bei einem Teil der Patienten besteht eine beträchtliche Depression.",
            "Die Erstmanifestation erfolgt im Regelfall nach dem 50. Lebensjahr."
        ],
        "options": [
            "Nur die Aussagen 1 und 2 sind richtig",
            "Nur die Aussagen 1 und 3 sind richtig",
            "Nur die Aussagen 2, 4 und 5 sind richtig",
            "Nur die Aussagen 1, 2, 3 und 4 sind richtig",
            "Alle Aussagen sind richtig"
        ],
        "correctIndices": [3],
        "explanation": ""
    },
    {
        "id": 16,
        "type": "Aussagenkombination",
        "text": "Zu den neurotischen Störungen zählen:",
        "statements": [
            "Agoraphobie",
            "Hysterie",
            "Manie",
            "Klaustrophobie",
            "Anorexia nervosa"
        ],
        "options": [
            "Nur die Aussagen 3 und 4 sind richtig",
            "Nur die Aussagen 3 und 5 sind richtig",
            "Nur die Aussagen 1, 2 und 4 sind richtig",
            "Nur die Aussagen 2, 4 und 5 sind richtig",
            "Alle Aussagen sind richtig"
        ],
        "correctIndices": [2],
        "explanation": ""
    },
    {
        "id": 17,
        "type": "Einfachauswahl",
        "text": "Hinsichtlich der Einrichtung einer Betreuung bei einem volljährigen Kranken nach dem Betreuungsgesetz (BtG) gilt:",
        "statements": [],
        "options": [
            "Der Betreuer wird im Regelfall vom Gesundheitsamt bestellt und eingesetzt.",
            "Das Vormundschaftsgericht kann einen Einwilligungsvorbehalt anordnen.",
            "Betreute sind stets geschäftsunfähig.",
            "Unabdingbare Folge der Einrichtung einer Betreuung ist die Entmündigung.",
            "Den Antrag auf Betreuung kann die betroffene (zu betreuende) Person laut Gesetz nicht selbst stellen."
        ],
        "correctIndices": [1],
        "explanation": ""
    },
    {
        "id": 18,
        "type": "Aussagenkombination",
        "text": "Zu den formalen Denkstörungen zählen:",
        "statements": [
            "Denkhemmung",
            "Zerfahrenheit",
            "Logorrhoe (sprachliche Enthemmungserscheinung in Form eines unkontrollierten Redeflusses)",
            "Halluzinationen",
            "Ideenflüchtigkeit"
        ],
        "options": [
            "Nur die Aussagen 1 und 4 sind richtig",
            "Nur die Aussagen 2 und 3 sind richtig",
            "Nur die Aussagen 2, 4 und 5 sind richtig",
            "Nur die Aussagen 1, 2, 3 und 5 sind richtig",
            "Alle Aussagen sind richtig"
        ],
        "correctIndices": [3],
        "explanation": ""
    },
    {
        "id": 19,
        "type": "Einfachauswahl",
        "text": "Ein an Schizophrenie erkrankter Patient ist dem Hund des Nachbarn vor der Haustür begegnet (der Hund hat dabei kurz die rechte Pfote gehoben). Der Patient berichtet daraufhin, dieser Hund habe sicherlich die Pfote gehoben, um ihn (den Patienten) vor einer drohenden Gefahr zu warnen, die im Aufzug auf ihn warte.\nEs handelt sich bei dem beschriebenen psychopathologischen Phänomen am wahrscheinlichsten um:",
        "statements": [],
        "options": [
            "Eine visuelle Halluzination",
            "Gedankenabreißen",
            "Eine Wahnwahrnehmung",
            "Eine illusionäre Verkennung",
            "Kontamination"
        ],
        "correctIndices": [2],
        "explanation": ""
    },
    {
        "id": 20,
        "type": "Einfachauswahl",
        "text": "Bei den Zönästhesien im Rahmen der so genannten zönästhetischen Schizophrenie handelt es sich in erster Linie um Folgendes:",
        "statements": [],
        "options": [
            "Manisch-depressive Stimmungslagen",
            "Bestimmte Leibgefühlsstörungen",
            "Komplexe visuelle Halluzinationen",
            "Phänomene der Gedankenbeeinflussung (z. B. Gedankenentzug, Gedankeneingebung)",
            "Chronische Störungen des Affektes (z. B. Affektverarmung, sozialer Rückzug)"
        ],
        "correctIndices": [1],
        "explanation": ""
    },
    {
        "id": 21,
        "type": "Aussagenkombination",
        "text": "Für die Manie ist charakteristisch:",
        "statements": [
            "Schlaflosigkeit",
            "Ideenflucht",
            "Gedankenabreißen",
            "Selbstüberschätzung",
            "Psychomotorische Enthemmung"
        ],
        "options": [
            "Nur die Aussagen 1 und 2 sind richtig",
            "Nur die Aussagen 2 und 3 sind richtig",
            "Nur die Aussagen 1, 2, 4 und 5 sind richtig",
            "Nur die Aussagen 1, 3, 4 und 5 sind richtig",
            "Alle Aussagen sind richtig"
        ],
        "correctIndices": [2],
        "explanation": ""
    },
    {
        "id": 22,
        "type": "Einfachauswahl",
        "text": "Hinsichtlich der Panikstörung gilt:",
        "statements": [],
        "options": [
            "Panikattacken treten laut Definition nur in bestimmten örtlichen Situationen (z. B. freie Plätze, größere Menschenansammlungen, Theater, U-Bahn) auf.",
            "Die Panikattacke geht häufig einher mit einer Angst vor Kontrollverlust.",
            "Im Regelfall ist zu Beginn der Behandlung die Aufnahme auf eine geschlossene Station unvermeidlich, da es anderenfalls zumeist zu Suizidhandlungen kommt.",
            "Im Allgemeinen ist eine Langzeittherapie mit Benzodiazepinen erforderlich.",
            "Bei der psychotherapeutischen Behandlung kommt eine Verhaltenstherapie nicht in Betracht."
        ],
        "correctIndices": [1],
        "explanation": ""
    },
    {
        "id": 23,
        "type": "Einfachauswahl",
        "text": "Für die dissoziale Persönlichkeitsstörung ist in erster Linie das folgende der genannten Merkmale kennzeichnend:",
        "statements": [],
        "options": [
            "Allgemeine Schwäche",
            "Ängstliches und gewissenhaftes Verhalten",
            "Erhöhte Suggestibilität",
            "Mangel an Empathie",
            "Angst vor Verlassenwerden"
        ],
        "correctIndices": [3],
        "explanation": ""
    },
    {
        "id": 24,
        "type": "Einfachauswahl",
        "text": "Bei Morphinabhängigen im Morphinrausch ist in erster Linie folgendes der genannten Phänomene charakteristisch:",
        "statements": [],
        "options": [
            "Sehr enge Pupillen",
            "Kataplexie (kurzdauernder Spannungsverlust von Muskeln)",
            "Hypersexualität",
            "Kontrollwahn",
            "Größenwahn"
        ],
        "correctIndices": [0],
        "explanation": ""
    },
    {
        "id": 25,
        "type": "Einfachauswahl",
        "text": "Welche der folgenden Aussagen über Abwehrmechanismen im Sinne der Psychoanalyse trifft zu?",
        "statements": [],
        "options": [
            "Projektion bedeutet Verlegung eigener abgewehrter Wünsche in eine andere Person.",
            "Reaktionsbildung bedeutet Abwehr der Realität von traumatisierenden Wahrnehmungen.",
            "Verdrängung bedeutet Verlagerung einer Emotion von einem bedrohlichen auf ein ungefährliches Objekt.",
            "Rationalisierung bedeutet künstliches Abtrennen der Gefühle vom gedanklichen Inhalt.",
            "Verleugnung bedeutet unbewusste Aktivierung eines entgegengesetzten Impulses."
        ],
        "correctIndices": [0],
        "explanation": ""
    },
    {
        "id": 26,
        "type": "Einfachauswahl",
        "text": "Ein Verhaltenstest bei Zwangsstörungen dient vor allem dazu,",
        "statements": [],
        "options": [
            "Aufschluss über Neutralisierungsstrategien zu gewinnen",
            "positive Verstärkung zu erfahren",
            "stereotype Rituale zu unterbrechen",
            "Verleugnung zu durchbrechen",
            "Widerstand in der Therapie zu thematisieren"
        ],
        "correctIndices": [0],
        "explanation": ""
    },
    {
        "id": 27,
        "type": "Aussagenkombination",
        "text": "Welche der folgenden Aussagen zur Behandlung mit Benzodiazepinen ist (sind) richtig?",
        "statements": [
            "Der therapeutische Nutzen bei Angststörungen ist nachgewiesen",
            "Die Verträglichkeit ist im allgemeinen gut",
            "Bei langfristiger Anwendung kann es zu Vergesslichkeit, Appetitlosigkeit, Verwirrtheitszuständen kommen",
            "Sind die heute bevorzugten Schlafmittel",
            "Eine Abhängigkeit tritt bei niedriger Dosierung nur selten auf"
        ],
        "options": [
            "Nur die Aussage 1 ist richtig",
            "Nur die Aussagen 2 und 3 sind richtig",
            "Nur die Aussagen 1, 2 und 4 sind richtig",
            "Nur die Aussagen 1, 2, 3 und 4 sind richtig",
            "Alle Aussagen sind richtig"
        ],
        "correctIndices": [3],
        "explanation": ""
    },
    {
        "id": 28,
        "type": "Aussagenkombination",
        "text": "Welche charakteristischen Symptome zeigen Patienten mit einer Borderline-Störung?",
        "statements": [
            "Emotionale Instabilität",
            "Unbeständige Beziehungen",
            "Häufig Selbstmordgedanken und -versuche",
            "Dementielle Symptome",
            "Chronisches Gefühl der Leere"
        ],
        "options": [
            "Nur die Aussage 1 ist richtig",
            "Nur die Aussagen 1 und 4 sind richtig",
            "Nur die Aussagen 2 und 3 sind richtig",
            "Nur die Aussagen 1, 2, 3 und 5 sind richtig",
            "Alle Aussagen sind richtig"
        ],
        "correctIndices": [3],
        "explanation": ""
    }
]

def main():
    with open(EXAMS_PATH, "r", encoding="utf-8") as f:
        exams = json.load(f)

    for exam in exams:
        if exam["id"] == "2002-october":
            exam["questions"] = QUESTIONS_2002_OCT
            print(f"Replaced 2002-october: {len(QUESTIONS_2002_OCT)} questions")
            break
    else:
        print("ERROR: 2002-october not found!")
        return

    with open(EXAMS_PATH, "w", encoding="utf-8") as f:
        json.dump(exams, f, ensure_ascii=False, indent=2)
    print("Saved.")

if __name__ == "__main__":
    main()
