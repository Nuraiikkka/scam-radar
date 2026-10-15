import re
import unicodedata


keywords = {
    "pyramid": [
        "recruit", "referral", "network marketing", "invite friends",
        "пирамида", "реферал", "сетевой маркетинг", "приглашай друзей", "вступай в команду"
    ],
    "betting": [
        "betting", "casino", "promo code", "jackpot", "slots",
        "ставки", "казино", "промокод", "букмекер", "слоты", "коэффициент"
    ],
    "job_offer": [
        "work from home", "no experience", "earn per day", "hiring now",
        "удаленная работа", "удалённая работа", "без опыта", "заработок в день", "подработка"
    ],
}


def normalize(text):
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", text).lower().replace("’", "'"))


def contexts(text):
    """Topic recognition is separate from evidence of fraudulent promotion."""
    text = normalize(text)
    found = []
    if re.search(r"\bgive\s?away\b|\bgiving away\b|\bgetting away.{0,35}iphone|\b(?:prize|winner)\b|розыгрыш|заберите приз", text):
        found.append("giveaway")
    if re.search(r"\b(?:trading account|forex|crypto|investment|withdrawal|withdraw|payout)\b|инвестиц|торгов\w* сч[её]т|вывод средств", text):
        found.append("investment_platform")
    return found


def contextual_risks(text):
    found = contexts(text)
    candidates = []
    if "giveaway" in found:
        evidence = []
        if re.search(r"(?:pay|send|transfer).{0,35}(?:fee|shipping|delivery|deposit|money)|(?:fee|payment).{0,25}(?:claim|receive|prize)|оплат\w*.{0,30}(?:доставк|комисси)|перевед\w*.{0,25}(?:деньги|залог)", text):
            evidence.append("Payment requested to receive a giveaway prize")
        if re.search(r"(?:send|share|enter|provide).{0,45}(?:otp|verification code|password|card details|cvv|seed phrase)|(?:пришлите|введите|сообщите).{0,35}(?:код из смс|пароль|cvv)", text):
            evidence.append("Sensitive credentials requested in a giveaway")
        if evidence:
            candidates.append(("giveaway", min(0.95, 0.8 + 0.1 * (len(evidence)-1)), evidence))
    if "investment_platform" in found:
        evidence = []
        if re.search(r"guaranteed (?:profit|returns?)|risk[ -]free (?:profit|returns?|invest\w*)|no risk.{0,25}(?:profit|return)|гарантирован\w* (?:прибыл|доход)|без риска.{0,25}(?:прибыл|доход)", text):
            evidence.append("Guaranteed or risk-free investment return promised")
        if re.search(r"(?:pay|deposit|send|transfer).{0,45}(?:unlock|release|activate).{0,30}(?:withdraw\w*|funds|payout)|(?:pay|deposit).{0,30}(?:before|to).{0,20}withdraw|(?:оплат\w*|пополн\w*).{0,35}(?:для вывода|разблокиров\w*)", text):
            evidence.append("Advance payment requested to unlock a withdrawal")
        if evidence:
            candidates.append(("investment_platform", min(0.95, 0.8 + 0.1 * (len(evidence)-1)), evidence))
    return candidates


def evidence_summary(transcript, ocr_text, category):
    """No assertion of safety when topic recognition yields no fraud evidence."""
    detected = contexts(transcript + " " + ocr_text)
    warnings = []
    if not transcript.strip():
        warnings.append("No speech transcript available; speech may be absent or recognition may have failed")
    if not ocr_text.strip():
        warnings.append("No readable on-screen text extracted")
    if "giveaway" in detected:
        warnings.append("Giveaway caption, external rules and destination sites have not been checked")
    if "investment_platform" in detected:
        warnings.append("A trading or withdrawal screen does not verify a platform's legitimacy")
    if category == "none":
        warnings.append("No matching fraud evidence found; this does not establish that the video is safe")
    return {
        "status": "risk_signals_detected" if category != "none" else "insufficient_evidence",
        "detected_contexts": detected,
        "warnings": warnings,
        "score_kind": "heuristic_not_calibrated_probability",
    }


def job_risk(text):
    """Evidence combinations, not a blacklist of employers or websites."""
    reasons = []
    amount = r"(?:\$\s*\d[\d,]*(?:\.\d+)?|\d[\d,]*(?:\.\d+)?\s*(?:dollars?|usd|доллар\w*|тенге|руб\w*))"
    period = r"(?:per\s+day|a\s+day|daily|in\s+\d+\s+hours?|за\s+\d+\s+час\w*|в\s+день)"
    earnings = bool(re.search(r"\b(?:make|earn|income|paid|заработ\w*|доход\w*)\b", text))
    daily_claim = earnings and bool(re.search(amount + r".{0,45}?" + period, text))
    easy = bool(re.search(r"stupidly easy|easy (?:way|hack|money)|as easy as that|no (?:effort|skills|experience)|легк\w* (?:заработ\w*|деньги)|без (?:усилий|опыта)", text))
    shortcut = bool(re.search(r"voice typing|voice by pay|voice.?to.?text|dictat\w*|голосов\w* ввод", text))
    writing = bool(re.search(r"transcrib\w*|transcription\w*|caption\w*|writing|write|content|расшифров\w*|транскри\w*", text))
    inflated = bool(re.search(r"(?:five|5|six|6)[ -]figures? (?:a|per) month", text))
    funnel = bool(re.search(r"(?:see|visit|check|link in).{0,25}profile|free tutorials|ссылк\w* в профил", text))
    if daily_claim:
        reasons.append("Specific earnings promised per day or within a few hours")
    if easy:
        reasons.append("Earnings presented as easy or requiring little effort")
    if shortcut and writing:
        reasons.append("Dictation shortcut presented as a replacement for paid writing/transcription work")
    if inflated and funnel:
        reasons.append("High monthly income claim used to direct viewers to profile/tutorials")
    # At least two independent indicators, including a concrete income promise.
    if not (daily_claim or inflated) or len(reasons) < 2:
        return 0.0, []
    return min(0.95, 0.70 + 0.08 * (len(reasons) - 2)), reasons


def classify(text):
    text = normalize(text)

    # Remove warning sentences rather than suppressing an entire mixed video.
    sentences = re.split(r"(?<=[.!?])\s+", text)
    warning = re.compile(r"\b(?:beware|scam warning|don't fall for|do not fall for|don't trust|do not trust|is a scam|это мошенничество|не верьте|остерегайтесь)\b")
    text = " ".join(s for s in sentences if not warning.search(s))

    best_category = "none"
    best_count = 0
    best_reasons = []

    for category in keywords:
        count = 0
        reasons = []

        for word in keywords[category]:
            if re.search(r"(?<!\w)" + re.escape(word) + r"(?!\w)", text):
                count = count + 1
                reasons.append("Keyword: " + word)

        if count > best_count:
            best_count = count
            best_category = category
            best_reasons = reasons

    score = best_count * 0.3
    if score > 1:
        score = 1

    job_score, job_reasons = job_risk(text)
    candidates = contextual_risks(text)
    candidates.append(("job_offer", job_score, job_reasons))
    contextual_category, contextual_score, contextual_reasons = max(candidates, key=lambda item: item[1])
    if contextual_score > score:
        return contextual_category, contextual_score, contextual_reasons
    # One generic keyword does not establish fraud.
    if best_count < 2:
        return "none", 0.0, []
    return best_category, score, best_reasons
