import argparse
import csv
import random
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent

SLOTS = {
    "platform": [
        "CryptoMax",
        "BitProfit",
        "QuantumTrade",
        "GoldInvest",
        "AiTrader Pro",
        "Nexus Capital",
        "TetherBox",
        "SmartYield",
        "AlphaCoin",
        "Kaz Invest Club",
    ],
    "pct": ["3", "5", "7", "10", "12", "15", "20", "30", "40", "50"],
    "amount": ["500", "1000", "5000", "10 000", "50 000", "100 000", "300", "2000"],
    "big": ["1 000 000", "500 000", "250 000", "2 000 000", "100 000"],
    "handle": ["@profit_daily", "@easy_money_kz", "@invest_team", "@rich_life_club", "@bonus_admin", "@hr_remote"],
    "tme": ["t.me/profit_daily", "t.me/easy_cash", "t.me/vip_signals", "t.me/bonus_drop", "t.me/remote_job_hr"],
    "coin": ["USDT", "биткоин", "Bitcoin", "TON", "крипту", "crypto"],
    "prize": ["iPhone 17", "MacBook", "PlayStation 5", "1 000 000 тенге", "Tesla", "AirPods"],
    "prize_en": ["iPhone 17", "MacBook", "PlayStation 5", "$5000", "a Tesla", "AirPods"],
    "team": ["Реал Мадрид", "Барселона", "Кайрат", "Астана", "Манчестер Сити", "Зенит"],
    "team_en": ["Real Madrid", "Barcelona", "Man City", "Liverpool", "Arsenal", "Juventus"],
    "food": ["плов", "бешбармак", "борщ", "пасту карбонара", "блины", "манты"],
    "food_en": ["pasta carbonara", "pancakes", "beef stew", "chicken curry", "banana bread", "ramen"],
    "city": ["Алматы", "Астана", "Шымкент", "Караганда", "Москва", "Казань"],
    "city_en": ["Almaty", "Astana", "London", "Berlin", "Istanbul", "Tokyo"],
    "gadget": ["iPhone 17", "Samsung Galaxy", "Xiaomi", "MacBook Air", "наушники Sony"],
    "gadget_en": ["iPhone 17", "Galaxy S26", "Pixel 10", "MacBook Air", "Sony headphones"],
}

HOOKS = {
    "ru": [
        "Ребята, слушайте внимательно!",
        "Я вам сейчас открою секрет.",
        "Не листай дальше!",
        "Всем привет, это важно.",
        "Смотрите до конца.",
        "Честно, я сама не верила.",
        "Друзья, коротко.",
        "Это видео изменит вашу жизнь.",
        "",
        "",
    ],
    "en": [
        "Guys, listen carefully!",
        "I am going to tell you a secret.",
        "Stop scrolling!",
        "Hi everyone, this matters.",
        "Watch till the end.",
        "Honestly, I did not believe it either.",
        "Quick one, friends.",
        "This video will change your life.",
        "",
        "",
    ],
    "kk": ["Достар, тыңдаңыз!", "Сәлем бәріне!", ""],
}

SCAM_CTAS = {
    "ru": [
        "Пиши мне в телеграм {handle}.",
        "Ссылка в профиле.",
        "Подробности в {tme}.",
        "Пиши плюс в комментариях.",
        "Места ограничены, успей сегодня.",
        "Пиши в личку, всё расскажу.",
        "Жми на ссылку в шапке.",
        "",
    ],
    "en": [
        "Write to me on telegram {handle}.",
        "Link in bio.",
        "Details at {tme}.",
        "Comment plus below.",
        "Spots are limited, hurry today.",
        "DM me and I will explain.",
        "Tap the link in my profile.",
        "",
    ],
    "kk": ["Телеграмға жаз {handle}.", "Сілтеме профильде.", ""],
}

SAFE_CTAS = {
    "ru": [
        "Подписывайтесь, чтобы не пропустить.",
        "Пишите в комментариях своё мнение.",
        "Ставьте лайк, если полезно.",
        "До встречи в следующем видео.",
        "Сохраните, чтобы не потерять.",
        "",
    ],
    "en": [
        "Follow for more.",
        "Tell me what you think in the comments.",
        "Like if this was useful.",
        "See you in the next video.",
        "Save this so you do not lose it.",
        "",
    ],
    "kk": ["Жазылыңыз!", "Пікіріңізді жазыңыз.", ""],
}

OFFERS = {
    ("investment_platform", "ru"): [
        "Платформа {platform} даёт {pct}% в день, вклад от {amount} тенге, вывод моментальный.",
        "Я вложила {amount} в {platform} и через неделю вывела {big}, пассивный доход без риска.",
        "Торговый бот {platform} сам торгует {coin}, гарантированная прибыль {pct}% каждый день.",
        "Инвестируй в {coin} через {platform} и получай доход в день от {amount} рублей.",
        "Арбитраж {coin} приносит {pct}% в неделю, я научу бесплатно.",
        "Минимальный депозит {amount}, доход {pct}% ежедневно, всё гарантировано и проверено.",
        "Мой секрет это платформа {platform}, удвоила депозит за три дня, вывод средств на карту за 5 минут.",
        "Пока не закрыли набор, {platform} платит {pct}% в день всем новым инвесторам.",
        "Закинул {amount} в {coin} по сигналам {platform} и уже забрал {big} прибыли.",
        "Это не банк, тут ставка {pct}% в месяц, деньги работают пока ты спишь.",
        "Купи пакет инвестора {platform} за {amount} и получай выплаты каждый день без усилий.",
        "Искусственный интеллект {platform} торгует на бирже за тебя, прибыль от {pct}% в сутки.",
    ],
    ("investment_platform", "en"): [
        "{platform} pays {pct}% daily, start with just ${amount}, instant withdrawal.",
        "I invested ${amount} in {platform} and withdrew ${big} in a week, passive income with zero risk.",
        "This trading bot trades {coin} for you with guaranteed profit of {pct}% per day.",
        "Invest in {coin} with {platform} and earn daily profit from ${amount}.",
        "Crypto arbitrage gives {pct}% per week, risk free, and I will teach you for free.",
        "Minimum deposit ${amount}, {pct}% daily returns, everything is guaranteed and verified.",
        "My secret is {platform}, I doubled my deposit in 3 days and withdrew to my card in 5 minutes.",
        "Before registration closes, {platform} pays {pct}% a day to every new investor.",
        "I put ${amount} into {coin} using {platform} signals and already took ${big} profit.",
        "This is not a bank, the rate here is {pct}% a month, your money works while you sleep.",
        "Buy the {platform} investor pack for ${amount} and get payouts every day with no effort.",
        "The {platform} AI trades the market for you, profit from {pct}% every day.",
    ],
    ("pyramid", "ru"): [
        "Приведи друга и получи {amount} тенге за каждого приглашённого, а за его друзей ещё бонус.",
        "Вступительный взнос всего {amount}, дальше ты просто приглашаешь людей и строишь свою команду.",
        "Чем больше людей в твоей структуре, тем выше уровень и доход.",
        "Реферальная программа платит 30% с каждого, кого ты пригласил, и 10% со второй линии.",
        "Это не пирамида, это сетевой маркетинг, купи стартовый пакет за {amount} и приглашай друзей.",
        "Пригласи пятерых и верни вложения, пригласи десять и выйди на {big} в месяц.",
        "Собираю команду, нужно только оплатить участие {amount} и привлечь трёх человек.",
        "Моя команда уже 2000 человек, я получаю бонус за каждого приглашенного.",
        "Каждый новый участник платит {amount}, и половина уходит тому, кто его пригласил.",
        "Зарабатывай не на продажах, а на приглашениях, твоя первая линия кормит тебя.",
        "Вступай в клуб, плати взнос {amount}, а потом подключай родственников и друзей.",
        "Твой доход растёт с каждым уровнем структуры, главное приглашать новых людей.",
    ],
    ("pyramid", "en"): [
        "Invite friends and get ${amount} for every person you invite, plus a bonus from their friends.",
        "The entry fee is only ${amount}, then you just recruit people and build your team.",
        "The more people in your downline, the higher your level and income.",
        "The referral program pays 30% from everyone you invite and 10% from the second line.",
        "This is not a pyramid, it is network marketing, buy the starter pack for ${amount} and invite friends.",
        "Invite five people to get your money back, invite ten and make ${big} a month.",
        "I am building a team, you only pay ${amount} to join and bring three people.",
        "My team has 2000 members and I earn a bonus for every person I recruit.",
        "Every new member pays ${amount} and half of it goes to the person who invited them.",
        "You earn from invitations, not from sales, your first line pays you.",
        "Join the club, pay the ${amount} fee, then sign up your relatives and friends.",
        "Your income grows with every level below you, just keep recruiting new people.",
    ],
    ("betting", "ru"): [
        "Договорной матч {team} сегодня, коэффициент 15, ставка от {amount}.",
        "Казино дарит фриспины по промокоду, я поднял {big} за вечер.",
        "Верный прогноз на матч {team}, экспресс заходит в 90% случаев.",
        "Букмекер с лучшими коэффициентами удваивает первый депозит, ставки на футбол и слоты.",
        "Я выиграл джекпот {big} в слоты, повтори за мной по промокоду.",
        "Продаю инсайды на матчи {team}, ставка заходит гарантированно, оплата после выигрыша.",
        "Схема ставок, которая не проигрывает, ставь {amount} и забирай x3.",
        "Новое онлайн-казино даёт бонус 200% на депозит и 100 фриспинов.",
        "Крути рулетку по моей стратегии и выводи по {amount} каждый час.",
        "Ставлю на {team} по инсайду, кэф 8, заходим вместе на {amount}.",
        "Мой VIP канал с прогнозами на спорт, проходимость ставок 95%.",
        "Слот с самой высокой отдачей, вчера сорвал занос на {big}.",
    ],
    ("betting", "en"): [
        "Fixed match today {team_en}, odds 15, bet from ${amount}.",
        "This casino gives free spins with my promo code, I won ${big} tonight.",
        "Sure win prediction for {team_en}, my parlay hits 90% of the time.",
        "The bookmaker with the best odds doubles your first deposit, bet on football and slots.",
        "I hit a ${big} jackpot on slots, copy me with the promo code.",
        "Selling insider tips for {team_en} games, the bet wins guaranteed, pay after you win.",
        "A betting system that never loses, bet ${amount} and take x3.",
        "New online casino with a 200% deposit bonus and 100 free spins.",
        "Spin the roulette with my strategy and cash out ${amount} every hour.",
        "I am betting on {team_en} with an insider tip, odds 8, join me with ${amount}.",
        "My VIP sports picks channel has a 95% win rate.",
        "The slot with the highest payout, yesterday I hit a ${big} win.",
    ],
    ("giveaway", "ru"): [
        "Розыгрыш {prize}, вы выиграли, осталось только оплатить доставку {amount} тенге.",
        "Разыгрываем {prize} среди подписчиков, победитель выбран, для получения приза переведите комиссию.",
        "Раздача {coin}, отправь {amount} на кошелёк и получи в два раза больше обратно.",
        "Поздравляем, вы победитель розыгрыша, введите данные карты для получения приза.",
        "Бесплатно раздаём {prize} в честь дня рождения блогера, оплатите только страховку {amount}.",
        "Последний день розыгрыша {prize}, подпишись, оставь комментарий и оплати участие {amount}.",
        "Вы выиграли {prize}, чтобы забрать подарок, оплатите доставку.",
        "Раздаём {big} тенге первым ста комментаторам, приз отправим после подтверждения карты.",
        "Ваш номер выпал в лотерее, приз {prize} ждёт, нужно только оплатить налог {amount}.",
        "Магазин закрывается и раздаёт {prize} за символическую оплату доставки.",
        "Каждый сотый подписчик получает {prize}, проверь, может это ты, и подтверди карту.",
        "Илон Маск раздаёт {coin}, переведи {amount} и получи вдвое больше.",
    ],
    ("giveaway", "en"): [
        "{prize_en} giveaway, you won, just pay the shipping of ${amount}.",
        "We are giving away {prize_en} to followers, the winner is chosen, send the fee to claim your prize.",
        "{coin} giveaway, send ${amount} to the wallet and get double back.",
        "Congratulations, you are the winner, enter your card details to claim your prize.",
        "Free {prize_en} for my birthday, you only pay the insurance of ${amount}.",
        "Last day of the {prize_en} giveaway, follow, comment and pay ${amount} to enter.",
        "You have won {prize_en}, to claim your gift pay for shipping.",
        "Giving ${big} to the first 100 comments, we send the prize after you confirm your card.",
        "Your number won the lottery, {prize_en} is waiting, you only need to pay the ${amount} tax.",
        "The store is closing and giving away {prize_en} for a small delivery fee.",
        "Every hundredth follower gets {prize_en}, check if it is you and confirm your card.",
        "Elon Musk is giving away {coin}, send ${amount} and get twice as much back.",
    ],
    ("job_offer", "ru"): [
        "Подработка без опыта, оплата за лайки от {amount} тенге в день.",
        "Удалённая работа, простые задания в телефоне, зарплата от {big} в месяц, без вложений.",
        "Нужны люди оформить карту на себя, платим {amount} за каждую.",
        "Вакансия оценивать товары на маркетплейсе, {amount} за задание, но сначала нужно внести депозит.",
        "Работа курьером документов, {big} в неделю, без собеседования.",
        "Ищу помощников, работа 2 часа в день, доход от {amount} в день, обучение платное {amount}.",
        "Хочешь работать из дома, ставь лайки и получай {amount} за каждое задание.",
        "Срочно набираем сотрудников без опыта, нужно только переводить деньги клиентов через свою карту.",
        "Пиши отзывы о товарах и получай {amount} за каждый, первый заказ оплачиваешь сам.",
        "Ищем операторов на телефон, зарплата {big}, оформление после оплаты пакета документов.",
        "Нужны студенты на лёгкую работу, просто принимай переводы на карту и переводи дальше.",
        "Работа на 1 час в день в приложении, выплаты от {amount}, вход за {amount}.",
    ],
    ("job_offer", "en"): [
        "Side job with no experience, get paid to like videos, ${amount} per day.",
        "Remote job with simple tasks on your phone, salary ${big} a month, no investment.",
        "We need people to open a bank card in their name, we pay ${amount} each.",
        "Job rating products on a marketplace, ${amount} per task, but first you make a deposit.",
        "Courier job for documents, ${big} a week, no interview.",
        "Looking for assistants, 2 hours a day, earn ${amount} a day, paid training of ${amount}.",
        "Want to work from home, like posts and earn ${amount} per task.",
        "Hiring now with no experience, you just move client money through your own card.",
        "Write product reviews and earn ${amount} each, you pay for the first order yourself.",
        "Hiring phone operators, salary ${big}, contract after you pay for the documents pack.",
        "Students needed for easy work, just receive transfers to your card and send them on.",
        "One hour a day in an app, payouts from ${amount}, entry costs ${amount}.",
    ],
    ("none", "ru"): [
        "Сегодня готовим {food} по бабушкиному рецепту, понадобится всего час.",
        "Гуляем по {city}, показываю лучшие кофейни и места для фото на закате.",
        "Обзор {gadget}, камера отличная, батарея держит день, но цена кусается.",
        "Банк повысил ставку по депозиту до {pct}% годовых, сравниваю условия разных банков.",
        "Напоминаю, если вам обещают {pct}% в день, это мошенники, не переводите деньги незнакомцам.",
        "Наша пекарня в {city} ищет пекаря, официальное трудоустройство, резюме на сайте компании.",
        "Как я выучила английский за год, книги, сериалы и разговорный клуб каждую неделю.",
        "Тренировка дома без инвентаря, приседания, планка и отжимания, повторяйте за мной.",
        "Футбол вечером, {team} сыграл вничью, разбираем лучшие моменты матча.",
        "Финансовая грамотность, откладывайте 10% зарплаты и не берите кредиты на телефоны.",
        "Разыгрываю свой старый скетчбук среди друзей, без оплат и доставок, просто ради удовольствия.",
        "Рассказываю про свою работу программистом, что нужно учить и сколько времени это заняло.",
        "Мой кот сегодня научился открывать холодильник, смотрите что было дальше.",
        "Собираю чемодан в поездку в {city}, что взять с собой на неделю.",
    ],
    ("none", "en"): [
        "Today we are cooking {food_en} from my grandma's recipe, it takes one hour.",
        "Walking around {city_en}, showing the best coffee shops and sunset photo spots.",
        "{gadget_en} review, great camera, the battery lasts a day, but the price is high.",
        "The bank raised its savings rate to {pct}% a year, I compare offers from different banks.",
        "Reminder, if someone promises you {pct}% a day it is a scam, never send money to strangers.",
        "Our bakery in {city_en} is hiring a baker, official contract, apply on the company website.",
        "How I learned Spanish in a year, books, series and a speaking club every week.",
        "Home workout with no equipment, squats, plank and push-ups, follow along.",
        "Football tonight, {team_en} drew the game, here are the best moments.",
        "Money tips, save 10% of your salary and avoid loans for new phones.",
        "Giving my old sketchbook to a friend, no fees and no shipping, just for fun.",
        "Talking about my job as a developer, what to learn and how long it took me.",
        "My cat learned to open the fridge today, watch what happened next.",
        "Packing my suitcase for a week in {city_en}, here is what I take.",
    ],
    ("investment_platform", "kk"): [
        "{platform} платформасы күніне {pct}% табыс береді, салым {amount} теңгеден.",
        "Инвестиция салып күн сайын табыс тап, кепілдік бар, тәуекел жоқ.",
        "{coin} арқылы күніне {pct}% пайда, ақшаңды {platform} платформасына сал.",
    ],
    ("job_offer", "kk"): [
        "Тәжірибесіз жұмыс, лайк басып күніне {amount} теңге тап.",
        "Үйден жұмыс, қарапайым тапсырмалар, жалақы {big} теңге.",
        "Өз атыңа карта ашып бер, әр картаға {amount} теңге төлейміз.",
    ],
    ("giveaway", "kk"): [
        "Сіз {prize} ұтып алдыңыз, жеткізу ақысын {amount} теңге төлеңіз.",
        "Ұтыс ойыны, жүлдені алу үшін карта деректерін енгізіңіз.",
    ],
    ("none", "kk"): [
        "Бүгін {food} дайындаймыз, әжемнің рецепті бойынша.",
        "{city} қаласында серуендеп жүрміз, ең жақсы кофеханаларды көрсетемін.",
        "Банк депозит мөлшерлемесін жылдық {pct}% дейін көтерді, шарттарды салыстырамын.",
        "Үйде жаттығу жасаймыз, менімен бірге қайталаңыз.",
    ],
}


def fill(template: str, rng: random.Random) -> str:
    text = template
    for key, values in SLOTS.items():
        token = "{" + key + "}"
        while token in text:
            text = text.replace(token, rng.choice(values), 1)
    return text


def compose(category: str, lang: str, offer: str, rng: random.Random) -> str:
    hook = rng.choice(HOOKS[lang])
    if category == "none":
        cta = rng.choice(SAFE_CTAS[lang])
    else:
        cta = rng.choice(SCAM_CTAS[lang])
    parts = []
    for part in (hook, offer, cta):
        if part:
            parts.append(part)
    return fill(" ".join(parts), rng)


def generate(per_offer: int, seed: int) -> list[dict]:
    rng = random.Random(seed)
    rows = []
    for (category, lang), offers in OFFERS.items():
        for index, offer in enumerate(offers):
            seen = set()
            attempts = 0
            while len(seen) < per_offer and attempts < per_offer * 20:
                attempts = attempts + 1
                text = compose(category, lang, offer, rng)
                if text in seen:
                    continue
                seen.add(text)
                rows.append(
                    {
                        "text": text,
                        "category": category,
                        "source": "synthetic:" + category + "_" + lang + "_" + str(index),
                        "lang": lang,
                    }
                )
    rng.shuffle(rows)
    return rows


def write_rows(rows: list[dict], output: Path) -> None:
    with open(output, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["text", "category", "source", "lang"])
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic labeled examples")
    parser.add_argument("--per-offer", type=int, default=5)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=Path, default=DATA_DIR / "labels.csv")
    args = parser.parse_args()
    rows = generate(args.per_offer, args.seed)
    write_rows(rows, args.output)
    print("Wrote " + str(len(rows)) + " rows to " + str(args.output))


if __name__ == "__main__":
    main()
