import pytest
import yt_dlp

from app.services import downloader
from app.settings.env.local import LocalConfig
from app.settings.env.prod import ProdConfig


def public_dns(host):
    return ["104.18.20.1"]


def private_dns(host):
    return ["10.0.0.5"]


def test_accepts_tiktok_links(monkeypatch):
    monkeypatch.setattr(downloader, "resolve_host", public_dns)
    url = downloader.validate_tiktok_url("  https://www.tiktok.com/@user/video/123?lang=en ")
    assert url == "https://www.tiktok.com/@user/video/123?lang=en"
    assert downloader.validate_tiktok_url("http://vm.tiktok.com/ZMabc/").startswith("https://vm.tiktok.com/")


@pytest.mark.parametrize(
    "url",
    [
        "https://evil.com/video",
        "https://tiktok.com.evil.com/x",
        "ftp://www.tiktok.com/x",
        "https://user:pass@www.tiktok.com/x",
        "https://www.tiktok.com:8080/x",
        "file:///etc/passwd",
        "javascript:alert(1)",
        "https://" + "a" * 2050,
    ],
)
def test_rejects_bad_links(monkeypatch, url):
    monkeypatch.setattr(downloader, "resolve_host", public_dns)
    with pytest.raises(downloader.DownloadError) as error:
        downloader.validate_tiktok_url(url)
    assert error.value.code == "invalid_url"


def test_rejects_private_network(monkeypatch):
    monkeypatch.setattr(downloader, "resolve_host", private_dns)
    with pytest.raises(downloader.DownloadError):
        downloader.validate_tiktok_url("https://www.tiktok.com/@a/video/1")


@pytest.mark.parametrize(
    "address",
    ["127.0.0.1", "10.1.2.3", "192.168.1.1", "169.254.169.254", "::1", "0.0.0.0", "::ffff:127.0.0.1", "224.0.0.1"],
)
def test_private_addresses_are_blocked(address):
    assert downloader.is_public_ip(address) is False


def test_public_address_is_allowed():
    assert downloader.is_public_ip("8.8.8.8") is True


@pytest.mark.parametrize(
    "message,code",
    [
        ("ERROR: This video is private", "video_private"),
        ("ERROR: Video not available, status code 10204", "video_unavailable"),
        ("ERROR: HTTP Error 404: Not Found", "video_unavailable"),
        ("ERROR: Read timed out", "download_timeout"),
        ("ERROR: something strange", "download_failed"),
    ],
)
def test_error_mapping(message, code):
    assert downloader.map_error(message).code == code


class FailingDownloader:
    def __init__(self, options):
        self.options = options

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def extract_info(self, url, download):
        raise yt_dlp.utils.DownloadError("ERROR: [TikTok] 123: This video is private")


class LongVideoDownloader(FailingDownloader):
    def extract_info(self, url, download):
        return {"duration": 9999, "title": "long"}


class WorkingDownloader(FailingDownloader):
    def extract_info(self, url, download):
        path = self.options["outtmpl"].replace("%(ext)s", "mp4")
        with open(path, "wb") as handle:
            handle.write(b"video-bytes")
        return {"duration": 10, "title": "ok"}


def test_download_private_video(monkeypatch, tmp_path):
    monkeypatch.setattr(downloader, "resolve_host", public_dns)
    monkeypatch.setattr(downloader.yt_dlp, "YoutubeDL", FailingDownloader)
    with pytest.raises(downloader.DownloadError) as error:
        downloader.download_video("https://www.tiktok.com/@a/video/1", tmp_path)
    assert error.value.code == "video_private"


def test_download_too_long(monkeypatch, tmp_path):
    monkeypatch.setattr(downloader, "resolve_host", public_dns)
    monkeypatch.setattr(downloader.yt_dlp, "YoutubeDL", LongVideoDownloader)
    with pytest.raises(downloader.DownloadError) as error:
        downloader.download_video("https://www.tiktok.com/@a/video/1", tmp_path)
    assert error.value.code == "video_too_long"


def test_download_success(monkeypatch, tmp_path):
    monkeypatch.setattr(downloader, "resolve_host", public_dns)
    monkeypatch.setattr(downloader.yt_dlp, "YoutubeDL", WorkingDownloader)
    result = downloader.download_video("https://www.tiktok.com/@a/video/1", tmp_path)
    assert result["path"].name == "download.mp4"


def test_download_options_are_safe(tmp_path):
    options = downloader.build_options(tmp_path)
    assert options["noplaylist"] is True
    assert options["max_filesize"] > 0
    assert options["socket_timeout"] > 0
    assert "tiktok" in options["allowed_extractors"]


def test_prod_requires_strong_secret(monkeypatch):
    monkeypatch.setenv("SCAMRADAR_SECRET_KEY", "short")
    with pytest.raises(ValueError):
        ProdConfig()


def test_prod_rejects_wildcard_cors(monkeypatch):
    monkeypatch.setenv("SCAMRADAR_SECRET_KEY", "x" * 40)
    monkeypatch.setenv("SCAMRADAR_CORS_ORIGINS", '["*"]')
    with pytest.raises(ValueError):
        ProdConfig()


def test_env_prefix_is_used(monkeypatch):
    monkeypatch.setenv("SCAMRADAR_MAX_FRAMES", "3")
    assert LocalConfig().max_frames == 3


def test_env_example_documents_every_setting():
    import re
    from pathlib import Path

    from app.settings.base import BaseConfig

    example = Path(__file__).resolve().parent.parent / "app" / "settings" / ".env.example"
    documented = set(re.findall(r"^SCAMRADAR_([A-Z_]+)=", example.read_text(), re.MULTILINE))
    fields = {name.upper() for name in BaseConfig.model_fields}
    assert fields - documented == set()
