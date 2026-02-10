import ffmpeg
import os
import uuid
import logging
from dataclasses import replace
from pathlib import Path
from app.core.video_styles import TextStyle

logger = logging.getLogger(__name__)

ASSETS_DIR = Path(__file__).resolve().parent.parent.parent / "assets" / "tweet"
BACKGROUND_PATH = str(ASSETS_DIR / "background.png")
AVATAR_PATH = str(ASSETS_DIR / "avatar.png")
VERIFIED_PATH = str(ASSETS_DIR / "verified.png")

CANVAS_WIDTH = 1080
CANVAS_HEIGHT = 1080

AVATAR_SIZE = 160
AVATAR_X = 120
AVATAR_Y = 300

BADGE_SIZE = 42
BADGE_X = 540
BADGE_Y = 335

_USERNAME_STYLE = TextStyle(
    font_name="Arial",
    primary_color="&H00FFFFFF",
    bold=True,
    outline=0,
    alignment=7,
    margin_h=0,
    margin_v=0,
    font_size_ratio=0.052,
    pos_x_ratio=0.28,
    pos_y_ratio=0.305,
)

_HANDLE_STYLE = TextStyle(
    font_name="Arial",
    primary_color="&H00888888",
    bold=False,
    outline=0,
    alignment=7,
    margin_h=0,
    margin_v=0,
    font_size_ratio=0.038,
    pos_x_ratio=0.28,
    pos_y_ratio=0.36,
)

_MAIN_TEXT_STYLE = TextStyle(
    font_name="Arial",
    primary_color="&H00FFFFFF",
    bold=False,
    outline=0,
    alignment=7,
    margin_h=0,
    margin_v=0,
    font_size_ratio=0.060,
    pos_x_ratio=0.0,
    pos_y_ratio=0.0,
)

MAIN_TEXT_MARGIN_L = 120
MAIN_TEXT_MARGIN_R = 100
MAIN_TEXT_MARGIN_V = 500


def _generate_tweet_ass(output_path: str, text: str) -> str:
    sanitized = text.replace("\n", "\\N").replace("\r", "")

    username = replace(_USERNAME_STYLE)
    handle = replace(_HANDLE_STYLE)
    main_text = replace(_MAIN_TEXT_STYLE)

    username.prepare_for_video(CANVAS_WIDTH, CANVAS_HEIGHT)
    handle.prepare_for_video(CANVAS_WIDTH, CANVAS_HEIGHT)
    main_text.prepare_for_video(CANVAS_WIDTH, CANVAS_HEIGHT)

    username_line = username.to_ass_style_line(name="Username")
    handle_line = handle.to_ass_style_line(name="Handle")

    main_style = (
        f"Style: MainText,{main_text.font_name},{main_text.font_size},"
        f"{main_text.primary_color},&H000000FF,"
        f"{main_text.primary_color},&H00000000,"
        f"0,0,0,0,100,100,0,0,1,0,"
        f"{main_text.alignment},{MAIN_TEXT_MARGIN_L},{MAIN_TEXT_MARGIN_R},{MAIN_TEXT_MARGIN_V},1"
    )

    content = [
        "[Script Info]",
        "ScriptType: v4.00+",
        f"PlayResX: {CANVAS_WIDTH}",
        f"PlayResY: {CANVAS_HEIGHT}",
        "ScaledBorderAndShadow: yes",
        "WrapStyle: 0",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Alignment, MarginL, MarginR, MarginV, Encoding",
        username_line,
        handle_line,
        main_style,
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
        f"Dialogue: 0,0:00:00.00,0:00:01.00,Username,,0,0,0,,{{\\pos({username.pos_x},{username.pos_y})}}Adevsays",
        f"Dialogue: 0,0:00:00.00,0:00:01.00,Handle,,0,0,0,,{{\\pos({handle.pos_x},{handle.pos_y})}}@a_dev_says",
        f"Dialogue: 0,0:00:00.00,0:00:01.00,MainText,,0,0,0,,{sanitized}",
    ]

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(content))
    return output_path


def _build_avatar_stream():
    return (
        ffmpeg.input(AVATAR_PATH)
        .filter('format', 'rgba')
        .filter('crop', 'min(iw,ih)', 'min(iw,ih)')
        .filter('scale', AVATAR_SIZE, AVATAR_SIZE)
        .filter('geq',
                 r='r(X,Y)', g='g(X,Y)', b='b(X,Y)',
                 a='if(lte(pow(X-W/2,2)+pow(Y-H/2,2),pow(W/2,2)),alpha(X,Y),0)')
    )


def _build_badge_stream():
    return (
        ffmpeg.input(VERIFIED_PATH)
        .filter('format', 'rgba')
        .filter('scale', BADGE_SIZE, BADGE_SIZE)
    )


def generate_tweet_image(text: str) -> str:
    os.makedirs("temp", exist_ok=True)
    os.makedirs("resultado", exist_ok=True)

    unique_id = uuid.uuid4().hex[:8]
    ass_path = os.path.abspath(os.path.join("temp", f"tweet_{unique_id}.ass"))
    output_path = os.path.abspath(os.path.join("resultado", f"tweet_{unique_id}.png"))

    try:
        _generate_tweet_ass(ass_path, text)
        ass_rel_path = os.path.join("temp", f"tweet_{unique_id}.ass").replace("\\", "/")

        background = ffmpeg.input(BACKGROUND_PATH).filter('scale', CANVAS_WIDTH, CANVAS_HEIGHT)

        composed = background.overlay(_build_avatar_stream(), x=AVATAR_X, y=AVATAR_Y)
        composed = composed.overlay(_build_badge_stream(), x=BADGE_X, y=BADGE_Y)
        composed = composed.filter('ass', filename=ass_rel_path)

        (
            ffmpeg.output(composed, output_path, vframes=1)
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )

        return output_path

    except ffmpeg.Error as e:
        stderr = e.stderr.decode() if e.stderr else str(e)
        logger.error(f"FFmpeg error: {stderr}")
        raise Exception(f"FFmpeg failed: {stderr}")
    except Exception as e:
        logger.error(f"Error in generate_tweet_image: {e}")
        raise
    finally:
        if os.path.exists(ass_path):
            try:
                os.remove(ass_path)
            except OSError:
                pass
