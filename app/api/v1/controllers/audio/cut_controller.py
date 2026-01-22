from fastapi import HTTPException
from fastapi import UploadFile
from fastapi import File
from fastapi.responses import StreamingResponse
from fastapi import status as http_status
import os
import shutil
import io
import logging
from uuid import uuid4
from app.services.audio.cut import cut_audio
from app.services.task_manager import task_manager
from app.services.task_manager import Task
from app.utils.process_wrapper import ProcessWrapper
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".mpga", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".mp3"}

def generate_task_id():
    logger.info("Creating new task")
    new_task = Task(id=str(uuid4()), porcentage=0, status="pending")
    task_manager.add_task(new_task)
    logger.info(f"Created new task: {new_task.id}")
    return new_task.id

def cut_audio_handler(file: UploadFile = File(...)):
    temp_file = None
    temp_output = None
    
    task_id = generate_task_id()
    try:
        # Definimos la lógica completa que queremos ejecutar bajo monitoreo de progreso
        def execute_process():
            # 1. Validar extensión
            file_extension = os.path.splitext(file.filename)[1].lower()
            if file_extension not in ALLOWED_EXTENSIONS:
                logger.warning(f"Extensión de archivo no permitida: {file_extension}")
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail=f"Extensión de archivo no permitida. Tipos soportados: {', '.join(ALLOWED_EXTENSIONS)}"
                )

            from app.core.config import settings
            os.makedirs(settings.TEMP_DIR, exist_ok=True)
            nonlocal temp_file
            temp_file = os.path.join(settings.TEMP_DIR, file.filename)

            # 3. Guardar archivo (Operación I/O que toma tiempo)
            logger.info(f"Guardando archivo temporal: {temp_file}")
            with open(temp_file, "wb") as b:
                shutil.copyfileobj(file.file, b)

            # 4. Procesar audio (Operación CPU que toma tiempo)
            logger.info("Iniciando procesamiento de audio...")
            return cut_audio(temp_file)

        # Ejecutamos todo el bloque con el wrapper
        # El simulador de progreso correrá mientras se guarda el archivo Y mientras se procesa
        temp_output = ProcessWrapper.run(task_id, execute_process)
        
        logger.info(f"Audio procesado exitosamente: {temp_output}")

        from app.services.google_drive import drive_service
        
        output_filename = f"edit_{file.filename}"
        
        try:
            drive_link = drive_service.upload_file(
                file_path=temp_output,
                filename=output_filename,
                mime_type='audio/mpeg'
            )
            
            os.remove(temp_output)
            
            logger.info(f"Archivo subido a Google Drive: {drive_link}")
            
            return JSONResponse({
                "success": True,
                "task_id": task_id,
                "drive_link": drive_link,
                "filename": output_filename,
                "message": "Archivo procesado y subido a Google Drive correctamente"
            })
        
        except Exception as e:
            logger.error(f"Error subiendo a Google Drive: {str(e)}")
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error subiendo archivo a Google Drive: {str(e)}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en cut_audio_handler: {str(e)}", exc_info=True)
        # El wrapper ya se encargó de actualizar el status a Failed
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error durante el procesamiento: {str(e)}"
        )
    finally:
        # Limpieza
        if temp_file and os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except OSError:
                pass

    
    
