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

class ScriptFromTemplateRequest(BaseModel):
    template: str
    tema: str
    provider: str = "grok"
    api_key: str | None = None



@router.post("/generate", response_model=ScriptResponse)
async def generate_script(body: ScriptRequest):
    logger.info(f"Received script generation request. Provider: {body.provider}, API Key Provided: {bool(body.api_key)}")
    try:
        provider = body.provider.lower()
        if provider == "grok":
            logger.info("Routing request to Grok service")
            result = await ask_grok(body.message, body.context, body.api_key)
            logger.info("Grok service returned successfully")
        elif provider == "openai":
            logger.info("Routing request to OpenAI service")
            result = await ask_openai(body.message, body.context, body.api_key)
            logger.info("OpenAI service returned successfully")
        elif provider == "gemini":
            logger.info("Routing request to Gemini service")
            result = await ask_gemini(body.message, body.context, body.api_key)
            logger.info("Gemini service returned successfully")
        elif provider == "claude":
            logger.info("Routing request to Claude service")
            result = await ask_claude(body.message, body.context, body.api_key)
            logger.info("Claude service returned successfully")
        else:
            logger.error(f"Unsupported provider requested: {provider}")
            raise ValueError(f"Unsupported provider: {provider}")
            
        return result
    except Exception as e:
        logger.error(f"Error calling {body.provider} API: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate_from_template", response_model=ScriptResponse)
async def generate_script_from_template(body: ScriptFromTemplateRequest):
    logger.info(f"Received script from template request. Provider: {body.provider}, API Key Provided: {bool(body.api_key)}")
    try:
        provider = body.provider.lower()
        
        # Pass body.template as the system_prompt_override and body.tema as the user message
        if provider == "grok":
            logger.info("Routing request to Grok service")
            result = await ask_grok(body.tema, "", body.api_key, system_prompt_override=body.template)
        elif provider == "openai":
            logger.info("Routing request to OpenAI service")
            result = await ask_openai(body.tema, "", body.api_key, system_prompt_override=body.template)
        elif provider == "gemini":
            logger.info("Routing request to Gemini service")
            result = await ask_gemini(body.tema, "", body.api_key, system_prompt_override=body.template)
        elif provider == "claude":
            logger.info("Routing request to Claude service")
            result = await ask_claude(body.tema, "", body.api_key, system_prompt_override=body.template)
        else:
            logger.error(f"Unsupported provider requested: {provider}")
            raise ValueError(f"Unsupported provider: {provider}")
            
        return result
    except Exception as e:
        logger.error(f"Error calling {body.provider} API: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
