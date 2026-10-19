import pytest

from app.services import pipeline
from app.settings.conf import settings
from tests.conftest import sample_path

pytestmark = pytest.mark.slow

EXPECTED = [
    ("scam_invest_ru.mp4", "investment_platform"),
    ("scam_invest_en.mp4", "investment_platform"),
    ("scam_betting_ru.mp4", "betting"),
    ("scam_giveaway_en.mp4", "giveaway"),
    ("scam_job_ru.mp4", "job_offer"),
    ("safe_cooking_ru.mp4", "none"),
    ("safe_travel_en.mp4", "none"),
    ("silent_scam_screen.mp4", "investment_platform"),
    ("silent_no_text.mp4", "none"),
]


@pytest.fixture
def full_models(monkeypatch):
    monkeypatch.setattr(settings, "whisper_enabled", True)
    monkeypatch.setattr(settings, "ocr_enabled", True)


@pytest.mark.parametrize("name,category", EXPECTED)
def test_sample_video_end_to_end(full_models, tmp_path, name, category):
    result = pipeline.analyze_local_video(sample_path(name), tmp_path)
    fused = result["fusion"]
    assert 0 <= fused.risk_score <= 1
    assert result["reasons"]
    assert fused.category == category, [reason["message_en"] for reason in result["reasons"]]


def test_russian_speech_and_screen_evidence(full_models, tmp_path):
    result = pipeline.analyze_local_video(sample_path("scam_invest_ru.mp4"), tmp_path)
    assert result["transcript"].language == "ru"
    assert "t.me/profit_daily" in result["links"]
    assert "https://t.me/profit_daily" in result["vision"].qr_codes
    sources = set()
    for reason in result["reasons"]:
        sources.add(reason["source"])
    assert "qr" in sources or "screen_text" in sources


def test_ocr_noise_is_normalized(full_models, tmp_path):
    result = pipeline.analyze_local_video(sample_path("silent_scam_screen.mp4"), tmp_path)
    assert result["transcript"].status == "no_audio"
    assert any(link.startswith("t.me/") for link in result["links"])


def test_video_without_text(full_models, tmp_path):
    result = pipeline.analyze_local_video(sample_path("silent_no_text.mp4"), tmp_path)
    assert result["fusion"].risk_score < settings.fusion_none_threshold
    assert result["reasons"][0]["code"] in ("no_content", "no_signals")


def test_evaluate_script_reports_metrics(full_models, tmp_path, monkeypatch):
    import json
    import sys

    from ml import evaluate

    monkeypatch.setattr(sys, "argv", ["evaluate.py", "--output", str(tmp_path)])
    evaluate.main()
    report = json.loads((tmp_path / "evaluation_latest.json").read_text())
    assert report["videos"] == 11
    assert 0 <= report["category_macro_f1"] <= 1
    assert (tmp_path / "evaluation_latest.md").read_text().startswith("# End-to-end evaluation")
