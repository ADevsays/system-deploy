from fastapi import APIRouter
from app.api.v1.controllers.tasks_controller import init_task_handler, clean_temp
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/init")
async def init_task_route():
    """Endpoint genérico para inicializar una nueva task"""
    return await init_task_handler()


@router.get("/clean")
async def clean_temp_tasks():
    return await clean_temp()