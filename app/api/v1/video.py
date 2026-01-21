from fastapi import APIRouter, UploadFile, File, Query
from app.api.v1.controllers.video import cut_video_handler, zoom_video_handler
from typing import Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/cut")
def cut_video_route(file: UploadFile = File(...), task_id: str = None):
    return cut_video_handler(file, task_id)

@router.post("/zoom")
def zoom_video_route(file: UploadFile = File(...), task_id: str = None):
    return zoom_video_handler(file, task_id)
