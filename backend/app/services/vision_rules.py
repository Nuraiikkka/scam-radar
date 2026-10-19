import re
from dataclasses import dataclass

import cv2

from app.services.vision_frames import Frame

SOURCE_PREFIX_EN = {
    "screen_text": "On screen",
    "speech": "In speech",
    "qr": "In a QR code",
    "rule": "Rule",
}
SOURCE_PREFIX_RU = {
    "screen_text": "На экране",
    "speech": "В речи",
    "qr": "В QR-коде",
    "rule": "Правило",
}

HOMOGLYPHS = {
    "а": "a",
    "в": "b",
    "е": "e",
    "ё": "e",
    "і": "i",
    "к": "k",
    "м": "m",
    "н": "h",
    "о": "o",
    "р": "p",
    "с": "c",
    "т": "t",
    "у": "y",
    "х": "x",
    "ı": "i",
}

TLDS = (
    "com|ru|kz|net|org|io|me|ly|app|bet|xyz|online|site|pro|club|top|vip|cc|biz|info|co|uk|de|us|gg|tv|"
    "link|live|shop|store|win|cash|money|finance|fund|invest|trade|website|space|fun|icu|tk|ml|ga|cf|uz|"
    "by|ua|su|click|casino|games|рф"
)
RISKY_TLDS = [
    "bet",
    "xyz",
    "top",
    "vip",
    "icu",
    "tk",
    "ml",
    "ga",
    "cf",
    "cash",
    "win",
    "online",
    "site",
    "click",
    "casino",
    "money",
    "invest",
    "trade",
    "fund",
    "finance",
]
SHORTENERS = ["bit.ly", "cutt.ly", "tinyurl.com", "clck.ru", "goo.su", "t.ly", "is.gd", "rb.gy", "shorturl.at"]
COMMON_SAFE = [
    "tiktok.com",
    "instagram.com",
    "youtube.com",
    "google.com",
    "wikipedia.org",
    "kaspi.kz",
    "egov.kz",
    "gov.kz",
    "apple.com",
]

DOMAIN_LIKE = re.compile(r"[a-z0-9-]+\.(?:" + TLDS + r")\b")
TELEGRAM_FIX = re.compile(r"\bt\s?[.,·:]?\s?me\s?[/|\\l1]\s?([a-z0-9_]{1,32})\b")
WHATSAPP_FIX = re.compile(r"\bwa\s?[.,·:]?\s?me\s?[/|\\l1]\s?(\+?\d{6,15})\b")
DOT_FIX = re.compile(r"\b([a-z0-9-]{2,63})\s?[,·]\s?(" + TLDS + r")\b")
SPACED_DOT_FIX = re.compile(r"\b([a-z0-9-]{2,63})\s\.\s?(" + TLDS + r")\b")

LINK_RE = re.compile(
    r"\b(?:https?://)?(?:www\.)?[a-z0-9][a-z0-9-]{0,62}(?:\.[a-z0-9-]{1,62})*\.(?:" + TLDS + r")\b(?:/[^\s,;\"'<>()]*)?"
)
HANDLE_RE = re.compile(r"(?<![\w.@])@([a-z0-9_]{5,32})\b")
PHONE_RE = re.compile(
    r"(?<![\d+])(?:\+7|8)[\s\-(]*\d{3}[\s\-)]*\d{3}[\s\-]*\d{2}[\s\-]*\d{2}(?!\d)"
    r"|(?<![\d+])\+\d{1,3}[\s\-]?\(?\d{2,4}\)?[\s\-]?\d{3}[\s\-]?\d{2,4}(?:[\s\-]?\d{1,4})?(?!\d)"
)
PERCENT_RE = re.compile(r"(\d{1,4}(?:[.,]\d{1,2})?)\s?(?:%|процент\w*|percent)")
MULTIPLIER_RE = re.compile(r"(?<![\w])(?:x|х)\s?(\d{1,3})(?![\w])|удво\w+|утро\w+|double your|triple your")
MONEY_RE = re.compile(
    r"(?:[$€₽₸£]\s?\d[\d\s.,]*\d?\s?(?:k|к|тыс|млн)?)"
    r"|(?:\b\d[\d\s.,]*\d?\s?(?:k|к|тыс\.?|млн|million|thousand)?\s?(?:\$|usd|usdt|долл\w*|руб\w*|₽|₸|тенге|eur|€|btc)(?![\w]))"
)
PERIOD_WORDS = [
    "в день",
    "ежедневно",
    "daily",
    "per day",
    "a day",
    "в неделю",
    "weekly",
    "per week",
    "в месяц",
    "ежемесячно",
    "monthly",
    "per month",
    "гарантир",
    "guarantee",
    "без риска",
    "risk free",
    "risk-free",
    "пассивн",
    "passive",
]
CONTACT_WORDS = [
    "telegram",
    "телеграм",
    "телега",
    "whatsapp",
    "ватсап",
    "вотсап",
    "вацап",
    "пиши в лс",
    "в личку",
    "в директ",
    "dm me",
    "message me",
    "link in bio",
    "ссылка в профиле",
    "ссылка в шапке",
    "ссылка в био",
    "write me",
    "пишите в",
]


@dataclass
class Cue:
    source: str
    kind: str
    code: str
    value: str
    weight: float
    message_en: str
    message_ru: str


def make_cue(source: str, kind: str, code: str, value: str, weight: float, text_en: str, text_ru: str) -> Cue:
    message_en = SOURCE_PREFIX_EN[source] + ": " + text_en
    message_ru = SOURCE_PREFIX_RU[source] + ": " + text_ru
    return Cue(
        source=source,
        kind=kind,
        code=code,
        value=value[:500],
        weight=weight,
        message_en=message_en,
        message_ru=message_ru,
    )


def map_homoglyphs(token: str) -> str:
    letters = []
    for char in token:
        letters.append(HOMOGLYPHS.get(char, char))
    return "".join(letters)


def normalize_text(text: str) -> str:
    lowered = text.lower()
    tokens = re.split(r"(\s+)", lowered)
    fixed_tokens = []
    for token in tokens:
        if "." in token or "/" in token or "@" in token:
            mapped = map_homoglyphs(token)
            if DOMAIN_LIKE.search(mapped) or mapped.startswith("@") or "t.me" in mapped:
                fixed_tokens.append(mapped)
                continue
        fixed_tokens.append(token)
    result = "".join(fixed_tokens)
    result = TELEGRAM_FIX.sub(r"t.me/\1", result)
    result = WHATSAPP_FIX.sub(r"wa.me/\1", result)
    result = DOT_FIX.sub(r"\1.\2", result)
    result = SPACED_DOT_FIX.sub(r"\1.\2", result)
    return result


def unique(items: list[str]) -> list[str]:
    seen = []
    for item in items:
        if item not in seen:
            seen.append(item)
    return seen


def clean_link(link: str) -> str:
    cleaned = link.rstrip(".,!?:;")
    for prefix in ["https://", "http://", "www."]:
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix) :]
    return cleaned


def find_links(normalized: str) -> list[str]:
    links = []
    for match in LINK_RE.finditer(normalized):
        link = clean_link(match.group(0))
        if "." in link and len(link) >= 4:
            links.append(link)
    return unique(links)


def normalize_phone(raw: str) -> str | None:
    digits = re.sub(r"\D", "", raw)
    if raw.strip().startswith("8") and len(digits) == 11:
        digits = "7" + digits[1:]
    if len(digits) < 10 or len(digits) > 15:
        return None
    return "+" + digits


def find_phones(text: str) -> list[str]:
    phones = []
    for match in PHONE_RE.finditer(text):
        phone = normalize_phone(match.group(0))
        if phone:
            phones.append(phone)
    return unique(phones)


def link_domain(link: str) -> str:
    return link.split("/")[0]


def link_cues(links: list[str], source: str) -> list[Cue]:
    cues = []
    for link in links:
        domain = link_domain(link)
        tld = domain.rsplit(".", 1)[-1]
        if domain in ("t.me", "telegram.me"):
            cues.append(
                make_cue(
                    source,
                    "messenger",
                    "telegram_link",
                    link,
                    0.35,
                    "Telegram link " + link + " moves the talk off the platform",
                    "ссылка на Telegram " + link + " уводит общение с платформы",
                )
            )
        elif domain == "wa.me":
            cues.append(
                make_cue(
                    source,
                    "messenger",
                    "whatsapp_link",
                    link,
                    0.35,
                    "WhatsApp link " + link + " moves the talk off the platform",
                    "ссылка на WhatsApp " + link + " уводит общение с платформы",
                )
            )
        elif domain in SHORTENERS:
            cues.append(
                make_cue(
                    source,
                    "link",
                    "short_link",
                    link,
                    0.3,
                    "shortened link " + link + " hides the real address",
                    "короткая ссылка " + link + " скрывает настоящий адрес",
                )
            )
        elif tld in RISKY_TLDS:
            cues.append(
                make_cue(
                    source,
                    "link",
                    "risky_domain",
                    link,
                    0.3,
                    "link " + link + " uses a domain zone often seen in scams",
                    "ссылка " + link + " в доменной зоне, частой у мошенников",
                )
            )
        elif domain in COMMON_SAFE or domain.endswith(".gov.kz"):
            cues.append(
                make_cue(
                    source,
                    "link",
                    "known_link",
                    link,
                    0.02,
                    "link to a well-known site " + link,
                    "ссылка на известный сайт " + link,
                )
            )
        else:
            cues.append(
                make_cue(source, "link", "external_link", link, 0.15, "external link " + link, "внешняя ссылка " + link)
            )
    return cues


def handle_cues(normalized: str, source: str) -> list[Cue]:
    cues = []
    for handle in unique(HANDLE_RE.findall(normalized)):
        cues.append(
            make_cue(
                source,
                "messenger",
                "messenger_handle",
                "@" + handle,
                0.2,
                "contact handle @" + handle + " invites you to write privately",
                "контакт @" + handle + " зовёт написать в личку",
            )
        )
    return cues


def contact_word_cues(normalized: str, source: str) -> list[Cue]:
    found = []
    for word in CONTACT_WORDS:
        if word in normalized:
            found.append(word)
    if not found:
        return []
    value = ", ".join(found[:3])
    return [
        make_cue(
            source,
            "messenger",
            "off_platform_contact",
            value,
            0.25,
            "asks to continue in a messenger (" + value + ")",
            "просит продолжить в мессенджере (" + value + ")",
        )
    ]


def phone_cues(phones: list[str], source: str) -> list[Cue]:
    cues = []
    for phone in phones:
        cues.append(
            make_cue(
                source,
                "phone",
                "phone_number",
                phone,
                0.2,
                "phone number " + phone + " for direct contact",
                "номер телефона " + phone + " для прямой связи",
            )
        )
    return cues


def has_period_word(normalized: str) -> bool:
    for word in PERIOD_WORDS:
        if word in normalized:
            return True
    return False


def parse_number(text: str) -> float:
    try:
        return float(text.replace(",", "."))
    except ValueError:
        return 0.0


def percent_cues(normalized: str, source: str) -> list[Cue]:
    values = unique(PERCENT_RE.findall(normalized))
    if not values:
        return []
    biggest = 0.0
    for value in values:
        biggest = max(biggest, parse_number(value))
    with_percent = []
    for value in values[:3]:
        with_percent.append(value + "%")
    shown = ", ".join(with_percent)
    if biggest >= 5 and has_period_word(normalized):
        return [
            make_cue(
                source,
                "percent",
                "high_return_claim",
                shown,
                0.4,
                "promises a high regular return (" + shown + ")",
                "обещает высокий регулярный доход (" + shown + ")",
            )
        ]
    return [
        make_cue(
            source,
            "percent",
            "percent_claim",
            shown,
            0.1,
            "mentions percentages (" + shown + ")",
            "упоминает проценты (" + shown + ")",
        )
    ]


def multiplier_cues(normalized: str, source: str) -> list[Cue]:
    match = MULTIPLIER_RE.search(normalized)
    if not match:
        return []
    value = match.group(0).strip()
    return [
        make_cue(
            source,
            "percent",
            "multiplier_claim",
            value,
            0.35,
            "promises to multiply your money (" + value + ")",
            "обещает умножить деньги (" + value + ")",
        )
    ]


def money_cues(normalized: str, source: str) -> list[Cue]:
    amounts = []
    for match in MONEY_RE.finditer(normalized):
        amount = match.group(0).strip()
        if re.search(r"\d", amount):
            amounts.append(amount)
    amounts = unique(amounts)
    if not amounts:
        return []
    shown = ", ".join(amounts[:3])
    return [
        make_cue(
            source,
            "money",
            "money_amount",
            shown,
            0.15,
            "shows money amounts (" + shown + ")",
            "показывает денежные суммы (" + shown + ")",
        )
    ]


def analyze_text(text: str, source: str) -> dict:
    if not text or not text.strip():
        return {"cues": [], "links": [], "phones": []}
    normalized = normalize_text(text)
    links = find_links(normalized)
    phones = find_phones(normalized)
    cues = []
    cues.extend(link_cues(links, source))
    cues.extend(handle_cues(normalized, source))
    cues.extend(contact_word_cues(normalized, source))
    cues.extend(phone_cues(phones, source))
    cues.extend(percent_cues(normalized, source))
    cues.extend(multiplier_cues(normalized, source))
    cues.extend(money_cues(normalized, source))
    return {"cues": cues, "links": links, "phones": phones}


def detect_qr_codes(frames: list[Frame]) -> list[str]:
    detector = cv2.QRCodeDetector()
    payloads = []
    for frame in frames:
        try:
            ok, decoded, points, _ = detector.detectAndDecodeMulti(frame.image)
        except cv2.error:
            continue
        if not ok:
            continue
        for payload in decoded:
            if payload:
                payloads.append(payload.strip())
    return unique(payloads)


def qr_cues(payloads: list[str]) -> list[Cue]:
    cues = []
    for payload in payloads:
        cues.append(
            make_cue(
                "qr",
                "qr",
                "qr_code",
                payload,
                0.3,
                "QR code leads to " + payload[:120],
                "QR-код ведёт на " + payload[:120],
            )
        )
    return cues


def score_cues(cues: list[Cue]) -> float:
    per_code_count = {}
    remaining = 1.0
    for cue in cues:
        count = per_code_count.get(cue.code, 0)
        if count >= 2:
            continue
        per_code_count[cue.code] = count + 1
        remaining = remaining * (1.0 - cue.weight)
    score = 1.0 - remaining
    return max(0.0, min(1.0, score))
