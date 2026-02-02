# routes.py (principal)
from fastapi import APIRouter
from app.api.v1.audio import router as audio_router
from app.api.v1.video import router as video_router
from app.api.v1.tasks import router as tasks_router
from app.api.v1.controllers.status_controller import status_controller
from fastapi.responses import StreamingResponse
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/")
async def api_status():
    return {"message": "API is running"}

@router.get("/status/{task_id}")
async def task_status(task_id:str):
    return await status_controller(task_id)

router.include_router(tasks_router, prefix="/tasks", tags=["tasks"])
router.include_router(audio_router, prefix="/audio", tags=["audio"])
router.include_router(video_router, prefix="/video", tags=["video"])

