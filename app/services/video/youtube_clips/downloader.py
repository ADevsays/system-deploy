import os
import json
import logging
import requests
from .helpers import run_command

logger = logging.getLogger(__name__)

def download_youtube_video(url: str, output_dir: str) -> str:
    output_template = os.path.join(output_dir, "%(id)s.%(ext)s")
    cmd = [
        "yt-dlp",
        "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "--merge-output-format", "mp4",
        "-o", output_template,
        url
    ]
    run_command(cmd, "YouTube video download")

    for fname in os.listdir(output_dir):
        if fname.endswith(".mp4"):
            return os.path.abspath(os.path.join(output_dir, fname))

    raise FileNotFoundError("Downloaded video not found in output directory")


def get_youtube_metadata(url: str, temp_dir: str = None) -> dict:
    """
    Extracts metadata using yt-dlp and downloads thumbnail if temp_dir is provided.
    """
    try:
        cmd = ["yt-dlp", "-J", "--no-playlist", url]
        result = run_command(cmd, "YouTube metadata extraction")
        data = json.loads(result.stdout.strip())
        
        meta = {
            "title": data.get("title", "Video de YouTube"),
            "uploader": data.get("uploader", "YouTube"),
            "thumbnail_url": data.get("thumbnail", ""),
            "thumbnail_path": None
        }

        if temp_dir and meta["thumbnail_url"]:
            try:
                thumb_resp = requests.get(meta["thumbnail_url"], timeout=10)
                if thumb_resp.status_code == 200:
                    thumb_path = os.path.join(temp_dir, "thumb.jpg")
                    with open(thumb_path, "wb") as f:
                        f.write(thumb_resp.content)
                    meta["thumbnail_path"] = thumb_path
            except Exception as e:
                logger.warning(f"Error downloading thumbnail: {str(e)}")

        return meta
    except Exception as e:
        logger.warning(f"Could not extract YouTube metadata: {str(e)}")
        return {
            "title": "Video de YouTube",
            "uploader": "YouTube",
            "thumbnail_url": "",
            "thumbnail_path": None
        }
