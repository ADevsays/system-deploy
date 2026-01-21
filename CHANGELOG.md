# Changelog - Docker Deployment

## 2026-01-17 - Preparación para Deployment en VPS

### ✅ Añadido

#### Infraestructura Docker
- **Dockerfile** - Imagen optimizada con Python 3.11 y FFmpeg
- **docker-compose.yml** - Orquestación con volúmenes y health checks
- **.dockerignore** - Optimización de build excluyendo archivos innecesarios

#### Configuración
- **app/core/config.py** - Sistema de configuración centralizado con variables de entorno
- **.env.example** - Plantilla de configuración con comentarios útiles
- **requirements.txt** - Dependencias del proyecto incluyendo Google Drive API

#### Integración Google Drive
- **app/services/google_drive.py** - Servicio completo para:
  - Autenticación OAuth 2.0
  - Upload de archivos procesados
  - Generación de enlaces públicos
  - Manejo de tokens y credenciales

#### Scripts de Utilidad
- **scripts/setup_auth.py** - Helper para autenticación inicial de Google Drive
- **scripts/validate_deployment.py** - Validación pre-deployment

#### Documentación
- **README.md** - Documentación completa del proyecto
- **DEPLOYMENT.md** - Guía paso a paso para deployment en VPS
- **CHANGELOG.md** - Este archivo

### 🔧 Modificado

#### Endpoints de Audio
- **app/api/v1/controllers/audio/cut_controller.py**
  - ✅ Ahora sube archivos a Google Drive en lugar de guardarlos localmente
  - ✅ Retorna enlace público del archivo procesado
  - ✅ Usa configuración centralizada para rutas
  - ✅ Limpia archivos temporales automáticamente

#### Servicios de Audio
- **app/services/audio/cut.py**
  - ✅ Usa `settings.TEMP_DIR` en lugar de path hardcodeado
  - ✅ Compatible con entornos containerizados

#### Aplicación Principal
- **app/main.py**
  - ✅ Importa configuración centralizada
  - ✅ CORS dinámico desde variables de entorno
  - ✅ Asegura creación de directorio temp al inicio

#### Rutas
- **app/api/v1/routes.py**
  - ⚠️ Endpoints de video deshabilitados temporalmente (enfoque en audio)

### 📝 Actualizado

- **.gitignore** - Añadidas exclusiones para:
  - Credenciales (credentials.json, token.json)
  - Variables de entorno (.env)
  - Archivos multimedia procesados
  - Cache de Python

### 🎯 Comportamiento Anterior vs Nuevo

#### Antes (Local)
```
Cliente → API → Procesar → Guardar en /results → Retornar path local
```

#### Ahora (VPS + Docker)
```
Cliente → API → Procesar → Subir a Drive → Retornar enlace público
                    ↓
              Limpiar temp
```

### 🚀 Próximos Pasos

1. **Configurar Google Cloud Console**
   - Habilitar Google Drive API
   - Crear credenciales OAuth 2.0
   - Descargar credentials.json

2. **Autenticación Inicial**
   ```bash
   python scripts/setup_auth.py
   ```

3. **Validar Configuración**
   ```bash
   python scripts/validate_deployment.py
   ```

4. **Deploy**
   ```bash
   docker-compose up -d --build
   ```

### 📊 Beneficios del Cambio

- ✅ **No almacena archivos en VPS** - Ahorro de espacio en disco
- ✅ **Enlaces públicos automáticos** - Fácil compartir resultados
- ✅ **Escalabilidad** - Google Drive maneja el almacenamiento
- ✅ **Configuración por entorno** - Fácil cambio entre dev/prod
- ✅ **Docker-ready** - Deploy consistente en cualquier servidor

### ⚠️ Notas Importantes

- Los endpoints de **video están temporalmente deshabilitados**
- Requiere **autenticación de Google Drive** antes del primer uso
- Los archivos temporales se eliminan automáticamente después de procesarlos
- El directorio `results/` ya **no se utiliza** en el nuevo sistema

### 🔒 Seguridad

- Credenciales **NO incluidas en el repositorio**
- Variables sensibles en `.env` (gitignored)
- CORS configurable por entorno
- OAuth 2.0 para Google Drive

---

**Autor:** Sistema de deployment automatizado  
**Fecha:** 2026-01-17  
**Versión:** 1.0.0 (Docker-ready)
