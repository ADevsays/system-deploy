"""
Script para automatizar el test del endpoint de audio
Uso: python scripts/test_audio_upload.py [ruta_archivo.mp3]
"""

import sys
import os
import requests
from pathlib import Path

# Configuración
BASE_URL = os.getenv("API_URL", "http://localhost:8000")
DEFAULT_AUDIO = "audio.mp3"

def test_audio_upload(audio_file: str):
    """
    Automatiza el flujo completo de test de audio:
    1. Inicializa una tarea
    2. Sube y procesa el audio
    3. Muestra el resultado
    """
    print("=" * 60)
    print("🎵 Test de Procesamiento de Audio")
    print("=" * 60)
    
    # Verificar que el archivo existe
    if not os.path.exists(audio_file):
        print(f"\n❌ Error: No se encuentra el archivo '{audio_file}'")
        return 1
    
    print(f"\n📁 Archivo: {audio_file}")
    print(f"🌐 API URL: {BASE_URL}")
    
    # Paso 1: Inicializar tarea
    print("\n1️⃣ Inicializando tarea...")
    try:
        response = requests.get(f"{BASE_URL}/tasks/init")
        response.raise_for_status()
        task_id = response.json()["task_id"]
        print(f"   ✅ Task ID: {task_id}")
    except Exception as e:
        print(f"   ❌ Error al inicializar tarea: {e}")
        return 1
    
    # Paso 2: Subir y procesar audio
    print("\n2️⃣ Subiendo y procesando audio...")
    print("   ⏳ Esto puede tardar varios segundos...")
    
    try:
        with open(audio_file, 'rb') as f:
            files = {'file': (os.path.basename(audio_file), f, 'audio/mpeg')}
            response = requests.post(
                f"{BASE_URL}/audio/cut",
                params={'task_id': task_id},
                files=files,
                timeout=120
            )
            response.raise_for_status()
            result = response.json()
        
        # Paso 3: Mostrar resultado
        print("\n" + "=" * 60)
        print("✅ ÉXITO - Audio procesado correctamente")
        print("=" * 60)
        print(f"\n📄 Archivo: {result.get('filename', 'N/A')}")
        print(f"🔗 Google Drive Link:\n   {result.get('drive_link', 'N/A')}")
        print(f"\n💬 Mensaje: {result.get('message', 'N/A')}")
        print("\n" + "=" * 60)
        return 0
        
    except requests.exceptions.Timeout:
        print("\n   ❌ Error: Timeout - El procesamiento tardó demasiado")
        return 1
    except requests.exceptions.HTTPError as e:
        print(f"\n   ❌ Error HTTP {e.response.status_code}:")
        try:
            error_detail = e.response.json()
            print(f"   {error_detail.get('detail', e.response.text)}")
        except:
            print(f"   {e.response.text}")
        return 1
    except Exception as e:
        print(f"\n   ❌ Error inesperado: {e}")
        return 1

def main():
    # Determinar qué archivo usar
    if len(sys.argv) > 1:
        audio_file = sys.argv[1]
    else:
        audio_file = DEFAULT_AUDIO
    
    exit_code = test_audio_upload(audio_file)
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
