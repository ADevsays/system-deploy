from fastapi import APIRouter, UploadFile, File, BackgroundTasks
from fastapi import status as http_status
from fastapi.responses import FileResponse
import os
import logging
from typing import Optional
from app.api.v1.controllers.audio.cut_controller import cut_audio_handler
from app.services.task_manager import task_manager

logger = logging.getLogger(__name__)


router = APIRouter()

@router.post("/cut")
def cut_audio_route(background_tasks: BackgroundTasks, file: UploadFile = File(...), google_token: Optional[str] = File(None), return_file: Optional[bool] = File(False)):
    return cut_audio_handler(background_tasks, file, google_token, return_file)


@router.get("/download/{task_id}")
def download_audio(task_id: str, background_tasks: BackgroundTasks):
    task = task_manager.get_task(task_id)
    if not task:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    if task.status == "pending" or task.status == "processing":
        from fastapi import HTTPException
        raise HTTPException(status_code=202, detail=f"Procesamiento en curso: {task.porcentage}%")
    if task.status == "failed" or not task.output_path:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail="El procesamiento falló")
    if not os.path.exists(task.output_path):
        from fastapi import HTTPException
        raise HTTPException(status_code=410, detail="El archivo ya fue descargado o expiró")

    output_path = task.output_path
    filename = os.path.basename(output_path).replace("output_", "", 1)

    def cleanup():
        if os.path.exists(output_path):
            try:
                os.remove(output_path)
            except OSError:
                pass

    background_tasks.add_task(cleanup)

    return FileResponse(
        path=output_path,
        media_type="audio/mpeg",
        filename=filename,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
