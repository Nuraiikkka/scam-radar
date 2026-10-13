keywords = {
    "investment_platform": [
        "guaranteed profit", "crypto", "forex", "passive income", "invest",
        "гарантированная прибыль", "крипто", "форекс", "пассивный доход",
        "инвестиции", "депозит", "трейдинг"
    ],
    "pyramid": [
        "recruit", "referral", "network marketing", "invite friends",
        "пирамида", "реферал", "сетевой маркетинг", "приглашай друзей", "вступай в команду"
    ],
    "betting": [
        "betting", "casino", "promo code", "jackpot", "slots",
        "ставки", "казино", "промокод", "букмекер", "слоты", "коэффициент"
    ],
    "giveaway": [
        "giveaway", "you won", "free iphone", "claim your prize", "winner",
        "розыгрыш", "ты выиграл", "вы выиграли", "бесплатный айфон", "заберите приз", "победитель"
    ],
    "job_offer": [
        "work from home", "no experience", "earn per day", "hiring now",
        "удаленная работа", "удалённая работа", "без опыта", "заработок в день", "подработка"
    ],
}


def classify(text):
    text = text.lower()

    best_category = "none"
    best_count = 0
    best_reasons = []

    for category in keywords:
        count = 0
        reasons = []

        for word in keywords[category]:
            if word in text:
                count = count + 1
                reasons.append("Keyword: " + word)

        if count > best_count:
            best_count = count
            best_category = category
            best_reasons = reasons

    score = best_count * 0.3
    if score > 1:
        score = 1

    return best_category, score, best_reasons
