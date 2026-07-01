import httpx
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

def get_gemini_api_url(api_key: str) -> str:
    return f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"

async def ask_gemini(message: str, context: str = "", api_key: str | None = None, system_prompt_override: str | None = None) -> dict:
    if not api_key:
        raise ValueError("Gemini API Key is required but was not provided.")
        
    headers = {
        "Content-Type": "application/json",
    }

    system_prompt = system_prompt_override if system_prompt_override is not None else settings.get_grok_system_prompt()
    system_prompt = system_prompt.replace("{{dynamic_context}}", context)

    payload = {
        "systemInstruction": {
            "parts": [{"text": system_prompt}]
        },
        "contents": [
            {
                "role": "user",
                "parts": [{"text": message}]
            }
        ],
        "tools": [
            {"googleSearch": {}}
        ]
    }

    url = get_gemini_api_url(api_key)
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

    # Extraer el texto
    output_text = ""
    try:
        output_text = data.get("candidates", [])[0].get("content", {}).get("parts", [])[0].get("text", "")
    except (IndexError, AttributeError):
        logger.error(f"Failed to parse Gemini response: {data}")

    # Extraer URLs de búsqueda (grounding metadata) si están presentes
    citations = []
    try:
        grounding_metadata = data.get("candidates", [])[0].get("groundingMetadata", {})
        web_search_queries = grounding_metadata.get("webSearchQueries", [])
        if web_search_queries:
            # Gemini a veces devuelve las queries, y a veces los chunks con URIs
            grounding_chunks = grounding_metadata.get("groundingChunks", [])
            for chunk in grounding_chunks:
                uri = chunk.get("web", {}).get("uri")
                if uri and uri not in citations:
                    citations.append(uri)
    except (IndexError, AttributeError):
        pass

    logger.info(f"Gemini response received. Citations: {len(citations)}")
    return {"response": output_text, "citations": citations}
