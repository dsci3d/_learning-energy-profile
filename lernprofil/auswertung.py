#!/usr/bin/env python3
"""
Scoring-Skript für den Fragebogen zur Lernenergie-Architektur (Version 0.2.1).

- Erwartet eine CSV-Datei mit mindestens den Spalten: item_code, rating
- Zusätzliche Spalten (z.B. item_text, dimension) werden ignoriert
- Gibt ein JSON-Profil mit 6 Dimensions-Scores (0–100) auf stdout oder in eine Datei aus.
- Generiert optional ASCII-Visualisierungen im Text-Report
- Alle Berechnungsschritte sind deterministisch und transparent.

Neu in Version 0.2.1:
- Flexible CSV-Verarbeitung (ignoriert zusätzliche Spalten)
- Strengere Type- und Range-Validierung
- Verbesserte Fehlerdiagnostik
- Robustere Chronotyp-Berechnung
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Any, Optional

VERSION = "0.2.1"

# ---------------------------------------------------------------------------
# Konstanten für Response-Quality
# ---------------------------------------------------------------------------

QUALITY_WARN_STRAIGHT = "Nur 1-2 verschiedene Antworten verwendet"
QUALITY_WARN_LOW_VAR = "Sehr geringe Antwortvariation"

# ---------------------------------------------------------------------------
# Domänenmodell
# ---------------------------------------------------------------------------

DIMENSION_LABELS: Dict[str, str] = {
    "attention": "Aufmerksamkeitsarchitektur",
    "sensory": "Sensorische Verarbeitung",
    "social": "Soziale Energetik",
    "executive": "Exekutive Funktionen & Strukturbedürfnis",
    "motivation": "Motivationsarchitektur",
    "regulation": "Autonome Regulation / Stress & Vigilanz",
}


@dataclass(frozen=True)
class ItemDefinition:
    code: str
    dimension_code: str
    include_in_main_scale: bool
    reverse_scored: bool
    facet: str = ""


def _i(code: str, dim: str, facet: str = "", include: bool = True, reverse: bool = False) -> ItemDefinition:
    return ItemDefinition(
        code=code,
        dimension_code=dim,
        facet=facet,
        include_in_main_scale=include,
        reverse_scored=reverse
    )


# Item-Definitionen für Version 0.2.x (88 Items, konsistent mit Fragebogen)
ITEM_DEFINITIONS: Dict[str, ItemDefinition] = {
    # Aufmerksamkeitsarchitektur (10 Hauptskala + 6 Chronotyp)
    "A1": _i("A1", "attention", "Fokusdauer"),
    "A2": _i("A2", "attention", "Distraktibilität", reverse=True),
    "A3": _i("A3", "attention", "Wiedereinstieg"),
    "A4": _i("A4", "attention", "Arbeitsstil_Sequenziell"),
    "A5": _i("A5", "attention", "Task_Switching_Energie", reverse=True),
    "A6": _i("A6", "attention", "Pausenplanung"),
    "A7": _i("A7", "attention", "Flow_Neigung"),
    "A8": _i("A8", "attention", "Chronotyp_Morgen", include=False),
    "A9": _i("A9", "attention", "Chronotyp_Abend", include=False),
    "A10": _i("A10", "attention", "Mikropausenbedarf", reverse=True),
    "A11": _i("A11", "attention", "Selbstmonitoring_Konzentration"),
    "A12": _i("A12", "attention", "Fokus_in_Stresssituationen"),
    "A13": _i("A13", "attention", "Chronotyp_Schlafzeit_Wochentag", include=False),
    "A14": _i("A14", "attention", "Chronotyp_Aufwachzeit_Wochentag", include=False),
    "A15": _i("A15", "attention", "Chronotyp_Leistungshoch_vormittag", include=False),
    "A16": _i("A16", "attention", "Chronotyp_Leistungshoch_abend", include=False),

    # Sensorische Verarbeitung (13 Items)
    "S1": _i("S1", "sensory", "Lärmempfindlichkeit"),
    "S2": _i("S2", "sensory", "Lichtempfindlichkeit"),
    "S3": _i("S3", "sensory", "Detailwahrnehmung"),
    "S4": _i("S4", "sensory", "Ordnung_Umgebung"),
    "S5": _i("S5", "sensory", "Erholung_nach_Reiz"),
    "S6": _i("S6", "sensory", "Sensation_Seeking", reverse=True),
    "S7": _i("S7", "sensory", "Musik_Positive_Wirkung", reverse=True),
    "S8": _i("S8", "sensory", "Musik_Ablenkung"),
    "S9": _i("S9", "sensory", "Coping_Strategien_Reize"),
    "S10": _i("S10", "sensory", "Neue_Reize_Positive_Wirkung", reverse=True),
    "S11": _i("S11", "sensory", "Multisensory_Ermüdung"),
    "S12": _i("S12", "sensory", "Umgebungsgestaltung_aktiv"),
    "S13": _i("S13", "sensory", "Multisensorische_Lernpräferenz"),

    # Soziale Energetik (13 Items)
    "SO1": _i("SO1", "social", "Soziale_Aufladung"),
    "SO2": _i("SO2", "social", "Alleinlernen_Präferenz", reverse=True),
    "SO3": _i("SO3", "social", "Gruppenarbeit_Energieminus", reverse=True),
    "SO4": _i("SO4", "social", "Diskussion_Nutzen"),
    "SO5": _i("SO5", "social", "Erholung_Alleinsein", reverse=True),
    "SO6": _i("SO6", "social", "Kleine_vertraute_Gruppen"),
    "SO7": _i("SO7", "social", "Zurückhaltung_große_Gruppen", reverse=True),
    "SO8": _i("SO8", "social", "Live_Sitzungen_Motivation"),
    "SO9": _i("SO9", "social", "Asynchron_Präferenz", reverse=True),
    "SO10": _i("SO10", "social", "Erklären_als_Energiequelle"),
    "SO11": _i("SO11", "social", "Soziale_Planung"),
    "SO12": _i("SO12", "social", "Soziale_Unterstützung_Nutzen"),
    "SO13": _i("SO13", "social", "Isolation_bei_Überforderung", reverse=True),

    # Exekutive Funktionen & Strukturbedürfnis (16 Items)
    "E1": _i("E1", "executive", "Planung_Teilschritte"),
    "E2": _i("E2", "executive", "Strukturbedarf_Start", reverse=True),
    "E3": _i("E3", "executive", "Überblick_bei_Vielzahl_Aufgaben", reverse=True),
    "E4": _i("E4", "executive", "Nutzung_Organisationstools"),
    "E5": _i("E5", "executive", "Vorliebe_vorgegebene_Struktur"),
    "E6": _i("E6", "executive", "Flexible_Nutzung_von_Plänen"),
    "E7": _i("E7", "executive", "Spontane_Improvisation", reverse=True),
    "E8": _i("E8", "executive", "Durchhaltevermögen"),
    "E9": _i("E9", "executive", "Re-Organisation_bei_Unterbrechungen"),
    "E10": _i("E10", "executive", "Kriterienbedarf_Qualität"),
    "E11": _i("E11", "executive", "Detailverlorenheit", reverse=True),
    "E12": _i("E12", "executive", "Deadline_Koordination"),
    "E13": _i("E13", "executive", "Arbeitsgedächtnis_Multitasking", reverse=True),
    "E14": _i("E14", "executive", "Instruktionskomplexität", reverse=True),
    "E15": _i("E15", "executive", "Lernprozess_Monitoring"),
    "E16": _i("E16", "executive", "Schwierigkeitseinschätzung"),

    # Motivationsarchitektur (16 Hauptskala + 2 Vermeidung)
    "M1": _i("M1", "motivation", "Intrinsische_Motivation"),
    "M2": _i("M2", "motivation", "Vermeidungsorientierung", include=False),
    "M3": _i("M3", "motivation", "Zielorientierung"),
    "M4": _i("M4", "motivation", "Fortschrittsanzeige"),
    "M5": _i("M5", "motivation", "Feedbackbedarf"),
    "M6": _i("M6", "motivation", "Feedbackdetailgrad"),
    "M7": _i("M7", "motivation", "Feedbacktonalität_Positive"),
    "M8": _i("M8", "motivation", "Feedbacktonalität_Kritisch"),
    "M9": _i("M9", "motivation", "Prokrastination", include=False),
    "M10": _i("M10", "motivation", "Interesse_Flow"),
    "M11": _i("M11", "motivation", "Extrinsische_Belohnung"),
    "M12": _i("M12", "motivation", "Persistenz_ohne_Feedback"),
    "M13": _i("M13", "motivation", "Intrinsische_Motivation_reversed", reverse=True),
    "M14": _i("M14", "motivation", "Feedbackabhängigkeit_reversed", reverse=True),
    "M15": _i("M15", "motivation", "Zielorientierung_reversed", reverse=True),
    "M16": _i("M16", "motivation", "Extrinsische_Abhängigkeit", reverse=True),
    "M17": _i("M17", "motivation", "Wenn_Dann_Planung"),
    "M18": _i("M18", "motivation", "Commitment_Strategien"),

    # Autonome Regulation / Stress & Vigilanz (12 Items)
    "R1": _i("R1", "regulation", "Subjektives_Stressniveau", reverse=True),
    "R2": _i("R2", "regulation", "Abschalten_Abends", reverse=True),
    "R3": _i("R3", "regulation", "Erschöpfung_nach_Lernen", reverse=True),
    "R4": _i("R4", "regulation", "Stress_durch_Unvorhergesehenes", reverse=True),
    "R5": _i("R5", "regulation", "Wahrnehmung_körperlicher_Stresszeichen"),
    "R6": _i("R6", "regulation", "Kurzpausen_Regulation"),
    "R7": _i("R7", "regulation", "Abendroutinen_Regeneration"),
    "R8": _i("R8", "regulation", "Druck_als_Leistungsfaktor"),
    "R9": _i("R9", "regulation", "Schlaf_in_Stressphasen", reverse=True),
    "R10": _i("R10", "regulation", "Belastungsausgleich"),
    "R11": _i("R11", "regulation", "Prioritätensetzung_in_Stress"),
    "R12": _i("R12", "regulation", "Belastungsgrenze_Wahrnehmung"),
}


LIKERT_MIN = 1
LIKERT_MAX = 5

# Instrument-Konsistenzprüfung beim Import
MAIN_ITEMS_DEFINED = [i for i in ITEM_DEFINITIONS.values() if i.include_in_main_scale]
INDEX_ITEMS_DEFINED = [i for i in ITEM_DEFINITIONS.values() if not i.include_in_main_scale]

assert len(ITEM_DEFINITIONS) == 88, "Instrument muss genau 88 Items haben"
assert len(MAIN_ITEMS_DEFINED) == 80, "Hauptskalen müssen genau 80 Items haben"
assert len(INDEX_ITEMS_DEFINED) == 8, "Zusatzindizes müssen genau 8 Items haben"
assert sum(1 for i in MAIN_ITEMS_DEFINED if i.reverse_scored) == 27, "Hauptskalen müssen genau 27 Reverse-Items haben"


# ---------------------------------------------------------------------------
# Kernlogik
# ---------------------------------------------------------------------------

def reverse_likert(value: int) -> int:
    """
    Invertiert einen Likert-Wert (1..5) zu seinem Gegenwert.
    1 -> 5, 2 -> 4, 3 -> 3, 4 -> 2, 5 -> 1
    """
    if not isinstance(value, int):
        raise TypeError(f"Likert-Wert muss int sein, erhalten: {type(value).__name__}")
    if not (LIKERT_MIN <= value <= LIKERT_MAX):
        raise ValueError(f"Likert-Wert muss zwischen {LIKERT_MIN} und {LIKERT_MAX} liegen, erhalten: {value}")
    return LIKERT_MIN + LIKERT_MAX - value


def classify_score(score: float) -> str:
    """
    Ordnet einen 0–100-Score grob in niedrig/mittel/hoch ein.
    """
    if not isinstance(score, (int, float)):
        raise TypeError(f"Score muss numerisch sein, erhalten: {type(score).__name__}")
    if not (0.0 <= score <= 100.0):
        raise ValueError(f"Score muss zwischen 0 und 100 liegen, erhalten: {score}")
    if score < 40:
        return "niedrig"
    if score < 75:
        return "mittel"
    return "hoch"


def check_response_quality(ratings: Dict[str, int]) -> Dict[str, Any]:
    """
    Berechnet Qualitätsindikatoren für die Antworten zur Erkennung von
    Careless Responding (unaufmerksames Antworten).
    """
    values = list(ratings.values())
    
    # Straight-Lining Detection (nur 1-2 verschiedene Antworten)
    unique_values = len(set(values))
    
    # Varianz berechnen
    mean_val = sum(values) / len(values)
    variance = sum((v - mean_val) ** 2 for v in values) / len(values)
    
    # Quality-Flag setzen
    quality_warnings = []
    if unique_values <= 2:
        quality_warnings.append(QUALITY_WARN_STRAIGHT)
    if variance < 0.5:
        quality_warnings.append(QUALITY_WARN_LOW_VAR)
    
    quality_flag = "ok" if not quality_warnings else "check"
    
    return {
        "num_unique_responses": unique_values,
        "response_variance": round(variance, 2),
        "mean_response": round(mean_val, 2),
        "quality_flag": quality_flag,
        "warnings": quality_warnings if quality_warnings else None
    }


def validate_ratings(ratings: Dict[str, int]) -> None:
    """
    Validiert ein Ratings-Dict auf Vollständigkeit und korrekte Werte.
    Wirft ValueError oder TypeError bei Problemen.
    """
    missing = set(ITEM_DEFINITIONS) - set(ratings)
    extra = set(ratings) - set(ITEM_DEFINITIONS)
    
    if missing:
        raise ValueError(f"Fehlende Items: {', '.join(sorted(missing))}")
    if extra:
        raise ValueError(f"Unbekannte Items: {', '.join(sorted(extra))}")
    
    for code, value in ratings.items():
        if not isinstance(value, int):
            raise TypeError(f"Rating für {code} ist kein int: {value!r}")
        if not (LIKERT_MIN <= value <= LIKERT_MAX):
            raise ValueError(f"Rating für {code} außerhalb des erlaubten Bereichs {LIKERT_MIN}-{LIKERT_MAX}: {value}")


def load_ratings_from_csv(path: Path) -> Dict[str, int]:
    """
    Liest eine individuelle Antwortdatei im Format:
        item_code,rating[,weitere_spalten...]
        A1,4[,...]
        A2,3[,...]
        ...

    Zusätzliche Spalten werden ignoriert. Es wird genau eine Person pro Datei erwartet.
    """
    ratings: Dict[str, int] = {}
    
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        
        # Flexible Spaltenprüfung: Mindestens item_code und rating müssen vorhanden sein
        required_fields = {"item_code", "rating"}
        if not reader.fieldnames or not required_fields.issubset(reader.fieldnames):
            raise ValueError(
                f"CSV muss mindestens die Spalten {required_fields} besitzen, "
                f"gefunden: {reader.fieldnames}"
            )
        
        for row_num, row in enumerate(reader, start=2):  # Start bei 2 (nach Header)
            code = row["item_code"].strip()
            
            if not code:  # Leere Zeile überspringen
                continue
            
            if code in ratings:
                raise ValueError(f"Doppelter Eintrag für Item {code} in Zeile {row_num} von {path}")
            
            if code not in ITEM_DEFINITIONS:
                raise ValueError(f"Unbekannter item_code '{code}' in Zeile {row_num} von {path}")
            
            raw_value_str = row["rating"].strip()
            try:
                raw_value = int(raw_value_str)
            except ValueError as exc:
                raise ValueError(
                    f"Ungültiger Wert für rating bei Item {code} in Zeile {row_num}: '{raw_value_str}'"
                ) from exc
            
            if not (LIKERT_MIN <= raw_value <= LIKERT_MAX):
                raise ValueError(
                    f"rating bei Item {code} in Zeile {row_num} muss zwischen "
                    f"{LIKERT_MIN} und {LIKERT_MAX} liegen, erhalten: {raw_value}"
                )
            
            ratings[code] = raw_value

    # Prüfen, ob alle Items vorhanden sind
    missing = sorted(set(ITEM_DEFINITIONS.keys()) - set(ratings.keys()))
    if missing:
        raise ValueError(
            f"Die folgenden Items fehlen in der Datei {path}: {', '.join(missing)}"
        )
    
    # Finale Validierung durch zentrale validate_ratings
    validate_ratings(ratings)

    return ratings


def compute_dimension_scores(ratings: Dict[str, int]) -> Dict[str, Dict[str, Any]]:
    """
    Berechnet für jede der 6 Hauptdimensionen einen Score (0–100) und die grobe Kategorie.
    """
    dim_values: Dict[str, List[int]] = {code: [] for code in DIMENSION_LABELS.keys()}
    dim_items: Dict[str, List[str]] = {code: [] for code in DIMENSION_LABELS.keys()}
    dim_raw_values: Dict[str, List[int]] = {code: [] for code in DIMENSION_LABELS.keys()}

    for code, value in ratings.items():
        item_def = ITEM_DEFINITIONS[code]
        if not item_def.include_in_main_scale:
            continue
        dim_code = item_def.dimension_code
        dim_items[dim_code].append(code)
        dim_raw_values[dim_code].append(value)
        final_val = reverse_likert(value) if item_def.reverse_scored else value
        dim_values[dim_code].append(final_val)

    results: Dict[str, Dict[str, Any]] = {}
    for dim_code, values in dim_values.items():
        label = DIMENSION_LABELS[dim_code]
        
        # Sicherheitsprüfung: Jede Dimension muss Items haben
        if not values:
            raise RuntimeError(f"Keine Items für Dimension '{dim_code}' ({label}) gefunden")
        
        mean_val = sum(values) / len(values)
        raw_mean = sum(dim_raw_values[dim_code]) / len(dim_raw_values[dim_code])
        score = (mean_val - LIKERT_MIN) / (LIKERT_MAX - LIKERT_MIN) * 100.0
        level = classify_score(score)
        
        # Anzahl Reverse-Items zählen
        num_reversed = sum(1 for code in dim_items[dim_code] 
                          if ITEM_DEFINITIONS[code].reverse_scored)
        
        results[dim_code] = {
            "label": label,
            "score": round(score, 1),
            "level": level,
            "num_items": len(values),
            "num_reversed": num_reversed,
            "raw_mean": round(raw_mean, 2),
            "items": sorted(dim_items[dim_code]),
        }

    return results


def compute_chronotype_index(ratings: Dict[str, int]) -> Dict[str, Any]:
    """
    Berechnet einen reliablen Chronotyp-Index aus 6 Items (Version 0.2.x).
    
    Morgen-Items: A8, A13, A14, A15 (hoher Wert = Morgentyp)
    Abend-Items: A9, A16 (hoher Wert = Abendtyp)
    
    Alle 6 Items müssen vorhanden sein (wurde bereits in validate_ratings geprüft).
    """
    morning_items = ["A8", "A13", "A14", "A15"]
    evening_items = ["A9", "A16"]
    
    # Harte Validierung: Alle Items müssen vorhanden sein
    try:
        morning_vals = [ratings[code] for code in morning_items]
        evening_vals = [ratings[code] for code in evening_items]
    except KeyError as e:
        raise ValueError(f"Fehlender Chronotyp-Wert für Item {e.args[0]}")
    
    # Scores berechnen
    morning_score = sum(morning_vals) / len(morning_vals)
    evening_score = sum(evening_vals) / len(evening_vals)
    
    morning_score_100 = (morning_score - LIKERT_MIN) / (LIKERT_MAX - LIKERT_MIN) * 100.0
    evening_score_100 = (evening_score - LIKERT_MIN) / (LIKERT_MAX - LIKERT_MIN) * 100.0
    
    # Balance-Score: Differenz zwischen Abend und Morgen
    balance = evening_score - morning_score
    
    # Interpretation
    if balance < -0.8:
        interpretation = "Deutlicher Morgentyp"
    elif balance < -0.4:
        interpretation = "Leichter Morgentyp"
    elif balance < 0.4:
        interpretation = "Neutraler/intermediärer Typ"
    elif balance < 0.8:
        interpretation = "Leichter Abendtyp"
    else:
        interpretation = "Deutlicher Abendtyp"
    
    return {
        "label": "Chronotyp-Profil",
        "morning_tendency": round(morning_score_100, 1),
        "evening_tendency": round(evening_score_100, 1),
        "balance_score": round(balance, 2),
        "interpretation": interpretation,
        "num_items": len(morning_items) + len(evening_items),
        "items": morning_items + evening_items,
    }


def compute_additional_indices(ratings: Dict[str, int]) -> Dict[str, Dict[str, Any]]:
    """
    Berechnet Zusatzindizes (Vermeidungsorientierung, Chronotyp).
    """
    indices: Dict[str, Dict[str, Any]] = {}

    # Vermeidungsorientierung: M2, M9
    avoid_items = ["M2", "M9"]
    if all(code in ratings for code in avoid_items):
        vals = [ratings[code] for code in avoid_items]
        mean_val = sum(vals) / len(vals)
        score = (mean_val - LIKERT_MIN) / (LIKERT_MAX - LIKERT_MIN) * 100.0
        indices["motivation_avoidance"] = {
            "label": "Vermeidungsorientierung (Motivation)",
            "score": round(score, 1),
            "level": classify_score(score),
            "num_items": len(vals),
            "raw_mean": round(mean_val, 2),
            "items": avoid_items,
        }

    # Chronotyp (erweitert in Version 0.2)
    try:
        indices["chronotype"] = compute_chronotype_index(ratings)
    except ValueError as e:
        # Das sollte nicht passieren, da validate_ratings bereits alle Items prüft
        raise RuntimeError(f"Interner Konsistenzfehler beim Chronotyp-Index: {e}") from e

    return indices


def compute_profile(ratings: Dict[str, int], profile_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Erzeugt die komplette JSON-Struktur für ein Profil (Version 0.2.1).
    """
    # Strikte Validierung
    validate_ratings(ratings)
    
    dimensions = compute_dimension_scores(ratings)
    additional = compute_additional_indices(ratings)
    quality = check_response_quality(ratings)
    
    profile: Dict[str, Any] = {
        "id": profile_id,
        "dimensions": dimensions,
        "additional_indices": additional,
        "response_quality": quality,
        "meta": {
            "version": VERSION,
            "num_items_instrument": len(ITEM_DEFINITIONS),
            "num_items_answered": len(ratings),
            "num_items_main_scales": sum(d["num_items"] for d in dimensions.values()),
            "num_items_additional": len(INDEX_ITEMS_DEFINED),
            "num_reversed_total": sum(d["num_reversed"] for d in dimensions.values()),
            "likert_min": LIKERT_MIN,
            "likert_max": LIKERT_MAX,
            "score_min": 0,
            "score_max": 100,
        },
    }
    return profile


# ---------------------------------------------------------------------------
# Visualisierung & Report
# ---------------------------------------------------------------------------

def generate_text_report(profile: Dict[str, Any]) -> str:
    """
    Erzeugt einen textuellen Report mit ASCII-Balkendiagrammen.
    """
    lines = []
    lines.append("=" * 80)
    lines.append(f"LERNENERGIE-PROFIL (Version {profile['meta']['version']})")
    lines.append(f"Profil-ID: {profile['id']}")
    lines.append("=" * 80)
    lines.append("")
    
    # Response Quality
    quality = profile.get("response_quality", {})
    lines.append("ANTWORTQUALITÄT")
    lines.append("-" * 80)
    lines.append(f"Anzahl verschiedener Antworten: {quality.get('num_unique_responses', 'N/A')}")
    lines.append(f"Antwortvariation: {quality.get('response_variance', 'N/A')}")
    lines.append(f"Durchschnittliche Antwort: {quality.get('mean_response', 'N/A')}")
    lines.append(f"Qualitätsflag: {quality.get('quality_flag', 'N/A')}")
    if quality.get('warnings'):
        lines.append(f"⚠️  Warnungen: {'; '.join(quality['warnings'])}")
    lines.append("")
    
    # Dimensionen
    lines.append("HAUPTDIMENSIONEN (0-100 Skala)")
    lines.append("-" * 80)
    
    dimensions = profile["dimensions"]
    max_label_len = max(len(d["label"]) for d in dimensions.values())
    
    # Definierte Reihenfolge der Dimensionen
    dim_order = ["attention", "sensory", "social", "executive", "motivation", "regulation"]
    
    for dim_code in dim_order:
        dim = dimensions.get(dim_code)
        if dim is None:
            continue  # Defensive: falls Dimension fehlt
        
        label = dim["label"]
        score = dim["score"]
        level = dim["level"]
        num_items = dim["num_items"]
        num_reversed = dim["num_reversed"]
        
        # ASCII-Balken
        bar_length = int(score / 2)  # 0-50 Zeichen
        bar = "█" * bar_length
        
        lines.append(f"{label:<{max_label_len}} │ {bar} {score:5.1f} ({level})")
        lines.append(f"{'':<{max_label_len}} │ Items: {num_items} (davon {num_reversed} reverse)")
        lines.append("")
    
    # Zusatzindizes
    lines.append("ZUSATZINDIZES")
    lines.append("-" * 80)
    
    additional = profile.get("additional_indices", {})
    
    # Vermeidungsorientierung
    if "motivation_avoidance" in additional:
        avoid = additional["motivation_avoidance"]
        lines.append(f"{avoid['label']}: {avoid['score']:.1f} ({avoid['level']})")
        lines.append("")
    
    # Chronotyp
    if "chronotype" in additional:
        chrono = additional["chronotype"]
        lines.append(f"{chrono['label']}:")
        lines.append(f"  Morgentendenz: {chrono['morning_tendency']:.1f}")
        lines.append(f"  Abendtendenz: {chrono['evening_tendency']:.1f}")
        lines.append(f"  Balance-Score: {chrono['balance_score']:.2f}")
        lines.append(f"  Interpretation: {chrono['interpretation']}")
        lines.append("")
    
    lines.append("=" * 80)
    lines.append("NÄCHSTE SCHRITTE")
    lines.append("-" * 80)
    lines.append("1. Dieses Profil mit einer KI analysieren lassen (datenschutzkonform)")
    lines.append("2. Konkrete Lernstrategien auf Basis des Profils entwickeln")
    lines.append("3. Profil bei Bedarf mit Lehrenden oder Lerncoaches besprechen")
    lines.append("=" * 80)
    
    # Instrument-Metadaten für Transparenz
    meta = profile.get("meta", {})
    lines.append("")
    lines.append("INSTRUMENT-METADATEN")
    lines.append("-" * 80)
    lines.append(f"Instrument-Items: {meta.get('num_items_instrument', 'N/A')}")
    lines.append(f"Beantwortete Items: {meta.get('num_items_answered', 'N/A')}")
    lines.append(f"Hauptskalen-Items: {meta.get('num_items_main_scales', 'N/A')}")
    lines.append(f"Reverse-Items (Hauptskalen): {meta.get('num_reversed_total', 'N/A')}")
    lines.append(f"Zusatzindex-Items: {meta.get('num_items_additional', 'N/A')}")
    lines.append(f"Likert-Skala: {meta.get('likert_min', 'N/A')}-{meta.get('likert_max', 'N/A')}")
    lines.append(f"Score-Bereich: {meta.get('score_min', 'N/A')}-{meta.get('score_max', 'N/A')}")
    lines.append("=" * 80)
    
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Berechne ein Lernenergie-Profil (6 Dimensionen + Zusatzindizes) "
            "auf Basis einer individuellen Antwortdatei im CSV-Format (Version 0.2.1)."
        )
    )
    parser.add_argument(
        "input_csv",
        type=Path,
        help="Pfad zur CSV-Datei mit mindestens den Spalten item_code,rating (genau eine Person).",
    )
    parser.add_argument(
        "--id",
        dest="profile_id",
        help="Optionale Profil-ID (Standard: Dateiname ohne Endung).",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Optionaler Pfad für die JSON-Ausgabe (Standard: Ausgabe auf stdout).",
    )
    parser.add_argument(
        "--report",
        "-r",
        type=Path,
        help="Optionaler Pfad für Text-Report (ASCII-Visualisierung).",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Keine Text-Ausgabe auf stdout (nur Datei-Ausgabe).",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> None:
    args = parse_args(argv)
    input_path: Path = args.input_csv

    if not input_path.exists():
        print(f"❌ Eingabedatei nicht gefunden: {input_path}", file=sys.stderr)
        raise SystemExit(1)

    profile_id = args.profile_id or input_path.stem

    # Profil berechnen mit verbesserter Fehlerbehandlung
    try:
        ratings = load_ratings_from_csv(input_path)
        profile = compute_profile(ratings, profile_id=profile_id)
    except (ValueError, TypeError) as exc:
        print(f"❌ Fehler bei der Auswertung: {exc}", file=sys.stderr)
        raise SystemExit(1)
    except Exception as exc:
        print(f"❌ Unerwarteter Fehler: {exc}", file=sys.stderr)
        raise SystemExit(2)
    
    # JSON-Ausgabe
    json_str = json.dumps(profile, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(json_str, encoding="utf-8")
        if not args.quiet:
            print(f"✓ JSON-Profil gespeichert: {args.output}")
    elif not args.quiet:
        print(json_str)
    
    # Text-Report
    if args.report or not args.output:
        report_text = generate_text_report(profile)
        if args.report:
            args.report.write_text(report_text, encoding="utf-8")
            if not args.quiet:
                print(f"✓ Text-Report gespeichert: {args.report}")
        elif not args.quiet and not args.output:
            print("\n" + report_text)


if __name__ == "__main__":
    main()