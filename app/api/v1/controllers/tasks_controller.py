from fastapi.responses import JSONResponse
from uuid import uuid4
from app.services.task_manager import task_manager, Task
import logging

logger = logging.getLogger(__name__)

async def init_task_handler():
    """Crea una nueva task genérica para cualquier operación"""
    logger.info("Creating new task")
    new_task = Task(id=str(uuid4()), porcentage=0, status="pending")
    task_manager.add_task(new_task)
    logger.info(f"Created new task: {new_task.id}")
    return JSONResponse(content={"task_id": new_task.id}, status_code=200)
