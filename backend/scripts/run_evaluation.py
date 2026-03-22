"""One-command alias for evaluation pipeline (manual and CI friendly)."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Run evaluation pipeline alias")
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--manifest", default="evaluation/datasets/manifest.json")
    parser.add_argument("--annotations-dir", default="evaluation/datasets/annotations")
    parser.add_argument("--ground-truth", default="evaluation/reports/sample_ground_truth.json")
    parser.add_argument("--extracted", default="evaluation/reports/sample_extracted.json")
    parser.add_argument("--output-dir", default="evaluation/reports")
    parser.add_argument("--tolerance-profile", default="evaluation/config/tolerance_profile.json")
    parser.add_argument("--contract", default="evaluation/criteria_contract.yaml")
    parser.add_argument("--enforce-thresholds", action="store_true")
    args = parser.parse_args()

    backend_root = Path(__file__).resolve().parents[1]

    cmd = [
        sys.executable,
        "-m",
        "src.evaluation.run_day2",
        "--project-root",
        args.project_root,
        "--manifest",
        args.manifest,
        "--annotations-dir",
        args.annotations_dir,
        "--ground-truth",
        args.ground_truth,
        "--extracted",
        args.extracted,
        "--output-dir",
        args.output_dir,
        "--tolerance-profile",
        args.tolerance_profile,
        "--contract",
        args.contract,
    ]
    if args.enforce_thresholds:
        cmd.append("--enforce-thresholds")

    completed = subprocess.run(cmd, cwd=str(backend_root), check=False)
    raise SystemExit(completed.returncode)


if __name__ == "__main__":
    main()
