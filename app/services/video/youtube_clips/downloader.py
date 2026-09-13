import os
import json
import logging
import shutil
import tempfile
import base64
import requests
from .helpers import run_command

logger = logging.getLogger(__name__)


def _get_ytdlp_base_args() -> list[str]:
    """
    Builds common base arguments for yt-dlp to handle server/VPS environments:
    - JS runtimes (node/deno)
    - Anti-bot / mobile client extractor args (youtube:player_client=android,web)
    - Cookies authentication (--cookies)
    - Proxy support (--proxy)
    """
    args = []

    # 1. Extractor args: default to android,web to bypass web client bot checks on datacenter IPs
    player_clients = os.getenv("YOUTUBE_PLAYER_CLIENT", "android,web")
    if player_clients:
        args.extend(["--extractor-args", f"youtube:player_client={player_clients}"])

    # 2. JavaScript runtime: yt-dlp requires a JS runtime to solve player n-sig challenges
    js_runtime = os.getenv("YOUTUBE_JS_RUNTIME")
    if js_runtime:
        args.extend(["--js-runtimes", js_runtime])
    elif shutil.which("deno"):
        pass  # Deno is enabled by default in yt-dlp if present
    elif shutil.which("node"):
        args.extend(["--js-runtimes", "node"])

    # 3. Cookies support: check file or environment variable
    cookies_path = os.getenv("YOUTUBE_COOKIES_FILE") or os.getenv("YOUTUBE_COOKIES_PATH")
    if not cookies_path:
        candidates = [
            "/app/cookies.txt",
            os.path.join(os.getcwd(), "cookies.txt"),
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "cookies.txt")),
        ]
        for candidate in candidates:
            if os.path.isfile(candidate) and os.path.getsize(candidate) > 0:
                cookies_path = candidate
                break

    # Inline cookies from env var (content or base64)
    cookies_content = os.getenv("YOUTUBE_COOKIES_CONTENT")
    if not cookies_path and cookies_content:
        try:
            try:
                decoded = base64.b64decode(cookies_content).decode("utf-8")
                if "# Netscape" in decoded or "youtube.com" in decoded:
                    cookies_content = decoded
            except Exception:
                pass

            temp_cookies = os.path.join(tempfile.gettempdir(), "yt_cookies.txt")
            with open(temp_cookies, "w", encoding="utf-8") as f:
                f.write(cookies_content)
            cookies_path = temp_cookies
        except Exception as e:
            logger.warning(f"Error saving inline cookies: {e}")

    if cookies_path and os.path.isfile(cookies_path) and os.path.getsize(cookies_path) > 0:
        logger.info(f"Using YouTube cookies: {cookies_path}")
        args.extend(["--cookies", cookies_path])

    # 4. Proxy support
    proxy = os.getenv("YOUTUBE_PROXY") or os.getenv("HTTP_PROXY") or os.getenv("HTTPS_PROXY")
    if proxy:
        logger.info(f"Using proxy for yt-dlp: {proxy}")
        args.extend(["--proxy", proxy])

    return args


def download_youtube_video(url: str, output_dir: str) -> str:
    output_template = os.path.join(output_dir, "%(id)s.%(ext)s")
    base_args = _get_ytdlp_base_args()
    cmd = [
        "yt-dlp",
        *base_args,
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
        base_args = _get_ytdlp_base_args()
        cmd = ["yt-dlp", *base_args, "-J", "--no-playlist", url]
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
