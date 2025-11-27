#!/usr/bin/env python3
"""
Visualisierungs-Tool für Lernenergie-Profile (Version 0.2.1).

Erzeugt professionelle Diagramme:
- Radar-Chart für die 6 Hauptdimensionen
- Balkendiagramme für Detailansichten
- HTML-Report mit allen Visualisierungen

Benötigt: matplotlib, numpy
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Any, List
import sys

try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.patches import Rectangle
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("⚠️  matplotlib nicht verfügbar. Installieren mit: pip install matplotlib", 
          file=sys.stderr)


def create_radar_chart(profile: Dict[str, Any], output_path: Path) -> None:
    """
    Erstellt ein Radar-Chart für die 6 Hauptdimensionen.
    """
    if not MATPLOTLIB_AVAILABLE:
        return
    
    dimensions = profile["dimensions"]
    dim_order = ["attention", "sensory", "social", "executive", "motivation", "regulation"]
    
    # Daten extrahieren
    labels = [dimensions[dim]["label"] for dim in dim_order]
    scores = [dimensions[dim]["score"] for dim in dim_order]
    
    # Anzahl der Dimensionen
    num_dims = len(labels)
    angles = np.linspace(0, 2 * np.pi, num_dims, endpoint=False).tolist()
    scores_plot = scores + [scores[0]]  # Schließe den Plot
    angles_plot = angles + [angles[0]]
    
    # Plot erstellen
    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
    
    # Radar-Chart zeichnen
    ax.plot(angles_plot, scores_plot, 'o-', linewidth=2, color='#2E86AB', label='Ihr Profil')
    ax.fill(angles_plot, scores_plot, alpha=0.25, color='#2E86AB')
    
    # Referenzlinien (niedrig/mittel/hoch Bereiche)
    ax.plot(angles_plot, [40] * len(angles_plot), '--', linewidth=0.8, 
            color='gray', alpha=0.5, label='Grenze niedrig/mittel')
    ax.plot(angles_plot, [75] * len(angles_plot), '--', linewidth=0.8, 
            color='gray', alpha=0.5, label='Grenze mittel/hoch')
    
    # Achsenbeschriftung
    ax.set_xticks(angles)
    ax.set_xticklabels(labels, size=10)
    ax.set_ylim(0, 100)
    ax.set_yticks([25, 50, 75, 100])
    ax.set_yticklabels(['25', '50', '75', '100'], size=8)
    ax.grid(True, linewidth=0.5, alpha=0.3)
    
    # Titel und Legende
    plt.title(f"Lernenergie-Profil: {profile['id']}\nVersion {profile['meta']['version']}", 
              size=14, pad=20)
    plt.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
    
    # Speichern
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()


def create_dimension_bars(profile: Dict[str, Any], output_path: Path) -> None:
    """
    Erstellt Balkendiagramme für alle Dimensionen mit Kategorie-Färbung.
    """
    if not MATPLOTLIB_AVAILABLE:
        return
    
    dimensions = profile["dimensions"]
    dim_order = ["attention", "sensory", "social", "executive", "motivation", "regulation"]
    
    # Daten extrahieren
    labels = [dimensions[dim]["label"] for dim in dim_order]
    scores = [dimensions[dim]["score"] for dim in dim_order]
    levels = [dimensions[dim]["level"] for dim in dim_order]
    
    # Farben für Kategorien
    color_map = {
        "niedrig": "#E63946",
        "mittel": "#F4A261",
        "hoch": "#2A9D8F"
    }
    colors = [color_map[level] for level in levels]
    
    # Plot erstellen
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Balken zeichnen
    y_pos = np.arange(len(labels))
    bars = ax.barh(y_pos, scores, color=colors, alpha=0.8, edgecolor='black', linewidth=0.5)
    
    # Referenzlinien für Kategoriegrenzen
    ax.axvline(x=40, color='gray', linestyle='--', linewidth=1, alpha=0.5)
    ax.axvline(x=75, color='gray', linestyle='--', linewidth=1, alpha=0.5)
    
    # Beschriftung der Balken mit Scores
    for i, (bar, score, level) in enumerate(zip(bars, scores, levels)):
        ax.text(score + 2, i, f"{score:.1f} ({level})", 
                va='center', fontsize=9, fontweight='bold')
    
    # Achsen
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels)
    ax.set_xlabel('Score (0-100)', fontsize=11)
    ax.set_xlim(0, 105)
    ax.set_title(f"Dimensionen des Lernenergie-Profils: {profile['id']}", fontsize=13, pad=15)
    ax.grid(axis='x', alpha=0.3, linewidth=0.5)
    
    # Legende für Kategorien
    legend_elements = [
        Rectangle((0, 0), 1, 1, fc=color_map["niedrig"], alpha=0.8, label="Niedrig (0-39)"),
        Rectangle((0, 0), 1, 1, fc=color_map["mittel"], alpha=0.8, label="Mittel (40-74)"),
        Rectangle((0, 0), 1, 1, fc=color_map["hoch"], alpha=0.8, label="Hoch (75-100)")
    ]
    ax.legend(handles=legend_elements, loc='lower right', fontsize=9)
    
    # Speichern
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()


def create_chronotype_visualization(profile: Dict[str, Any], output_path: Path) -> None:
    """
    Erstellt eine Visualisierung des Chronotyp-Profils.
    """
    if not MATPLOTLIB_AVAILABLE:
        return
    
    chronotype = profile.get("additional_indices", {}).get("chronotype")
    if not chronotype:
        return
    
    morning = chronotype["morning_tendency"]
    evening = chronotype["evening_tendency"]
    interpretation = chronotype["interpretation"]
    
    # Plot erstellen
    fig, ax = plt.subplots(figsize=(10, 5))
    
    # Balken für Morgen- und Abendtendenz
    categories = ["Morgentendenz", "Abendtendenz"]
    scores = [morning, evening]
    colors = ["#F4D03F", "#5DADE2"]
    
    bars = ax.bar(categories, scores, color=colors, alpha=0.8, edgecolor='black', linewidth=1)
    
    # Referenzlinien
    ax.axhline(y=50, color='gray', linestyle='--', linewidth=1, alpha=0.5, label='Neutral (50)')
    
    # Beschriftung
    for bar, score in zip(bars, scores):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 2,
                f'{score:.1f}',
                ha='center', va='bottom', fontweight='bold', fontsize=11)
    
    # Achsen und Titel
    ax.set_ylabel('Tendenz-Score (0-100)', fontsize=11)
    ax.set_ylim(0, 105)
    ax.set_title(f"Chronotyp-Profil: {interpretation}", fontsize=13, pad=15)
    ax.legend(fontsize=9)
    ax.grid(axis='y', alpha=0.3, linewidth=0.5)
    
    # Interpretation als Text
    balance = chronotype["balance_score"]
    balance_text = f"Balance-Score: {balance:.2f}\n"
    if balance < 0:
        balance_text += "(Negative Werte = Morgentendenz überwiegt)"
    else:
        balance_text += "(Positive Werte = Abendtendenz überwiegt)"
    
    ax.text(0.5, 0.02, balance_text, transform=ax.transAxes,
            ha='center', va='bottom', fontsize=9, style='italic',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))
    
    # Speichern
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()


def generate_html_report(profile: Dict[str, Any], output_path: Path, 
                        img_dir: Path) -> None:
    """
    Generiert einen vollständigen HTML-Report mit eingebetteten Visualisierungen.
    Prüft Existenz der Bild-Dateien und passt HTML entsprechend an.
    """
    # Prüfe verfügbare Visualisierungen
    has_radar = (img_dir / "radar_chart.png").exists()
    has_bars = (img_dir / "dimension_bars.png").exists()
    has_chronotype = (img_dir / "chronotype.png").exists()
    
    html = f"""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Lernenergie-Profil: {profile['id']}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            margin: 0 0 10px 0;
        }}
        .section {{
            background: white;
            padding: 25px;
            margin-bottom: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .quality-warning {{
            background-color: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 4px;
        }}
        .quality-ok {{
            background-color: #d4edda;
            border-left: 4px solid #28a745;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 4px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #f8f9fa;
            font-weight: 600;
        }}
        .score-niedrig {{ color: #E63946; font-weight: bold; }}
        .score-mittel {{ color: #F4A261; font-weight: bold; }}
        .score-hoch {{ color: #2A9D8F; font-weight: bold; }}
        img {{
            max-width: 100%;
            height: auto;
            display: block;
            margin: 20px auto;
        }}
        .next-steps {{
            background-color: #e7f3ff;
            border-left: 4px solid #2196F3;
            padding: 15px;
            margin-top: 20px;
            border-radius: 4px;
        }}
        .next-steps ol {{
            margin: 10px 0 0 20px;
            padding: 0;
        }}
        .next-steps li {{
            margin: 8px 0;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Lernenergie-Profil</h1>
        <p>Profil-ID: {profile['id']} | Version: {profile['meta']['version']}</p>
    </div>
"""
    
    # Response Quality
    quality = profile.get("response_quality", {})
    quality_class = "quality-warning" if quality.get("quality_flag") == "check" else "quality-ok"
    html += f"""
    <div class="section">
        <h2>Antwortqualität</h2>
        <div class="{quality_class}">
            <strong>Qualitätsflag:</strong> {quality.get('quality_flag', 'N/A').upper()}<br>
            <strong>Verschiedene Antworten:</strong> {quality.get('num_unique_responses', 'N/A')}<br>
            <strong>Antwortvariation:</strong> {quality.get('response_variance', 'N/A')}<br>
            <strong>Durchschnitt:</strong> {quality.get('mean_response', 'N/A')}
"""
    if quality.get('warnings'):
        html += f"<br><br><strong>⚠️ Warnungen:</strong><br>{'<br>'.join(quality['warnings'])}"
    html += """
        </div>
    </div>
"""
    
    # Visualisierungen
    html += """
    <div class="section">
        <h2>Profil-Übersicht</h2>
"""
    
    if has_radar:
        html += '        <img src="radar_chart.png" alt="Radar-Chart">\n'
    else:
        html += '        <p><em>Radar-Chart nicht verfügbar (matplotlib nicht installiert oder Fehler bei Generierung).</em></p>\n'
    
    if has_bars:
        html += '        <img src="dimension_bars.png" alt="Dimensionen-Balken">\n'
    else:
        html += '        <p><em>Dimensionen-Balkendiagramm nicht verfügbar (matplotlib nicht installiert oder Fehler bei Generierung).</em></p>\n'
    
    html += """
    </div>
"""
    
    # Dimensionen-Tabelle
    dimensions = profile["dimensions"]
    dim_order = ["attention", "sensory", "social", "executive", "motivation", "regulation"]
    
    html += """
    <div class="section">
        <h2>Dimensionen im Detail</h2>
        <table>
            <thead>
                <tr>
                    <th>Dimension</th>
                    <th>Score</th>
                    <th>Kategorie</th>
                    <th>Items</th>
                    <th>Reverse-Items</th>
                </tr>
            </thead>
            <tbody>
"""
    
    for dim_code in dim_order:
        dim = dimensions[dim_code]
        score_class = f"score-{dim['level']}"
        html += f"""
                <tr>
                    <td>{dim['label']}</td>
                    <td class="{score_class}">{dim['score']:.1f}</td>
                    <td class="{score_class}">{dim['level'].upper()}</td>
                    <td>{dim['num_items']}</td>
                    <td>{dim['num_reversed']}</td>
                </tr>
"""
    
    html += """
            </tbody>
        </table>
    </div>
"""
    
    # Chronotyp
    if "chronotype" in profile.get("additional_indices", {}):
        chronotype = profile["additional_indices"]["chronotype"]
        html += f"""
    <div class="section">
        <h2>Chronotyp-Profil</h2>
"""
        if has_chronotype:
            html += f'        <img src="chronotype.png" alt="Chronotyp">\n'
        else:
            html += '        <p><em>Chronotyp-Visualisierung nicht verfügbar (matplotlib nicht installiert oder Fehler bei Generierung).</em></p>\n'
        
        html += f"""        <p><strong>Interpretation:</strong> {chronotype['interpretation']}</p>
        <p><strong>Morgentendenz:</strong> {chronotype['morning_tendency']:.1f}</p>
        <p><strong>Abendtendenz:</strong> {chronotype['evening_tendency']:.1f}</p>
        <p><strong>Balance-Score:</strong> {chronotype['balance_score']:.2f}</p>
    </div>
"""
    
    # Vermeidungsorientierung
    if "motivation_avoidance" in profile.get("additional_indices", {}):
        avoid = profile["additional_indices"]["motivation_avoidance"]
        score_class = f"score-{avoid['level']}"
        html += f"""
    <div class="section">
        <h2>Vermeidungsorientierung</h2>
        <p><strong>Score:</strong> <span class="{score_class}">{avoid['score']:.1f} ({avoid['level'].upper()})</span></p>
        <p>Vermeidungsorientierung erfasst, inwieweit Sie durch das Vermeiden von Fehlern oder Misserfolgen motiviert sind.</p>
    </div>
"""
    
    # Nächste Schritte
    html += """
    <div class="section">
        <h2>Nächste Schritte</h2>
        <div class="next-steps">
            <ol>
                <li>Dieses Profil mit einer datenschutzkonformen KI analysieren lassen 
                    (z.B. Academic Cloud oder KI-Assist der FU Berlin)</li>
                <li>Konkrete Lernstrategien auf Basis Ihres Profils entwickeln</li>
                <li>Profil bei Bedarf mit Lehrenden oder Lerncoaches besprechen</li>
                <li>Nach einigen Wochen den Fragebogen wiederholen, um Entwicklungen zu erfassen</li>
            </ol>
        </div>
    </div>
    
    <div class="section">
        <h2>Wichtige Hinweise</h2>
        <p>Dieses Profil ist ein Prototyp zur strukturierten Selbstreflexion. 
        Es ersetzt keine professionelle Beratung oder Diagnostik.</p>
        <p><strong>Datenschutz:</strong> Dieses Profil wurde lokal auf Ihrem Computer erstellt. 
        Sie entscheiden selbst, ob und mit wem Sie es teilen.</p>
    </div>
</body>
</html>
"""
    
    output_path.write_text(html, encoding="utf-8")


def visualize_profile(profile_path: Path, output_dir: Path) -> None:
    """
    Erstellt alle Visualisierungen für ein Profil.
    """
    # Profil laden
    with profile_path.open('r', encoding='utf-8') as f:
        profile = json.load(f)
    
    # Output-Verzeichnis erstellen
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Erstelle Visualisierungen für Profil: {profile['id']}")
    
    # Visualisierungen erstellen
    if MATPLOTLIB_AVAILABLE:
        print("  → Radar-Chart...")
        create_radar_chart(profile, output_dir / "radar_chart.png")
        
        print("  → Dimensionen-Balken...")
        create_dimension_bars(profile, output_dir / "dimension_bars.png")
        
        print("  → Chronotyp-Visualisierung...")
        create_chronotype_visualization(profile, output_dir / "chronotype.png")
    else:
        print("  ⚠️  Matplotlib nicht verfügbar - überspringe Diagramme")
    
    # HTML-Report
    print("  → HTML-Report...")
    generate_html_report(profile, output_dir / "report.html", output_dir)
    
    print(f"\n✓ Alle Visualisierungen gespeichert in: {output_dir}")
    print(f"  → Öffnen Sie {output_dir / 'report.html'} im Browser")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Erstellt Visualisierungen für ein Lernenergie-Profil (Version 0.2.1)"
    )
    parser.add_argument(
        "profile_json",
        type=Path,
        help="Pfad zur JSON-Profil-Datei",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("visualizations"),
        help="Output-Verzeichnis für Visualisierungen (Standard: ./visualizations)",
    )
    
    args = parser.parse_args()
    
    if not args.profile_json.exists():
        print(f"❌ Profil-Datei nicht gefunden: {args.profile_json}", file=sys.stderr)
        sys.exit(1)
    
    visualize_profile(args.profile_json, args.output)


if __name__ == "__main__":
    main()
