import argparse
import csv
import shutil
import subprocess
import wave
from pathlib import Path

import cv2
import numpy as np
import qrcode
from PIL import Image, ImageDraw, ImageFont

DATA_DIR = Path(__file__).resolve().parent.parent
SAMPLES_DIR = DATA_DIR / "samples"
BUILD_DIR = SAMPLES_DIR / "build"
WIDTH = 540
HEIGHT = 960
FPS = 15
SILENT_SECONDS = 6
FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/Library/Fonts/Arial Unicode.ttf",
]

SAMPLES = [
    {
        "name": "scam_invest_ru",
        "category": "investment_platform",
        "lang": "ru",
        "voice": "Milena",
        "speech": "Ребята, слушайте. Платформа КриптоМакс даёт тридцать процентов в день. "
        "Я вложила десять тысяч и через неделю вывела миллион. Пассивный доход без риска. "
        "Пишите мне в телеграм, ссылка в профиле.",
        "lines": ["ДОХОД 30% В ДЕНЬ", "БЕЗ РИСКА", "t.me/profit_daily"],
        "qr": "https://t.me/profit_daily",
        "color": (40, 20, 70),
    },
    {
        "name": "scam_invest_en",
        "category": "investment_platform",
        "lang": "en",
        "voice": "Samantha",
        "speech": "Stop scrolling. This trading bot trades crypto for you with guaranteed profit "
        "of twenty percent per day. I invested five hundred dollars and withdrew ten thousand. "
        "Link in bio, write to me on telegram.",
        "lines": ["EARN 20% DAILY", "GUARANTEED PROFIT", "@profit_daily"],
        "qr": "",
        "color": (10, 50, 40),
    },
    {
        "name": "scam_betting_ru",
        "category": "betting",
        "lang": "ru",
        "voice": "Milena",
        "speech": "Договорной матч сегодня, коэффициент пятнадцать. Букмекер удваивает первый депозит. "
        "Ставка заходит гарантированно, прогнозы в моём телеграм канале.",
        "lines": ["ДОГОВОРНОЙ МАТЧ", "КОЭФФИЦИЕНТ 15", "+7 701 555 12 34"],
        "qr": "",
        "color": (70, 30, 10),
    },
    {
        "name": "scam_giveaway_en",
        "category": "giveaway",
        "lang": "en",
        "voice": "Samantha",
        "speech": "Congratulations, you won the iPhone giveaway. To claim your prize, "
        "just pay the shipping fee of ten dollars and enter your card details on our site.",
        "lines": ["IPHONE GIVEAWAY", "YOU WON!", "PAY SHIPPING $9.99", "bit.ly/free-iphone17"],
        "qr": "",
        "color": (20, 40, 80),
    },
    {
        "name": "scam_job_ru",
        "category": "job_offer",
        "lang": "ru",
        "voice": "Milena",
        "speech": "Подработка без опыта. Оплата за лайки от пяти тысяч тенге в день. "
        "Простые задания в телефоне. Пиши в личку, всё расскажу.",
        "lines": ["РАБОТА ЗА ЛАЙКИ", "5000 ₸ В ДЕНЬ", "@hr_remote"],
        "qr": "",
        "color": (60, 60, 20),
    },
    {
        "name": "scam_pyramid_en",
        "category": "pyramid",
        "lang": "en",
        "voice": "Samantha",
        "speech": "The entry fee is only one hundred dollars. Then you invite friends and get fifty dollars "
        "for every person you invite, plus a bonus from their friends. Build your team today.",
        "lines": ["INVITE 5 FRIENDS", "GET $500", "JOIN MY TEAM"],
        "qr": "",
        "color": (50, 10, 40),
    },
    {
        "name": "safe_cooking_ru",
        "category": "none",
        "lang": "ru",
        "voice": "Milena",
        "speech": "Сегодня готовим плов по бабушкиному рецепту. Нам понадобится рис, морковь, мясо и лук. "
        "Подписывайтесь, чтобы не пропустить новые рецепты.",
        "lines": ["РЕЦЕПТ ПЛОВА", "ШАГ 1: РИС"],
        "qr": "",
        "color": (90, 50, 20),
    },
    {
        "name": "safe_travel_en",
        "category": "none",
        "lang": "en",
        "voice": "Samantha",
        "speech": "Walking around Almaty today. I am showing you the best coffee shops and the mountains "
        "at sunset. Follow for more travel videos.",
        "lines": ["ALMATY VLOG", "DAY 2"],
        "qr": "",
        "color": (20, 70, 90),
    },
    {
        "name": "safe_warning_ru",
        "category": "none",
        "lang": "ru",
        "voice": "Milena",
        "speech": "Напоминаю: если вам обещают тридцать процентов в день, это мошенники. "
        "Никогда не переводите деньги незнакомцам. Откладывайте десять процентов зарплаты.",
        "lines": ["ОСТОРОЖНО, МОШЕННИКИ", "ФИНАНСОВАЯ ГРАМОТНОСТЬ"],
        "qr": "",
        "color": (30, 30, 30),
    },
    {
        "name": "silent_scam_screen",
        "category": "investment_platform",
        "lang": "ru",
        "voice": "",
        "speech": "",
        "lines": ["ПАССИВНЫЙ ДОХОД", "40% В МЕСЯЦ", "ГАРАНТИРОВАННО", "tmelx_invest"],
        "qr": "https://t.me/x_invest",
        "color": (10, 10, 60),
    },
    {
        "name": "silent_no_text",
        "category": "none",
        "lang": "none",
        "voice": "",
        "speech": "",
        "lines": [],
        "qr": "",
        "color": (0, 90, 60),
    },
]


def tool_path(name: str) -> str:
    path = shutil.which(name)
    if path is None:
        raise SystemExit(name + " is not installed")
    return path


def load_font(size: int):
    for candidate in FONT_CANDIDATES:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    raise SystemExit("No font with Cyrillic support was found")


def make_speech(sample: dict) -> None:
    if not sample["speech"]:
        return
    target = BUILD_DIR / (sample["name"] + ".aiff")
    subprocess.run([tool_path("say"), "-v", sample["voice"], "-o", str(target), sample["speech"]], check=True)


def audio_seconds(sample: dict) -> float:
    aiff = BUILD_DIR / (sample["name"] + ".aiff")
    if not aiff.exists():
        return SILENT_SECONDS
    wav = BUILD_DIR / (sample["name"] + ".wav")
    subprocess.run([tool_path("ffmpeg"), "-y", "-loglevel", "error", "-i", str(aiff), str(wav)], check=True)
    with wave.open(str(wav), "rb") as handle:
        seconds = handle.getnframes() / handle.getframerate()
    wav.unlink()
    return seconds + 1.0


def draw_frame(sample: dict, frame_index: int, font, qr_image) -> np.ndarray:
    image = Image.new("RGB", (WIDTH, HEIGHT), sample["color"])
    draw = ImageDraw.Draw(image)
    shift = (frame_index * 2) % 60
    draw.ellipse((60 + shift, 700, 200 + shift, 840), fill=(255, 255, 255, 40), outline=(200, 200, 200))
    top = 120
    for line in sample["lines"]:
        box = draw.textbbox((0, 0), line, font=font)
        text_width = box[2] - box[0]
        text_height = box[3] - box[1]
        left = (WIDTH - text_width) // 2
        draw.rectangle((left - 16, top - 12, left + text_width + 16, top + text_height + 20), fill=(0, 0, 0))
        draw.text((left, top), line, font=font, fill=(255, 255, 255))
        top = top + text_height + 60
    if qr_image is not None:
        image.paste(qr_image, ((WIDTH - qr_image.width) // 2, HEIGHT - qr_image.height - 60))
    rgb = np.array(image)
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)


def make_video(sample: dict) -> None:
    font = load_font(42)
    qr_image = None
    if sample["qr"]:
        qr_image = qrcode.make(sample["qr"]).get_image().convert("RGB").resize((260, 260))
    seconds = audio_seconds(sample)
    frame_count = int(seconds * FPS)
    raw_path = BUILD_DIR / (sample["name"] + "_raw.mp4")
    writer = cv2.VideoWriter(str(raw_path), cv2.VideoWriter_fourcc(*"mp4v"), FPS, (WIDTH, HEIGHT))
    for index in range(frame_count):
        writer.write(draw_frame(sample, index, font, qr_image))
    writer.release()

    output = SAMPLES_DIR / (sample["name"] + ".mp4")
    command = [tool_path("ffmpeg"), "-y", "-loglevel", "error", "-i", str(raw_path)]
    aiff = BUILD_DIR / (sample["name"] + ".aiff")
    if aiff.exists():
        command = command + ["-i", str(aiff), "-c:a", "aac", "-b:a", "64k", "-shortest"]
    command = command + [
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "30",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(output),
    ]
    subprocess.run(command, check=True)
    raw_path.unlink()


def write_manifest() -> None:
    with open(SAMPLES_DIR / "samples.csv", "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["file", "category", "lang", "has_speech", "description"])
        for sample in SAMPLES:
            description = "no text on screen"
            if sample["lines"]:
                description = " / ".join(sample["lines"])
            has_speech = "no"
            if sample["speech"]:
                has_speech = "yes"
            writer.writerow([sample["name"] + ".mp4", sample["category"], sample["lang"], has_speech, description])


def main() -> None:
    parser = argparse.ArgumentParser(description="Build small synthetic sample videos")
    parser.add_argument("--step", choices=["speech", "video", "all"], default="all")
    args = parser.parse_args()
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    for sample in SAMPLES:
        if args.step in ("speech", "all"):
            make_speech(sample)
        if args.step in ("video", "all"):
            make_video(sample)
            print("built " + sample["name"] + ".mp4")
    if args.step in ("video", "all"):
        write_manifest()


if __name__ == "__main__":
    main()
