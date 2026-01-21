import ffmpeg
import os
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

CONFIG_FILTER = {
    "start_periods": 1,
    "start_duration": 0,
    "start_threshold": "-30dB",
    "stop_periods": -1,
    "stop_duration": 0.1,
    "stop_threshold": "-40dB"
}

def cut_audio(input_file: str):
    """
    Función pura para cortar silencios de un audio usando FFmpeg.
    No maneja tareas ni estados, solo procesa el archivo.
    """
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"El archivo de entrada no existe: {input_file}")

    config_cut = (
        f"silenceremove="
        f"start_periods={CONFIG_FILTER['start_periods']}:"
        f"start_duration={CONFIG_FILTER['start_duration']}:"
        f"start_threshold={CONFIG_FILTER['start_threshold']}:"
        f"stop_periods={CONFIG_FILTER['stop_periods']}:"
        f"stop_duration={CONFIG_FILTER['stop_duration']}:"
        f"stop_threshold={CONFIG_FILTER['stop_threshold']}"
    )

    input_basename = os.path.basename(input_file)
    output_path = os.path.join(settings.TEMP_DIR, f"output_{input_basename}")
    
    os.makedirs(settings.TEMP_DIR, exist_ok=True)

    try:
        (
            ffmpeg.input(input_file)
            .output(
                output_path,
                af=config_cut,
                acodec="libmp3lame",  # Codec MP3
                ar="44100",  # Sample rate
            )
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True, quiet=False)
        )

        return output_path

    except ffmpeg.Error as e:
        error_msg = e.stderr.decode() if e.stderr else str(e)
        raise Exception(f"Error procesando audio con FFmpeg: {error_msg}") from e