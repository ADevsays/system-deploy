import os
from pathlib import Path
from dotenv import load_dotenv

# Encontrar la raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent.parent
env_path = BASE_DIR / ".env"
env_example_path = BASE_DIR / ".env.example"

# Cargar configuración (Prioridad: .env > .env.example)
if env_path.exists():
    print(f"--- Loading config from {env_path} ---")
    load_dotenv(dotenv_path=env_path, override=True)
elif env_example_path.exists():
    print(f"--- Loading config from {env_example_path} (Using example as fallback) ---")
    load_dotenv(dotenv_path=env_example_path, override=True)
else:
    print("--- WARNING: No .env or .env.example found ---")
    load_dotenv()

class Settings:
    TEMP_DIR: str = os.getenv("TEMP_DIR", "/app/temp")
    GOOGLE_DRIVE_FOLDER_ID: str = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "")
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REFRESH_TOKEN: str = os.getenv("GOOGLE_REFRESH_TOKEN", "")
    GOOGLE_REDIRECT_URI: str = os.getenv("GOOGLE_REDIRECT_URI", "https://content.codecollab.cloud/rest/oauth2-credential/callback")
    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
    
    @classmethod
    def ensure_temp_dir(cls):
        os.makedirs(cls.TEMP_DIR, exist_ok=True)

settings = Settings()
