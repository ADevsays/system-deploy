import ffmpeg
import os
import re
import subprocess
import uuid

CONFIG_FILTER = {
    "start_periods": 1,
    "start_duration": 0,
    "start_threshold": "-30dB",
    "stop_periods": -1,
    "stop_duration": 0.5,
    "stop_threshold": "-35dB"
}


def get_duration(input_file: str) -> float:
    try:
        probe = ffmpeg.probe(input_file)
        return float(probe['format']['duration'])
    except:
        return 0


def detect_silence(input_file: str) -> list:
    silence_filter = (
        f"silencedetect="
        f"n={CONFIG_FILTER['start_threshold']}:"
        f"d={CONFIG_FILTER['stop_duration']}"
    )

    cmd = [
        "ffmpeg",
        "-i", input_file,
        "-af", silence_filter,
        "-f", "null",
        "-"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    output = result.stderr

    silence_periods = []
    pattern = r'silence_start: ([\d.]+).*?silence_end: ([\d.]+)'

    for match in re.finditer(pattern, output, re.DOTALL):
        start = float(match.group(1))
        end = float(match.group(2))
        silence_periods.append((start, end))

    return silence_periods


def build_segments(silence_periods: list, duration: float) -> list:
    if not silence_periods:
        return [(0, duration)]

    segments = []

    if silence_periods[0][0] > 0:
        segments.append((0, silence_periods[0][0]))

    for i in range(len(silence_periods) - 1):
        start = silence_periods[i][1]
        end = silence_periods[i + 1][0]
        if start < end:
            segments.append((start, end))

    if silence_periods[-1][1] < duration:
        segments.append((silence_periods[-1][1], duration))

    return segments


def process_segment(input_file: str, segment_num: int, temp_dir: str, output_filename: str = None) -> str:
    if output_filename is None:
        output_filename = f"processed_segment_{segment_num}.mp4"
    output_path = os.path.join(temp_dir, output_filename)

    duration = get_duration(input_file)
    silence_periods = detect_silence(input_file)
    segments = build_segments(silence_periods, duration)

    if not segments:
        raise Exception("No segments found")

    input_stream = ffmpeg.input(input_file)
    video = input_stream.video
    audio = input_stream.audio

    trimmed_videos = []
    trimmed_audios = []

    for start, end in segments:
        v = video.filter('trim', start=start, end=end).filter('setpts', 'PTS-STARTPTS')
        a = audio.filter('atrim', start=start, end=end).filter('asetpts', 'PTS-STARTPTS')
        trimmed_videos.append(v)
        trimmed_audios.append(a)

    if len(trimmed_videos) == 1:
        final_video = trimmed_videos[0]
        final_audio = trimmed_audios[0]
    else:
        final_video = ffmpeg.concat(*trimmed_videos, v=1, a=0)
        final_audio = ffmpeg.concat(*trimmed_audios, v=0, a=1)

    (
        ffmpeg
        .output(final_video, final_audio, output_path, vcodec='libx264', preset='ultrafast', acodec='aac')
        .overwrite_output()
        .run(capture_stdout=True, capture_stderr=True, quiet=False)
    )
    return output_path


def cut_video_remove_silence(input_file: str) -> str:

    if not os.path.exists(input_file):
        raise FileNotFoundError(f"El archivo de entrada no existe: {input_file}")

    input_basename = os.path.basename(input_file)
    input_name, input_ext = os.path.splitext(input_basename)

    if len(input_name) > 15:
        input_name = input_name[:15]

    output_path = os.path.join("temp", f"cut_{input_name}{input_ext}")

    try:
        duration = get_duration(input_file)
        max_segment_duration = 8 * 60

        if duration <= max_segment_duration:
            output_filename = f"cut_{input_name}{input_ext}"
            return process_segment(input_file, 0, "temp", output_filename)

        temp_dir = os.path.join("temp", f"temp_{uuid.uuid4().hex[:8]}")
        os.makedirs(temp_dir, exist_ok=True)

        chunk_files = []
        num_chunks = int(duration // max_segment_duration) + (1 if duration % max_segment_duration > 0 else 0)

        for i in range(num_chunks):
            chunk_start = i * max_segment_duration
            chunk_duration = min(max_segment_duration, duration - chunk_start)
            chunk_file = os.path.join(temp_dir, f"chunk_{i}{input_ext}")

            # Usar -ss ANTES de -i para seeking preciso
            # Re-encodear en lugar de copy para evitar problemas de keyframes
            cmd = [
                "ffmpeg",
                "-ss", str(chunk_start),  # ← ANTES de -i para seeking rápido
                "-i", input_file,
                "-t", str(chunk_duration),  # ← Usar -t (duración) en lugar de -to
                "-c:v", "libx264",
                "-preset", "ultrafast",
                "-c:a", "aac",
                "-avoid_negative_ts", "make_zero",  # ← Normalizar timestamps
                "-y",
                chunk_file
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            chunk_files.append(chunk_file)

        processed_chunks = []
        for i, chunk_file in enumerate(chunk_files):
            processed = process_segment(chunk_file, i, temp_dir)
            processed_chunks.append(processed)

        concat_file = os.path.join(temp_dir, "concat.txt")
        with open(concat_file, 'w') as f:
            for chunk in processed_chunks:
                f.write(f"file '{os.path.abspath(chunk)}'\n")

        cmd = [
            "ffmpeg",
            "-f", "concat",
            "-safe", "0",
            "-i", concat_file,
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-c:a", "aac",
            "-af", "aresample=async=1",  # Forzar sincronización de audio
            "-y",
            output_path
        ]
        subprocess.run(cmd, check=True, capture_output=True)

        for chunk in chunk_files + processed_chunks:
            if os.path.exists(chunk):
                os.remove(chunk)
        os.remove(concat_file)
        os.rmdir(temp_dir)

        return output_path

    except ffmpeg.Error as e:
        raise Exception(f"Error procesando video con FFmpeg: {e.stderr.decode() if e.stderr else str(e)}") from e
    except subprocess.CalledProcessError as e:
        raise Exception(f"Error ejecutando ffmpeg: {e}") from e
    except Exception as e:
        raise Exception(f"Error en cut_video_remove_silence: {str(e)}") from e
