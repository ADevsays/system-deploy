import httpx
import logging
import json
import asyncio
from app.core.config import settings

logger = logging.getLogger(__name__)

XAI_API_URL = "https://api.x.ai/v1/chat/completions"

GROK_SYSTEM_PROMPT = """
Eres un experto en marketing viral y creación de contenido para redes sociales (TikTok, Reels, YouTube Shorts).
Tu tarea es transformar el título original de un video de YouTube en títulos cortos, impactantes y variados.

EJEMPLOS DE TRANSFORMACIÓN:
Entrada: "Cómo Aprender a Hackear en el 2026 - Una guía práctica"
Resultados sugeridos:
1. "Guía práctica para ser hacker 2026"
2. "Cómo aprender a Hackear en el 2026"
3. "Aprende a HACKEAR con este vídeo (mira el final)"

REGLAS:
1. Genera títulos cortos y resumidos (máximo 50 caracteres).
2. Todo el título debe estar en MAYÚSCULAS.
3. Identifica UNA SOLA palabra del título que sea la más importante para resaltar.
4. Los títulos DEBEN ser clickbait forzoso pero descriptivo y meramente basado en el título recibido
5. EVITA títulos genéricos como "PARTE 1" o "SIGUE VIENDO".
6. Devuelve ÚNICAMENTE un objeto JSON con el siguiente formato:
{
  "results": [
    { "title": "TÍTULO 1", "yellow_word": "PALABRA" },
    { "title": "TÍTULO 2", "yellow_word": "OTRA" }
  ]
}
"""

async def _ask_grok_metadata(message: str) -> dict:
    api_key = settings.XAI_API_KEY
    if not api_key:
        logger.warning("XAI_API_KEY no configurada. Usando fallback de títulos.")
        return {"results": [{"title": "CLIP VIRAL INCREÍBLE", "yellow_word": "VIRAL"}]}

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "grok-4-1-fast-non-reasoning",
        "messages": [
            {"role": "system", "content": GROK_SYSTEM_PROMPT},
            {"role": "user", "content": message},
        ]
    }

    MAX_RETRIES = 2
    for attempt in range(1, MAX_RETRIES + 2):
        try:
            logger.info(f"Petición a Grok para títulos (intento {attempt}/{MAX_RETRIES + 1}): {message[:80]}...")
            async with httpx.AsyncClient(timeout=45.0) as client:
                response = await client.post(XAI_API_URL, headers=headers, json=payload)
                if response.status_code != 200:
                    logger.error(f"Error en API x.ai (Status {response.status_code}): {response.text}")
                    return {"results": [{"title": "ERROR EN CONEXIÓN API", "yellow_word": "ERROR"}]}

                data = response.json()
                content_str = data["choices"][0]["message"]["content"].strip()

                if "```json" in content_str:
                    content_str = content_str.split("```json")[1].split("```")[0].strip()
                elif "```" in content_str:
                    content_str = content_str.split("```")[1].split("```")[0].strip()

                parsed_data = json.loads(content_str)
                return parsed_data
        except (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.TimeoutException) as e:
            if attempt <= MAX_RETRIES:
                wait_s = 2 ** attempt
                logger.warning(f"Timeout llamando a Grok. Reintentando en {wait_s}s...")
                await asyncio.sleep(wait_s)
            else:
                logger.error(f"Timeout persistente con Grok: {e}")
        except Exception as e:
            logger.error(f"Error parseando respuesta de Grok: {e}")
            break

    return {"results": [{"title": "PROCESANDO CONTENIDO", "yellow_word": "CONTENIDO"}]}


async def generate_clips_metadata(video_title: str, count: int) -> list:
    """
    Genera metadatos (título viral + yellow_word) para N clips.
    Garantiza una lista de tamaño exacto `count`.
    """
    message = f"Genera {count} títulos diferentes y virales basados en este video: {video_title}"
    data = await _ask_grok_metadata(message)
    results = data.get("results", [])

    if len(results) > count:
        results = results[:count]

    while len(results) < count:
        idx = len(results) + 1
        results.append({
            "title": f"MIRA LO QUE PASA EN EL CLIP {idx}",
            "yellow_word": "PASA"
        })

    return results
