from fastapi import HTTPException
from fastapi import status as http_status
from fastapi.responses import JSONResponse, FileResponse
from fastapi import BackgroundTasks
import os
import logging
from uuid import uuid4
from app.services.image.tweet import generate_tweet_image
from app.services.task_manager import task_manager, Task
from app.utils.process_wrapper import ProcessWrapper
from app.core.config import settings

logger = logging.getLogger(__name__)


def _generate_task_id():
    new_task = Task(id=str(uuid4()), porcentage=0, status="pending")
    task_manager.add_task(new_task)
    return new_task.id


async def tweet_image_handler(text: str, return_file: bool = True):
    task_id = _generate_task_id()
    output_path = None

    try:
        def execute_process():
            return generate_tweet_image(text)

        output_path = ProcessWrapper.run(task_id, execute_process)
        logger.info(f"Tweet image generated: {output_path}")

        from app.services.google_drive import drive_service

        try:
            drive_data = drive_service.upload_file(
                file_path=output_path,
                filename=f"tweet_{uuid4().hex[:8]}.png",
                mime_type='image/png',
                folder_id=settings.GOOGLE_DRIVE_MEME_FOLDER_ID
            )

            if not return_file:
                if os.path.exists(output_path):
                    os.remove(output_path)

                return JSONResponse({
                    "success": True,
                    "task_id": task_id,
                    "drive_link": drive_data["drive_url"],
                    "file_id": drive_data["file_id"],
                    "message": "Tweet image generated and uploaded to Google Drive"
                })

            def cleanup():
                if output_path and os.path.exists(output_path):
                    os.remove(output_path)

            tasks = BackgroundTasks()
            tasks.add_task(cleanup)

            return FileResponse(
                path=output_path,
                filename=f"tweet_{uuid4().hex[:8]}.png",
                media_type='image/png',
                background=tasks,
                headers={
                    "X-Drive-Link": drive_data["drive_url"],
                    "X-File-ID": drive_data["file_id"],
                    "X-Task-ID": task_id
                }
            )

        except Exception as e:
            logger.error(f"Error uploading to Google Drive: {str(e)}")
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error uploading tweet image to Google Drive: {str(e)}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in tweet_image_handler: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating tweet image: {str(e)}"
        )
    finally:
        if output_path and not return_file and os.path.exists(output_path):
            try:
                os.remove(output_path)
            except OSError:
                pass
