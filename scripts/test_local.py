import sys
import os
import requests
import time
from pathlib import Path
import urllib3

# Añadir la raíz del proyecto al path para poder importar app
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

BASE_URL = os.getenv("API_URL", "http://localhost:8000")
SSL_VERIFY = os.getenv("SSL_VERIFY", "true").lower() == "true"

# Deshabilitar warnings de SSL si SSL_VERIFY es False
if not SSL_VERIFY:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_health_check():
    """Test 1: API está corriendo"""
    print("\n🔍 Test 1: Health Check")
    try:
        response = requests.get(f"{BASE_URL}/", verify=SSL_VERIFY)
        assert response.status_code == 200
        assert response.json()["message"] == "API is running"
        print("✅ API está corriendo correctamente")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_task_creation():
    """Test 2: Crear tarea"""
    print("\n🔍 Test 2: Crear Tarea")
    try:
        response = requests.get(f"{BASE_URL}/tasks/init", verify=SSL_VERIFY)
        assert response.status_code == 200
        task_id = response.json()["task_id"]
        print(f"✅ Tarea creada: {task_id}")
        return task_id
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_task_status(task_id):
    """Test 3: Verificar estado de tarea"""
    print(f"\n🔍 Test 3: Verificar Estado de Tarea")
    try:
        response = requests.get(f"{BASE_URL}/status/{task_id}", verify=SSL_VERIFY)
        assert response.status_code == 200
        status = response.json()
        print(f"✅ Estado de tarea obtenido: {status['status']}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_google_drive_config():
    """Test 4: Configuración de Google Drive"""
    print("\n🔍 Test 4: Configuración Google Drive (OAuth Web)")
    
    # Intentar cargar settings
    from app.core.config import settings
    
    checks = {
        "GOOGLE_CLIENT_ID": bool(settings.GOOGLE_CLIENT_ID),
        "GOOGLE_CLIENT_SECRET": bool(settings.GOOGLE_CLIENT_SECRET),
        "GOOGLE_REFRESH_TOKEN": bool(settings.GOOGLE_REFRESH_TOKEN),
        "GOOGLE_DRIVE_FOLDER_ID": bool(settings.GOOGLE_DRIVE_FOLDER_ID)
    }
    
    all_ok = True
    for var, exists in checks.items():
        status = "✅" if exists else "❌"
        print(f"{status} {var}")
        if not exists:
            all_ok = False
    
    if not all_ok:
        print("\n⚠️  Faltan variables de entorno en tu .env")
        print("   Asegúrate de haber ejecutado scripts/get_refresh_token.py")
    
    return all_ok

def test_audio_processing(task_id):
    """Test 5: Procesar audio (opcional, requiere archivo de prueba)"""
    print("\n🔍 Test 5: Procesamiento de Audio")
    
    test_audio_path = "audio.mp3"
    
    if not os.path.exists(test_audio_path):
        print(f"⚠️  Archivo de prueba no encontrado: {test_audio_path}")
        print("   Salta este test (puedes probarlo manualmente después)")
        return None
    
    try:
        with open(test_audio_path, "rb") as f:
            files = {"file": (test_audio_path, f, "audio/mpeg")}
            data = {"task_id": task_id}
            
            print(f"   Procesando {test_audio_path}...")
            response = requests.post(
                f"{BASE_URL}/audio/cut",
                files=files,
                data=data,
                timeout=120,
                verify=SSL_VERIFY
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Audio procesado exitosamente")
                print(f"   Drive Link: {result.get('drive_link', 'N/A')}")
                return True
            else:
                print(f"❌ Error: {response.status_code}")
                print(f"   {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("=" * 60)
    print("Testing Local - Content Processing API")
    print("=" * 60)
    print(f"\nBase URL: {BASE_URL}")
    print(f"SSL Verify: {SSL_VERIFY}")
    print("\nAsegúrate de que la API esté corriendo:")
    print("  uvicorn app.main:app --reload")
    print("  o")
    print("  docker-compose up")
    
    input("\nPresiona Enter para continuar...")
    
    results = {
        "health": False,
        "task_creation": False,
        "task_status": False,
        "google_drive": False,
        "audio_processing": None
    }
    
    # Test 1: Health Check
    results["health"] = test_health_check()
    if not results["health"]:
        print("\n❌ La API no está respondiendo. Verifica que esté corriendo.")
        return 1
    
    # Test 2: Crear tarea
    task_id = test_task_creation()
    results["task_creation"] = task_id is not None
    
    # Test 3: Estado de tarea
    if task_id:
        results["task_status"] = test_task_status(task_id)
    
    # Test 4: Google Drive
    results["google_drive"] = test_google_drive_config()
    
    # Test 5: Procesar audio (opcional)
    if task_id and results["google_drive"]:
        results["audio_processing"] = test_audio_processing(task_id)
    
    # Resumen
    print("\n" + "=" * 60)
    print("RESUMEN DE TESTS")
    print("=" * 60)
    
    for test, result in results.items():
        if result is None:
            status = "⏭️ "
        elif result:
            status = "✅"
        else:
            status = "❌"
        print(f"{status} {test.replace('_', ' ').title()}")
    
    print("\n" + "=" * 60)
    
    critical_tests = ["health", "task_creation", "task_status", "google_drive"]
    all_critical_passed = all(results[t] for t in critical_tests)
    
    if all_critical_passed:
        print("✅ TESTS CRÍTICOS PASADOS")
        print("\n¡Tu API está lista para deployment!")
        print("\nPróximos pasos:")
        print("1. Sube tu archivo .env configurado al VPS")
        print("2. docker-compose up -d --build")
        print("3. Probar en producción")
        return 0
    else:
        print("❌ ALGUNOS TESTS FALLARON")
        print("\nRevisa los errores antes de deployar")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests cancelados por el usuario")
        sys.exit(1)
