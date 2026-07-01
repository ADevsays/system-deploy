from fastapi import HTTPException, UploadFile, File, BackgroundTasks
from fastapi import status as http_status
from fastapi.responses import JSONResponse
import os
import shutil
import threading
import logging
from uuid import uuid4
from app.services.audio.cut import cut_audio
from app.services.task_manager import task_manager, Task
from app.utils.process_wrapper import ProcessWrapper

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".mpga", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".mp3"}


def generate_task_id():
    logger.info("Creating new task")
    new_task = Task(id=str(uuid4()), porcentage=0, status="pending")
    task_manager.add_task(new_task)
    logger.info(f"Created new task: {new_task.id}")
    return new_task.id


def _run_async_cut(task_id: str, temp_input: str, original_filename: str):
    temp_output = None
    try:
        from app.core.config import settings
        temp_output = ProcessWrapper.run(task_id, lambda: cut_audio(temp_input))
        task_manager.set_output_path(task_id, temp_output)
        logger.info(f"Async cut completed for task {task_id}: {temp_output}")
    except Exception as e:
        logger.error(f"Async cut failed for task {task_id}: {e}", exc_info=True)
    finally:
        if os.path.exists(temp_input):
            try:
                os.remove(temp_input)
            except OSError:
                pass


def cut_audio_handler(background_tasks: BackgroundTasks, file: UploadFile = File(...), google_token: str = None, return_file: bool = False):
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=f"Extensión de archivo no permitida. Tipos soportados: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    from app.core.config import settings
    os.makedirs(settings.TEMP_DIR, exist_ok=True)

    task_id = generate_task_id()

    if return_file:
        temp_input = os.path.join(settings.TEMP_DIR, f"input_{task_id}_{file.filename}")
        with open(temp_input, "wb") as b:
            shutil.copyfileobj(file.file, b)

        thread = threading.Thread(
            target=_run_async_cut,
            args=(task_id, temp_input, file.filename),
            daemon=True
        )
        thread.start()

        return JSONResponse({
            "task_id": task_id,
            "status": "processing",
            "message": "Procesamiento iniciado. Consulta /status/{task_id} para saber cuándo está listo y luego descarga desde /audio/download/{task_id}"
        })

    temp_file = None
    temp_output = None
    try:
        def execute_process():
            nonlocal temp_file
            temp_file = os.path.join(settings.TEMP_DIR, file.filename)
            logger.info(f"Guardando archivo temporal: {temp_file}")
            with open(temp_file, "wb") as b:
                shutil.copyfileobj(file.file, b)
            logger.info("Iniciando procesamiento de audio...")
            return cut_audio(temp_file)

        temp_output = ProcessWrapper.run(task_id, execute_process)
        logger.info(f"Audio procesado exitosamente: {temp_output}")

        from app.services.google_drive import drive_service

        if google_token:
            drive_data = drive_service.upload_file_with_user_token(
                file_path=temp_output,
                filename=file.filename,
                access_token=google_token,
                mime_type='audio/mpeg'
            )
        else:
            drive_data = drive_service.upload_file(
                file_path=temp_output,
                filename=file.filename,
                mime_type='audio/mpeg'
            )

        os.remove(temp_output)
        logger.info(f"Archivo subido a Google Drive: {drive_data['drive_url']}")

        return JSONResponse({
            "success": True,
            "task_id": task_id,
            "drive_link": drive_data["drive_url"],
            "file_id": drive_data["file_id"],
            "filename": file.filename,
            "message": "Archivo procesado y subido a Google Drive correctamente"
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en cut_audio_handler: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error durante el procesamiento: {str(e)}"
        )
    finally:
        if temp_file and os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except OSError:
                pass
