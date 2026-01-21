"""
Script para obtener el Refresh Token de Google Drive (Web App Flow)
Este script te ayuda a obtener el GOOGLE_REFRESH_TOKEN necesario para el archivo .env
"""

import os
import sys

# Asegurar que podemos importar app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google_auth_oauthlib.flow import Flow
from app.core.config import settings

def main():
    print("=" * 60)
    print("Google Drive Refresh Token Generator (Web App Approach)")
    print("=" * 60)

    # 1. Configuración desde .env
    client_id = settings.GOOGLE_CLIENT_ID
    client_secret = settings.GOOGLE_CLIENT_SECRET
    redirect_uri = settings.GOOGLE_REDIRECT_URI
    
    if not client_id or not client_secret:
        print(settings.GOOGLE_CLIENT_ID)
        print(settings.GOOGLE_CLIENT_SECRET)
        print("\n❌ ERROR: Debes configurar GOOGLE_CLIENT_ID y GOOGLE_CLIENT_SECRET en tu .env")
        print("Obtén estos valores desde Google Cloud Console (la captura que enviaste).")
        return

    # 2. Configurar el flujo
    client_config = {
        "web": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }

    flow = Flow.from_client_config(
        client_config,
        scopes=[
            'https://www.googleapis.com/auth/drive',
            'https://www.googleapis.com/auth/drive.file',
            'https://www.googleapis.com/auth/drive.appdata',
            'https://www.googleapis.com/auth/drive.photos.readonly'
        ],
        redirect_uri=redirect_uri
    )

    # 3. Generar URL de autorización
    auth_url, _ = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent' # Forzar para asegurar que devuelva refresh_token
    )

    print("\n1. Abre esta URL en tu navegador y autoriza el acceso:")
    print(f"\n{auth_url}")
    
    print("\n2. Después de autorizar, serás redirigido a una URL que no cargará (o dará error).")
    print("   ¡No importa! Copia el valor del parámetro 'code' de esa URL.")
    print("   Ejemplo: https://.../callback?code=4/0AfgeXhw...&scope=...")
    
    print("\n3. Pega el código aquí:")
    code = input("\n> ").strip()

    if not code:
        print("❌ Operación cancelada.")
        return

    # 4. Intercambiar código por tokens
    try:
        flow.fetch_token(code=code)
        refresh_token = flow.credentials.refresh_token
        
        print("\n" + "=" * 60)
        print("✅ ¡ÉXITO! Aquí tienes tus variables para el archivo .env:")
        print("=" * 60)
        print(f"\nGOOGLE_REFRESH_TOKEN={refresh_token}")
        print("\nCopia este valor en tu archivo .env en el VPS.")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ ERROR al intercambiar el código: {str(e)}")
        print("Causas comunes: el código expiró o el Redirect URI no coincide exactamente.")

if __name__ == "__main__":
    main()
