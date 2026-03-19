# Copilot-Instruktionen

## Briefing-Datei

Wenn `.briefing.md` im Repo-Root existiert, lies sie zuerst. Sie enthaelt ein automatisch generiertes Regelwerk mit allen Projekt-Konventionen und Arbeitsregeln. Diese Datei wird per `briefer export` aus dem Index erzeugt und ist gitignored.

Falls `.briefing.md` nicht vorhanden ist, erzeuge sie:

```bash
briefer export
```

## Kernregeln (Fallback)

Diese Regeln gelten immer, auch ohne Briefing-Datei:

- Deutsche Umlaute (ae, oe, ue, ss) im Fliesstext verwenden — kein ASCII-Ersatz
- Keine Icons oder Emojis in Dateien
- In .md/.qmd-Dateien keine manuellen Zeilenumbrueche innerhalb von Fliesstext-Absaetzen
- Ueberschriften in QMD nie manuell nummerieren (Quarto `number-sections: true` verwenden)
- API-Keys und Secrets nie im Klartext — immer Umgebungsvariablen oder .env
