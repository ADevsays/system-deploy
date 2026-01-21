"""
Script para autenticar con Google Drive y generar token.json
Ejecutar antes del primer deployment
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.google_drive import drive_service

def main():
    print("=" * 60)
    print("Google Drive Authentication Setup")
    print("=" * 60)
    print("\nEste script te ayudará a autenticar con Google Drive")
    print("y generar el archivo token.json necesario para el deployment.\n")
    
    try:
        print("Iniciando autenticación...")
        drive_service.authenticate()
        print("\n✅ Autenticación exitosa!")
        print("✅ Archivo token.json generado")
        print("\nAhora puedes:")
        print("1. Copiar credentials.json y token.json a tu VPS")
        print("2. Ejecutar docker-compose up -d --build\n")
        
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print("\nAsegúrate de:")
        print("1. Tener credentials.json en la raíz del proyecto")
        print("2. Haber configurado correctamente la Google Drive API")
        print("\nVer DEPLOYMENT.md para más detalles.\n")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ Error durante la autenticación: {e}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
