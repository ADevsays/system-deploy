# Content Processing API

API para procesamiento de audio y video usando FastAPI y FFmpeg, con integración a Google Drive.

## 🎯 Características

- ✂️ **Corte de silencios en audio** - Elimina automáticamente silencios al inicio, final e intermedios
- 🎬 **Procesamiento de video** - Zoom inteligente y corte de silencios
- ☁️ **Integración Google Drive** - Los archivos procesados se suben automáticamente a Drive
- 📊 **Sistema de tareas con progreso** - Monitoreo en tiempo real del procesamiento
- 🐳 **Docker-ready** - Listo para desplegar en VPS

## 🚀 Quick Start

### Desarrollo Local

```bash
# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus configuraciones

# Ejecutar servidor
uvicorn app.main:app --reload --port 8000
```

### Deployment con Docker

Ver [DEPLOYMENT.md](./DEPLOYMENT.md) para instrucciones completas.

```bash
# Build y ejecutar
docker-compose up -d --build

# Ver logs
docker-compose logs -f api
```

## 📡 API Endpoints

### Audio Processing

**POST** `/audio/cut`
- Sube un archivo de audio y elimina silencios
- Retorna enlace de Google Drive con el resultado

```bash
curl -X POST \
  -F "file=@audio.mp3" \
  -F "task_id=<task_id>" \
  http://localhost:8000/audio/cut
```

### Video & YouTube Processing

**POST** `/video/youtube-clips`
- Descarga video de YouTube, recorta pausas/anuncios, trocea en clips y renderiza formato 3:4 con subtítulos ASS.
- **Calidad seleccionable**: `quality`: `"480p"`, `"720p"` (por defecto) o `"1080p"`.
- Sube los resultados directamente a Google Drive.

```bash
curl -X POST http://localhost:8000/video/youtube-clips \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "task_id": "<task_id>",
    "quality": "720p",
    "num_clips": 3,
    "clip_duration": 60,
    "composition_mode": "normal",
    "add_cta": false
  }'
```

**DELETE** `/video/youtube-clips/{file_id}`
- Elimina un clip generado de Google Drive usando su ID o URL.

### Task Management

**GET** `/tasks/init`
- Inicializa una nueva tarea
- Retorna `task_id` para usar en procesamiento

**GET** `/status/{task_id}`
- Consulta el estado y progreso de una tarea

## 🔧 Configuración

### Variables de Entorno

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `GOOGLE_DRIVE_FOLDER_ID` | ID de carpeta en Drive | `1a2b3c4d5e6f7g8h` |
| `GOOGLE_CREDENTIALS_PATH` | Ruta a credentials.json | `/app/credentials.json` |
| `TEMP_DIR` | Directorio temporal | `/app/temp` |
| `CORS_ORIGINS` | Orígenes permitidos (separados por coma) | `http://localhost:5173,https://app.com` |
| `YOUTUBE_DOWNLOAD_QUALITY` | Calidad por defecto para descargas (`480p`, `720p`, `1080p`) | `720p` |
| `APIFY_TOKEN` | Token de Apify para descargas sin bloqueo de IP | `apify_api_...` |

### Google Drive Setup

1. Crear proyecto en [Google Cloud Console](https://console.cloud.google.com/)
2. Habilitar Google Drive API
3. Crear credenciales OAuth 2.0 (Desktop app)
4. Descargar `credentials.json`
5. Ejecutar primera autenticación para generar `token.json`

Ver [DEPLOYMENT.md](./DEPLOYMENT.md) para detalles.

## 📁 Estructura del Proyecto

```
system-deploy/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── controllers/     # Lógica de endpoints
│   │       ├── audio.py          # Rutas de audio
│   │       ├── video.py          # Rutas de video
│   │       └── routes.py         # Router principal
│   ├── core/
│   │   └── config.py             # Configuración centralizada
│   ├── services/
│   │   ├── audio/                # Servicios de procesamiento audio
│   │   ├── video/                # Servicios de procesamiento video
│   │   ├── google_drive.py       # Integración Google Drive
│   │   └── task_manager.py       # Sistema de tareas
│   ├── utils/
│   │   └── process_wrapper.py    # Wrapper para progreso
│   └── main.py                   # Aplicación FastAPI
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

## 🔒 Seguridad

- 🚫 No commiteés `credentials.json` ni `token.json`
- 🚫 No commiteés archivos `.env` con datos reales
- ✅ Usa `.env.example` como plantilla
- ✅ Configura CORS apropiadamente para producción

## 📝 TODO

- [ ] Implementar rate limiting
- [ ] Agregar más formatos de video
- [ ] Sistema de webhooks para notificaciones
- [ ] Dashboard de monitoreo

## 🛠️ Stack Tecnológico

- **Python 3.11**
- **FastAPI** - Framework web
- **FFmpeg** - Procesamiento multimedia
- **Google Drive API** - Almacenamiento en la nube
- **Docker** - Containerización

## 📄 Licencia

[Tu licencia aquí]
