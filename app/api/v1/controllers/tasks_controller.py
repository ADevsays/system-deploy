from fastapi.responses import JSONResponse
from uuid import uuid4
from app.services.task_manager import task_manager, Task
import logging
from pathlib import Path
import os

logger = logging.getLogger(__name__)

async def init_task_handler():
    """Crea una nueva task genérica para cualquier operación"""
    logger.info("Creating new task")
    new_task = Task(id=str(uuid4()), porcentage=0, status="pending")
    task_manager.add_task(new_task)
    logger.info(f"Created new task: {new_task.id}")
    return JSONResponse(content={"task_id": new_task.id}, status_code=200)

def clean_temp():
    from app.core.config import settings
    folder = settings.TEMP_DIR

    if not os.path.exists(folder):
        return JSONResponse(content={"message": "Temp folder does not exist"}, status_code=404)

    for file_name in os.listdir(folder):
        temp_file = os.path.join(folder, file_name)
        
        try:
            # Verificamos si es archivo o carpeta para borrar correctamente
            if os.path.isfile(temp_file) or os.path.islink(temp_file):
                os.remove(temp_file)
            elif os.path.isdir(temp_file):
                shutil.rmtree(temp_file)
        except Exception as e:
            # Es mejor loguear el error que solo poner 'pass' 
            # para saber si algo se quedó bloqueado
            print(f"No se pudo borrar {temp_file}: {e}")
            continue

    return JSONResponse(content={"message": "Temp folder cleaned"}, status_code=200)