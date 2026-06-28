from fastapi import APIRouter, HTTPException, Header, Depends
from fastapi.responses import Response
import logging

from app.core.config import settings
from app.core.schemas import (
    TTSRequest,
    UserCreate,
    UserResponse,
    UserLimitUpdate,
    UserStatusUpdate,
    UsageResponse,
)
from app.services import elevenlabs as elevenlabs_service
from app.services import elevenlabs_users as users_repo

logger = logging.getLogger(__name__)

router = APIRouter()


def require_admin(x_admin_key: str = Header(...)):
    if x_admin_key != settings.ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid admin key")
    return True


def _user_to_response(user: dict) -> UserResponse:
    return UserResponse(
        id=user["id"],
        email=user["email"],
        character_limit=user["character_limit"],
        characters_used=user["characters_used"],
        characters_remaining=user["characters_remaining"],
        is_active=user["is_active"],
        created_at=str(user["created_at"]),
        updated_at=str(user["updated_at"]),
    )


# ─── User-facing endpoints ───────────────────────────────────────────


@router.post("/tts")
async def text_to_speech(body: TTSRequest):
    user = await users_repo.get_user_by_email(body.email)
    if user is None or not user["is_active"]:
        raise HTTPException(status_code=403, detail="Access denied")

    char_count = len(body.text)
    remaining = user["character_limit"] - user["characters_used"]
    if char_count > remaining:
        raise HTTPException(
            status_code=429,
            detail=f"Quota exceeded: {char_count} characters requested, {remaining} remaining",
        )

    try:
        audio = await elevenlabs_service.text_to_speech(
            voice_id=body.voice_id,
            text=body.text,
            model_id=body.model_id,
            stability=body.stability,
            similarity_boost=body.similarity_boost,
            style=body.style,
            use_speaker_boost=body.use_speaker_boost,
            output_format=body.output_format,
        )
    except Exception as e:
        logger.error(f"ElevenLabs API error: {e}")
        raise HTTPException(status_code=502, detail=f"ElevenLabs API error: {str(e)}")

    await users_repo.consume_characters(body.email, char_count)
    logger.info(f"TTS completed for {body.email}: {char_count} characters consumed")

    content_type = "audio/mpeg" if "mp3" in body.output_format else "audio/wav"
    return Response(
        content=audio,
        media_type=content_type,
        headers={"X-Characters-Used": str(char_count)},
    )


@router.get("/voices")
async def list_voices():
    try:
        return await elevenlabs_service.list_voices()
    except Exception as e:
        logger.error(f"ElevenLabs API error listing voices: {e}")
        raise HTTPException(status_code=502, detail=f"ElevenLabs API error: {str(e)}")


@router.get("/usage/{email}", response_model=UsageResponse)
async def get_usage(email: str):
    user = await users_repo.get_user_by_email(email)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    usage_pct = (user["characters_used"] / user["character_limit"] * 100) if user["character_limit"] > 0 else 0
    return UsageResponse(
        email=user["email"],
        characters_used=user["characters_used"],
        character_limit=user["character_limit"],
        characters_remaining=user["characters_remaining"],
        usage_percentage=round(usage_pct, 2),
        is_active=user["is_active"],
    )


# ─── Admin endpoints ─────────────────────────────────────────────────


@router.get("/admin/users", response_model=list[UserResponse], dependencies=[Depends(require_admin)])
async def admin_list_users():
    users = await users_repo.list_users()
    return [_user_to_response(u) for u in users]


@router.post("/admin/users", response_model=UserResponse, status_code=201, dependencies=[Depends(require_admin)])
async def admin_create_user(body: UserCreate):
    existing = await users_repo.get_user_by_email(body.email)
    if existing:
        raise HTTPException(status_code=409, detail="User already exists")

    try:
        user = await users_repo.create_user(body.email, body.character_limit)
        return _user_to_response(user)
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/admin/users/{email}", response_model=UserResponse, dependencies=[Depends(require_admin)])
async def admin_get_user(email: str):
    user = await users_repo.get_user_by_email(email)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return _user_to_response(user)


@router.patch("/admin/users/{email}/limit", response_model=UserResponse, dependencies=[Depends(require_admin)])
async def admin_update_limit(email: str, body: UserLimitUpdate):
    user = await users_repo.get_user_by_email(email)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    updated = await users_repo.update_user_limit(email, body.character_limit)
    return _user_to_response(updated)


@router.patch("/admin/users/{email}/status", response_model=UserResponse, dependencies=[Depends(require_admin)])
async def admin_update_status(email: str, body: UserStatusUpdate):
    user = await users_repo.get_user_by_email(email)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    updated = await users_repo.update_user_status(email, body.is_active)
    return _user_to_response(updated)


@router.post("/admin/users/{email}/reset", response_model=UserResponse, dependencies=[Depends(require_admin)])
async def admin_reset_usage(email: str, _=Depends(require_admin)):
    user = await users_repo.get_user_by_email(email)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    updated = await users_repo.reset_usage(email)
    return _user_to_response(updated)


@router.delete("/admin/users/{email}", dependencies=[Depends(require_admin)])
async def admin_delete_user(email: str):
    deleted = await users_repo.delete_user(email)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")
    return {"detail": f"User {email} deleted"}
