from fastapi import APIRouter, UploadFile, File, Form, Body, Path as FastApiPath
from app.api.v1.controllers.video import (
    cut_video_handler,
    zoom_video_handler,
    meme_video_handler,
    youtube_clips_handler,
    delete_youtube_clip_handler
)
from typing import Optional, List
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class ExcludeSegment(BaseModel):
    start: float = Field(..., description="Start timestamp in seconds to exclude")
    end: float = Field(..., description="End timestamp in seconds to exclude")


class YoutubeClipsRequest(BaseModel):
    url: str = Field(..., description="Full YouTube video URL or ID", example="https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    task_id: str = Field(..., description="Task ID obtained from GET /tasks/init for progress tracking", example="task_12345")
    exclude_segments: Optional[List[ExcludeSegment]] = Field(None, description="Optional list of time intervals (sponsorships, intros) to remove before clipping")
    num_clips: Optional[int] = Field(None, description="Exact number of clips to generate. If set with clip_duration, limits the output count.", example=3)
    clip_duration: Optional[int] = Field(None, description="Duration in seconds for each clip. Default is 180s.", example=60)
    composition_mode: Optional[str] = Field("normal", description="Composition mode: 'normal' (3:4 canvas with top/bottom bars) or 'fullscreen' (blurred background)", example="normal")
    add_cta: Optional[bool] = Field(False, description="Whether to append a 3-second Call-To-Action screen with channel logo and thumbnail at the end of each clip", example=False)


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
    color: str = Form("white"),
    return_file: bool = Form(False)
):
    return await meme_video_handler(file, text, template, color, return_file)


@router.post(
    "/youtube-clips",
    summary="Process YouTube video into 3:4 viral clips",
    description="Downloads a YouTube video, removes specified segments (e.g. ads), splits it into N clips or by duration, generates viral titles with Grok AI, renders in 3:4 format with ASS subtitles, and uploads to Google Drive folder 11nrbGOByVtQHs2b1ipwTo41khIY1-V6F without saving files locally."
)
def youtube_clips_route(payload: YoutubeClipsRequest):
    return youtube_clips_handler(
        url=payload.url,
        task_id=payload.task_id,
        exclude_segments=payload.exclude_segments,
        num_clips=payload.num_clips,
        clip_duration=payload.clip_duration,
        composition_mode=payload.composition_mode,
        add_cta=payload.add_cta
    )


@router.delete(
    "/youtube-clips/{file_id:path}",
    summary="Delete a generated YouTube clip from Google Drive",
    description="Deletes a video file from Google Drive by its file ID or full Drive URL."
)
def delete_youtube_clip_route(
    file_id: str = FastApiPath(..., description="Google Drive File ID or full drive URL to delete")
):
    return delete_youtube_clip_handler(file_id)


@router.delete(
    "/drive/{file_id:path}",
    summary="Delete any video file from Google Drive",
    description="Generic endpoint to delete any uploaded file from Google Drive using its file_id or drive_url."
)
def delete_drive_video_route(
    file_id: str = FastApiPath(..., description="Google Drive File ID or full drive URL to delete")
):
    return delete_youtube_clip_handler(file_id)
