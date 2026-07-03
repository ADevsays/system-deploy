import asyncio
import sys
import os

# Add the project root to the python path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app.services.grok import ask_grok
from app.core.config import settings

async def main():
    try:
        # Use a template and context similar to what generate_from_template does
        result = await ask_grok(
            message="Este es un mensaje de prueba",
            context="",
            api_key=settings.XAI_API_KEY, 
            system_prompt_override="Eres un asistente util."
        )
        print("SUCCESS:", result)
    except Exception as e:
        if hasattr(e, 'response'):
            print("ERROR:", e.response.status_code, e.response.text)
        else:
            print("ERROR:", str(e))

if __name__ == "__main__":
    asyncio.run(main())
