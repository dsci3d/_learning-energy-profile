# Learning Energy Profile

**A research tool for optimizing personal study architectures**

Developed by **Peter Kocmann**
- Freie Universität Berlin,
- Charité – Universitätsmedizin Berlin,
- Technische Universität Berlin,
- University of Potsdam

as part of the "Efficient Learning with AI" workshop

---

## What is the Learning Energy Profile?

Learning is an energetic system. Success depends not only on intelligence but on the match between person and study architecture. This tool analyzes your individual **Learning Energy Profile** across 6 evidence-based dimensions:

1. **Attention Architecture** – How robust is your focus?
2. **Sensory Processing** – How sensitive are you to stimuli?
3. **Social Energetics** – Do you learn better alone or in groups?
4. **Executive Functions** – How strong is your need for structure?
5. **Motivation Architecture** – What drives you?
6. **Autonomic Regulation** – How well do you manage stress?

**The goal:** Instead of generic "learning style" models, you get an individual profile showing how you learn optimally – based on stress physiology, attention research, and polyvagal theory.

---

## Quick Start

### 1. Installation

```bash
git clone https://github.com/dsci3d/learning-energy-profile.git
cd learning-energy-profile
pip install -r requirements.txt
```

### 2. Complete the Questionnaire

The questionnaire (88 items, Likert scale 1-5) is available at:
- **Interactive web version:** (coming soon)
- CSV template in repo: `questionnaire_template.csv`

### 3. Calculate Your Profile

```bash
# Basic analysis (JSON + text report)
python auswertung_orchestrator.py --csv your_responses.csv --workflow basic

# Full analysis (including visualizations + HTML report)
python auswertung_orchestrator.py --csv your_responses.csv --workflow full
```

**Output:**
- `profil_[ID].json` – Your complete Learning Energy Profile
- `report_[ID].txt` – Text-based report with interpretations
- `report_[ID].html` – Interactive HTML report with charts (only with `--workflow full`)

---

## Project Structure

```
learning-energy-profile/
├── LICENSE                                    # CC BY-NC-SA 4.0
├── README.md                                  # This file
├── requirements.txt                           # Python dependencies
└── examples/                                  # Example data
    ├── questionnaire_template.csv             # Blank questionnaire template
    ├── questionnaire_answered_example2.csv    # Example: High social energy profile
    └── questionnaire_answered_example1.csv    # Example: High focus, low sensory threshold
└── lernprofil/                                # Python model
    ├── auswertung.py                          # Core: Questionnaire analysis + profile calculation
    ├── auswertung_orchestrator.py             # Workflow manager (recommended entry point)
    ├── auswertung_visualize.py                # Radar charts, bar charts, HTML report
    ├── auswertung_test.py                     # 21 unit tests (scoring logic)
    ├── auswertung_validation.py               # Integration validation
```

---

## Workflows

The **orchestrator** provides 4 predefined workflows:

| Workflow | Description | Output |
|----------|-------------|--------|
| `minimal` | JSON profile only | `profil_[ID].json` |
| `basic` | JSON + text report | + `report_[ID].txt` |
| `full` | Everything + visualizations | + `report_[ID].html` + charts |
| `validate` | System tests | Validation log |

**Example:**
```bash
python auswertung_orchestrator.py --csv questionnaire_answered.csv --workflow full --output-dir results/
```

---

## Scientific Foundation

The Learning Energy Profile is based on:
- **Stress physiology** (Allostatic Load, cortisol regulation)
- **Attention research** (Vigilance, cognitive capacity)
- **Polyvagal Theory** (Porges) – Autonomic regulation and safety signals
- **Motivation psychology** (Deci & Ryan: Self-Determination Theory)
- **Executive functions** (Working memory, inhibition, cognitive flexibility)

**Important distinction:** This is not a "learning styles" test (visual/auditory/kinesthetic), but an **energetic architecture model** of your learning conditions.

---

## Research Code Notice

⚠️ **This is research code, not production-ready software.**

- Developed for teaching and research purposes in higher education contexts
- Fully transparent and traceable (all calculation steps documented)
- Not a replacement for professional psychological diagnostics
- Validation ongoing in workshop contexts

**For production use:** Own validation recommended. Questions: kocmann@zedat.fu-berlin.de

---

## Language Note

Documentation and README are in English for international accessibility. Code comments and variable names are in German, as this tool was developed in a German academic context. This does not affect functionality.

---

## License & Terms of Use

**Copyright © 2025-2026 Peter Kocmann**

This project is licensed under **Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)**.

**You may:**
- ✅ Use the tool and share results
- ✅ Modify and extend the code
- ✅ Use in teaching and research

**Under these conditions:**
- **Attribution:** Credit Peter Kocmann as creator
- **Non-commercial:** No commercial use without permission
- **Share-alike:** Distribute modifications under same license

Full license: https://creativecommons.org/licenses/by-nc-sa/4.0/

---

## Workshop Integration

This tool is part of the **"Efficient Learning with AI"** workshop at Technische Universität Berlin.

**Complete workshop materials:**
https://publish.obsidian.md/dsci3d/Effzient+Lernen+mit+KI/1+Workshop+Übersicht

**Conceptual embedding:**
The Learning Energy Profile is the first step in a larger study architecture:
1. **Create profile** (this tool)
2. **AI duo as coach + reviewer** (workshop module)
3. **Obsidian + flashcards** as active learning surfaces
4. **Individual learning path configuration**

---

## Technical Details

### System Requirements
- Python 3.8+
- Optional: matplotlib + numpy (for visualizations)

### CSV Format
```csv
item_code,rating
A1,4
A2,3
...
```
- **88 items** (A1-A88)
- **Likert scale 1-5** (1 = does not apply, 5 = fully applies)
- Additional columns (e.g., `item_text`, `dimension`) are ignored

### Profile Structure (JSON)
```json
{
  "id": "example",
  "dimensions": {
    "attention": {"score": 65.3, "level": "medium", ...},
    "sensory": {...},
    ...
  },
  "additional_indices": {
    "chronotype": {...},
    "motivation_avoidance": {...}
  },
  "response_quality": {...},
  "meta": {"version": "0.2.1", ...}
}
```

### Run Tests
```bash
# Unit tests (21 tests)
python auswertung_test.py

# Integration validation
python auswertung_validation.py

# Or via orchestrator
python auswertung_orchestrator.py --workflow validate
```

---

## Contributing & Contact

**Developed by:** Peter Kocmann  
**Affiliation:** Freelance lecturer at 
- FU Berlin (Continuing Education),
- Charité – Universitätsmedizin Berlin,
- Technische Universität Berlin and
- University of Potsdam

**Expertise:** Making technical concepts accessible to non-technical audiences (20+ years)

**Questions, feedback, collaboration:**
- kocmann@zedat.fu-berlin.de
- https://publish.obsidian.md/dsci3d/

**Contributions:** Pull requests welcome but must respect the license (CC BY-NC-SA 4.0).

---

## Citation

If you use this tool in academic work, please cite:

```
Kocmann, P. (2025). Learning Energy Profile: An evidence-based tool for optimizing 
personal study architectures. GitHub Repository. 
https://github.com/dsci3d/learning-energy-profile
```

---

**Version:** 0.2.1  
**Last updated:** November 2025
**Status:** Research code – Actively developed in workshop context

