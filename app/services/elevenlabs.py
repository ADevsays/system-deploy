import httpx
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

ELEVENLABS_BASE_URL = "https://api.elevenlabs.io/v1"


def _headers() -> dict:
    return {
        "xi-api-key": settings.ELEVEN_LABS_API,
        "Content-Type": "application/json",
    }


async def text_to_speech(
    voice_id: str,
    text: str,
    model_id: str = "eleven_multilingual_v2",
    stability: float = 0.5,
    similarity_boost: float = 0.75,
    style: float = 0.0,
    use_speaker_boost: bool = True,
    output_format: str = "mp3_44100_128",
) -> bytes:
    url = f"{ELEVENLABS_BASE_URL}/text-to-speech/{voice_id}"

    payload = {
        "text": text,
        "model_id": model_id,
        "voice_settings": {
            "stability": stability,
            "similarity_boost": similarity_boost,
            "style": style,
            "use_speaker_boost": use_speaker_boost,
        },
    }

    params = {"output_format": output_format}

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            url,
            headers=_headers(),
            json=payload,
            params=params,
        )
        response.raise_for_status()

    logger.info(f"TTS generated for voice {voice_id}, {len(text)} characters")
    return response.content


async def list_voices() -> dict:
    url = f"{ELEVENLABS_BASE_URL}/voices"

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, headers=_headers())
        response.raise_for_status()

    return response.json()
