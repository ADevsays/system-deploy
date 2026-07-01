from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.grok import ask_grok
from app.services.openai import ask_openai
from app.services.gemini import ask_gemini
from app.services.claude import ask_claude
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class TemplateScriptRequest(BaseModel):
    message: str
    context: str = ""
    provider: str = "grok"
    api_key: str | None = None

class TemplateScriptResponse(BaseModel):
    response: str

@router.post("/template_script", response_model=TemplateScriptResponse)
async def generate_template_script(body: TemplateScriptRequest):
    logger.info(f"Received template script request. Provider: {body.provider}, API Key Provided: {bool(body.api_key)}")
    try:
        provider = body.provider.lower()
        
        system_prompt = settings.get_template_script_prompt()

        if provider == "grok":
            logger.info("Routing request to Grok service")
            result = await ask_grok(body.message, body.context, body.api_key, system_prompt_override=system_prompt)
        elif provider == "openai":
            logger.info("Routing request to OpenAI service")
            result = await ask_openai(body.message, body.context, body.api_key, system_prompt_override=system_prompt)
        elif provider == "gemini":
            logger.info("Routing request to Gemini service")
            result = await ask_gemini(body.message, body.context, body.api_key, system_prompt_override=system_prompt)
        elif provider == "claude":
            logger.info("Routing request to Claude service")
            result = await ask_claude(body.message, body.context, body.api_key, system_prompt_override=system_prompt)
        else:
            logger.error(f"Unsupported provider requested: {provider}")
            raise ValueError(f"Unsupported provider: {provider}")
            
        return result
    except Exception as e:
        logger.error(f"Error calling {body.provider} API: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
