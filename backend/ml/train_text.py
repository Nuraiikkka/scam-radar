import argparse
import csv
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import FeatureUnion, Pipeline

BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_DIR = BACKEND_DIR.parent
DEFAULT_LABELS = REPO_DIR / "data" / "labels.csv"
MODELS_DIR = BACKEND_DIR / "ml" / "models"
CATEGORIES = ["investment_platform", "pyramid", "betting", "giveaway", "job_offer", "none"]


def load_rows(path: Path) -> list[dict]:
    rows = []
    with open(path, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            text = (row.get("text") or "").strip()
            category = (row.get("category") or "").strip()
            if not text or category not in CATEGORIES:
                continue
            rows.append(
                {
                    "text": text,
                    "category": category,
                    "source": (row.get("source") or "unknown").strip(),
                    "lang": (row.get("lang") or "").strip(),
                }
            )
    return rows


def group_of(row: dict) -> str:
    source = row["source"]
    if source.startswith("synthetic:"):
        return source
    return "row:" + row["text"][:40]


def build_pipeline() -> Pipeline:
    features = FeatureUnion(
        [
            ("chars", TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), min_df=2, sublinear_tf=True)),
            ("words", TfidfVectorizer(analyzer="word", ngram_range=(1, 2), min_df=1, sublinear_tf=True)),
        ]
    )
    classifier = LogisticRegression(C=4.0, max_iter=3000, class_weight="balanced")
    return Pipeline([("features", features), ("classifier", classifier)])


def texts_of(rows: list[dict]) -> list[str]:
    texts = []
    for row in rows:
        texts.append(row["text"])
    return texts


def labels_of(rows: list[dict]) -> list[str]:
    labels = []
    for row in rows:
        labels.append(row["category"])
    return labels


def pick_rows(rows: list[dict], indexes) -> list[dict]:
    picked = []
    for index in indexes:
        picked.append(rows[index])
    return picked


def make_folds(rows: list[dict], seed: int) -> list[tuple[list[dict], list[dict]]]:
    groups = []
    for row in rows:
        groups.append(group_of(row))
    splitter = StratifiedGroupKFold(n_splits=4, shuffle=True, random_state=seed)
    folds = []
    for train_indexes, test_indexes in splitter.split(rows, labels_of(rows), groups):
        folds.append((pick_rows(rows, train_indexes), pick_rows(rows, test_indexes)))
    return folds


def cross_validate(folds: list[tuple[list[dict], list[dict]]]) -> list[float]:
    scores = []
    for train, test in folds:
        pipeline = build_pipeline()
        pipeline.fit(texts_of(train), labels_of(train))
        predicted = pipeline.predict(texts_of(test))
        scores.append(f1_score(labels_of(test), predicted, labels=CATEGORIES, average="macro", zero_division=0))
    return scores


def print_confusion(matrix) -> None:
    short_names = ["inv", "pyr", "bet", "give", "job", "none"]
    print("confusion matrix (rows = true, columns = predicted)")
    header = "     "
    for name in short_names:
        header = header + " " + name.rjust(5)
    print(header)
    for index in range(len(short_names)):
        line = short_names[index].rjust(5)
        for value in matrix[index]:
            line = line + " " + str(value).rjust(5)
        print(line)


def count_by(rows: list[dict], key: str) -> dict:
    counts = {}
    for row in rows:
        counts[row[key]] = counts.get(row[key], 0) + 1
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the text classifier")
    parser.add_argument("--labels", type=Path, default=DEFAULT_LABELS)
    parser.add_argument("--version", default=None)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--output-dir", type=Path, default=MODELS_DIR)
    args = parser.parse_args()

    rows = load_rows(args.labels)
    if len(rows) < 60:
        raise SystemExit("Need at least 60 labeled rows, found " + str(len(rows)))
    synthetic = 0
    for row in rows:
        if row["source"].startswith("synthetic"):
            synthetic = synthetic + 1

    folds = make_folds(rows, args.seed)
    train, test = folds[0]
    pipeline = build_pipeline()
    pipeline.fit(texts_of(train), labels_of(train))

    true_labels = labels_of(test)
    predicted = list(pipeline.predict(texts_of(test)))
    accuracy = accuracy_score(true_labels, predicted)
    macro_f1 = f1_score(true_labels, predicted, labels=CATEGORIES, average="macro", zero_division=0)
    report_text = classification_report(true_labels, predicted, labels=CATEGORIES, digits=3, zero_division=0)
    report = classification_report(true_labels, predicted, labels=CATEGORIES, output_dict=True, zero_division=0)
    matrix = confusion_matrix(true_labels, predicted, labels=CATEGORIES)

    print("dataset rows: " + str(len(rows)) + " (synthetic: " + str(synthetic) + ")")
    print("train rows: " + str(len(train)) + ", held-out rows: " + str(len(test)))
    print("held-out split is by template group, so test templates are never seen in training")
    print("accuracy: " + format(accuracy, ".3f"))
    print("macro F1: " + format(macro_f1, ".3f"))
    print(report_text)
    print_confusion(matrix)
    fold_scores = cross_validate(folds)
    fold_mean = sum(fold_scores) / len(fold_scores)
    shown_scores = []
    rounded_scores = []
    for score in fold_scores:
        shown_scores.append(format(score, ".3f"))
        rounded_scores.append(round(score, 4))
    print(
        "4-fold group cross-validation macro F1: "
        + ", ".join(shown_scores)
        + " (mean "
        + format(fold_mean, ".3f")
        + ")"
    )

    version = args.version
    if version is None:
        version = "v" + datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    metrics = {
        "version": version,
        "trained_at": datetime.now(UTC).isoformat(),
        "dataset_rows": len(rows),
        "synthetic_rows": synthetic,
        "train_rows": len(train),
        "test_rows": len(test),
        "languages": count_by(rows, "lang"),
        "accuracy": round(accuracy, 4),
        "macro_f1": round(macro_f1, 4),
        "cv_macro_f1": rounded_scores,
        "cv_macro_f1_mean": round(fold_mean, 4),
        "per_class": {},
        "confusion_matrix": matrix.tolist(),
        "labels": CATEGORIES,
    }
    for category in CATEGORIES:
        values = report[category]
        metrics["per_class"][category] = {
            "precision": round(values["precision"], 4),
            "recall": round(values["recall"], 4),
            "f1": round(values["f1-score"], 4),
            "support": int(values["support"]),
        }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    bundle = {"pipeline": pipeline, "version": version, "labels": CATEGORIES, "metrics": metrics}
    model_path = args.output_dir / ("text_model_" + version + ".joblib")
    joblib.dump(bundle, model_path)
    shutil.copyfile(model_path, args.output_dir / "text_model_latest.joblib")
    metrics_path = args.output_dir / ("text_model_" + version + ".metrics.json")
    with open(metrics_path, "w", encoding="utf-8") as handle:
        json.dump(metrics, handle, ensure_ascii=False, indent=2)
    shutil.copyfile(metrics_path, args.output_dir / "text_model_latest.metrics.json")
    print("saved model " + str(model_path))


if __name__ == "__main__":
    main()
