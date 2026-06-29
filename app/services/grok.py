import httpx
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

XAI_API_URL = "https://api.x.ai/v1/responses"


async def ask_grok(message: str, context: str = "", api_key: str | None = None) -> dict:
    key_to_use = api_key if api_key else settings.XAI_API_KEY
    headers = {
        "Authorization": f"Bearer {key_to_use}",
        "Content-Type": "application/json",
    }

    system_prompt = settings.get_grok_system_prompt()
    # Inyectar el contexto dinámico en el placeholder
    system_prompt = system_prompt.replace("{{dynamic_context}}", context)

    payload = {
        "model": "grok-4.3",
        "reasoning_effort": "low",
        "input": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message},
        ],
        "tools": [{"type": "web_search"}],
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(XAI_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

    output_text = _extract_output_text(data)
    citations = _extract_citations(data)

    logger.info(f"Grok response received. Citations: {len(citations)}")
    return {"response": output_text, "citations": citations}


def _extract_output_text(data: dict) -> str:
    for item in data.get("output", []):
        if item.get("type") == "message":
            for content in item.get("content", []):
                if content.get("type") == "output_text":
                    return content.get("text", "")
    return ""


def _extract_citations(data: dict) -> list[str]:
    urls = []
    for item in data.get("output", []):
        if item.get("type") == "message":
            for content in item.get("content", []):
                for annotation in content.get("annotations", []):
                    url = annotation.get("url")
                    if url and url not in urls:
                        urls.append(url)
    return urls
