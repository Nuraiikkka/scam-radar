import logging
import threading
from dataclasses import dataclass

from app.services.vision_frames import Frame
from app.settings.conf import settings

logger = logging.getLogger("scamradar.ocr")

MIN_CONFIDENCE = 0.3

reader_lock = threading.Lock()
loaded_readers = {}


@dataclass
class OcrLine:
    text: str
    confidence: float
    timestamp: float


def get_reader():
    import easyocr

    with reader_lock:
        key = ",".join(settings.ocr_languages)
        if key not in loaded_readers:
            storage = settings.model_cache_dir / "easyocr"
            storage.mkdir(parents=True, exist_ok=True)
            loaded_readers[key] = easyocr.Reader(
                settings.ocr_languages,
                gpu=settings.ocr_gpu,
                model_storage_directory=str(storage),
                user_network_directory=str(storage),
                download_enabled=True,
                verbose=False,
            )
        return loaded_readers[key]


def read_frame(reader, frame: Frame) -> list[OcrLine]:
    results = reader.readtext(frame.image, detail=1, paragraph=False)
    lines = []
    for item in results:
        text = str(item[1]).strip()
        confidence = float(item[2])
        if text and confidence >= MIN_CONFIDENCE:
            lines.append(OcrLine(text=text, confidence=confidence, timestamp=frame.timestamp))
    return lines


def read_frames(frames: list[Frame]) -> list[OcrLine]:
    if not settings.ocr_enabled or not frames:
        return []
    reader = get_reader()
    all_lines = []
    for frame in frames:
        all_lines.extend(read_frame(reader, frame))
    return all_lines


def join_unique_lines(lines: list[OcrLine]) -> str:
    seen = set()
    texts = []
    for line in lines:
        key = line.text.lower()
        if key in seen:
            continue
        seen.add(key)
        texts.append(line.text)
    return "\n".join(texts)
