"""
YouTube audio downloader using yt-dlp.
Returns the local path to the downloaded audio file.
"""

import os
import uuid
import yt_dlp


def download_youtube_audio(url: str, output_dir: str = "uploads") -> tuple[str, str]:
    """
    Download audio from a YouTube URL.

    Returns:
        (file_path, video_title)
    """
    os.makedirs(output_dir, exist_ok=True)
    file_id   = str(uuid.uuid4())
    out_template = os.path.join(output_dir, f"{file_id}.%(ext)s")

    ydl_opts = {
        "format":            "bestaudio/best",
        "outtmpl":           out_template,
        "postprocessors": [{
            "key":            "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        "quiet":    True,
        "no_warnings": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        title = info.get("title", "YouTube Meeting")

    file_path = os.path.join(output_dir, f"{file_id}.mp3")
    return file_path, title
