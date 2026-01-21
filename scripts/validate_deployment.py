"""
Script de validación pre-deployment
Verifica que todos los archivos y configuraciones necesarias estén presentes
"""

import os
import sys
from pathlib import Path

def check_file_exists(filepath, required=True):
    """Verifica si un archivo existe"""
    exists = os.path.exists(filepath)
    status = "✅" if exists else ("❌" if required else "⚠️")
    print(f"{status} {filepath}")
    return exists

def main():
    print("=" * 60)
    print("Pre-Deployment Validation")
    print("=" * 60)
    print()
    
    all_checks_passed = True
    
    print("📁 Archivos requeridos:")
    required_files = [
        "Dockerfile",
        "docker-compose.yml",
        "requirements.txt",
        ".env.example",
        "app/main.py",
        "app/core/config.py",
        "app/services/google_drive.py"
    ]
    
    for file in required_files:
        if not check_file_exists(file):
            all_checks_passed = False
    
    print("\n🔐 Archivos de credenciales:")
    cred_files = [
        ("credentials.json", True),
        ("token.json", False),
        (".env", False)
    ]
    
    for file, required in cred_files:
        exists = check_file_exists(file, required)
        if required and not exists:
            all_checks_passed = False
    
    print("\n📝 Configuración:")
    
    if os.path.exists(".env"):
        print("✅ Archivo .env encontrado")
        with open(".env", "r") as f:
            content = f.read()
            if "GOOGLE_DRIVE_FOLDER_ID=your_folder_id_here" in content:
                print("⚠️  .env contiene valores por defecto, actualízalo")
                all_checks_passed = False
            else:
                print("✅ .env parece estar configurado")
    else:
        print("❌ Archivo .env no encontrado")
        print("   Copia .env.example a .env y configúralo")
        all_checks_passed = False
    
    print("\n" + "=" * 60)
    
    if all_checks_passed:
        print("✅ VALIDACIÓN EXITOSA")
        print("\nTodo listo para deployment!")
        print("\nPróximos pasos:")
        print("1. Si no tienes token.json, ejecuta: python scripts/setup_auth.py")
        print("2. Construir imagen: docker-compose build")
        print("3. Ejecutar: docker-compose up -d")
        return 0
    else:
        print("❌ VALIDACIÓN FALLIDA")
        print("\nRevisa los elementos marcados con ❌ antes de continuar")
        print("Ver DEPLOYMENT.md para más detalles")
        return 1

if __name__ == "__main__":
    sys.exit(main())
