import httpx
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"

async def ask_claude(message: str, context: str = "", api_key: str | None = None) -> dict:
    if not api_key:
        raise ValueError("Claude API Key is required but was not provided.")
        
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }

    system_prompt = settings.get_grok_system_prompt()
    system_prompt = system_prompt.replace("{{dynamic_context}}", context)

    payload = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 2048,
        "system": system_prompt,
        "messages": [
            {"role": "user", "content": message},
        ]
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(CLAUDE_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

    output_text = data.get("content", [])[0].get("text", "")
    
    logger.info("Claude response received.")
    # Claude API natively does not do web search on this endpoint without custom tool use setup
    return {"response": output_text, "citations": []}
