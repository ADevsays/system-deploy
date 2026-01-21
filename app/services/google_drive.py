import os
import io
import logging
from typing import Optional
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload
from app.core.config import settings

logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/drive.file']

class GoogleDriveService:
    def __init__(self):
        self.creds: Optional[Credentials] = None
        self.service = None
        
    def authenticate(self):
        """
        Autentica con Google Drive usando Refresh Token para modo desatendido (VPS).
        Si no hay Refresh Token, intenta usar el flujo tradicional de archivos.
        """
        # Prioridad: Variables de entorno (Ideal para VPS/Docker)
        if settings.GOOGLE_REFRESH_TOKEN and settings.GOOGLE_CLIENT_ID:
            logger.info("Authenticating using environment Refresh Token...")
            self.creds = Credentials(
                None,  # El access token se generará automáticamente al refrescar
                refresh_token=settings.GOOGLE_REFRESH_TOKEN,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=settings.GOOGLE_CLIENT_ID,
                client_secret=settings.GOOGLE_CLIENT_SECRET,
                scopes=SCOPES
            )
            # IMPORTANTE: Refrescar inmediatamente para obtener el access token
            try:
                logger.info("Refreshing access token from refresh token...")
                self.creds.refresh(Request())
                logger.info("Access token obtained successfully")
            except Exception as e:
                logger.error(f"Failed to refresh token: {str(e)}")
                raise Exception(f"Failed to refresh access token: {str(e)}")
        else:
            # Fallback: Archivo token.json (Útil para desarrollo local)
            token_path = 'token.json'
            if os.path.exists(token_path):
                logger.info("Loading credentials from token.json...")
                self.creds = Credentials.from_authorized_user_file(token_path, SCOPES)
            else:
                logger.error("No valid credentials found. Please provide GOOGLE_REFRESH_TOKEN in .env")
                raise Exception("Authentication required: No credentials available")
        
        # Validar que tenemos credenciales válidas
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                logger.info("Credentials expired, refreshing...")
                self.creds.refresh(Request())
            else:
                logger.error("No valid credentials after authentication attempt")
                raise Exception("Authentication required")
        
        self.service = build('drive', 'v3', credentials=self.creds)
        logger.info("Google Drive authentication successful")

    
    def upload_file(self, file_path: str, filename: str, mime_type: str = 'audio/mpeg') -> str:
        """
        Sube un archivo a Google Drive y retorna el enlace compartido.
        
        Args:
            file_path: Ruta local del archivo a subir
            filename: Nombre con el que se guardará en Drive
            mime_type: Tipo MIME del archivo
            
        Returns:
            URL pública del archivo en Google Drive
        """
        # Autenticar automáticamente si no está autenticado
        if not self.service:
            logger.info("Service not initialized, authenticating...")
            self.authenticate()
        
        if not settings.GOOGLE_DRIVE_FOLDER_ID:
            raise ValueError("GOOGLE_DRIVE_FOLDER_ID not configured in .env")
        
        try:
            file_metadata = {
                'name': filename,
                'parents': [settings.GOOGLE_DRIVE_FOLDER_ID]
            }
            
            media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)
            
            logger.info(f"Uploading {filename} to Google Drive...")
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            
            file_id = file.get('id')
            logger.info(f"File uploaded successfully with ID: {file_id}")
            
            # Hacer el archivo público
            self.service.permissions().create(
                fileId=file_id,
                body={'type': 'anyone', 'role': 'reader'}
            ).execute()
            
            # Retornar enlace público
            return f"https://drive.google.com/file/d/{file_id}/view?usp=sharing"
            
        except Exception as e:
            logger.error(f"Error uploading file to Google Drive: {str(e)}")
            raise

drive_service = GoogleDriveService()
