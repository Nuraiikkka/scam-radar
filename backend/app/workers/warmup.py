import logging

from app.logging_setup import setup_logging
from app.services import audio, text_classifier, vision_ocr
from app.settings.conf import settings

logger = logging.getLogger("scamradar.warmup")


def main() -> None:
    setup_logging(settings.logs_dir, "worker.log", settings.debug)
    if settings.whisper_enabled:
        audio.get_whisper_model()
        logger.info("whisper model ready", extra={"stage": settings.whisper_model_size})
    if settings.ocr_enabled:
        vision_ocr.get_reader()
        logger.info("ocr model ready", extra={"stage": ",".join(settings.ocr_languages)})
    logger.info("text model ready", extra={"stage": text_classifier.model_version()})


if __name__ == "__main__":
    main()
