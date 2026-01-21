# Quick Start Guide

## 🚀 Inicio Rápido - Setup en 5 minutos

### 1️⃣ Configurar Google Drive (Primera vez)

#### Obtener credenciales

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea proyecto → Habilita "Google Drive API"
3. Credentials → Create → OAuth 2.0 → Desktop App
4. Descarga como `credentials.json` en la raíz del proyecto

#### Obtener Folder ID

1. Crea carpeta en Google Drive para resultados
2. Copia el ID de la URL:
   ```
   https://drive.google.com/drive/folders/[COPIA_ESTE_ID]
   ```

### 2️⃣ Configurar Variables

```bash
# Copiar plantilla
cp .env.example .env

# Editar (reemplaza los valores)
nano .env
```

Configura:
```env
GOOGLE_DRIVE_FOLDER_ID=tu_folder_id_real_aqui
```

### 3️⃣ Autenticar Google Drive

```bash
# Instalar dependencias localmente (solo para auth)
pip install -r requirements.txt

# Ejecutar autenticación (abrirá navegador)
python scripts/setup_auth.py
```

Esto generará `token.json` que necesitas para el deployment.

### 4️⃣ Validar Setup

```bash
python scripts/validate_deployment.py
```

Si todo está ✅, continúa al paso 5.

### 5️⃣ Deploy con Docker

#### En tu VPS:

```bash
# Copiar archivos necesarios
scp credentials.json token.json .env user@vps:/ruta/proyecto/

# SSH al VPS
ssh user@vps
cd /ruta/proyecto

# Construir y ejecutar
docker-compose up -d --build

# Ver logs
docker-compose logs -f
```

### 6️⃣ Probar la API

```bash
# Health check
curl http://tu-vps-ip:8000/

# Iniciar tarea
TASK_ID=$(curl -s http://tu-vps-ip:8000/tasks/init | jq -r '.task_id')
echo "Task ID: $TASK_ID"

# Procesar audio (reemplaza audio.mp3 con tu archivo)
curl -X POST \
  -F "file=@audio.mp3" \
  -F "task_id=$TASK_ID" \
  http://tu-vps-ip:8000/audio/cut
```

Respuesta esperada:
```json
{
  "success": true,
  "drive_link": "https://drive.google.com/file/d/...",
  "filename": "edit_audio.mp3",
  "message": "Archivo procesado y subido a Google Drive correctamente"
}
```

---

## 🔧 Comandos Útiles

### Docker

```bash
# Ver logs en tiempo real
docker-compose logs -f api

# Reiniciar servicio
docker-compose restart api

# Detener todo
docker-compose down

# Re-build después de cambios
docker-compose up -d --build

# Limpiar volúmenes
docker-compose down -v
```

### SSH/SCP (Transferir archivos)

```bash
# Transferir credenciales
scp credentials.json user@vps:/path/to/project/

# Transferir .env
scp .env user@vps:/path/to/project/

# Transferir token
scp token.json user@vps:/path/to/project/
```

---

## ⚠️ Troubleshooting Rápido

| Error | Solución |
|-------|----------|
| `credentials.json not found` | Asegúrate de copiar el archivo al VPS |
| `Invalid authentication` | Regenera `token.json` con `setup_auth.py` |
| `Permission denied Drive` | Verifica que el Folder ID sea correcto |
| `Connection refused` | Verifica firewall del VPS (puerto 8000) |
| `Module not found` | Re-build la imagen: `docker-compose build` |

---

## 📖 Más Información

- Documentación completa: [README.md](README.md)
- Guía de deployment: [DEPLOYMENT.md](DEPLOYMENT.md)
- Changelog: [CHANGELOG.md](CHANGELOG.md)

---

**¿Listo para producción?** ✅

Si completaste todos los pasos, tu API está lista para procesar audio y subir a Drive.
