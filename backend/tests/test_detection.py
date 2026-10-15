"""Regression examples from reported misses and benign counterexamples.

These verify heuristic behavior, not measured real-world accuracy.
"""
import pytest

from app.services.text_classifier import classify, evidence_summary
from app.services.fusion import fuse
from app.services.vision import rules_on_text, VisionResult
from app.services import pipeline


REV = (
    "I'm going to teach you how to make $500 extra dollars per day. "
    "Go to Rev.com. Get paid to write captions, transcribe, or subtitle. "
    "I have an easy hack for you. Go to Tools and Voice Typing. "
    "You make $1.10 per minute. Like, save, and follow for more side hustles."
)
WRITING = (
    "Here's how you could make $500 in 3 hours in a stupidly easy way. "
    "Go to textbroken.com. Get paid for every word you write. "
    "Get $192 for writing 12,000 words. Select a voice by pay. "
    "It's as easy as that. See how I make 5 figures a month, "
    "see my profile for free tutorials."
)


@pytest.mark.parametrize('text', [REV, WRITING,
    'Earn $700 per day with no effort using voice typing to write content.',
    'Заработай 500 долларов в день без опыта. Голосовой ввод для транскрипции.',
])
def test_suspicious_earnings(text):
    category, score, reasons = classify(text)
    assert category == 'job_offer'
    assert score >= 0.7
    assert len(reasons) >= 2
    assert fuse(category, score, 0)[0] == 'job_offer'


@pytest.mark.parametrize('text', [
    'We are hiring an editor. Salary $500 per day. Five years experience required.',
    'Our transcription service is 99% accurate. Pricing is $1.10 per audio minute.',
    'This article explains investments and the risks of crypto.',
    "Beware: make $500 in 3 hours in a stupidly easy way is a scam.",
    'Не верьте обещанию заработать 500 долларов в день без опыта.',
    '',
])
def test_benign_or_warning(text):
    assert classify(text)[0] == 'none'


def test_warning_does_not_hide_separate_promotion():
    assert classify('Beware of scams. ' + WRITING)[0] == 'job_offer'


def test_accuracy_percentage_is_not_investment_return():
    assert rules_on_text(['Transcription is 99% accurate'])[0] == 0
    assert rules_on_text(['Guaranteed investment return 99%'])[0] > 0


def test_silent_video_uses_ocr(monkeypatch):
    monkeypatch.setattr(pipeline.audio, 'transcribe', lambda _: '')
    monkeypatch.setattr(pipeline.vision, 'analyze', lambda _: VisionResult(ocr_text=[WRITING]))
    result = pipeline.run('silent.mp4')
    assert result['category'] == 'job_offer'
    assert result['risk_score'] >= 0.7


def test_generic_visual_cues_do_not_invent_category():
    category, score = fuse('none', 0, 1)
    assert category == 'none'
    assert 0 <= score <= 0.29


GIVEAWAY = "And getting away this new iPhone 18 Pro Max to one of you, rules are in the caption, super easy. Thanks for being here. Good luck."
WITHDRAWAL = "Withdraw RICHARD Real 848.77 ZAR Payment Method Bank-Card Payout Withdrawal Amount Min 95 ZAR Important Info any fund withdrawals from my trading account will result in the proportional removal of my trading bonus. XM's Withdrawal Priority Procedure."


@pytest.mark.parametrize('text,topic', [
    (GIVEAWAY, 'giveaway'),
    (WITHDRAWAL, 'investment_platform'),
    ('Our giveaway has a winner. Claim your prize at the store, no payment required.', 'giveaway'),
    ('Learn about crypto and forex investment risks.', 'investment_platform'),
])
def test_topic_alone_is_not_fraud(text, topic):
    category, _, _ = classify(text)
    assert category == 'none'
    summary = evidence_summary(text, '', category)
    assert topic in summary['detected_contexts']
    assert summary['status'] == 'insufficient_evidence'
    assert summary['warnings']


@pytest.mark.parametrize('text,expected', [
    (GIVEAWAY + ' Pay a shipping fee to receive the prize.', 'giveaway'),
    ('You won an iPhone prize. Send your verification code to claim it.', 'giveaway'),
    ('Розыгрыш телефона. Оплатите доставку для получения приза.', 'giveaway'),
    ('Invest in our crypto platform for guaranteed returns.', 'investment_platform'),
    (WITHDRAWAL + ' Deposit $100 to unlock your withdrawal.', 'investment_platform'),
    ('Вывод средств. Пополните счет для вывода денег.', 'investment_platform'),
])
def test_context_with_concrete_risk(text, expected):
    category, score, reasons = classify(text)
    assert category == expected
    assert score >= 0.8
    assert reasons


def test_financial_warning_is_not_promotion():
    assert classify('Beware: invest in crypto for guaranteed returns is a scam.')[0] == 'none'


def test_empty_input_reports_insufficient_evidence():
    summary = evidence_summary('', '', 'none')
    assert summary['status'] == 'insufficient_evidence'
    assert len(summary['warnings']) == 3
