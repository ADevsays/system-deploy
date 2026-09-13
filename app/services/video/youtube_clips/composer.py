import os
import subprocess
import logging
from pathlib import Path
from .helpers import run_command
from app.utils.subtitle_utils import generate_youtube_clip_ass
from app.core.config import settings

logger = logging.getLogger(__name__)

COMPOSITION_NORMAL = "normal"
COMPOSITION_FULLSCREEN = "fullscreen"

def _resolve_assets_dir() -> Path:
    candidates = [
        settings.BASE_DIR / "app" / "assets",
        settings.BASE_DIR / "assets"
    ]
    for c in candidates:
        if c.exists():
            return c
    return candidates[0]


def apply_3_4_composition(
    input_file: str,
    output_file: str,
    title: str,
    yellow_word: str,
    part: int,
    composition_mode: str = COMPOSITION_NORMAL,
    add_cta: bool = False,
    uploader: str = "",
    original_title: str = "",
    thumbnail_path: str = None
) -> str:
    input_file = os.path.abspath(input_file)
    output_file = os.path.abspath(output_file)
    if thumbnail_path:
        thumbnail_path = os.path.abspath(thumbnail_path)

    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file does not exist: {input_file}")

    probe_cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-of", "csv=p=0",
        input_file
    ]
    probe = subprocess.run(probe_cmd, capture_output=True, text=True)
    if probe.returncode != 0:
        raise Exception(f"ffprobe error: {probe.stderr}")

    probe_output = probe.stdout.strip()
    if not probe_output:
        raise Exception(f"ffprobe returned empty dimensions for {input_file}")

    try:
        orig_width, orig_height = map(int, probe_output.split(","))
    except ValueError as e:
        raise Exception(f"Error parsing dimensions from '{probe_output}': {str(e)}")

    canvas_h = orig_height if orig_height % 2 == 0 else orig_height + 1
    canvas_w = int(canvas_h * 3 / 4)
    canvas_w = canvas_w if canvas_w % 2 == 0 else canvas_w + 1

    assets_dir = _resolve_assets_dir()
    asset_path = str(assets_dir / "bounce-clip-base.mp4")
    has_asset = os.path.exists(asset_path)

    if not has_asset:
        logger.warning(
            f"Asset not found at {asset_path}. Video will render without bounce overlay."
        )

    duration_cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "csv=p=0",
        input_file
    ]
    duration_probe = run_command(duration_cmd, "duration probe")
    duration = float(duration_probe.stdout.strip())

    cta_start = duration - 3.0 if add_cta and duration > 3.0 else 0.0

    job_id = os.path.basename(output_file).split('_')[1] if '_' in os.path.basename(output_file) else "clip"
    ass_path = os.path.join(os.path.dirname(input_file), f"sub_{job_id}_{part}.ass")
    generate_youtube_clip_ass(
        ass_path, title, yellow_word, part, canvas_w, canvas_h, composition_mode,
        add_cta, cta_start, uploader, original_title
    )

    fonts_path = assets_dir / "fonts"
    fc_conf_path = str(fonts_path / "fonts.conf")
    _fonts_raw = str(fonts_path).replace("\\", "/")
    fonts_dir = "'" + _fonts_raw.replace(":", "\\:") + "'"
    fc_env = os.environ.copy()
    if os.path.exists(fc_conf_path):
        fc_env["FONTCONFIG_FILE"] = fc_conf_path

    ass_dir = os.path.dirname(ass_path)
    ass_basename = os.path.basename(ass_path)

    yt_logo_path = str(assets_dir / "Youtube_logo.png")
    has_logo = os.path.exists(yt_logo_path)

    if add_cta:
        font_size = int(canvas_w * 0.045)
        logo_w = int(font_size * 1.5)
        thumb_h = int((canvas_w * 0.8) * 9 / 16)
        thumb_top_y = (canvas_h - thumb_h) // 2
        inline_y = thumb_top_y - font_size - 20
        
        char_w = int(font_size * 0.55)
        clean_uploader = uploader.upper().strip().replace("{", "").replace("}", "")
        text_w = len(clean_uploader) * char_w
        gap = int(font_size * 0.4)
        total_inline_w = logo_w + gap + text_w
        logo_x = (canvas_w - total_inline_w) // 2
        logo_y = inline_y
    else:
        logo_w, logo_x, logo_y = 0, 0, 0

    if composition_mode == COMPOSITION_FULLSCREEN:
        cmd, filter_complex = _build_fullscreen_cmd(
            input_file, output_file, str(duration),
            canvas_w, canvas_h,
            asset_path, has_asset,
            ass_basename, fonts_dir,
            add_cta, cta_start, thumbnail_path, has_logo, yt_logo_path, logo_w, logo_x, logo_y
        )
    else:
        cmd, filter_complex = _build_normal_cmd(
            input_file, output_file, str(duration),
            canvas_w, canvas_h,
            asset_path, has_asset,
            ass_basename, fonts_dir,
            add_cta, cta_start, thumbnail_path, has_logo, yt_logo_path, logo_w, logo_x, logo_y
        )

    logger.debug(f"filter_complex [{composition_mode}]: {filter_complex}")
    run_command(cmd, f"composition 3:4 mode={composition_mode} (Part {part})", env=fc_env, cwd=ass_dir)
    return output_file


def _apply_cta_filters(cmd, fc, last_out, canvas_w, canvas_h, add_cta, cta_start, thumbnail_path, has_logo, yt_logo_path, logo_w, logo_x, logo_y):
    if not add_cta:
        return cmd, fc, last_out

    thumb_idx = len([x for x in cmd if x == '-i'])
    cmd.extend(["-i", thumbnail_path])
    
    if has_logo:
        logo_idx = thumb_idx + 1
        cmd.extend(["-i", yt_logo_path])
        
    thumb_w = int(canvas_w * 0.8)
    
    fc = fc.rstrip("; ") + f"; [{last_out}]boxblur=30:5:enable='gte(t,{cta_start})'[bg_blur]; "
    fc += f"[{thumb_idx}:v]scale={thumb_w}:-1,setsar=1[thumb]; "
    fc += f"[bg_blur][thumb]overlay=x=(W-w)/2:y=(H-h)/2+10*sin(t*15):enable='gte(t,{cta_start})'[bg_thumb]; "
    
    if has_logo:
        fc += f"[{logo_idx}:v]scale={logo_w}:-1[logo]; "
        fc += f"[bg_thumb][logo]overlay=x={logo_x}:y={logo_y}:enable='gte(t,{cta_start})'[bg_logo]"
        return cmd, fc, "bg_logo"
    
    return cmd, fc, "bg_thumb"


def _build_normal_cmd(
    input_file, output_file, duration,
    canvas_w, canvas_h,
    asset_path, has_asset,
    ass_basename, fonts_dir,
    add_cta, cta_start, thumbnail_path, has_logo, yt_logo_path, logo_w, logo_x, logo_y
):
    video_h = int(canvas_h * 0.6)
    video_h = video_h if video_h % 2 == 0 else video_h + 1
    offset_y = int(canvas_h * 0.2)
    
    cmd = ["ffmpeg", "-i", input_file]
    if has_asset:
        cmd.extend(["-stream_loop", "-1", "-i", asset_path])
        asset_scale_w = int(canvas_w * 0.75)
        asset_scale_h = int(asset_scale_w * (1920 / 1440))
        asset_x = (canvas_w - asset_scale_w) // 2
        asset_y = canvas_h - asset_scale_h

        fc = (
            f"[0:v]scale=-1:{video_h},crop={canvas_w}:{video_h},pad={canvas_w}:{canvas_h}:0:{offset_y}:black[main]; "
            f"[1:v]scale={asset_scale_w}:-1,colorkey=black:0.1:0.1[asset]; "
            f"[main][asset]overlay={asset_x}:{asset_y}[tempmovie]"
        )
        last_out = "tempmovie"
    else:
        fc = f"[0:v]scale=-1:{video_h},crop={canvas_w}:{video_h},pad={canvas_w}:{canvas_h}:0:{offset_y}:black[main]"
        last_out = "main"

    cmd, fc, last_out = _apply_cta_filters(cmd, fc, last_out, canvas_w, canvas_h, add_cta, cta_start, thumbnail_path, has_logo, yt_logo_path, logo_w, logo_x, logo_y)

    fc += f"; [{last_out}]subtitles={ass_basename}:fontsdir={fonts_dir}:charenc=UTF-8"
    
    cmd.extend([
        "-t", duration,
        "-filter_complex", fc,
        "-map", "0:a?",
        "-c:v", "libx264", "-preset", "ultrafast",
        "-c:a", "aac", "-y", output_file
    ])

    return cmd, fc


def _build_fullscreen_cmd(
    input_file, output_file, duration,
    canvas_w, canvas_h,
    asset_path, has_asset,
    ass_basename, fonts_dir,
    add_cta, cta_start, thumbnail_path, has_logo, yt_logo_path, logo_w, logo_x, logo_y
):
    blur = "boxblur=luma_radius=30:luma_power=3:chroma_radius=30:chroma_power=3"
    
    cmd = ["ffmpeg", "-i", input_file]
    if has_asset:
        cmd.extend(["-stream_loop", "-1", "-i", asset_path])
        asset_scale_w = int(canvas_w * 0.75)
        asset_scale_h = int(asset_scale_w * (1920 / 1440))
        asset_x = (canvas_w - asset_scale_w) // 2
        asset_y = canvas_h - asset_scale_h

        fc = (
            f"[0:v]scale={canvas_w}:{canvas_h}:force_original_aspect_ratio=increase,"
            f"crop={canvas_w}:{canvas_h},{blur}[bg];"
            f"[0:v]scale={canvas_w}:-2[fg];"
            f"[bg][fg]overlay=(W-w)/2:(H-h)/2[main];"
            f"[1:v]scale={asset_scale_w}:-1,colorkey=black:0.1:0.1[asset];"
            f"[main][asset]overlay={asset_x}:{asset_y}[tempmovie]"
        )
        last_out = "tempmovie"
    else:
        fc = (
            f"[0:v]scale={canvas_w}:{canvas_h}:force_original_aspect_ratio=increase,"
            f"crop={canvas_w}:{canvas_h},{blur}[bg];"
            f"[0:v]scale={canvas_w}:-2[fg];"
            f"[bg][fg]overlay=(W-w)/2:(H-h)/2[main]"
        )
        last_out = "main"

    cmd, fc, last_out = _apply_cta_filters(cmd, fc, last_out, canvas_w, canvas_h, add_cta, cta_start, thumbnail_path, has_logo, yt_logo_path, logo_w, logo_x, logo_y)

    fc += f"; [{last_out}]subtitles={ass_basename}:fontsdir={fonts_dir}:charenc=UTF-8"

    cmd.extend([
        "-t", duration,
        "-filter_complex", fc,
        "-map", "0:a?",
        "-c:v", "libx264", "-preset", "ultrafast",
        "-c:a", "aac", "-y", output_file
    ])

    return cmd, fc
