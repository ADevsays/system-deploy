from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.api.v1.routes import router
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import init_db
import logging
import sys


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(router)

settings.ensure_temp_dir()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Configurar el logger raíz
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO, # <-- Esto es la clave
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)