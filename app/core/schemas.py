from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class TTSRequest(BaseModel):
    email: str
    text: str
    voice_id: str
    model_id: str = "eleven_multilingual_v2"
    stability: float = 0.48
    similarity_boost: float = 1.0
    style: float = 0.41
    use_speaker_boost: bool = True
    velocity: float = 0.98
    output_format: str = "mp3_44100_128"


class UserCreate(BaseModel):
    email: str
    character_limit: Optional[int] = None


class UserResponse(BaseModel):
    id: int
    email: str
    character_limit: int
    characters_used: int
    characters_remaining: int
    is_active: bool
    created_at: str
    updated_at: str


class UserLimitUpdate(BaseModel):
    character_limit: int


class UserStatusUpdate(BaseModel):
    is_active: bool


class UsageResponse(BaseModel):
    email: str
    characters_used: int
    character_limit: int
    characters_remaining: int
    usage_percentage: float
    is_active: bool
