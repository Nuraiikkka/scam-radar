import logging
import threading
from dataclasses import dataclass, field
from pathlib import Path

import joblib

from app.settings.conf import settings

logger = logging.getLogger("scamradar.text")

SCAM_CATEGORIES = ["investment_platform", "pyramid", "betting", "giveaway", "job_offer"]
ALL_CATEGORIES = SCAM_CATEGORIES + ["none"]

CATEGORY_NAMES_EN = {
    "investment_platform": "an investment platform pitch",
    "pyramid": "a pyramid or referral scheme",
    "betting": "betting or casino promotion",
    "giveaway": "a fake giveaway",
    "job_offer": "a suspicious job offer",
    "none": "ordinary content",
}
CATEGORY_NAMES_RU = {
    "investment_platform": "реклама инвестиционной платформы",
    "pyramid": "пирамида или реферальная схема",
    "betting": "реклама ставок или казино",
    "giveaway": "фальшивый розыгрыш",
    "job_offer": "подозрительное предложение работы",
    "none": "обычный контент",
}
SOURCE_PREFIX_EN = {"speech": "In speech", "screen_text": "On screen"}
SOURCE_PREFIX_RU = {"speech": "В речи", "screen_text": "На экране"}
SOURCE_PLACE_EN = {"speech": "speech", "screen_text": "screen text"}
SOURCE_PLACE_RU = {"speech": "речи", "screen_text": "тексте на экране"}

KEYWORDS = {
    "investment_platform": [
        ("пассивный доход", 0.3),
        ("пассивного дохода", 0.3),
        ("гарантированн", 0.3),
        ("без риска", 0.3),
        ("инвестиц", 0.12),
        ("инвестир", 0.12),
        ("платформ", 0.08),
        ("криптовалют", 0.12),
        ("крипт", 0.08),
        ("usdt", 0.2),
        ("биткоин", 0.12),
        ("торговый бот", 0.3),
        ("арбитраж", 0.25),
        ("депозит", 0.12),
        ("доход в день", 0.35),
        ("прибыль в день", 0.35),
        ("passive income", 0.3),
        ("guaranteed", 0.3),
        ("risk free", 0.3),
        ("risk-free", 0.3),
        ("invest", 0.12),
        ("crypto", 0.1),
        ("bitcoin", 0.12),
        ("trading bot", 0.3),
        ("deposit", 0.12),
        ("profit per day", 0.35),
        ("daily profit", 0.35),
        ("withdraw", 0.12),
        ("вывод средств", 0.15),
        ("табыс", 0.1),
        ("инвестиция", 0.12),
    ],
    "pyramid": [
        ("приведи друга", 0.25),
        ("приглашай друзей", 0.25),
        ("пригласи", 0.15),
        ("реферал", 0.25),
        ("рефераль", 0.25),
        ("за каждого приглашённого", 0.35),
        ("за каждого приглашенного", 0.35),
        ("сетевой маркетинг", 0.25),
        ("вступительный взнос", 0.35),
        ("свою команду", 0.15),
        ("уровень", 0.06),
        ("структур", 0.1),
        ("invite friends", 0.25),
        ("invite your friends", 0.25),
        ("referral", 0.25),
        ("for every person you invite", 0.35),
        ("recruit", 0.2),
        ("downline", 0.35),
        ("network marketing", 0.25),
        ("entry fee", 0.35),
        ("build your team", 0.2),
        ("mlm", 0.3),
    ],
    "betting": [
        ("ставк", 0.2),
        ("букмекер", 0.3),
        ("казино", 0.3),
        ("слот", 0.15),
        ("коэффициент", 0.15),
        ("договорн", 0.35),
        ("прогноз на матч", 0.3),
        ("экспресс", 0.12),
        ("джекпот", 0.25),
        ("фриспин", 0.3),
        ("промокод", 0.1),
        ("betting", 0.25),
        ("casino", 0.3),
        ("slots", 0.2),
        ("odds", 0.12),
        ("fixed match", 0.4),
        ("jackpot", 0.25),
        ("free spins", 0.3),
        ("bet ", 0.12),
        ("1xbet", 0.4),
        ("bookmaker", 0.3),
        ("sure win", 0.35),
    ],
    "giveaway": [
        ("розыгрыш", 0.2),
        ("разыгрываем", 0.2),
        ("раздача", 0.2),
        ("раздаём", 0.2),
        ("раздаем", 0.2),
        ("вы выиграли", 0.35),
        ("оплатите доставку", 0.4),
        ("оплатить доставку", 0.4),
        ("победител", 0.12),
        ("бесплатно", 0.08),
        ("приз", 0.1),
        ("подарок", 0.08),
        ("giveaway", 0.2),
        ("you won", 0.35),
        ("you have won", 0.35),
        ("pay for shipping", 0.4),
        ("pay the shipping", 0.4),
        ("winner", 0.12),
        ("free iphone", 0.3),
        ("claim your", 0.25),
        ("prize", 0.12),
        ("for free", 0.06),
    ],
    "job_offer": [
        ("подработк", 0.15),
        ("вакансия", 0.08),
        ("удалённая работа", 0.12),
        ("удаленная работа", 0.12),
        ("без опыта", 0.15),
        ("оплата за лайки", 0.4),
        ("за лайки", 0.3),
        ("простые задания", 0.3),
        ("оформить карту", 0.35),
        ("оформи карту", 0.35),
        ("курьер", 0.08),
        ("зарплата от", 0.12),
        ("в день без вложений", 0.3),
        ("work from home", 0.15),
        ("remote job", 0.12),
        ("no experience", 0.15),
        ("paid to like", 0.4),
        ("simple tasks", 0.3),
        ("hiring now", 0.12),
        ("earn per task", 0.35),
        ("open a bank card", 0.35),
        ("салары", 0.05),
        ("жұмыс", 0.08),
    ],
}

model_lock = threading.Lock()
model_cache = {}


@dataclass
class TextResult:
    probabilities: dict = field(default_factory=dict)
    rule_scores: dict = field(default_factory=dict)
    matched_keywords: dict = field(default_factory=dict)
    scam_probability: float = 0.0
    text_score: float = 0.0
    best_category: str = "none"
    model_version: str = "none"
    reasons: list = field(default_factory=list)
    has_text: bool = False


def load_model(path: Path):
    if not path.exists():
        return None
    mtime = path.stat().st_mtime
    key = str(path)
    with model_lock:
        cached = model_cache.get(key)
        if cached is not None and cached[0] == mtime:
            return cached[1]
        bundle = joblib.load(path)
        model_cache[key] = (mtime, bundle)
        logger.info("text model loaded", extra={"stage": bundle.get("version")})
        return bundle


def get_model():
    bundle = load_model(settings.text_model_path)
    if bundle is None:
        logger.warning("text model file not found, using keyword rules only")
    return bundle


def model_version() -> str:
    bundle = get_model()
    if bundle is None:
        return "rules-only"
    return str(bundle["version"])


def keyword_scores(text: str) -> tuple[dict, dict]:
    lowered = text.lower()
    scores = {}
    matched = {}
    for category in SCAM_CATEGORIES:
        remaining = 1.0
        found = []
        for keyword, weight in KEYWORDS[category]:
            if keyword in lowered:
                remaining = remaining * (1.0 - weight)
                found.append(keyword.strip())
        scores[category] = 1.0 - remaining
        matched[category] = found
    return scores, matched


def model_probabilities(bundle, text: str) -> dict:
    pipeline = bundle["pipeline"]
    values = pipeline.predict_proba([text])[0]
    probabilities = {}
    for category in ALL_CATEGORIES:
        probabilities[category] = 0.0
    for index, label in enumerate(pipeline.classes_):
        probabilities[str(label)] = float(values[index])
    return probabilities


def pairwise_scam_probability(probabilities: dict) -> float:
    best_scam = 0.0
    for category in SCAM_CATEGORIES:
        best_scam = max(best_scam, probabilities[category])
    total = best_scam + probabilities["none"]
    if total <= 0:
        return 0.0
    return best_scam / total


def percent(value: float) -> str:
    return str(int(round(value * 100))) + "%"


def build_reasons(result: TextResult, source: str) -> list:
    reasons = []
    category = result.best_category
    confident = result.probabilities.get(category, 0.0) >= 0.4
    if category != "none" and confident and result.scam_probability >= 0.5 and result.model_version != "rules-only":
        reasons.append(
            {
                "source": source,
                "code": "classifier_" + category,
                "message_en": SOURCE_PREFIX_EN[source]
                + ": sounds like "
                + CATEGORY_NAMES_EN[category]
                + " (model confidence "
                + percent(result.probabilities[category])
                + ")",
                "message_ru": SOURCE_PREFIX_RU[source]
                + ": похоже на "
                + CATEGORY_NAMES_RU[category]
                + " (уверенность модели "
                + percent(result.probabilities[category])
                + ")",
                "weight": result.scam_probability,
            }
        )
    for scam_category in SCAM_CATEGORIES:
        words = result.matched_keywords.get(scam_category, [])
        if not words or result.rule_scores[scam_category] < 0.2:
            continue
        quoted = []
        for word in words[:4]:
            quoted.append("«" + word + "»")
        shown = ", ".join(quoted)
        reasons.append(
            {
                "source": "rule",
                "code": "keywords_" + scam_category,
                "message_en": "Rule: "
                + SOURCE_PLACE_EN[source]
                + " uses phrases typical for "
                + CATEGORY_NAMES_EN[scam_category]
                + ": "
                + shown,
                "message_ru": "Правило: в "
                + SOURCE_PLACE_RU[source]
                + " есть фразы, типичные для категории «"
                + CATEGORY_NAMES_RU[scam_category]
                + "»: "
                + shown,
                "weight": result.rule_scores[scam_category],
            }
        )
    return reasons


def classify_text(text: str, source: str) -> TextResult:
    clean = (text or "").strip()
    if not clean:
        return TextResult(model_version=model_version())
    rule_scores, matched = keyword_scores(clean)
    rule_total = max(rule_scores.values())
    bundle = get_model()
    if bundle is None:
        probabilities = {}
        for category in SCAM_CATEGORIES:
            probabilities[category] = rule_scores[category]
        probabilities["none"] = 1.0 - rule_total
        scam_probability = rule_total
        text_score = rule_total
        version = "rules-only"
    else:
        probabilities = model_probabilities(bundle, clean)
        scam_probability = pairwise_scam_probability(probabilities)
        text_score = 0.75 * scam_probability + 0.25 * rule_total
        version = str(bundle["version"])
    best_category = "none"
    best_value = 0.0
    for category in SCAM_CATEGORIES:
        value = probabilities[category] + 0.2 * rule_scores[category]
        if value > best_value:
            best_value = value
            best_category = category
    result = TextResult(
        probabilities=probabilities,
        rule_scores=rule_scores,
        matched_keywords=matched,
        scam_probability=scam_probability,
        text_score=max(0.0, min(1.0, text_score)),
        best_category=best_category,
        model_version=version,
        has_text=True,
    )
    result.reasons = build_reasons(result, source)
    return result
