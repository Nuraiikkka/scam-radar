import contextvars
import json
import logging
from datetime import UTC, datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path

request_id_var = contextvars.ContextVar("request_id", default=None)

EXTRA_FIELDS = ["path", "method", "status", "duration_ms", "analysis_id", "error_code", "stage"]


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        data = {
            "time": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id_var.get(),
        }
        for field in EXTRA_FIELDS:
            if hasattr(record, field):
                data[field] = getattr(record, field)
        if record.exc_info:
            data["exception"] = self.formatException(record.exc_info)
        return json.dumps(data, ensure_ascii=False)


logging_is_ready = False


def setup_logging(logs_dir: Path, filename: str, debug: bool) -> None:
    global logging_is_ready
    if logging_is_ready:
        return
    root = logging.getLogger()
    logs_dir.mkdir(parents=True, exist_ok=True)
    formatter = JsonFormatter()

    file_handler = RotatingFileHandler(logs_dir / filename, maxBytes=10_000_000, backupCount=5, encoding="utf-8")
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    root.handlers = [file_handler, console_handler]
    if debug:
        root.setLevel(logging.DEBUG)
    else:
        root.setLevel(logging.INFO)
    for noisy in ["httpx", "urllib3", "PIL", "multipart", "python_multipart", "faster_whisper", "easyocr"]:
        logging.getLogger(noisy).setLevel(logging.WARNING)
    logging_is_ready = True
