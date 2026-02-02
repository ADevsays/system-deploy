from fastapi import HTTPException, UploadFile, File, Form
from fastapi import status as http_status
from fastapi.responses import JSONResponse
import os
import shutil
import logging
from uuid import uuid4
from app.services.video.meme import create_meme
from app.core.video_styles import VideoTemplate, StyleRegistry
from app.services.task_manager import task_manager, Task
from app.utils.process_wrapper import ProcessWrapper
from app.core.config import settings

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv"}

def generate_task_id():
    logger.info("Creating new task for meme generation")
    new_task = Task(id=str(uuid4()), porcentage=0, status="pending")
    task_manager.add_task(new_task)
    logger.info(f"Created new task: {new_task.id}")
    return new_task.id

async def meme_video_handler(
    file: UploadFile = File(...), 
    text: str = Form(...), 
    template: str = Form("meme_modern_thin")
):
    temp_file = None
    temp_output = None
    
    task_id = generate_task_id()
    
    try:
        def execute_process():
            # 1. Validar extensión
            file_extension = os.path.splitext(file.filename)[1].lower()
            if file_extension not in ALLOWED_EXTENSIONS:
                logger.warning(f"Extensión de archivo no permitida: {file_extension}")
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail=f"Extensión de archivo no permitida. Tipos soportados: {', '.join(ALLOWED_EXTENSIONS)}"
                )

            # 2. Asegurar directorio temporal
            os.makedirs(settings.TEMP_DIR, exist_ok=True)
            nonlocal temp_file
            temp_file = os.path.join(settings.TEMP_DIR, f"{uuid4().hex}_{file.filename}")

            # 3. Guardar archivo
            logger.info(f"Guardando archivo temporal: {temp_file}")
            with open(temp_file, "wb") as b:
                shutil.copyfileobj(file.file, b)

            # 4. Resolver template
            try:
                video_template = VideoTemplate(template)
            except ValueError:
                video_template = VideoTemplate.MEME_THIN
            
            style_template = StyleRegistry.resolve(video_template)

            # 5. Generar Meme
            logger.info(f"Iniciando generación de meme con texto: {text}")
            return create_meme(temp_file, text, style_template)

        # Ejecutamos el proceso con seguimiento de progreso
        temp_output = ProcessWrapper.run(task_id, execute_process)
        
        logger.info(f"Meme generado exitosamente: {temp_output}")

        # 6. Subir a Google Drive
        from app.services.google_drive import drive_service
        try:
            drive_data = drive_service.upload_file(
                file_path=temp_output,
                filename=f"meme_{file.filename}",
                mime_type='video/mp4'
            )
            
            # Limpiar el archivo de salida
            if os.path.exists(temp_output):
                os.remove(temp_output)
            
            return JSONResponse({
                "success": True,
                "task_id": task_id,
                "drive_link": drive_data["drive_url"],
                "file_id": drive_data["file_id"],
                "filename": file.filename,
                "message": "Meme generado y subido a Google Drive correctamente"
            })
            
        except Exception as e:
            logger.error(f"Error subiendo a Google Drive: {str(e)}")
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error subiendo meme a Google Drive: {str(e)}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en meme_video_handler: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error durante la generación del meme: {str(e)}"
        )
    finally:
        # Limpieza del archivo original subido
        if temp_file and os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except OSError:
                pass
