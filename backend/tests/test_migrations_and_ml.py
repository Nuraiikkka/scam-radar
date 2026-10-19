import json
import subprocess
import sys

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import create_engine

from app.db import Base
from tests.conftest import BACKEND_DIR, REPO_DIR, alembic_config


def test_migrations_match_models():
    from app.db import engine

    with engine.connect() as connection:
        context = MigrationContext.configure(connection)
        differences = compare_metadata(context, Base.metadata)
    assert differences == []


def test_downgrade_and_upgrade(tmp_path, monkeypatch):
    url = "sqlite:///" + str(tmp_path / "migrate.db")
    monkeypatch.setattr("app.settings.conf.settings.database_url", url)
    config = alembic_config()
    command.upgrade(config, "head")
    command.downgrade(config, "base")
    command.upgrade(config, "head")
    engine = create_engine(url)
    with engine.connect() as connection:
        tables = set(connection.exec_driver_sql("SELECT name FROM sqlite_master WHERE type='table'").scalars())
    assert {"users", "videos", "analyses", "signals", "feedback"} <= tables


def test_training_script(tmp_path):
    output = tmp_path / "models"
    completed = subprocess.run(
        [sys.executable, str(BACKEND_DIR / "ml" / "train_text.py"), "--version", "vtest", "--output-dir", str(output)],
        capture_output=True,
        text=True,
        check=True,
        cwd=str(BACKEND_DIR),
    )
    assert "macro F1" in completed.stdout
    assert "confusion matrix" in completed.stdout
    assert (output / "text_model_vtest.joblib").exists()
    assert (output / "text_model_latest.joblib").exists()
    metrics = json.loads((output / "text_model_vtest.metrics.json").read_text())
    assert metrics["dataset_rows"] >= 300
    assert set(metrics["per_class"]) == {"investment_platform", "pyramid", "betting", "giveaway", "job_offer", "none"}


def test_add_example_tool(tmp_path):
    labels = tmp_path / "labels.csv"
    tool = REPO_DIR / "data" / "tools" / "add_example.py"
    ok = subprocess.run(
        [sys.executable, str(tool), "--text", "Тестовый пример текста", "--category", "none", "--labels", str(labels)],
        capture_output=True,
        text=True,
    )
    assert ok.returncode == 0
    duplicate = subprocess.run(
        [sys.executable, str(tool), "--text", "Тестовый пример текста", "--category", "none", "--labels", str(labels)],
        capture_output=True,
        text=True,
    )
    assert duplicate.returncode != 0
    wrong = subprocess.run(
        [sys.executable, str(tool), "--text", "Another valid text", "--category", "spam", "--labels", str(labels)],
        capture_output=True,
        text=True,
    )
    assert wrong.returncode != 0
    assert labels.read_text(encoding="utf-8").count("\n") == 2


def test_dataset_is_large_and_balanced():
    import csv

    with open(REPO_DIR / "data" / "labels.csv", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) >= 300
    categories = {}
    languages = set()
    for row in rows:
        categories[row["category"]] = categories.get(row["category"], 0) + 1
        languages.add(row["lang"])
        assert row["source"].startswith("synthetic:") or row["source"].startswith("real:")
    assert len(categories) == 6
    assert min(categories.values()) >= 30
    assert {"ru", "en"} <= languages
