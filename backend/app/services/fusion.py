from dataclasses import dataclass, field

from app.services.text_classifier import SCAM_CATEGORIES, TextResult
from app.services.vision_rules import Cue, score_cues
from app.settings.conf import settings

MAX_REASONS = 8
MONEY_CODES = ["high_return_claim", "multiplier_claim", "money_amount", "percent_claim"]


@dataclass
class FusionResult:
    risk_score: float
    category: str
    reasons: list = field(default_factory=list)
    text_score: float = 0.0
    vision_score: float = 0.0


def clamp(value: float) -> float:
    if value != value:
        return 0.0
    return max(0.0, min(1.0, value))


def cue_reason(cue: Cue) -> dict:
    return {
        "source": cue.source,
        "code": cue.code,
        "message_en": cue.message_en,
        "message_ru": cue.message_ru,
        "weight": cue.weight,
    }


def combined_text_score(speech: TextResult, screen: TextResult, speech_cues: list[Cue]) -> float:
    base = max(speech.text_score, screen.text_score)
    speech_cue_score = score_cues(speech_cues)
    return clamp(1.0 - (1.0 - base) * (1.0 - 0.5 * speech_cue_score))


def pick_category(speech: TextResult, screen: TextResult, cues: list[Cue]) -> str:
    best_category = "none"
    best_value = 0.0
    for category in SCAM_CATEGORIES:
        value = 0.0
        for result in (speech, screen):
            if not result.has_text:
                continue
            candidate = result.probabilities.get(category, 0.0) + 0.2 * result.rule_scores.get(category, 0.0)
            value = max(value, candidate)
        if value > best_value:
            best_value = value
            best_category = category
    if best_category != "none" and best_value >= 0.05:
        return best_category
    for cue in cues:
        if cue.code in MONEY_CODES:
            return "investment_platform"
    return "none"


def weighted_risk(text_score: float, vision_score: float, has_text: bool, has_vision: bool) -> float:
    text_weight = settings.fusion_text_weight
    vision_weight = settings.fusion_vision_weight
    if has_text and has_vision:
        total = text_weight + vision_weight
        if total <= 0:
            return 0.0
        return clamp((text_weight * text_score + vision_weight * vision_score) / total)
    if has_text:
        return clamp(text_score)
    if has_vision:
        return clamp(vision_score)
    return 0.0


def nothing_found_reason() -> dict:
    return {
        "source": "rule",
        "code": "no_content",
        "message_en": "Rule: no speech or on-screen text was found, so there is nothing to check",
        "message_ru": "Правило: в видео нет речи и текста на экране, проверять нечего",
        "weight": 0.0,
    }


def no_signals_reason() -> dict:
    return {
        "source": "rule",
        "code": "no_signals",
        "message_en": "Rule: no typical scam signals were found",
        "message_ru": "Правило: типичных признаков мошенничества не найдено",
        "weight": 0.0,
    }


def no_category_reason() -> dict:
    return {
        "source": "rule",
        "code": "contacts_without_pitch",
        "message_en": "Rule: contact details were found, but no scam pitch, so the risk stays low",
        "message_ru": "Правило: найдены контакты, но нет мошеннического предложения, поэтому риск низкий",
        "weight": 0.0,
    }


def reason_weight(reason: dict) -> float:
    return reason["weight"]


def fits_category(reason: dict, category: str) -> bool:
    code = reason["code"]
    if code.startswith("classifier_") or code.startswith("keywords_"):
        return code.endswith("_" + category)
    return True


def strip_weight(reason: dict) -> dict:
    return {
        "source": reason["source"],
        "code": reason["code"],
        "message_en": reason["message_en"],
        "message_ru": reason["message_ru"],
    }


def fuse(
    speech: TextResult, screen: TextResult, speech_cues: list[Cue], vision_cues: list[Cue], has_vision_content: bool
) -> FusionResult:
    text_score = combined_text_score(speech, screen, speech_cues)
    vision_score = clamp(score_cues(vision_cues))
    has_text = speech.has_text or screen.has_text
    has_vision = has_vision_content or len(vision_cues) > 0
    risk = weighted_risk(text_score, vision_score, has_text, has_vision)

    all_cues = list(speech_cues) + list(vision_cues)
    category = pick_category(speech, screen, all_cues)

    candidates = []
    for reason in speech.reasons + screen.reasons:
        if fits_category(reason, category):
            candidates.append(reason)
    for cue in all_cues:
        candidates.append(cue_reason(cue))
    candidates.sort(key=reason_weight, reverse=True)

    reasons = []
    seen_messages = set()
    for reason in candidates:
        if reason["message_en"] in seen_messages:
            continue
        seen_messages.add(reason["message_en"])
        reasons.append(strip_weight(reason))
        if len(reasons) >= MAX_REASONS:
            break

    threshold = settings.fusion_none_threshold
    if risk >= threshold and category == "none":
        risk = clamp(threshold - 0.01)
        reasons.insert(0, strip_weight(no_category_reason()))
    if risk < threshold:
        category = "none"

    if not reasons:
        if not has_text and not has_vision:
            reasons.append(strip_weight(nothing_found_reason()))
        else:
            reasons.append(strip_weight(no_signals_reason()))

    return FusionResult(
        risk_score=round(clamp(risk), 4),
        category=category,
        reasons=reasons,
        text_score=round(text_score, 4),
        vision_score=round(vision_score, 4),
    )
