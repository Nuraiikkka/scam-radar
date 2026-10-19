import numpy as np
import qrcode

from app.services import vision_rules
from app.services.vision_frames import Frame


def codes(cues):
    result = []
    for cue in cues:
        result.append(cue.code)
    return result


def test_normalize_fixes_telegram_misread():
    assert "t.me/x" in vision_rules.normalize_text("Пиши tmelx")
    assert "t.me/profit" in vision_rules.normalize_text("t me/profit")
    assert "t.me/profit" in vision_rules.normalize_text("t,me|profit")


def test_normalize_fixes_cyrillic_lookalikes_in_links():
    assert "t.me/cash" in vision_rules.normalize_text("т.ме/cash")
    assert "site.com" in vision_rules.normalize_text("sitе.соm")


def test_normalize_fixes_comma_instead_of_dot():
    assert "profit.bet" in vision_rules.normalize_text("profit,bet")


def test_find_links():
    links = vision_rules.find_links(
        vision_rules.normalize_text("Go to https://www.Profit-Max.xyz/join now, or bit.ly/abc")
    )
    assert "profit-max.xyz/join" in links
    assert "bit.ly/abc" in links


def test_numbers_are_not_links():
    assert vision_rules.find_links("price 3.50 and version 2.1") == []


def test_find_phones():
    phones = vision_rules.find_phones("Звони +7 701 555 12 34 или 8 (777) 123-45-67")
    assert phones == ["+77015551234", "+77771234567"]


def test_link_cues_types():
    cues = vision_rules.link_cues(
        ["t.me/a", "wa.me/77011234567", "bit.ly/x", "win.bet", "tiktok.com/@a", "shop.kz"], "screen_text"
    )
    assert codes(cues) == [
        "telegram_link",
        "whatsapp_link",
        "short_link",
        "risky_domain",
        "known_link",
        "external_link",
    ]


def test_high_return_claim():
    result = vision_rules.analyze_text("Доход 30% в день гарантированно", "screen_text")
    assert "high_return_claim" in codes(result["cues"])


def test_plain_percent_is_weak():
    result = vision_rules.analyze_text("Скидка 20% на пиццу", "screen_text")
    assert codes(result["cues"]) == ["percent_claim"]


def test_multiplier_and_money():
    result = vision_rules.analyze_text("Удвой депозит x10, вывод $500", "speech")
    found = codes(result["cues"])
    assert "multiplier_claim" in found
    assert "money_amount" in found


def test_handles_and_contact_words():
    result = vision_rules.analyze_text("Пиши в телеграм @profit_daily", "screen_text")
    found = codes(result["cues"])
    assert "messenger_handle" in found
    assert "off_platform_contact" in found


def test_email_is_not_a_handle():
    result = vision_rules.analyze_text("mail me at anna@gmail.com", "screen_text")
    assert "messenger_handle" not in codes(result["cues"])


def test_every_cue_has_reason_with_source():
    result = vision_rules.analyze_text("30% в день t.me/a +7 701 555 12 34 $500 @handle_one", "screen_text")
    assert result["cues"]
    for cue in result["cues"]:
        assert cue.message_en.startswith("On screen:")
        assert cue.message_ru.startswith("На экране:")


def test_empty_and_kazakh_text():
    assert vision_rules.analyze_text("", "speech")["cues"] == []
    result = vision_rules.analyze_text("Күніне 30% табыс, жаз @kz_money_bot", "speech")
    assert "messenger_handle" in codes(result["cues"])


def test_score_is_bounded_and_capped():
    cue = vision_rules.make_cue("screen_text", "link", "external_link", "a.com", 0.9, "x", "y")
    assert 0 <= vision_rules.score_cues([cue] * 50) <= 1
    assert vision_rules.score_cues([]) == 0


def test_detect_qr_codes():
    image = np.array(qrcode.make("https://t.me/qr_test").get_image().convert("RGB").resize((300, 300)))
    canvas = np.full((600, 400, 3), 255, dtype=np.uint8)
    canvas[150:450, 50:350] = image
    payloads = vision_rules.detect_qr_codes([Frame(timestamp=0.0, image=canvas)])
    assert payloads == ["https://t.me/qr_test"]
    cues = vision_rules.qr_cues(payloads)
    assert cues[0].source == "qr"
    assert cues[0].message_en.startswith("In a QR code:")


def test_detect_qr_on_blank_frame():
    blank = np.zeros((100, 100, 3), dtype=np.uint8)
    assert vision_rules.detect_qr_codes([Frame(timestamp=0.0, image=blank)]) == []
