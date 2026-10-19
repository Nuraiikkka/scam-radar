from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from app.settings.conf import settings


@dataclass
class Frame:
    timestamp: float
    image: np.ndarray


def plan_timestamps(duration: float, interval: float, max_frames: int) -> list[float]:
    if duration <= 0:
        return [0.0]
    step = interval
    if duration / step > max_frames:
        step = duration / max_frames
    timestamps = []
    current = min(0.5, duration / 2)
    while current < duration and len(timestamps) < max_frames:
        timestamps.append(round(current, 2))
        current = current + step
    if not timestamps:
        timestamps.append(0.0)
    return timestamps


def resize_frame(image: np.ndarray, max_width: int) -> np.ndarray:
    height, width = image.shape[:2]
    if width <= max_width:
        return image
    scale = max_width / width
    new_size = (max_width, int(height * scale))
    return cv2.resize(image, new_size, interpolation=cv2.INTER_AREA)


def is_similar(first: np.ndarray, second: np.ndarray) -> bool:
    small_first = cv2.resize(cv2.cvtColor(first, cv2.COLOR_BGR2GRAY), (64, 64))
    small_second = cv2.resize(cv2.cvtColor(second, cv2.COLOR_BGR2GRAY), (64, 64))
    difference = cv2.absdiff(small_first, small_second)
    return float(difference.mean()) < 2.0


def sample_frames(video_path: Path) -> list[Frame]:
    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        return []
    try:
        fps = capture.get(cv2.CAP_PROP_FPS) or 0.0
        frame_count = capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0.0
        duration = 0.0
        if fps > 0:
            duration = frame_count / fps
        timestamps = plan_timestamps(duration, settings.frame_interval_seconds, settings.max_frames)
        frames = []
        for timestamp in timestamps:
            capture.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)
            ok, image = capture.read()
            if not ok or image is None:
                continue
            image = resize_frame(image, settings.frame_max_width)
            if frames and is_similar(frames[-1].image, image):
                continue
            frames.append(Frame(timestamp=timestamp, image=image))
        return frames
    finally:
        capture.release()
