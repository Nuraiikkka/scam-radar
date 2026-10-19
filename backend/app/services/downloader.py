import ipaddress
import socket
from pathlib import Path
from urllib.parse import urlsplit

import yt_dlp

from app.settings.conf import settings


class DownloadError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


ERROR_PATTERNS = [
    ("private", "video_private", "This video is private"),
    ("log in", "video_private", "This video needs a login to watch"),
    ("login required", "video_private", "This video needs a login to watch"),
    ("not available", "video_unavailable", "The video was removed or is not available"),
    ("unavailable", "video_unavailable", "The video was removed or is not available"),
    ("removed", "video_unavailable", "The video was removed or is not available"),
    ("http error 404", "video_unavailable", "The video was removed or is not available"),
    ("does not exist", "video_unavailable", "The video was removed or is not available"),
    ("max_filesize", "video_too_large", "The video file is too large"),
    ("larger than max-filesize", "video_too_large", "The video file is too large"),
    ("timed out", "download_timeout", "Downloading the video took too long"),
    ("timeout", "download_timeout", "Downloading the video took too long"),
    ("unsupported url", "invalid_url", "This link is not a TikTok video"),
]


def is_public_ip(address: str) -> bool:
    ip = ipaddress.ip_address(address)
    if ip.is_private or ip.is_loopback or ip.is_link_local:
        return False
    if ip.is_multicast or ip.is_reserved or ip.is_unspecified:
        return False
    if ip.version == 6 and ip.ipv4_mapped is not None:
        return is_public_ip(str(ip.ipv4_mapped))
    return True


def resolve_host(host: str) -> list[str]:
    try:
        infos = socket.getaddrinfo(host, 443, proto=socket.IPPROTO_TCP)
    except socket.gaierror:
        raise DownloadError("invalid_url", "The link host could not be found")
    addresses = []
    for info in infos:
        addresses.append(info[4][0])
    return addresses


def validate_tiktok_url(url: str, check_dns: bool = True) -> str:
    cleaned = url.strip()
    if len(cleaned) > 2048:
        raise DownloadError("invalid_url", "The link is too long")
    parts = urlsplit(cleaned)
    if parts.scheme not in ("http", "https"):
        raise DownloadError("invalid_url", "The link must start with https://")
    if parts.username or parts.password:
        raise DownloadError("invalid_url", "The link must not contain a login")
    host = (parts.hostname or "").lower()
    if host not in settings.allowed_url_hosts:
        raise DownloadError("invalid_url", "Only TikTok links are supported")
    try:
        port = parts.port
    except ValueError:
        raise DownloadError("invalid_url", "The link has an invalid port")
    if port is not None and port not in (80, 443):
        raise DownloadError("invalid_url", "The link has an invalid port")
    if check_dns:
        for address in resolve_host(host):
            if not is_public_ip(address):
                raise DownloadError("invalid_url", "The link points to a private network")
    clean_url = "https://" + host + parts.path
    if parts.query:
        clean_url = clean_url + "?" + parts.query
    return clean_url


def map_error(message: str) -> DownloadError:
    lowered = message.lower()
    for pattern, code, text in ERROR_PATTERNS:
        if pattern in lowered:
            return DownloadError(code, text)
    return DownloadError("download_failed", "Could not download the video")


def check_duration(info, *, incomplete):
    duration = info.get("duration")
    if duration and duration > settings.max_video_seconds:
        return "video too long"
    return None


def build_options(target_dir: Path) -> dict:
    return {
        "outtmpl": str(target_dir / "download.%(ext)s"),
        "format": "best[ext=mp4][vcodec!=none][acodec!=none]/best[vcodec!=none]/best",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "socket_timeout": settings.download_timeout_seconds,
        "retries": settings.download_retries,
        "fragment_retries": settings.download_retries,
        "max_filesize": settings.max_upload_mb * 1024 * 1024,
        "match_filter": check_duration,
        "allowed_extractors": ["tiktok", "vm\\.tiktok"],
        "restrictfilenames": True,
        "cachedir": False,
    }


def download_video(url: str, target_dir: Path) -> dict:
    safe_url = validate_tiktok_url(url)
    target_dir.mkdir(parents=True, exist_ok=True)
    options = build_options(target_dir)
    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(safe_url, download=True)
    except yt_dlp.utils.DownloadError as exc:
        raise map_error(str(exc))
    except yt_dlp.utils.ExtractorError as exc:
        raise map_error(str(exc))
    if info is None:
        raise DownloadError("download_failed", "Could not download the video")
    duration = info.get("duration")
    if duration and duration > settings.max_video_seconds:
        raise DownloadError(
            "video_too_long", "The video is longer than " + str(settings.max_video_seconds) + " seconds"
        )
    files = sorted(target_dir.glob("download.*"))
    video_files = []
    for path in files:
        if path.suffix not in (".part", ".ytdl", ".json"):
            video_files.append(path)
    if not video_files:
        raise DownloadError("video_too_large", "The video file is too large or could not be saved")
    return {
        "path": video_files[0],
        "duration": info.get("duration"),
        "title": info.get("title"),
    }
