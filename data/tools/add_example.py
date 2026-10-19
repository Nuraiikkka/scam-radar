import argparse
import csv
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent
CATEGORIES = ["investment_platform", "pyramid", "betting", "giveaway", "job_offer", "none"]
LANGUAGES = ["ru", "en", "kk", "other"]
FIELDS = ["text", "category", "source", "lang"]


def validate(text: str, category: str, source: str, lang: str) -> None:
    if len(text.strip()) < 10:
        raise SystemExit("Text is too short, write at least 10 characters")
    if category not in CATEGORIES:
        raise SystemExit("Category must be one of: " + ", ".join(CATEGORIES))
    if lang not in LANGUAGES:
        raise SystemExit("Language must be one of: " + ", ".join(LANGUAGES))
    if not source.strip():
        raise SystemExit("Source must not be empty, for example real:tiktok or synthetic:manual")


def already_exists(labels: Path, text: str) -> bool:
    if not labels.exists():
        return False
    with open(labels, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row["text"].strip().lower() == text.strip().lower():
                return True
    return False


def append_row(labels: Path, row: dict) -> None:
    new_file = not labels.exists()
    with open(labels, "a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        if new_file:
            writer.writeheader()
        writer.writerow(row)


def main() -> None:
    parser = argparse.ArgumentParser(description="Add one labeled example to data/labels.csv")
    parser.add_argument("--text", required=True)
    parser.add_argument("--category", required=True)
    parser.add_argument("--source", default="real:manual")
    parser.add_argument("--lang", default="ru")
    parser.add_argument("--labels", type=Path, default=DATA_DIR / "labels.csv")
    args = parser.parse_args()
    validate(args.text, args.category, args.source, args.lang)
    if already_exists(args.labels, args.text):
        raise SystemExit("This text is already in the dataset")
    append_row(
        args.labels,
        {
            "text": args.text.strip(),
            "category": args.category,
            "source": args.source.strip(),
            "lang": args.lang,
        },
    )
    print("Added 1 example with category " + args.category)


if __name__ == "__main__":
    main()
