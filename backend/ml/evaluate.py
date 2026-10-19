import argparse
import csv
import json
import shutil
import sys
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path

from sklearn.metrics import accuracy_score, f1_score

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.services import pipeline
from app.services.text_classifier import ALL_CATEGORIES

REPO_DIR = BACKEND_DIR.parent
DEFAULT_SAMPLES = REPO_DIR / "data" / "samples"
REPORTS_DIR = BACKEND_DIR / "ml" / "reports"


def load_manifest(samples_dir: Path) -> list[dict]:
    with open(samples_dir / "samples.csv", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def run_one(video_path: Path) -> dict:
    work_dir = Path(tempfile.mkdtemp(prefix="evaluate-"))
    started = time.monotonic()
    try:
        result = pipeline.analyze_local_video(video_path, work_dir)
        top_reason = ""
        if result["reasons"]:
            top_reason = result["reasons"][0]["message_en"]
        return {
            "category": result["fusion"].category,
            "risk_score": result["fusion"].risk_score,
            "seconds": round(time.monotonic() - started, 1),
            "top_reason": top_reason,
            "error": "",
        }
    except pipeline.PipelineError as exc:
        return {"category": "error", "risk_score": None, "seconds": 0, "top_reason": "", "error": exc.code}
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


def markdown_table(rows: list[dict]) -> str:
    lines = [
        "| Video | Lang | Expected | Actual | Risk | Match | Seconds | Top reason |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        risk = "-"
        if row["risk_score"] is not None:
            risk = format(row["risk_score"], ".2f")
        match = "NO"
        if row["expected"] == row["category"]:
            match = "yes"
        lines.append(
            "| "
            + row["file"]
            + " | "
            + row["lang"]
            + " | "
            + row["expected"]
            + " | "
            + row["category"]
            + " | "
            + risk
            + " | "
            + match
            + " | "
            + str(row["seconds"])
            + " | "
            + row["top_reason"].replace("|", "/")
            + " |"
        )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the full pipeline on labeled sample videos")
    parser.add_argument("--samples", type=Path, default=DEFAULT_SAMPLES)
    parser.add_argument("--output", type=Path, default=REPORTS_DIR)
    args = parser.parse_args()

    rows = []
    for item in load_manifest(args.samples):
        outcome = run_one(args.samples / item["file"])
        row = {"file": item["file"], "lang": item["lang"], "expected": item["category"]}
        row.update(outcome)
        rows.append(row)
        print(item["file"] + ": expected " + item["category"] + ", got " + outcome["category"])

    expected = []
    actual = []
    expected_scam = []
    actual_scam = []
    for row in rows:
        expected.append(row["expected"])
        actual.append(row["category"])
        expected_scam.append(row["expected"] != "none")
        actual_scam.append(row["category"] != "none" and row["category"] != "error")
    present = []
    for category in ALL_CATEGORIES:
        if category in expected:
            present.append(category)
    report = {
        "evaluated_at": datetime.now(UTC).isoformat(),
        "videos": len(rows),
        "category_accuracy": round(accuracy_score(expected, actual), 4),
        "category_macro_f1": round(f1_score(expected, actual, labels=present, average="macro", zero_division=0), 4),
        "scam_vs_safe_accuracy": round(accuracy_score(expected_scam, actual_scam), 4),
        "rows": rows,
    }
    args.output.mkdir(parents=True, exist_ok=True)
    with open(args.output / "evaluation_latest.json", "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
    table = markdown_table(rows)
    with open(args.output / "evaluation_latest.md", "w", encoding="utf-8") as handle:
        handle.write("# End-to-end evaluation\n\n")
        handle.write("Videos: " + str(len(rows)) + "\n\n")
        handle.write("Category accuracy: " + str(report["category_accuracy"]) + "\n\n")
        handle.write("Category macro F1: " + str(report["category_macro_f1"]) + "\n\n")
        handle.write("Scam vs safe accuracy: " + str(report["scam_vs_safe_accuracy"]) + "\n\n")
        handle.write(table + "\n")
    print(table)
    print("category accuracy " + str(report["category_accuracy"]) + ", macro F1 " + str(report["category_macro_f1"]))


if __name__ == "__main__":
    main()
