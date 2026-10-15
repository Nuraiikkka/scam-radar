"""Computer Vision (Aisulu + Nuray rules). Keep the analyze() signature stable.

Pipeline: sample frames -> OCR -> rules on OCR text -> VisionResult
Degrades gracefully if opencv / easyocr are not installed.
"""
import logging
import re
from dataclasses import dataclass, field
from typing import List

from app.settings import settings as config

log = logging.getLogger(__name__)


@dataclass
class VisionResult:
    ocr_text: List[str] = field(default_factory=list)
    score: float = 0.0                     # 0..1 visual scam likelihood
    cues: List[str] = field(default_factory=list)
    duration_sec: float = 0.0


# ---- Rules on OCR text (Nuray) -------------------------------------------------
URL_RE = re.compile(r"(https?://\S+|t\.me/\S+|wa\.me/\S+|\b\w+\.(?:com|ru|kz|io|site|xyz)\b)", re.I)
PHONE_RE = re.compile(r"\+?\d[\d\s\-()]{9,}\d")
PERCENT_RE = re.compile(r"\b(\d{2,4})\s?%")
MONEY_RE = re.compile(r"(\$|€|₸|₽|usd|тг|тенге|руб)\s?\d[\d\s.,]*|\d[\d\s.,]*\s?(\$|€|₸|₽|usd|тг|тенге|руб)", re.I)


def rules_on_text(lines: List[str]) -> "tuple[float, List[str]]":
    blob = " ".join(lines)
    score, cues = 0.0, []
    if URL_RE.search(blob):
        score += 0.25; cues.append("Link / messenger contact shown on screen")
    if PHONE_RE.search(blob):
        score += 0.15; cues.append("Phone number shown on screen")
    if PERCENT_RE.search(blob) and re.search(
        r"profit|return|yield|interest|доход|прибыл|доходност", blob, re.I
    ):
        score += 0.2; cues.append("Percentage shown alongside an investment return claim")
    if MONEY_RE.search(blob):
        score += 0.2; cues.append("Money amounts shown on screen")
    return min(1.0, score), cues


# ---- Frame sampling + OCR (Aisulu) ---------------------------------------------
def sample_frames(video_path: str):
    """Return (list of BGR frames, duration_sec). TODO(Aisulu): smarter sampling (scene change)."""
    import cv2  # type: ignore
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    total = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0
    duration = total / fps if fps else 0
    # Spread a limited frame budget across the whole video, not just its intro.
    step = max(1, int(fps * config.FRAME_EVERY_SEC))
    if total > 1 and config.MAX_FRAMES > 1:
        step = max(step, int((total - 1) / (config.MAX_FRAMES - 1)))
    frames, i = [], 0
    while len(frames) < config.MAX_FRAMES:
        cap.set(cv2.CAP_PROP_POS_FRAMES, i)
        ok, frame = cap.read()
        if not ok:
            break
        frames.append(frame)
        i += step
    cap.release()
    return frames, duration


_reader = None


def ocr_frames(frames) -> List[str]:
    global _reader
    import easyocr  # type: ignore
    if _reader is None:
        _reader = easyocr.Reader(config.OCR_LANGS, gpu=False)
    seen, out = set(), []
    for fr in frames:
        for text in _reader.readtext(fr, detail=0):
            key = text.strip().lower()
            if len(key) > 2 and key not in seen:
                seen.add(key); out.append(text.strip())
    return out


def detect_visual_cues(frames) -> "tuple[float, List[str]]":
    """TODO(Aisulu): QR codes (cv2.QRCodeDetector), bet-slip / profit-screenshot / logo detection."""
    try:
        import cv2  # type: ignore
        det = cv2.QRCodeDetector()
        for fr in frames:
            data, _, _ = det.detectAndDecode(fr)
            if data:
                return 0.3, ["QR code shown in video"]
    except Exception:
        pass
    return 0.0, []


def analyze(video_path: str) -> VisionResult:
    if not video_path:
        return VisionResult()
    try:
        frames, duration = sample_frames(video_path)
    except ImportError:
        log.warning("opencv not installed, skipping vision")
        return VisionResult()
    except Exception as e:
        log.exception("frame sampling failed: %s", e)
        return VisionResult()
    lines: List[str] = []
    try:
        lines = ocr_frames(frames)
    except ImportError:
        log.warning("easyocr not installed, skipping OCR")
    except Exception as e:
        log.exception("ocr failed: %s", e)
    s1, c1 = rules_on_text(lines)
    s2, c2 = detect_visual_cues(frames)
    return VisionResult(ocr_text=lines, score=round(min(1.0, s1 + s2), 3), cues=c1 + c2, duration_sec=duration)
