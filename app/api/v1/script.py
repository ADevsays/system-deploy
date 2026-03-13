from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.grok import ask_grok
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class ScriptRequest(BaseModel):
    message: str
    context: str = ""


class ScriptResponse(BaseModel):
    response: str



@router.post("/generate", response_model=ScriptResponse)
async def generate_script(body: ScriptRequest):
    try:
        result = await ask_grok(body.message, body.context)
        return result
    except Exception as e:
        logger.error(f"Error calling Grok API: {e}")
        raise HTTPException(status_code=500, detail=str(e))
