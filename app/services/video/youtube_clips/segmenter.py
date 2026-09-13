import os
import logging
import subprocess
from .helpers import run_command

logger = logging.getLogger(__name__)

DEFAULT_SEGMENT_DURATION = 3 * 60

def split_into_segments(
    input_file: str,
    output_dir: str,
    base_name: str,
    num_clips: int = None,
    clip_duration: int = None
) -> list[str]:
    probe_cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "csv=p=0",
        input_file
    ]
    probe = run_command(probe_cmd, "duration probe for segments")
    total_duration = float(probe.stdout.strip())

    if num_clips and clip_duration:
        num_segments = num_clips
        segment_dur = float(clip_duration)
    elif num_clips:
        num_segments = num_clips
        segment_dur = total_duration / num_clips
    elif clip_duration:
        segment_dur = float(clip_duration)
        num_segments = int(total_duration // segment_dur) + (1 if total_duration % segment_dur > 0 else 0)
    else:
        segment_dur = float(DEFAULT_SEGMENT_DURATION)
        num_segments = int(total_duration // segment_dur) + (1 if total_duration % segment_dur > 0 else 0)

    logger.info(
        f"Segmenting: total={total_duration:.1f}s | "
        f"segment_dur={segment_dur:.1f}s | "
        f"num_segments={num_segments}"
    )

    segments = []
    for i in range(num_segments):
        start = i * segment_dur
        if start >= total_duration:
            break
        output_path = os.path.join(output_dir, f"{base_name}_part{i + 1:02d}.mp4")
        logger.info(f"  Segment {i + 1}/{num_segments}: start={start:.1f}s, dur={segment_dur:.1f}s -> {os.path.basename(output_path)}")
        cmd = [
            "ffmpeg",
            "-ss", str(start),
            "-i", input_file,
            "-t", str(segment_dur),
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-c:a", "aac",
            "-avoid_negative_ts", "make_zero",
            "-y",
            output_path
        ]
        run_command(cmd, f"segment split {i + 1}")
        segments.append(output_path)

    return segments


def exclude_segments_logic(raw_file: str, exclude_segments: list, temp_dir: str, job_id: str) -> str:
    """
    Excludes specified time ranges (e.g. sponsorships, ads) from the video
    and concatenates the remaining parts.
    """
    logger.info(f"Excluding segments: {exclude_segments}")
    exclude_segments.sort(key=lambda x: x.get('start', 0) if isinstance(x, dict) else x.start)

    probe_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", raw_file]
    duration = float(subprocess.run(probe_cmd, capture_output=True, text=True).stdout.strip())

    keep_zones = []
    current_time = 0.0

    for seg in exclude_segments:
        s = float(seg.get('start', 0) if isinstance(seg, dict) else seg.start)
        e = float(seg.get('end', 0) if isinstance(seg, dict) else seg.end)
        if s > current_time:
            keep_zones.append((current_time, s))
        current_time = max(current_time, e)

    if current_time < duration:
        keep_zones.append((current_time, duration))

    total_kept = sum(e - s for s, e in keep_zones)
    logger.info(f"Keep zones: {[(f'{s:.1f}s', f'{e:.1f}s') for s, e in keep_zones]}")
    logger.info(f"Kept duration: {total_kept:.1f}s of {duration:.1f}s original")

    v_filters = []
    a_filters = []
    for i, (start, end) in enumerate(keep_zones):
        v_filters.append(f"[0:v]trim=start={start}:end={end},setpts=PTS-STARTPTS[v{i}]")
        a_filters.append(f"[0:a]atrim=start={start}:end={end},asetpts=PTS-STARTPTS[a{i}]")

    concat_inputs = "".join([f"[v{i}][a{i}]" for i in range(len(keep_zones))])
    filter_complex = f"{';'.join(v_filters)};{';'.join(a_filters)};{concat_inputs}concat=n={len(keep_zones)}:v=1:a=1[v][a]"

    trimmed_file = os.path.join(temp_dir, f"trimmed_{job_id}.mp4")
    cmd = [
        "ffmpeg", "-i", raw_file,
        "-filter_complex", filter_complex,
        "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-preset", "ultrafast",
        "-y", trimmed_file
    ]
    run_command(cmd, "trimming with segment exclusion")
    return trimmed_file
