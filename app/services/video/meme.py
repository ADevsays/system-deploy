import ffmpeg
import os
import uuid
import logging
from app.services.video.ass_service import AssService

logger = logging.getLogger(__name__)

def get_video_info(input_file: str) -> dict:
    try:
        probe = ffmpeg.probe(input_file)
        video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
        return {
            'duration': float(probe['format']['duration']),
            'width': int(video_stream['width']),
            'height': int(video_stream['height'])
        }
    except Exception as e:
        logger.error(f"Error obteniendo info del video: {e}")
        return {'duration': 10.0, 'width': 1080, 'height': 1920}

from app.core.video_styles import TextStyle, StyleRegistry

def create_meme(video_path: str, text: str, template: TextStyle) -> str:
    """
    Servicio que crea un meme. 
    Recibe la configuración de estilo ya resuelta.
    Mantiene calidad original, audio y elimina sombras.
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video no encontrado: {video_path}")

    os.makedirs("temp", exist_ok=True)
    os.makedirs("resultado", exist_ok=True)

    unique_id = uuid.uuid4().hex[:8]
    rel_ass_path = os.path.join("temp", f"meme_{unique_id}.ass")
    ass_path = os.path.abspath(rel_ass_path)
    output_filename = f"meme_{unique_id}.mp4"
    output_path = os.path.abspath(os.path.join("resultado", output_filename))

    try:
        info = get_video_info(video_path)
        
        # 1. Preparar el estilo para las dimensiones reales de este video
        # (Esto calcula automáticamente font_size, pos_x y pos_y basados en los ratios del template)
        template.prepare_for_video(info['width'], info['height'])

        # 2. Generar el archivo .ass con el servicio genérico
        AssService.generate_ass(
            output_path=ass_path,
            text=text,
            duration=info['duration'],
            width=info['width'],
            height=info['height'],
            template=template
        )

        # 3. Configurar FFmpeg para mantener audio y calidad
        ass_filter_path = rel_ass_path.replace("\\", "/")
        
        logger.info(f"Procesando meme de alta calidad: {output_filename}")

        input_video = ffmpeg.input(video_path)
        # Aplicamos el filtro de ASS solo al flujo de video
        video = input_video.video.filter("ass", filename=ass_filter_path)
        # Tomamos el audio original sin cambios
        audio = input_video.audio

        (
            ffmpeg
            .output(video, audio, output_path, 
                    vcodec='libx264', 
                    crf=18,             # Calidad alta (rango 18-23 es excelente)
                    preset='slow',      # Mejor compresión/calidad
                    acodec='copy')      # Copiar audio original sin pérdida
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )

        return output_path

    except ffmpeg.Error as e:
        stderr = e.stderr.decode() if e.stderr else str(e)
        logger.error(f"FFmpeg error: {stderr}")
        raise Exception(f"FFmpeg falló: {stderr}")
    except Exception as e:
        logger.error(f"Error en create_meme: {e}")
        raise e
    finally:
        # 3. Limpiar archivo temporal
        if os.path.exists(ass_path):
            try:
                os.remove(ass_path)
                logger.info(f"Temporal .ass eliminado: {ass_path}")
            except Exception as e:
                logger.warning(f"No se pudo eliminar el temporal: {e}")
