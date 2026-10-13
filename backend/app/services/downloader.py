import os
import tempfile


class DownloadError(Exception):
    pass


def download(url):
    try:
        import yt_dlp
    except ImportError:
        raise DownloadError("yt-dlp is not installed. Run: pip install yt-dlp")

    folder = tempfile.mkdtemp()
    options = {
        "outtmpl": os.path.join(folder, "video.%(ext)s"),
        "format": "mp4/best",
        "quiet": True,
        "noplaylist": True,
    }

    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info)
    except Exception as error:
        raise DownloadError("Could not download video: " + str(error))
