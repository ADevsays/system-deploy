import httpx
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

async def ask_openai(message: str, context: str = "", api_key: str | None = None, system_prompt_override: str | None = None) -> dict:
    if not api_key:
        raise ValueError("OpenAI API Key is required but was not provided.")
        
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    system_prompt = system_prompt_override if system_prompt_override is not None else settings.get_grok_system_prompt()
    system_prompt = system_prompt.replace("{{dynamic_context}}", context)

    payload = {
        "model": "o3-mini",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message},
        ]
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(OPENAI_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

    output_text = data.get("choices", [])[0].get("message", {}).get("content", "")
    
    logger.info("OpenAI response received.")
    # OpenAI doesn't natively return citations in the same way without tools/search, returning empty list
    return {"response": output_text, "citations": []}
