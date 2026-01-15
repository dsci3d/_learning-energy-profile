# Learning Energy Profile

**A research tool for exploring personal study architectures**

Developed by **Peter Kocmann**
- Freie Universität Berlin (Continuing Education),
- Charité – Universitätsmedizin Berlin,
- Technische Universität Berlin,
- University of Potsdam

---

⚠️ Scientific Status & Research Code Notice
This repository contains **research code**, developed for teaching and exploratory purposes in higher education. 
- **Transparency:** All calculation steps are fully documented and traceable.
- **Not Diagnostic:** This is not a replacement for professional psychological diagnostics.
- **Formative Use:** Intended for personal experimentation and reflection.
- **Work in Progress:** Reliability and validity studies are ongoing (see [Scientific Changelog](#scientific-changelog)).
- **Institutional Use:** For high-stakes or institutional deployment, independent validation is recommended.
- **Commercial Use:** Requires explicit permission (see License).

---

## What is the Learning Energy Profile?

Learning is an energetic system. Success depends not only on cognitive ability but on the **Person-Environment Fit**. 
This tool analyzes your individual **Learning Energy Profile** across 6 research-informed dimensions (self-report proxies):

1. **Attention Architecture** – Focus stability and distractibility (Vigilance & cognitive capacity; Posner & Petersen, 1990).
2. **Sensory Processing** – Sensitivity to environmental stimuli (Sensory Processing Sensitivity; Aron & Aron, 1997).
3. **Social Energetics** — Energy gain/loss in social contexts (Extraversion proxy; Costa & McCrae, 1992).
4. **Executive Functions** — Perceived need for structure and cognitive flexibility (self-report indicator; cf. Miyake et al., 2000).
5. **Motivation Architecture** – Self-Determination Theory (Deci & Ryan, 2000) and approach/avoidance orientation.
6. **Stress Regulation** — Stress appraisal, coping, and recovery indicators (Lazarus & Folkman, 1984; McEwen, 1998).

**Additional Indices (non-core):**
- **Chronotype** — Morning/evening tendency (supplementary, not a core dimension)
- **Motivation Avoidance** — Avoidance orientation subindex (exposed separately in JSON output)

**The Goal:** 
Moving beyond the debunked "learning styles" myth, we focus on study conditions that release cognitive capacity by aligning with your physiological and psychological needs.

**Important:** 
Outputs are testable hypotheses for personal experimentation, not predictions of learning outcomes.

---

## Quick Start

### 1. Installation

```bash
git clone https://github.com/dsci3d/learning-energy-profile.git
cd learning-energy-profile
pip install -r requirements.txt
```

### 2. Complete the Questionnaire

The questionnaire consists of **88 items** (Likert scale 1-5).
- Use the `questionnaire_template.csv` in the `examples/` folder.
- Run the analyzer to generate your profile.

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
└── auswertung/..                              # Analysis report
    ├── bericht.txt                            # Questionnaire: (example) report
    ├── profil.json                            # Questionnaire: (example) aggregated data
└── charts/..                                  # Automatically generated output directory
    ├── chronotype.png                         # Visualizes morning/evening tendencies
    ├── dimension_bars.png                     # Horizontal bar chart of all dimensions
    ├── radar_chart.png                        # Radar chart of the overall profile
    └── report.html                            # Compact HTML report including all charts
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
└── lernprofil_sessions/                       # Session-Index: verknüpft Outputs verschiedener Module
    └── session_JJJJMMTT_HHMMSS.json           # JSON mit Pfaden zu profil.json, bericht.txt, charts/
└── systemprompt/                              # Systemprompts for AI
    ├── systemprompt_0.21.md                   # Systemprompt version 0.21
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
- **88 items** (e.g., A1, S1, R1, ...)
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

## Scientific Changelog

### [0.3.0] - 2025-12-18

**Status:** Research code – Actively developed in workshop context

**Refinement of Theoretical Foundation (Dimension 6)**

- **Change:** Shifted focus from specific Polyvagal Theory claims to broader frameworks of **Autonomic Regulation** and **Stress Physiology** (Lazarus & Folkman, 1984; McEwen's Allostatic Load, 1998).
- **Reasoning:** Acknowledging the ongoing scientific debate regarding the neuroanatomical premises of the Polyvagal Theory (Grossman, 2023; Neuhuber, 2022). To maintain high evidence standards, LEP now prioritizes HRV-based research and transactional stress models.
- **Evidence Update:** Integrated findings on "Metacognitive Laziness" (Fan et al., 2024) regarding AI-human interaction.

---

## Key References

- **Fan, Y., et al. (2024).** Beware of metacognitive laziness: Effects of generative AI on learning. _British Journal of Educational Technology_.
- **Grossman, P. (2023).** Fundamental challenges and likely refutations of the five basic premises of the polyvagal theory. _Biological Psychology_.
- **Lazarus, R. S., & Folkman, S. (1984).** _Stress, appraisal, and coping_. Springer.
- **Pashler, H., et al. (2008).** Learning styles: Concepts and evidence. _Psychological Science in the Public Interest_.
- **McEwen, B. S. (1998).** Protective and damaging effects of stress mediators. _NEJM_.

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
