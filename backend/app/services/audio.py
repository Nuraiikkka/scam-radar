import json
import logging
import shutil
import subprocess
import threading
import wave
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from app.settings.conf import settings

logger = logging.getLogger("scamradar.audio")

SUPPORTED_LANGUAGES = ["ru", "en", "kk"]
SILENCE_RMS = 0.004

model_lock = threading.Lock()
loaded_models = {}


class MediaError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass
class MediaInfo:
    duration: float
    has_audio: bool
    has_video: bool


@dataclass
class TranscriptResult:
    text: str
    language: str | None
    status: str


def find_tool(name: str) -> str:
    path = shutil.which(name)
    if path is None:
        raise MediaError("ffmpeg_missing", name + " is not installed on the server")
    return path


def probe_media(video_path: Path) -> MediaInfo:
    command = [
        find_tool("ffprobe"),
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_streams",
        "-show_format",
        str(video_path),
    ]
    try:
        result = subprocess.run(command, capture_output=True, timeout=30, check=False)
    except subprocess.TimeoutExpired:
        raise MediaError("invalid_video", "Could not read the video file in time")
    if result.returncode != 0:
        raise MediaError("invalid_video", "The file is not a readable video")
    try:
        data = json.loads(result.stdout.decode("utf-8", errors="replace"))
    except json.JSONDecodeError:
        raise MediaError("invalid_video", "The file is not a readable video")
    has_audio = False
    has_video = False
    for stream in data.get("streams", []):
        if stream.get("codec_type") == "audio":
            has_audio = True
        if stream.get("codec_type") == "video" and stream.get("disposition", {}).get("attached_pic") != 1:
            has_video = True
    duration_text = data.get("format", {}).get("duration")
    try:
        duration = float(duration_text)
    except (TypeError, ValueError):
        duration = 0.0
    if not has_video:
        raise MediaError("invalid_video", "The file has no video track")
    return MediaInfo(duration=duration, has_audio=has_audio, has_video=has_video)


def extract_audio(video_path: Path, wav_path: Path) -> None:
    command = [
        find_tool("ffmpeg"),
        "-nostdin",
        "-y",
        "-loglevel",
        "error",
        "-i",
        str(video_path),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-t",
        str(settings.max_video_seconds),
        "-f",
        "wav",
        str(wav_path),
    ]
    try:
        result = subprocess.run(command, capture_output=True, timeout=120, check=False)
    except subprocess.TimeoutExpired:
        raise MediaError("audio_failed", "Extracting audio took too long")
    if result.returncode != 0 or not wav_path.exists():
        raise MediaError("audio_failed", "Could not extract audio from the video")


def audio_rms(wav_path: Path) -> float:
    with wave.open(str(wav_path), "rb") as wav_file:
        frames = wav_file.readframes(wav_file.getnframes())
    if not frames:
        return 0.0
    samples = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
    if samples.size == 0:
        return 0.0
    return float(np.sqrt(np.mean(samples * samples)))


def get_whisper_model():
    from faster_whisper import WhisperModel

    with model_lock:
        key = settings.whisper_model_size
        if key not in loaded_models:
            download_root = settings.model_cache_dir / "whisper"
            download_root.mkdir(parents=True, exist_ok=True)
            loaded_models[key] = WhisperModel(
                settings.whisper_model_size,
                device=settings.whisper_device,
                compute_type=settings.whisper_compute_type,
                download_root=str(download_root),
            )
        return loaded_models[key]


def transcribe_wav(wav_path: Path) -> TranscriptResult:
    model = get_whisper_model()
    segments, info = model.transcribe(str(wav_path), beam_size=1, vad_filter=True)
    pieces = []
    for segment in segments:
        text = segment.text.strip()
        if text:
            pieces.append(text)
    text = " ".join(pieces).strip()
    language = info.language
    if not text:
        return TranscriptResult(text="", language=language, status="no_speech")
    if language not in SUPPORTED_LANGUAGES:
        return TranscriptResult(text=text, language=language, status="unsupported_language")
    return TranscriptResult(text=text, language=language, status="ok")


def transcribe_video(video_path: Path, work_dir: Path, media: MediaInfo) -> TranscriptResult:
    if not settings.whisper_enabled:
        return TranscriptResult(text="", language=None, status="disabled")
    if not media.has_audio:
        return TranscriptResult(text="", language=None, status="no_audio")
    wav_path = work_dir / "audio.wav"
    extract_audio(video_path, wav_path)
    try:
        if audio_rms(wav_path) < SILENCE_RMS:
            return TranscriptResult(text="", language=None, status="silent")
        return transcribe_wav(wav_path)
    finally:
        wav_path.unlink(missing_ok=True)
