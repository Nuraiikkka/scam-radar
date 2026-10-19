import random

from app.services import fusion, text_classifier, vision_rules
from app.settings.conf import settings


def test_model_file_exists():
    assert settings.text_model_path.exists()
    assert text_classifier.model_version() == "v1.0.0"


def test_russian_investment_scam():
    result = text_classifier.classify_text(
        "Платформа даёт 30% в день, пассивный доход без риска, вклад от 5000, пиши в телеграм", "speech"
    )
    assert result.best_category == "investment_platform"
    assert result.text_score > 0.6
    assert result.reasons
    assert result.reasons[0]["source"] in ("speech", "rule")


def test_english_betting_scam():
    result = text_classifier.classify_text(
        "Fixed match today, odds 15, sure win, casino free spins promo code", "speech"
    )
    assert result.best_category == "betting"


def test_safe_text_scores_low():
    result = text_classifier.classify_text("Today we cook pancakes from my grandma's recipe, follow for more", "speech")
    assert result.scam_probability < 0.5


def test_empty_text():
    result = text_classifier.classify_text("   ", "speech")
    assert result.has_text is False
    assert result.text_score == 0


def test_kazakh_text_does_not_crash():
    result = text_classifier.classify_text("Сіз iPhone ұтып алдыңыз, жеткізу ақысын төлеңіз", "speech")
    assert 0 <= result.text_score <= 1


def test_rules_only_fallback(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "text_model_path", tmp_path / "missing.joblib")
    result = text_classifier.classify_text("Пассивный доход без риска, гарантированно, USDT", "speech")
    assert result.model_version == "rules-only"
    assert result.best_category == "investment_platform"
    assert result.text_score > 0.5
    assert any(reason["source"] == "rule" for reason in result.reasons)


def empty_result():
    return text_classifier.TextResult()


def test_fusion_nothing_found():
    result = fusion.fuse(empty_result(), empty_result(), [], [], False)
    assert result.risk_score == 0
    assert result.category == "none"
    assert result.reasons[0]["code"] == "no_content"


def test_fusion_scam_from_speech_only():
    speech = text_classifier.classify_text(
        "Я вложила 10000 в платформу и вывела миллион, пассивный доход 30% в день", "speech"
    )
    result = fusion.fuse(speech, empty_result(), [], [], False)
    assert result.category == "investment_platform"
    assert result.risk_score >= settings.fusion_none_threshold


def test_fusion_contacts_without_pitch_stay_below_threshold():
    cues = vision_rules.analyze_text("t.me/a t.me/b @handle_one @handle_two +7 701 555 12 34", "screen_text")["cues"]
    result = fusion.fuse(empty_result(), empty_result(), [], cues, True)
    assert result.category == "none"
    assert result.risk_score < settings.fusion_none_threshold


def test_fusion_weights_from_settings(monkeypatch):
    speech = text_classifier.classify_text("Invest now, guaranteed profit 20% daily, passive income", "speech")
    cues = vision_rules.analyze_text("cafe.kz", "screen_text")["cues"]
    monkeypatch.setattr(settings, "fusion_text_weight", 1.0)
    monkeypatch.setattr(settings, "fusion_vision_weight", 0.0)
    text_only = fusion.fuse(speech, empty_result(), [], cues, True)
    monkeypatch.setattr(settings, "fusion_text_weight", 0.0)
    monkeypatch.setattr(settings, "fusion_vision_weight", 1.0)
    vision_only = fusion.fuse(speech, empty_result(), [], cues, True)
    assert text_only.risk_score > vision_only.risk_score


def test_fusion_threshold_from_settings(monkeypatch):
    speech = text_classifier.classify_text("Invest now, guaranteed profit 20% daily, passive income", "speech")
    monkeypatch.setattr(settings, "fusion_none_threshold", 0.99)
    result = fusion.fuse(speech, empty_result(), [], [], False)
    assert result.category == "none"


def test_fusion_always_bounded_and_explained():
    rng = random.Random(3)
    words = ["доход", "30%", "в день", "casino", "t.me/a", "giveaway", "работа", "plov", "@abcdef", "x10", "$500"]
    for _ in range(200):
        text = " ".join(rng.choice(words) for _ in range(rng.randint(0, 8)))
        speech = text_classifier.classify_text(text, "speech")
        screen = text_classifier.classify_text(text[::-1], "screen_text")
        cues = vision_rules.analyze_text(text, "screen_text")["cues"]
        result = fusion.fuse(speech, screen, cues, cues, bool(text))
        assert 0 <= result.risk_score <= 1
        assert result.reasons
        for reason in result.reasons:
            assert reason["source"] in ("speech", "screen_text", "qr", "rule", "classifier")
            assert reason["message_en"] and reason["message_ru"]


def test_clamp_handles_nan():
    assert fusion.clamp(float("nan")) == 0
    assert fusion.clamp(5) == 1
    assert fusion.clamp(-1) == 0


def test_fusion_keeps_only_reasons_for_the_final_category():
    speech = text_classifier.classify_text(
        "Договорной матч, коэффициент 15, ставка заходит гарантированно, депозит удваиваем", "speech"
    )
    result = fusion.fuse(speech, empty_result(), [], [], False)
    assert result.category == "betting"
    for reason in result.reasons:
        if reason["code"].startswith("keywords_") or reason["code"].startswith("classifier_"):
            assert reason["code"].endswith("_betting")
