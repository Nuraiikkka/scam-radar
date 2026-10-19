from dataclasses import dataclass, field
from pathlib import Path

from app.services import vision_frames, vision_ocr, vision_rules


@dataclass
class VisionResult:
    ocr_text: str = ""
    qr_codes: list[str] = field(default_factory=list)
    links: list[str] = field(default_factory=list)
    phones: list[str] = field(default_factory=list)
    cues: list[vision_rules.Cue] = field(default_factory=list)
    score: float = 0.0
    frames_count: int = 0


def analyze_frames(frames: list[vision_frames.Frame]) -> VisionResult:
    lines = vision_ocr.read_frames(frames)
    ocr_text = vision_ocr.join_unique_lines(lines)
    qr_codes = vision_rules.detect_qr_codes(frames)

    screen = vision_rules.analyze_text(ocr_text, "screen_text")
    cues = list(screen["cues"])
    links = list(screen["links"])
    phones = list(screen["phones"])

    cues.extend(vision_rules.qr_cues(qr_codes))
    for payload in qr_codes:
        qr = vision_rules.analyze_text(payload, "qr")
        for cue in qr["cues"]:
            if cue.kind != "link":
                cues.append(cue)
        links.extend(qr["links"])
        phones.extend(qr["phones"])

    return VisionResult(
        ocr_text=ocr_text,
        qr_codes=qr_codes,
        links=vision_rules.unique(links),
        phones=vision_rules.unique(phones),
        cues=cues,
        score=vision_rules.score_cues(cues),
        frames_count=len(frames),
    )


def analyze_video(video_path: Path) -> VisionResult:
    frames = vision_frames.sample_frames(video_path)
    return analyze_frames(frames)
