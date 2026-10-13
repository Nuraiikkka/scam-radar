import sys
sys.path.append(".")

from app.services.text_classifier import classify
from app.services.fusion import fuse

examples = [
    ("Crypto trading with guaranteed profit, passive income every day", "investment_platform"),
    ("Крипто и форекс, гарантированная прибыль, пассивный доход", "investment_platform"),
    ("Invite friends and recruit your team, referral network marketing", "pyramid"),
    ("Приглашай друзей, вступай в команду, сетевой маркетинг", "pyramid"),
    ("Use promo code, casino jackpot and betting odds", "betting"),
    ("Ставки на спорт, промокод, букмекер, казино", "betting"),
    ("Free iPhone giveaway! You won, claim your prize", "giveaway"),
    ("Розыгрыш айфона! Ты выиграл, заберите приз", "giveaway"),
    ("Work from home, no experience, earn per day", "job_offer"),
    ("Удалённая работа без опыта, заработок в день", "job_offer"),
    ("Today I cook pasta with tomato sauce", "none"),
    ("Мой университет запускает розыгрыш книг в библиотеке", "none"),
    ("Лекция про инвестиции в образование", "none"),
    ("Funny cat video, like and subscribe", "none"),
]

correct = 0
total = 0

for example in examples:
    text = example[0]
    true_category = example[1]

    category, score, reasons = classify(text)
    final_category, final_score = fuse(category, score, 0)

    total = total + 1
    if final_category == true_category:
        correct = correct + 1
        print("OK    ", true_category, "->", final_category, final_score)
    else:
        print("ERROR ", true_category, "->", final_category, final_score, "|", text)

print("")
print("Правильно:", correct, "из", total)
print("Accuracy:", round(correct / total * 100), "%")
