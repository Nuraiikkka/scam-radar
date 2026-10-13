import logging

from app.settings import settings

log = logging.getLogger(__name__)

model = None


def transcribe(video_path):
    global model

    if video_path == "":
        return ""

    try:
        import whisper
    except ImportError:
        log.warning("Whisper is not installed, skipping speech recognition")
        return ""

    try:
        if model is None:
            model = whisper.load_model(settings.WHISPER_MODEL)
        result = model.transcribe(video_path)
        return result["text"].strip()
    except Exception as error:
        log.error("Whisper error: %s", error)
        return ""
