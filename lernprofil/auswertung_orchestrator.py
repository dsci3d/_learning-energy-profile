#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lernprofil-Orchestrator - Unified Workflow Manager
===================================================
Version 1.3

Zentrale Steuerung für die Auswertung von Lernenergie-Profilen.
Koordiniert Fragebogen-Auswertung, Profil-Berechnung, Visualisierung und Validierung.

QUICK START
-----------
python auswertung_orchestrator.py                                      # Interaktiver Modus
python auswertung_orchestrator.py --csv questionaire_answered.csv      # Direkt mit CSV
python auswertung_orchestrator.py --csv questionaire_answered.csv --workflow full

VORDEFINIERTE WORKFLOWS
-----------------------
basic     = Profil-Berechnung + Text-Report
full      = Profil-Berechnung + Text-Report + HTML-Report + Visualisierungen
validate  = System-Tests + Validierung
minimal   = Nur Profil-Berechnung (JSON Output)

DIE 4 MODULE (Reihenfolge bei Ausführung)
------------------------------------------
1. auswertung.py (Core)
   - Lädt CSV mit Fragebogen-Antworten
   - Validiert Input (88 Items, Likert 1-5)
   - Berechnet 6 Dimensionen + Zusatzindizes
   - Erstellt JSON-Profil + Text-Report

2. auswertung_visualize.py (Optional)
   - Erstellt Radar-Chart (6 Dimensionen)
   - Erstellt Balkendiagramme
   - Erstellt Chronotyp-Visualisierung
   - Generiert HTML-Report mit eingebetteten Grafiken

3. auswertung_test.py (Optional)
   - 21 Unit-Tests für Berechnungslogik
   - Prüft Reverse-Coding, Score-Transformation
   - Validiert dimensionale Unabhängigkeit
   - Testet Extremprofile

4. auswertung_validation.py (Optional)
   - Integrations-Validierung
   - Prüft Version-Konsistenz
   - Validiert Meta-Struktur
   - Testet Fehlerbehandlung

VERZEICHNIS-STRUKTUR
--------------------
lernprofil_reports/
└── session_YYYYMMDD_HHMMSS_ffffff/
    ├── 01_compute/
    │   ├── profil.json
    │   ├── report.txt
    │   ├── stdout.txt
    │   ├── stderr.txt
    │   └── command.txt
    ├── 03_visualize/
    │   ├── report.html
    │   ├── radar_chart.png
    │   ├── dimension_bars.png
    │   ├── chronotype.png
    │   ├── stdout.txt
    │   ├── stderr.txt
    │   └── command.txt
    ├── 04_tests/
    │   ├── test_results.txt
    │   ├── stdout.txt
    │   ├── stderr.txt
    │   └── command.txt
    ├── 05_validation/
    │   ├── validation_results.txt
    │   ├── stdout.txt
    │   ├── stderr.txt
    │   └── command.txt
    └── session_summary.json

WICHTIG: CSV-DATEI FORMAT
--------------------------
Die CSV-Datei muss Ihre ausgefüllten Fragebogen-Antworten enthalten:
  - Spalten: item_code, rating
  - 88 Zeilen (eine pro Item)
  - rating: Werte 1-5 (Likert-Skala)

Empfohlener Dateiname: questionaire_answered.csv
(Generischer Name aus Datenschutzgründen, kein Personenbezug!)

INSTRUMENT-STRUKTUR
-------------------
88 Items total:
  - 80 Items Hauptskalen (6 Dimensionen)
  - 8 Items Zusatzindizes
  - 27 Reverse-Items

6 Dimensionen:
  1. Attention (Aufmerksamkeit)
  2. Sensory (Sensorik)
  3. Social (Soziales)
  4. Executive (Exekutive Funktionen)
  5. Motivation (Motivation)
  6. Regulation (Regulation)

Zusatzindizes:
  - Chronotype (Morgen-/Abendtyp)
  - Motivation Avoidance (Vermeidungsorientierung)

BEISPIELE
---------
# Interaktiver Modus
python auswertung_orchestrator.py

# Basic Workflow
python auswertung_orchestrator.py --csv questionaire_answered.csv --workflow basic

# Full Workflow mit Visualisierung
python auswertung_orchestrator.py --csv questionaire_answered.csv --workflow full

# Nur Validierung
python auswertung_orchestrator.py --workflow validate

# Custom Profile-ID
python auswertung_orchestrator.py --csv questionaire_answered.csv --id "Profil_2025_01"

Author: PK
Version: 1.3
Date: 2025-11
"""

import argparse
import json
import subprocess
import sys
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class WorkflowConfig:
    """Zentrale Konfiguration für alle Scripts"""
    csv_path: Path
    profile_id: Optional[str] = None
    output_dir: Optional[Path] = None
    
    def __post_init__(self):
        self.csv_path = Path(self.csv_path).expanduser().resolve()
        
        if self.output_dir is None:
            # Default: Reports im aktuellen Verzeichnis
            self.output_dir = Path.cwd() / "lernprofil_reports"
        else:
            self.output_dir = Path(self.output_dir).expanduser().resolve()
        
        # Profile-ID aus Dateinamen ableiten wenn nicht angegeben
        if self.profile_id is None:
            self.profile_id = self.csv_path.stem


@dataclass
class StageResult:
    """Ergebnis einer Workflow-Stage"""
    stage_name: str
    success: bool
    duration_seconds: float
    output_files: List[Path]
    error_message: Optional[str] = None


class LernprofilOrchestrator:
    """
    Koordiniert alle Auswertungs-Steps und verwaltet Session-Reports.
    """
    
    WORKFLOWS: Dict[str, List[str]] = {
        'minimal': ['compute'],
        'basic': ['compute', 'text_report'],
        'full': ['compute', 'text_report', 'visualize'],
        'validate': ['test', 'validation']
    }
    
    def __init__(self, config: WorkflowConfig, timeout: int = 300):
        self.config = config
        self.timeout = timeout
        self.session_dir = self._create_session_dir()
        self.results: List[StageResult] = []
        
        # Scripts im gleichen Verzeichnis wie orchestrator
        self.script_dir = Path(__file__).parent.resolve()
        self.scripts = {
            'auswertung': self.script_dir / 'auswertung.py',
            'visualize': self.script_dir / 'auswertung_visualize.py',
            'test': self.script_dir / 'auswertung_test.py',
            'validation': self.script_dir / 'auswertung_validation.py'
        }
        
        self._validate_scripts()
    
    def _create_session_dir(self) -> Path:
        """Erstellt Session-Verzeichnis mit Timestamp (inkl. Mikrosekunden gegen Kollisionen)"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        base = self.config.output_dir / f"session_{timestamp}"
        session_dir = base
        
        # Falls dennoch Kollision: Zähler anhängen
        counter = 1
        while session_dir.exists():
            session_dir = self.config.output_dir / f"session_{timestamp}_{counter}"
            counter += 1
        
        session_dir.mkdir(parents=True, exist_ok=True)
        return session_dir
    
    def _validate_scripts(self) -> None:
        """Prüft ob alle benötigten Scripts vorhanden sind"""
        missing = []
        for name, path in self.scripts.items():
            if not path.exists():
                missing.append(f"{name}: {path}")
        
        if missing:
            print("❌ Fehlende Scripts:")
            for m in missing:
                print(f"   {m}")
            raise FileNotFoundError("Erforderliche Scripts nicht gefunden")
    
    def _run_stage(self, stage_name: str, cmd: List[str], 
                   stage_dir: Optional[Path] = None) -> StageResult:
        """
        Führt eine einzelne Stage aus.
        
        Args:
            stage_name: Name der Stage
            cmd: Kommandozeilen-Argumente
            stage_dir: Optionales Unterverzeichnis für Stage-Outputs
        """
        start_time = datetime.now()
        
        if stage_dir:
            stage_dir.mkdir(parents=True, exist_ok=True)
        else:
            stage_dir = self.session_dir
        
        print(f"\n{'='*60}")
        print(f"STAGE: {stage_name}")
        print(f"{'='*60}")
        print(f"Command: {' '.join(str(c) for c in cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                encoding='utf-8',
                env={**os.environ, 'PYTHONIOENCODING': 'utf-8'}
            )
            
            duration = (datetime.now() - start_time).total_seconds()
            
            # Outputs speichern
            (stage_dir / "stdout.txt").write_text(result.stdout, encoding='utf-8')
            (stage_dir / "stderr.txt").write_text(result.stderr, encoding='utf-8')
            (stage_dir / "command.txt").write_text(' '.join(str(c) for c in cmd), encoding='utf-8')
            
            if result.returncode != 0:
                error_msg = result.stderr or "Unknown error"
                # Nur erste Zeile im Terminal zeigen (studierendenfreundlich)
                first_line = error_msg.splitlines()[0] if error_msg else "Unknown error"
                print(f"❌ Stage fehlgeschlagen: {first_line}")
                print(f"   Vollständiger Fehler in: {stage_dir / 'stderr.txt'}")
                return StageResult(
                    stage_name=stage_name,
                    success=False,
                    duration_seconds=duration,
                    output_files=[],
                    error_message=first_line
                )
            
            print(f"✓ Stage erfolgreich ({duration:.1f}s)")
            
            # Sammle Output-Files (exklusive Log-Dateien)
            output_files = [
                f for f in stage_dir.glob("*.*")
                if f.name not in ["stdout.txt", "stderr.txt", "command.txt"]
            ]
            
            return StageResult(
                stage_name=stage_name,
                success=True,
                duration_seconds=duration,
                output_files=output_files
            )
            
        except subprocess.TimeoutExpired:
            duration = (datetime.now() - start_time).total_seconds()
            error_msg = f"Timeout nach {self.timeout}s"
            print(f"❌ {error_msg}")
            return StageResult(
                stage_name=stage_name,
                success=False,
                duration_seconds=duration,
                output_files=[],
                error_message=error_msg
            )
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            print(f"❌ Fehler: {e}")
            return StageResult(
                stage_name=stage_name,
                success=False,
                duration_seconds=duration,
                output_files=[],
                error_message=str(e)
            )
    
    def _stage_compute(self) -> StageResult:
        """Stage 1: Profil berechnen"""
        stage_dir = self.session_dir / "01_compute"
        output_json = stage_dir / "profil.json"
        output_txt = stage_dir / "report.txt"
        
        cmd = [
            sys.executable,
            str(self.scripts['auswertung']),
            str(self.config.csv_path),
            '--id', self.config.profile_id,
            '--output', str(output_json),
            '--report', str(output_txt)
        ]
        
        return self._run_stage("Profil-Berechnung", cmd, stage_dir=stage_dir)
    
    def _stage_text_report(self) -> StageResult:
        """Stage 2: Text-Report (bereits in Stage 1 enthalten)"""
        # Prüfe ob Report existiert
        report_txt = self.session_dir / "01_compute" / "report.txt"
        if report_txt.exists():
            return StageResult(
                stage_name="Text-Report",
                success=True,
                duration_seconds=0.0,
                output_files=[report_txt]
            )
        else:
            print("❌ report.txt nicht gefunden (Stage 1 fehlgeschlagen?)")
            return StageResult(
                stage_name="Text-Report",
                success=False,
                duration_seconds=0.0,
                output_files=[],
                error_message="report.txt nicht gefunden"
            )
    
    def _stage_visualize(self) -> StageResult:
        """Stage 3: HTML-Report + Visualisierungen"""
        stage_dir = self.session_dir / "03_visualize"
        profil_json = self.session_dir / "01_compute" / "profil.json"
        
        if not profil_json.exists():
            return StageResult(
                stage_name="Visualisierung",
                success=False,
                duration_seconds=0.0,
                output_files=[],
                error_message="profil.json nicht gefunden (Stage 1 fehlgeschlagen?)"
            )
        
        cmd = [
            sys.executable,
            str(self.scripts['visualize']),
            str(profil_json),
            '--output', str(stage_dir)
        ]
        
        result = self._run_stage("Visualisierung", cmd, stage_dir=stage_dir)
        
        # Prüfe ob HTML erstellt wurde
        html_report = stage_dir / "report.html"
        if html_report.exists():
            print(f"   → HTML-Report: {html_report}")
            
            # Prüfe optionale Grafiken
            for img in ['radar_chart.png', 'dimension_bars.png', 'chronotype.png']:
                img_path = stage_dir / img
                if img_path.exists():
                    print(f"   → {img}: ✓")
        
        return result
    
    def _stage_test(self) -> StageResult:
        """Stage 4: Unit-Tests"""
        stage_dir = self.session_dir / "04_tests"
        test_output = stage_dir / "test_results.txt"
        
        cmd = [
            sys.executable,
            str(self.scripts['test'])
        ]
        
        result = self._run_stage("Unit-Tests", cmd, stage_dir=stage_dir)
        
        # Test-Output in dedizierte Datei kopieren
        if result.success:
            stdout = (stage_dir / "stdout.txt").read_text(encoding='utf-8')
            test_output.write_text(stdout, encoding='utf-8')
            print(f"   → Test-Ergebnisse: {test_output}")
            # Füge zu output_files hinzu
            result.output_files.append(test_output)
        
        return result
    
    def _stage_validation(self) -> StageResult:
        """Stage 5: Validierung"""
        stage_dir = self.session_dir / "05_validation"
        validation_output = stage_dir / "validation_results.txt"
        
        cmd = [
            sys.executable,
            str(self.scripts['validation'])
        ]
        
        result = self._run_stage("Validierung", cmd, stage_dir=stage_dir)
        
        # Validation-Output in dedizierte Datei kopieren
        if result.success:
            stdout = (stage_dir / "stdout.txt").read_text(encoding='utf-8')
            validation_output.write_text(stdout, encoding='utf-8')
            print(f"   → Validierungs-Ergebnisse: {validation_output}")
            # Füge zu output_files hinzu
            result.output_files.append(validation_output)
        
        return result
    
    def run_workflow(self, workflow_name: str) -> bool:
        """Führt vordefinierten Workflow aus"""
        if workflow_name not in self.WORKFLOWS:
            print(f"❌ Unbekannter Workflow: {workflow_name}")
            print(f"   Verfügbar: {', '.join(self.WORKFLOWS.keys())}")
            return False
        
        stages = self.WORKFLOWS[workflow_name]
        
        print("\n" + "="*60)
        print(f"WORKFLOW: {workflow_name.upper()}")
        print("="*60)
        print(f"Stages: {' → '.join(stages)}")
        print(f"Session: {self.session_dir}")
        
        self._show_config()
        
        # Führe Stages aus
        for stage in stages:
            stage_method = getattr(self, f'_stage_{stage}', None)
            if stage_method is None:
                print(f"❌ Stage nicht implementiert: {stage}")
                return False
            
            result = stage_method()
            self.results.append(result)
            
            if not result.success:
                print(f"\n❌ Workflow abgebrochen nach fehlgeschlagener Stage: {result.stage_name}")
                self._write_session_summary()
                return False
        
        self._write_session_summary()
        self._print_final_summary()
        return True
    
    def _write_session_summary(self) -> None:
        """Schreibt Session-Summary als JSON"""
        summary = {
            'session_dir': str(self.session_dir),
            'timestamp': datetime.now().isoformat(),
            'config': {
                'csv_path': str(self.config.csv_path),
                'profile_id': self.config.profile_id,
                'output_dir': str(self.config.output_dir)
            },
            'results': [
                {
                    'stage': r.stage_name,
                    'success': r.success,
                    'duration_seconds': r.duration_seconds,
                    'output_files': [str(f) for f in r.output_files],
                    'error_message': r.error_message
                }
                for r in self.results
            ]
        }
        
        summary_path = self.session_dir / "session_summary.json"
        summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding='utf-8')
    
    def _print_final_summary(self) -> None:
        """Zeigt finale Zusammenfassung"""
        print("\n" + "="*60)
        print("SESSION ABGESCHLOSSEN")
        print("="*60)
        
        total_duration = sum(r.duration_seconds for r in self.results)
        successful = sum(1 for r in self.results if r.success)
        
        print(f"Stages: {successful}/{len(self.results)} erfolgreich")
        print(f"Dauer: {total_duration:.1f}s")
        print(f"Output: {self.session_dir}")
        
        # Wichtigste Output-Dateien
        print("\nWichtige Dateien:")
        important_files = [
            ('01_compute/profil.json', 'JSON-Profil'),
            ('01_compute/report.txt', 'Text-Report'),
            ('03_visualize/report.html', 'HTML-Report'),
            ('03_visualize/radar_chart.png', 'Radar-Chart')
        ]
        
        for fpath, desc in important_files:
            full_path = self.session_dir / fpath
            if full_path.exists():
                print(f"  ✓ {desc}: {fpath}")
        
        print("\nDetails: session_summary.json")
    
    def _show_config(self) -> None:
        """Zeigt aktuelle Konfiguration"""
        print("\nKonfiguration:")
        
        # Spezialbehandlung für validate-Workflow
        if self.config.csv_path.name == 'dummy.csv':
            print("  CSV:        (nicht verwendet für validate)")
        else:
            print(f"  CSV:        {self.config.csv_path}")
        
        print(f"  Profile-ID: {self.config.profile_id}")
        print(f"  Output:     {self.config.output_dir}")
        print(f"  Timeout:    {self.timeout}s")
    
    def interactive_menu(self) -> None:
        """Interaktives Menü zur Workflow-Auswahl"""
        print("\n" + "="*60)
        print("LERNPROFIL-ORCHESTRATOR - WORKFLOW AUSWAHL")
        print("="*60)
        
        self._show_config()
        
        print("\nVerfügbare Workflows:")
        print("  1. minimal  - Nur Profil-Berechnung (JSON)")
        print("  2. basic    - Profil + Text-Report")
        print("  3. full     - Profil + Text + HTML + Visualisierungen")
        print("  4. validate - System-Tests + Validierung")
        print("  Q. Beenden")
        
        while True:
            choice = input("\nAuswahl (1-4 oder Q): ").strip().upper()
            
            workflow_map = {
                '1': 'minimal',
                '2': 'basic',
                '3': 'full',
                '4': 'validate'
            }
            
            if choice == 'Q':
                print("Abgebrochen.")
                return
            
            if choice in workflow_map:
                workflow = workflow_map[choice]
                success = self.run_workflow(workflow)
                
                if success:
                    # Frage ob weiterer Workflow
                    again = input("\nWeiteren Workflow ausführen? (j/N): ").strip().lower()
                    if again != 'j':
                        return
                else:
                    return
            else:
                print("Ungültige Auswahl. Bitte 1-4 oder Q eingeben.")


def interactive_setup() -> WorkflowConfig:
    """Interaktiver Setup-Dialog (ohne Rekursion)"""
    print("\n" + "="*60)
    print("LERNPROFIL-ORCHESTRATOR - SETUP")
    print("="*60)
    
    while True:
        # CSV-Pfad
        print("\n1. CSV-Datei mit Fragebogen-Antworten:")
        print("   (Format: item_code, rating | 88 Zeilen | Likert 1-5)")
        print("   Empfohlen: questionaire_answered.csv")
        
        csv_path = None
        while csv_path is None:
            csv_input = input("   Pfad zur CSV: ").strip()
            if not csv_input:
                # Suche im aktuellen Verzeichnis
                csvs = list(Path.cwd().glob("*.csv"))
                if csvs:
                    print("\n   Gefundene CSV-Dateien:")
                    for i, csv in enumerate(csvs, 1):
                        print(f"   {i}. {csv.name}")
                    selection = input("   Nummer auswählen (oder Pfad eingeben): ").strip()
                    if selection.isdigit() and 1 <= int(selection) <= len(csvs):
                        csv_input = str(csvs[int(selection)-1])
                    else:
                        csv_input = selection
            
            csv = Path(csv_input).expanduser()
            if csv.is_file():
                csv_path = csv
            else:
                print("   [FEHLER] Keine gültige Datei. Bitte erneut versuchen.")
        
        # Profile-ID
        print("\n2. Profile-ID (optional):")
        default_id = csv_path.stem
        print(f"   Standard: {default_id}")
        profile_id = input("   Enter für Standard, oder eigene ID: ").strip()
        if not profile_id:
            profile_id = default_id
        
        # Output-Verzeichnis
        print("\n3. Output-Verzeichnis (optional):")
        default_output = Path.cwd() / "lernprofil_reports"
        print(f"   Standard: {default_output}")
        output_dir = input("   Enter für Standard, oder eigener Pfad: ").strip()
        if not output_dir:
            output_dir = str(default_output)
        
        # Bestätigung
        print("\n" + "-"*60)
        print("KONFIGURATION:")
        print(f"  CSV:        {csv_path}")
        print(f"  Profile-ID: {profile_id}")
        print(f"  Output:     {output_dir}")
        print("-"*60)
        
        confirm = input("\nKorrekt? (j/N): ").strip().lower()
        if confirm == 'j':
            return WorkflowConfig(
                csv_path=csv_path,
                profile_id=profile_id,
                output_dir=Path(output_dir)
            )
        # Sonst: Loop wiederholen


def main():
    parser = argparse.ArgumentParser(
        description="Lernprofil-Orchestrator v1.3 - Unified workflow manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  # Interaktiver Modus
  %(prog)s
  
  # Direkte Workflow-Ausführung
  %(prog)s --csv questionaire_answered.csv --workflow basic
  %(prog)s --csv questionaire_answered.csv --workflow full
  
  # Custom Profile-ID
  %(prog)s --csv questionaire_answered.csv --id "Profil_2025" --workflow full
  
  # Nur Validierung (benötigt keine CSV)
  %(prog)s --workflow validate

Wichtig: CSV-Datei muss Spalten 'item_code' und 'rating' enthalten!
        """
    )
    
    parser.add_argument('--csv', dest='csv_path',
                       help='Pfad zur CSV-Datei mit Fragebogen-Antworten (empfohlen: questionaire_answered.csv)')
    parser.add_argument('--workflow',
                       choices=['minimal', 'basic', 'full', 'validate'],
                       help='Workflow direkt ausführen')
    parser.add_argument('--id', dest='profile_id',
                       help='Profile-ID (Standard: CSV-Dateiname)')
    parser.add_argument('--output-dir',
                       help='Output-Verzeichnis (Standard: ./lernprofil_reports)')
    parser.add_argument('--timeout', type=int, default=300,
                       help='Timeout pro Stage in Sekunden (Standard: 300)')
    
    args = parser.parse_args()
    
    # Wenn keine CSV angegeben, gehe zu interaktivem Setup
    if not args.csv_path and not args.workflow:
        config = interactive_setup()
        timeout = args.timeout
    elif not args.csv_path and args.workflow == 'validate':
        # Validierung braucht keine CSV
        config = WorkflowConfig(
            csv_path=Path('dummy.csv'),  # Dummy, wird nicht benutzt
            output_dir=Path(args.output_dir) if args.output_dir else None
        )
        timeout = args.timeout
    elif not args.csv_path:
        print("❌ Fehler: --csv erforderlich für diesen Workflow")
        print("   Tipp: Für Validierung --workflow validate ohne --csv verwenden")
        return 1
    else:
        config = WorkflowConfig(
            csv_path=args.csv_path,
            profile_id=args.profile_id,
            output_dir=Path(args.output_dir) if args.output_dir else None
        )
        timeout = args.timeout
    
    # Orchestrator initialisieren mit Fehlerbehandlung
    try:
        orchestrator = LernprofilOrchestrator(config, timeout=timeout)
    except FileNotFoundError as e:
        print(f"❌ Initialisierung fehlgeschlagen: {e}")
        print("   Prüfen Sie, ob alle benötigten Scripts vorhanden sind:")
        print("   - auswertung.py")
        print("   - auswertung_visualize.py")
        print("   - auswertung_test.py")
        print("   - auswertung_validation.py")
        return 1
    except Exception as e:
        print(f"❌ Unerwarteter Fehler bei der Initialisierung: {e}")
        return 2
    
    if args.workflow:
        success = orchestrator.run_workflow(args.workflow)
        return 0 if success else 1
    else:
        orchestrator.interactive_menu()
        return 0


if __name__ == '__main__':
    sys.exit(main())