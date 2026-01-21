import os
import ffmpeg
import logging
from typing import Optional, List, Tuple, Dict
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ZoomConfig:
    num_zooms: int = 7
    zoom_duration: float = 4.0
    target_zoom: float = 1.25
    smooth_return: bool = False


def get_video_info(input_file: str) -> dict:
    try:
        probe = ffmpeg.probe(input_file)
        video_stream = next((s for s in probe['streams'] if s['codec_type'] == 'video'), None)
        if not video_stream:
            raise Exception("No video stream found")

        return {
            "duration": float(probe['format']['duration']),
            "width": int(video_stream['width']),
            "height": int(video_stream['height']),
            "fps": eval(video_stream.get('r_frame_rate', '30/1'))
        }
    except Exception as e:
        raise Exception(f"Error probing video: {str(e)}") from e


def calculate_zoom_frames(duration: float, config: ZoomConfig) -> List[Tuple[float, float]]:
    frames = []
    if duration <= 0: return []
    
    section_length = duration / (config.num_zooms + 1)
    
    for i in range(1, config.num_zooms + 1):
        center_time = i * section_length
        start = max(0, center_time - (config.zoom_duration / 2))
        end = min(duration, center_time + (config.zoom_duration / 2))
        frames.append((start, end))
        
    return frames


def build_zoom_expressions(frames: List[Tuple[float, float]], target_zoom: float, smooth_return: bool = True) -> Tuple[str, str, str]:
    zoom_expr = "1"
    x_expr = "iw/2-(iw/zoom/2)"
    y_expr = "ih/2-(ih/zoom/2)"
    
    for start, end in frames:
        dur = end - start
        if dur <= 0: continue
        
        start_s = f"{start:.3f}"
        end_s = f"{end:.3f}"
        
        # If smooth_return is True, use PI (full sine wave 0->1->0)
        # If smooth_return is False, use PI/2 (half sine wave 0->1), then hard cut
        pi_mult = "3.14159265" if smooth_return else "(3.14159265/2)"
        
        anim_factor = f"sin((time-{start_s})/{dur}*{pi_mult})"
        current_zoom_val = f"(1+({target_zoom}-1)*{anim_factor})"
        
        cond = f"between(time,{start_s},{end_s})"
        
        zoom_expr = f"if({cond},{current_zoom_val},{zoom_expr})"
        
        target_x = "iw-(iw/zoom)"
        target_y = "ih-(ih/zoom)"
        
        x_expr = f"if({cond},{target_x},{x_expr})"
        y_expr = f"if({cond},{target_y},{y_expr})"
        
    return zoom_expr, x_expr, y_expr


def zoom_pan(input_file: str, output_file: Optional[str] = None, config: Optional[ZoomConfig] = None) -> str:
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file not found: {input_file}")

    if config is None:
        config = ZoomConfig()

    if output_file is None:
        base, ext = os.path.splitext(input_file)
        if len(base) > 50: base = base[:50]
        output_file = os.path.join("temp", f"{os.path.basename(base)}_smartzoom{ext}")

    os.makedirs(os.path.dirname(output_file) or "temp", exist_ok=True)

    try:
        video_info = get_video_info(input_file)
        width = video_info['width']
        height = video_info['height']
        duration = video_info['duration']
        
        fps_val = video_info['fps']
        fps = float(fps_val) if isinstance(fps_val, (int, float)) else 30.0
        
        zoom_frames = calculate_zoom_frames(duration, config)
        
        logger.info(f"Config: {config}")
        logger.info(f"Zoom Frames: {zoom_frames}")
        
        z_expr, x_expr, y_expr = build_zoom_expressions(zoom_frames, config.target_zoom, config.smooth_return)
        
        logger.info(f"Zoom Expr: {z_expr}")
        
        in_stream = ffmpeg.input(input_file)
        
        video = in_stream.video.filter(
            'zoompan',
            z=z_expr,
            x=x_expr,
            y=y_expr,
            d=1,
            s=f'{width}x{height}',
            fps=fps
        )
        
        audio = in_stream.audio
        
        out = ffmpeg.output(
            video, 
            audio, 
            output_file, 
            vcodec='libx264', 
            crf=18, 
            preset='slow', 
            acodec='copy'
        )
        
        out.run(overwrite_output=True, capture_stdout=True, capture_stderr=True)
        
        return output_file
        
    except ffmpeg.Error as e:
        error_log = e.stderr.decode() if e.stderr else str(e)
        logger.error(f"FFmpeg error: {error_log}")
        raise Exception(f"FFmpeg error: {error_log[-500:]}") from e
