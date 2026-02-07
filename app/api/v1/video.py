from fastapi import APIRouter, UploadFile, File, Form
from app.api.v1.controllers.video import cut_video_handler, zoom_video_handler
from app.api.v1.controllers.video.meme_controller import meme_video_handler
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

@router.post("/meme")
async def meme_video_route(
    file: UploadFile = File(...), 
    text: str = Form(...), 
    template: str = Form("meme_modern_thin"),
    return_file: bool = Form(False)
):
    return await meme_video_handler(file, text, template, return_file)
