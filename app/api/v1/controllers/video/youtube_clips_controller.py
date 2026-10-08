import os
import logging
from fastapi import HTTPException
from fastapi import status as http_status
from fastapi.responses import JSONResponse
from app.services.task_manager import task_manager
from app.utils.process_wrapper import ProcessWrapper
from app.services.video.youtube_clips import process_youtube_url
from app.core.config import settings

logger = logging.getLogger(__name__)

RESULTS_DIR = str(settings.BASE_DIR / "results")
YOUTUBE_FOLDER_ID = "11nrbGOByVtQHs2b1ipwTo41khIY1-V6F"


def youtube_clips_handler(
    url: str,
    task_id: str = None,
    exclude_segments: list = None,
    num_clips: int = None,
    clip_duration: int = None,
    composition_mode: str = "normal",
    add_cta: bool = False,
    quality: str = "720p",
    start_time: str = None,
    end_time: str = None
):
    logger.info(f"Starting YouTube clips handler for URL: {url} (quality: {quality}, start: {start_time}, end: {end_time})")

    if not task_id:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="task_id is required"
        )

    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
        )

    from app.services.video.youtube_clips.downloader import normalize_quality
    try:
        quality_str, _ = normalize_quality(quality or getattr(settings, "YOUTUBE_DOWNLOAD_QUALITY", "720p"))
    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    local_clips = []
    try:
        def execute_process():
            return process_youtube_url(
                url=url,
                results_dir=RESULTS_DIR,
                exclude_segments=exclude_segments,
                num_clips=num_clips,
                clip_duration=clip_duration,
                composition_mode=composition_mode,
                add_cta=add_cta,
                quality=quality_str,
                start_time=start_time,
                end_time=end_time
            )

        local_clips = ProcessWrapper.run(task_id, execute_process)
        logger.info(f"Generated {len(local_clips)} local clips. Preparing Google Drive upload...")

        from app.services.google_drive import drive_service
        drive_folder = settings.GOOGLE_DRIVE_YOUTUBE_FOLDER_ID or YOUTUBE_FOLDER_ID

        segments_urls = []
        files_metadata = []

        for clip_path in local_clips:
            filename = os.path.basename(clip_path)
            logger.info(f"Uploading {filename} to Google Drive folder {drive_folder}...")
            upload_res = drive_service.upload_file(
                file_path=clip_path,
                filename=filename,
                mime_type="video/mp4",
                folder_id=drive_folder
            )
            drive_url = upload_res.get("drive_url")
            file_id = upload_res.get("file_id")

            segments_urls.append(drive_url)
            files_metadata.append({
                "file_id": file_id,
                "drive_url": drive_url,
                "filename": filename
            })

            # Remove local clip immediately after upload so nothing remains on disk
            if os.path.exists(clip_path):
                try:
                    os.remove(clip_path)
                    logger.info(f"Removed local file: {clip_path}")
                except OSError as err:
                    logger.warning(f"Could not remove local file {clip_path}: {err}")

        return JSONResponse({
            "success": True,
            "task_id": task_id,
            "segments": segments_urls,
            "files": files_metadata,
            "count": len(segments_urls),
            "folder_id": drive_folder,
            "message": f"Se generaron y subieron {len(segments_urls)} clips a Google Drive exitosamente"
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in youtube_clips_handler: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error procesando URL de YouTube: {str(e)}"
        )
    finally:
        # Guarantee no leftover files in results folder for this task
        for c in local_clips:
            if os.path.exists(c):
                try:
                    os.remove(c)
                except OSError:
                    pass


def delete_youtube_clip_handler(file_id: str):
    """
    Deletes a video clip from Google Drive using its file_id or drive_url.
    """
    logger.info(f"Received request to delete Google Drive file: {file_id}")
    if not file_id:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="file_id is required"
        )

    try:
        from app.services.google_drive import drive_service
        drive_service.delete_file(file_id)
        return JSONResponse({
            "success": True,
            "file_id": file_id,
            "message": "Archivo eliminado de Google Drive correctamente"
        })
    except Exception as e:
        logger.error(f"Error deleting file {file_id} from Google Drive: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar archivo de Google Drive: {str(e)}"
        )
