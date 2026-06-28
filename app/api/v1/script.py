from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.grok import ask_grok
from app.services.openai import ask_openai
from app.services.gemini import ask_gemini
from app.services.claude import ask_claude
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class ScriptRequest(BaseModel):
    message: str
    context: str = ""
    provider: str = "grok"
    api_key: str | None = None


class ScriptResponse(BaseModel):
    response: str



@router.post("/generate", response_model=ScriptResponse)
async def generate_script(body: ScriptRequest):
    try:
        provider = body.provider.lower()
        if provider == "grok":
            result = await ask_grok(body.message, body.context, body.api_key)
        elif provider == "openai":
            result = await ask_openai(body.message, body.context, body.api_key)
        elif provider == "gemini":
            result = await ask_gemini(body.message, body.context, body.api_key)
        elif provider == "claude":
            result = await ask_claude(body.message, body.context, body.api_key)
        else:
            raise ValueError(f"Unsupported provider: {provider}")
            
        return result
    except Exception as e:
        logger.error(f"Error calling {body.provider} API: {e}")
        raise HTTPException(status_code=500, detail=str(e))
