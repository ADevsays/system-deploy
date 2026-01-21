from fastapi import UploadFile, File, HTTPException
from fastapi import status as http_status
from fastapi.responses import StreamingResponse
from app.services.video.zoom_pan import zoom_pan
import shutil
import os
import logging
import io

logger = logging.getLogger(__name__)
ALLOWED_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".flv", ".wmv", ".webm"}


def zoom_video_handler(file: UploadFile = File(...), task_id: str = None):
    logger.info("Iniciando proceso de zoom de video")

    temp_file = None
    temp_output = None

    try:
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension not in ALLOWED_EXTENSIONS:
            logger.warning(f"Extensión no permitida: {file_extension}")
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=f"Extensión no permitida. Soportados: {', '.join(ALLOWED_EXTENSIONS)}"
            )

        os.makedirs("temp", exist_ok=True)
        temp_file = os.path.join("temp", file.filename)

        with open(temp_file, "wb") as b:
            shutil.copyfileobj(file.file, b)

        logger.info(f"Archivo temporal: {temp_file}")

        temp_output = zoom_pan(temp_file)
        logger.info(f"Video procesado: {temp_output}")

        # Guardar en carpeta results en lugar de descargar
        results_folder = "results"
        os.makedirs(results_folder, exist_ok=True)
        
        output_filename = f"zoom_{file.filename}"
        output_path = os.path.join(results_folder, output_filename)
        
        # Mover archivo procesado a results
        shutil.move(temp_output, output_path)
        logger.info(f"Archivo guardado en: {output_path}")

        # Devolver información del archivo guardado
        return JSONResponse({
            "success": True,
            "file_path": os.path.abspath(output_path),
            "filename": output_filename,
            "message": "Archivo procesado y guardado correctamente"
        })

    except HTTPException:
        raise
    except FileNotFoundError as e:
        logger.error(f"Archivo no encontrado: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Archivo temporal no encontrado"
        )
    except Exception as e:
        logger.error(f"Error en zoom: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error procesando video: {str(e)}"
        )
    finally:
        if temp_file and os.path.exists(temp_file):
            try:
                os.remove(temp_file)
                logger.info(f"Archivo temporal eliminado: {temp_file}")
            except OSError as e:
                logger.warning(f"Error eliminando {temp_file}: {e}")
        
        if temp_output and os.path.exists(temp_output):
            try:
                os.remove(temp_output)
                logger.info(f"Archivo de salida eliminado: {temp_output}")
            except OSError as e:
                logger.warning(f"Error eliminando {temp_output}: {e}")
