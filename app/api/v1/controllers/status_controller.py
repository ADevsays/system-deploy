from fastapi.responses import JSONResponse
from app.services.task_manager import task_manager
import logging

logger = logging.getLogger(__name__)
async def status_controller(task_id: str):  
    task = task_manager.get_task(str(task_id))
    if not task:
        return JSONResponse(content={"error": "No se encontro la tarea"}, status_code=404)
    
    payload = {
        "id": task.id,
        "status": task.status,
        "porcentage": task.porcentage,
    }

    return JSONResponse(content={"task": payload})