"""Shared inference for the video pipeline and the optional text CLI."""
from functools import lru_cache
import logging
import math
from pathlib import Path
from threading import Lock

from app.settings import settings

log = logging.getLogger(__name__)
_load_lock = Lock()


@lru_cache(maxsize=2)
def _load(path, modified_ns):
    # Local artifacts only. joblib must never load user uploads or remote files.
    import joblib
    with _load_lock:
        artifact = joblib.load(path)
    if artifact.get('features') != ['transcript', 'ocr_text']:
        raise ValueError('Model feature schema does not match transcript+OCR')
    threshold = float(artifact['threshold'])
    if not math.isfinite(threshold) or not 0 < threshold < 1:
        raise ValueError('Invalid model threshold')
    if list(artifact['model'].classes_) != [0, 1]:
        raise ValueError('Expected classes 0=legitimate and 1=scam')
    return artifact


def predict(transcript, ocr_text='', *, enabled=None, model_path=None):
    if enabled is None:
        enabled = settings.ML_ENABLED
    result = {'status': 'disabled', 'verdict': None, 'score': None, 'threshold': None,
              'model': 'optiscam_binary_tfidf', 'experimental': True}
    if not enabled:
        return result
    text = ' '.join((transcript + ' ' + ocr_text).split())
    if len(text) < 40:
        return {**result, 'status': 'insufficient_text'}
    path = Path(model_path or settings.ML_MODEL_PATH).resolve()
    try:
        artifact = _load(str(path), path.stat().st_mtime_ns)
        score = float(artifact['model'].predict_proba([text])[0, 1])
        if not math.isfinite(score) or not 0 <= score <= 1:
            raise ValueError('Invalid model score')
        threshold = float(artifact['threshold'])
        return {**result, 'status': 'ok', 'score': score, 'threshold': threshold,
                'verdict': 'scam' if score >= threshold else 'legitimate'}
    except FileNotFoundError:
        log.warning('ML model not found: %s', path)
        return {**result, 'status': 'model_missing'}
    except Exception:
        log.exception('ML inference failed')
        return {**result, 'status': 'model_error'}
