from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi import status as http_status
from fastapi.responses import StreamingResponse
import shutil
import os
import logging
import io
from typing import Optional
from app.api.v1.controllers.audio.cut_controller import cut_audio_handler

# Configurar logging
logger = logging.getLogger(__name__)

# Extensiones de archivo permitidas
ALLOWED_EXTENSIONS = {".mp3", ".wav", ".ogg", ".aac", ".flac", ".m4a"}

router = APIRouter()

@router.post("/cut")
def cut_audio_route(file: UploadFile = File(...), google_token: Optional[str] = Form(None), return_file: Optional[bool] = Form(False)):
    return cut_audio_handler(file, google_token, return_file)
