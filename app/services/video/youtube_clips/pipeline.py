import os
import uuid
import logging
import asyncio
import re
import shutil
from app.core.config import settings
from .metadata import generate_clips_metadata
from .downloader import download_youtube_video, get_youtube_metadata
from .segmenter import split_into_segments, exclude_segments_logic
from .composer import apply_3_4_composition

logger = logging.getLogger(__name__)

def process_youtube_url(
    url: str,
    results_dir: str,
    exclude_segments: list = None,
    num_clips: int = None,
    clip_duration: int = None,
    composition_mode: str = "normal",
    add_cta: bool = False
) -> list[str]:
    """
    Synchronous wrapper for async YouTube clip processing.
    """
    return asyncio.run(
        _process_youtube_url_async(
            url=url,
            results_dir=results_dir,
            exclude_segments=exclude_segments,
            num_clips=num_clips,
            clip_duration=clip_duration,
            composition_mode=composition_mode,
            add_cta=add_cta
        )
    )


async def _process_youtube_url_async(
    url: str,
    results_dir: str,
    exclude_segments: list = None,
    num_clips: int = None,
    clip_duration: int = None,
    composition_mode: str = "normal",
    add_cta: bool = False
) -> list[str]:
    url_match = re.search(r'https?://[^\s<>"]+|www\.[^\s<>"]+', url)
    if url_match:
        url = url_match.group(0)

    job_id = uuid.uuid4().hex[:8]
    temp_dir = os.path.join(settings.TEMP_DIR, f"yt_{job_id}")
    os.makedirs(temp_dir, exist_ok=True)
    os.makedirs(results_dir, exist_ok=True)

    try:
        # 1. Metadata and thumbnail
        youtube_meta = get_youtube_metadata(url, temp_dir=temp_dir if add_cta else None)
        original_title = youtube_meta.get("title", "Video de YouTube")
        uploader = youtube_meta.get("uploader", "YouTube")
        thumbnail_path = youtube_meta.get("thumbnail_path")
        
        # 2. Download
        logger.info(f"Downloading YouTube video: {url}")
        raw_file = download_youtube_video(url, temp_dir)

        # 3. Trim / Exclude segments
        if exclude_segments:
            trimmed_file = exclude_segments_logic(raw_file, exclude_segments, temp_dir, job_id)
        else:
            trimmed_file = raw_file
            logger.info("Processing complete video without segment exclusion")

        # 4. Segmentation
        clips_to_process = split_into_segments(
            trimmed_file, temp_dir, f"segment_{job_id}",
            num_clips=num_clips, clip_duration=clip_duration
        )
        num_final_clips = len(clips_to_process)

        # 5. Metadata generation (Grok / fallback)
        logger.info(f"Requesting {num_final_clips} viral titles for: {original_title}")
        metadata_results = await generate_clips_metadata(original_title, num_final_clips)

        # 6. Composition
        final_clips = []
        for i, segment_path in enumerate(clips_to_process):
            part_number = i + 1
            clip_meta = metadata_results[i] if i < len(metadata_results) else {"title": "NUEVO CLIP", "yellow_word": ""}
            title = clip_meta.get("title", "NUEVO CLIP")
            yellow_word = clip_meta.get("yellow_word", "")

            final_path = os.path.join(results_dir, f"yt_{job_id}_part{part_number}.mp4")
            
            logger.info(f"Composing 3:4 clip ({part_number}/{num_final_clips}): {segment_path}")
            apply_3_4_composition(
                segment_path, final_path, title, yellow_word, part_number, composition_mode,
                add_cta=add_cta, uploader=uploader, original_title=original_title, thumbnail_path=thumbnail_path
            )

            final_clips.append(os.path.abspath(final_path))

        return final_clips

    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
