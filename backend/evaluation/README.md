# Evaluation Commands (Day 5)

This folder contains benchmark inputs, contract configuration, and generated reports.

## One-command alias (manual)

From workspace root:

```powershell
"C:/Users/Asus/Desktop/IIT  Hackathon/Skills/antigravity-awesome-skills/skills/notebooklm/.venv/Scripts/python.exe" "backend/scripts/run_evaluation.py"
```

Strict threshold gate mode:

```powershell
"C:/Users/Asus/Desktop/IIT  Hackathon/Skills/antigravity-awesome-skills/skills/notebooklm/.venv/Scripts/python.exe" "backend/scripts/run_evaluation.py" --enforce-thresholds
```

From backend root:

```powershell
"C:/Users/Asus/Desktop/IIT  Hackathon/Skills/antigravity-awesome-skills/skills/notebooklm/.venv/Scripts/python.exe" "scripts/run_evaluation.py"
```

## Direct module command (manual or CI)

From backend root:

```powershell
"C:/Users/Asus/Desktop/IIT  Hackathon/Skills/antigravity-awesome-skills/skills/notebooklm/.venv/Scripts/python.exe" -m src.evaluation.run_day2 --project-root "." --manifest "evaluation/datasets/manifest.json" --annotations-dir "evaluation/datasets/annotations" --ground-truth "evaluation/reports/sample_ground_truth.json" --extracted "evaluation/reports/sample_extracted.json" --output-dir "evaluation/reports" --tolerance-profile "evaluation/config/tolerance_profile.json" --contract "evaluation/criteria_contract.yaml"
```

## Required output artifacts

As defined in [evaluation/criteria_contract.yaml](evaluation/criteria_contract.yaml):
- summary.json
- by_criterion.json
- by_doc_type.json
- ocr_quality_report.json
- failures.csv

Additionally generated:
- run_manifest.json

## CI snippet

Use this command in CI jobs from backend working directory:

```powershell
"C:/Users/Asus/Desktop/IIT  Hackathon/Skills/antigravity-awesome-skills/skills/notebooklm/.venv/Scripts/python.exe" -m src.evaluation.run_day2 --project-root "." --manifest "evaluation/datasets/manifest.json" --annotations-dir "evaluation/datasets/annotations" --ground-truth "evaluation/reports/sample_ground_truth.json" --extracted "evaluation/reports/sample_extracted.json" --output-dir "evaluation/reports" --tolerance-profile "evaluation/config/tolerance_profile.json" --contract "evaluation/criteria_contract.yaml"
```

The command exits non-zero if:
- input validation fails
- payload integrity fails
- benchmark run fails
- any required output artifact is missing

In strict mode (`--enforce-thresholds`), it also exits non-zero when extraction thresholds in [evaluation/criteria_contract.yaml](evaluation/criteria_contract.yaml) are violated.
