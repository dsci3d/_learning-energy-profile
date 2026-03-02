# Learning Energy Profile — Projektregeln

## Instrument-Integrität

**Instrument-Konstanten nicht verändern**: 88 Items, 27 Reverse-Items, 6 Dimensionen (Aufmerksamkeitsarchitektur, Sensorische Verarbeitung, Soziale Energetik, Exekutive Funktionen, Motivationsarchitektur, Autonome Regulation), 2 Zusatzindizes (Chronotyp, Vermeidungsorientierung). Jede Änderung an Item-Zuordnung, Reverse-Coding oder Scoring-Formel `(mean-1)/4*100` erfordert explizite Freigabe.

**Klassifikationsgrenzen fix**: niedrig < 40, mittel 40–74, hoch >= 75. Keine Anpassung ohne wissenschaftliche Begründung.

**Item-Konsistenz-Assertions beibehalten**: Die bestehenden Assertions in `auswertung.py` (Gesamtzahl Items, Reverse-Items pro Dimension) sind Sicherheitsnetze — nicht entfernen oder abschwächen.

## Wissenschaftliche Sorgfalt

**Prototyp-Status transparent halten**: Keine Formulierungen, die Validierung oder Normierung suggerieren. Das Instrument hat explorativen Charakter — das muss in allen Outputs (Bericht, HTML-Report, README) erkennbar bleiben.

**Keine diagnostischen Aussagen**: Weder Code noch Textausgaben dürfen klinische Diagnosen, pathologisierende Labels oder Vergleiche mit klinischen Populationen enthalten.

## Code-Konventionen

**Deutsche Namensgebung beibehalten**: Variablen, Docstrings und Kommentare auf Deutsch (bewusste Designentscheidung laut README). Englisch nur für Python-Builtins und Library-Interfaces.

**Ausgabe-Struktur**: Timestamp-Unterordner (`YYYY-MM-DD_HH-MM-SS/`) für alle generierten Dateien. Keine flachen Outputs im Projektstamm.

## Datenformat

**CSV-Input-Format stabil**: Spalten `item_code,rating`. Zusätzliche Spalten werden ignoriert, aber die Pflichtfelder dürfen nicht umbenannt werden. Kompatibilität mit `questionnaire_template.csv`.
