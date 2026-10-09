import os
import json
import logging
import shutil
import tempfile
import base64
from uuid import uuid4
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


def format_time_hhmmss(val: str | int | float | None, default: str = "00:00:00") -> str:
    if not val:
        return default
    if isinstance(val, (int, float)):
        seconds = int(val)
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        return f"{h:02d}:{m:02d}:{s:02d}"

    val_str = str(val).strip()
    parts = val_str.split(":")
    if len(parts) == 3:
        return f"{int(parts[0]):02d}:{int(parts[1]):02d}:{int(parts[2]):02d}"
    elif len(parts) == 2:
        return f"00:{int(parts[0]):02d}:{int(parts[1]):02d}"
    elif len(parts) == 1 and parts[0].isdigit():
        seconds = int(parts[0])
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        return f"{h:02d}:{m:02d}:{s:02d}"
    return val_str


def normalize_quality(quality: str | int | None) -> tuple[str, int]:
    if not quality:
        return "720p", 720

    clean = str(quality).strip().lower().rstrip("p")
    if clean in ("480", "720", "1080"):
        h = int(clean)
        return f"{h}p", h

    raise ValueError(f"Invalid quality '{quality}'. Allowed values are 480, 720, 1080 (or 480p, 720p, 1080p).")


def download_via_apify_cutter(
    url: str,
    output_dir: str,
    apify_token: str,
    start_time: str = "00:00:00",
    end_time: str = None,
    quality: str = "720p"
) -> str:
    start_hhmmss = format_time_hhmmss(start_time, default="00:00:00")
    end_hhmmss = format_time_hhmmss(end_time, default="") if end_time else None
    quality_str, _ = normalize_quality(quality)

    logger.info(f"Downloading trimmed YouTube video via Apify Cutter Actor: {url} ({start_hhmmss} -> {end_hhmmss}) (quality: {quality_str})")

    payload = {
        "url": url,
        "trim": True,
        "startTime": start_hhmmss,
        "quality": quality_str,
        "format": "mp4",
        "convertToVertical": False
    }
    if end_hhmmss:
        payload["endTime"] = end_hhmmss

    endpoint = f"https://api.apify.com/v2/acts/nodexagent~youtube-video-cut-and-download/run-sync-get-dataset-items?token={apify_token}&timeout=360"
    resp = requests.post(endpoint, json=payload, timeout=400)
    if resp.status_code not in (200, 201):
        raise Exception(f"Apify cutter actor run failed (HTTP {resp.status_code}): {resp.text[:300]}")

    items = resp.json()
    if not items or not isinstance(items, list):
        raise Exception(f"Invalid dataset response from Apify cutter: {resp.text[:300]}")

    file_url = items[0].get("fileUrl") or items[0].get("downloadedFileUrl")
    if not file_url:
        raise Exception(f"No fileUrl returned by Apify cutter: {items[0]}")

    dest_path = os.path.join(output_dir, f"trimmed_{uuid4().hex[:8]}.mp4")
    logger.info(f"Streaming trimmed video from Apify Storage to: {dest_path}")

    with requests.get(file_url, stream=True, timeout=180) as r:
        r.raise_for_status()
        with open(dest_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)

    if not os.path.exists(dest_path) or os.path.getsize(dest_path) == 0:
        raise FileNotFoundError(f"Failed to save trimmed video from Apify to {dest_path}")

    logger.info(f"Successfully downloaded trimmed video via Apify: {dest_path} ({os.path.getsize(dest_path)} bytes)")
    return os.path.abspath(dest_path)


def download_via_apify(url: str, output_dir: str, apify_token: str, quality: str = "720p") -> str:
    quality_str, _ = normalize_quality(quality)
    logger.info(f"Downloading YouTube video via Apify Actor: {url} (quality: {quality_str})")
    payload = {
        "videos": [{"url": url}],
        "storeInKVStore": True,
        "preferredFormat": "mp4",
        "preferredQuality": quality_str
    }

    endpoint = f"https://api.apify.com/v2/acts/streamers~youtube-video-downloader/run-sync-get-dataset-items?token={apify_token}&timeout=360"
    resp = requests.post(endpoint, json=payload, timeout=400)
    if resp.status_code not in (200, 201):
        raise Exception(f"Apify actor run failed (HTTP {resp.status_code}): {resp.text[:300]}")

    items = resp.json()
    if not items or not isinstance(items, list):
        raise Exception(f"Invalid dataset response from Apify: {resp.text[:300]}")

    file_url = items[0].get("downloadedFileUrl")
    if not file_url:
        raise Exception(f"No downloadedFileUrl returned by Apify: {items[0]}")

    video_id = items[0].get("id", "yt_video")
    dest_path = os.path.join(output_dir, f"{video_id}.mp4")
    logger.info(f"Streaming video from Apify Storage to: {dest_path}")

    with requests.get(file_url, stream=True, timeout=180) as r:
        r.raise_for_status()
        with open(dest_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)

    if not os.path.exists(dest_path) or os.path.getsize(dest_path) == 0:
        raise FileNotFoundError(f"Failed to save video from Apify to {dest_path}")

    logger.info(f"Successfully downloaded video via Apify: {dest_path} ({os.path.getsize(dest_path)} bytes)")
    return os.path.abspath(dest_path)


def download_youtube_video(
    url: str,
    output_dir: str,
    quality: str = "720p",
    start_time: str = None,
    end_time: str = None
) -> str:
    quality_str, height = normalize_quality(quality)
    is_trim = bool(start_time or end_time)

    apify_token = os.getenv("APIFY_TOKEN", "").strip()
    if apify_token:
        if is_trim:
            try:
                return download_via_apify_cutter(
                    url,
                    output_dir,
                    apify_token,
                    start_time=start_time or "00:00:00",
                    end_time=end_time,
                    quality=quality_str
                )
            except Exception as e:
                logger.warning(f"Apify cutter actor failed ({e}), falling back to full Apify downloader...")
                try:
                    return download_via_apify(url, output_dir, apify_token, quality=quality_str)
                except Exception as e2:
                    logger.warning(f"Full Apify downloader also failed: {e2}, falling back to local yt-dlp")
        else:
            try:
                return download_via_apify(url, output_dir, apify_token, quality=quality_str)
            except Exception as e:
                logger.warning(f"Apify download failed: {e}, falling back to local yt-dlp")

    output_template = os.path.join(output_dir, "%(id)s.%(ext)s")
    base_args = _get_ytdlp_base_args()
    if is_trim:
        start_hhmmss = format_time_hhmmss(start_time, default="00:00:00")
        end_hhmmss = format_time_hhmmss(end_time, default="") if end_time else ""
        section_str = f"*{start_hhmmss}-{end_hhmmss}"
        base_args.extend(["--download-sections", section_str])

    format_selector = (
        f"bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]/"
        f"bestvideo[height<={height}]+bestaudio/"
        f"best[height<={height}][ext=mp4]/"
        f"best[height<={height}]/"
        "best"
    )
    cmd = [
        "yt-dlp",
        *base_args,
        "-f", format_selector,
        "--merge-output-format", "mp4",
        "-o", output_template,
        url
    ]
    run_command(cmd, f"YouTube video download ({quality_str})")

    for fname in os.listdir(output_dir):
        if fname.endswith(".mp4"):
            return os.path.abspath(os.path.join(output_dir, fname))

    raise FileNotFoundError("Downloaded video not found in output directory")


def get_youtube_metadata(url: str, temp_dir: str = None) -> dict:
    """
    Extracts metadata using official YouTube oEmbed (fast, no bot blocks)
    and falls back to yt-dlp.
    """
    # 1. Try official oEmbed API first (fast and immune to bot blocks)
    try:
        oembed_url = f"https://www.youtube.com/oembed?url={url}&format=json"
        oembed_resp = requests.get(oembed_url, timeout=6)
        if oembed_resp.status_code == 200:
            data = oembed_resp.json()
            meta = {
                "title": data.get("title", "Video de YouTube"),
                "uploader": data.get("author_name", "YouTube"),
                "thumbnail_url": data.get("thumbnail_url", ""),
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
        logger.warning(f"oEmbed metadata failed, trying yt-dlp: {e}")

    # 2. Fallback to yt-dlp
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
