import time

from app.services import audio, vision, text_classifier, fusion


def run(video_path):
    start = time.time()

    transcript = audio.transcribe(video_path)

    v = vision.analyze(video_path)

    all_text = transcript + " " + " ".join(v.ocr_text)
    category, text_score, reasons = text_classifier.classify(all_text)

    final_category, final_score = fusion.fuse(category, text_score, v.score)

    signals = []
    for reason in reasons:
        signals.append({"source": "text", "description": reason})
    for cue in v.cues:
        signals.append({"source": "vision", "description": cue})

    return {
        "category": final_category,
        "risk_score": final_score,
        "transcript": transcript,
        "ocr_text": " | ".join(v.ocr_text),
        "text_score": text_score,
        "vision_score": v.score,
        "signals": signals,
        "duration_sec": v.duration_sec,
        "processing_ms": int((time.time() - start) * 1000),
    }


def run_mock():
    return {
        "category": "investment_platform",
        "risk_score": 0.87,
        "transcript": "Demo transcript: guaranteed profit, join now",
        "ocr_text": "Join now | t.me/demo",
        "text_score": 0.9,
        "vision_score": 0.8,
        "signals": [
            {"source": "text", "description": "Keyword: guaranteed profit"},
            {"source": "vision", "description": "Link shown on screen"},
        ],
        "duration_sec": 0.0,
        "processing_ms": 5,
    }
