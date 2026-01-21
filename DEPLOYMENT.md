# Content Processing API - Deployment Guide

## 🚀 Despliegue en VPS con Docker

### Prerrequisitos

1. **VPS con Docker instalado**
2. **Credenciales de Google Drive OAuth 2.0**

### Configuración de Google Drive API (Web Application)

#### 1. Obtener Credenciales de tu Cliente

1. Utiliza el **ID de cliente** y el **Secreto del cliente** que aparecen en tu pantalla de Google Cloud (la captura que enviaste).
2. Asegúrate de que el **Redirect URI** (`https://content.codecollab.cloud/rest/oauth2-credential/callback`) esté configurado.

#### 2. Generar el Refresh Token (Solo una vez)

Como el VPS no tiene navegador, generaremos un token de larga duración una sola vez:

1. Configura `GOOGLE_CLIENT_ID` y `GOOGLE_CLIENT_SECRET` en tu `.env` local.
2. Ejecuta: `python scripts/get_refresh_token.py`.
3. Sigue las instrucciones para obtener el `GOOGLE_REFRESH_TOKEN`.
4. Añade ese valor a tu `.env`.

### Deployment en VPS

Con este enfoque, el VPS **no necesita archivos JSON**, solo variables de entorno.

#### 1. Clonar el repositorio en el VPS

```bash
git clone <tu-repo-url>
cd system-deploy
```

#### 2. Configurar variables de entorno

Copia el archivo de ejemplo y edítalo:

```bash
cp .env.example .env
nano .env
```

Configura las siguientes variables:

```env
GOOGLE_DRIVE_FOLDER_ID=tu_folder_id_aqui
GOOGLE_CREDENTIALS_PATH=/app/credentials.json
TEMP_DIR=/app/temp
CORS_ORIGINS=https://tudominio.com,http://localhost:5173
```

#### 3. Copiar credentials.json al servidor

Desde tu máquina local:

```bash
scp credentials.json user@tu-vps-ip:/ruta/al/proyecto/
```

#### 4. Configurar Variables en el VPS

Copia tu archivo `.env` al VPS incluyendo las variables de Google:
- `GOOGLE_DRIVE_FOLDER_ID`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REFRESH_TOKEN`
- `GOOGLE_REDIRECT_URI`

No hace falta copiar `credentials.json` ni `token.json` al VPS si usas estas variables.

#### 5. Construir y ejecutar con Docker

```bash
docker-compose up -d --build
```

#### 6. Verificar que está funcionando

```bash
curl http://localhost:8000/
```

Deberías recibir: `{"message": "API is running"}`

### Endpoints disponibles

- `GET /` - Health check
- `GET /status/{task_id}` - Verificar estado de una tarea
- `GET /tasks/init` - Inicializar nueva tarea
- `POST /audio/cut` - Procesar audio (cortar silencios)

### Ejemplo de uso

```bash
# 1. Inicializar tarea
TASK_ID=$(curl -s http://tu-vps-ip:8000/tasks/init | jq -r '.task_id')

# 2. Subir y procesar audio
curl -X POST \
  -F "file=@audio.mp3" \
  -F "task_id=$TASK_ID" \
  http://tu-vps-ip:8000/audio/cut

# La respuesta incluirá drive_link con el enlace público del archivo
```

### Logs y debugging

```bash
# Ver logs en tiempo real
docker-compose logs -f api

# Ver logs de las últimas 100 líneas
docker-compose logs --tail=100 api
```

### Actualización

```bash
git pull
docker-compose up -d --build
```

### Detener el servicio

```bash
docker-compose down
```

### Notas importantes

- ✅ Los archivos procesados se suben automáticamente a Google Drive
- ✅ Los archivos temporales se eliminan después de cada procesamiento
- ✅ NO se almacenan archivos dentro del VPS (excepto en `/app/temp` temporalmente)
- ⚠️ Asegúrate de que `credentials.json` y `token.json` tengan los permisos correctos
- ⚠️ El volumen Docker `temp_data` se limpia automáticamente

### Troubleshooting

**Error: "Credentials file not found"**
- Verifica que `credentials.json` esté en la raíz del proyecto
- Verifica que el volumen esté montado correctamente en docker-compose.yml

**Error: "Invalid authentication"**
- Regenera el `token.json` siguiendo el paso 4
- Verifica que las credenciales OAuth no hayan expirado

**Error: "Permission denied to upload to Drive"**
- Verifica que el GOOGLE_DRIVE_FOLDER_ID sea correcto
- Asegúrate de que la cuenta autenticada tenga permisos de escritura en la carpeta
