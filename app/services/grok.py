import httpx
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

XAI_API_URL = "https://api.x.ai/v1/responses"


async def ask_grok(message: str, context: str = "", api_key: str | None = None) -> dict:
    logger.info("Starting ask_grok")
    key_to_use = api_key if api_key else settings.XAI_API_KEY
    if not key_to_use:
        logger.warning("No API key provided or found in settings.XAI_API_KEY")

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

    logger.info(f"Using XAI_API_URL: {XAI_API_URL}")
    logger.info(f"Payload prepared: {payload}")

    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            logger.info("Sending request to xAI API...")
            response = await client.post(XAI_API_URL, headers=headers, json=payload)
            logger.info(f"Received response from xAI API. Status code: {response.status_code}")
            
            # Log first 500 characters of the raw response text for debugging
            response_text = response.text
            logger.info(f"Raw response body: {response_text[:500]}")
            
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPStatusError as exc:
            logger.error(f"HTTPStatusError from xAI: {exc.response.status_code} - {exc.response.text}")
            raise
        except Exception as exc:
            logger.error(f"Error during xAI httpx request: {str(exc)}")
            raise

    logger.info("Extracting output text and citations from response data")
    output_text = _extract_output_text(data)
    citations = _extract_citations(data)

    logger.info(f"Extraction complete. Output length: {len(output_text)}, Citations: {len(citations)}")
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
