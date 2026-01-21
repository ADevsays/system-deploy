from fastapi import UploadFile, File, HTTPException
from fastapi import status as http_status
from fastapi.responses import StreamingResponse
from app.services.video.cut import cut_video_remove_silence
import shutil
import os
import logging
import io
from uuid import uuid4
from app.services.task_manager import task_manager
from app.services.task_manager import Task
from app.utils.process_wrapper import ProcessWrapper
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)
ALLOWED_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".flv", ".wmv", ".webm"}

def cut_video_handler(file: UploadFile = File(...), task_id: str = None):
    logger.info("Iniciando proceso de corte de video")

    if not task_id:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="task_id es requerido"
        )
    
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} no encontrada"
        )

    temp_file = None
    temp_output = None

    try:
        def execute_process():
            nonlocal temp_file, temp_output
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

            return cut_video_remove_silence(temp_file)

        temp_output = ProcessWrapper.run(task_id, execute_process)
        logger.info(f"Video procesado: {temp_output}")

        # Guardar en carpeta results en lugar de descargar
        results_folder = "results"
        os.makedirs(results_folder, exist_ok=True)
        
        output_filename = f"cut_{file.filename}"
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
        logger.error(f"Error en cut: {str(e)}", exc_info=True)
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
