import os
import base64
from email.mime.text import MIMEText
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from tools.excepciones import GmailNoDisponibleError
from googleapiclient.errors import HttpError

SCOPES = ['https://www.googleapis.com/auth/gmail.send',
          'https://www.googleapis.com/auth/gmail.readonly']

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CREDENTIALS_FILE = os.path.join(BASE_DIR, 'credentials.json')
TOKEN_FILE = os.path.join(BASE_DIR, 'token.json')

def get_gmail_service():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

    return build('gmail', 'v1', credentials=creds)


def enviar_correo(destinatario: str, asunto: str, cuerpo: str):
    try:
     service = get_gmail_service()
     message = MIMEText(cuerpo)
     message['to'] = destinatario
     message['subject'] = asunto
     raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

     resultado = service.users().messages().send(
        userId='me',
        body={'raw': raw}
    ).execute()
     return resultado
    except HttpError as e:
        raise GmailNoDisponibleError(f"Error de la API de Gmail: {e}") from e
    except Exception as e:
        raise GmailNoDisponibleError(f"No se pudo conectar con Gmail: {e}") from e


def consultar_correos(max_resultados: int = 5):
    try:
     service = get_gmail_service()
     resultados = service.users().messages().list(
        userId='me', maxResults=max_resultados
     ).execute()
     mensajes = resultados.get('messages', [])

     lista_correos = []
     for msg in mensajes:
        detalle = service.users().messages().get(userId='me', id=msg['id']).execute()
        headers = detalle['payload']['headers']
        asunto = next((h['value'] for h in headers if h['name'] == 'Subject'), '(sin asunto)')
        remitente = next((h['value'] for h in headers if h['name'] == 'From'), '(desconocido)')
        lista_correos.append({
            'id': msg['id'],
            'asunto': asunto,
            'remitente': remitente,
            'snippet': detalle.get('snippet', '')
    })
     return lista_correos
    except HttpError as e:
        raise GmailNoDisponibleError(f"Error de la API de Gmail: {e}") from e
    except Exception as e:
        raise GmailNoDisponibleError(f"No se pudo conectar con Gmail: {e}") from e

def consultar_correos_por_criterio(query: str, max_resultados: int = 10):
    """
    Busca correos usando la sintaxis de búsqueda de Gmail.
    Ejemplos de query:
      - 'from:cliente@gmail.com' o 'to:cliente@gmail.com' (correos de/para un cliente)
      - 'subject:factura' (correos con esa palabra en el asunto)
      - 'INV/2026/00005' (buscar el número de una factura en el contenido)
    """
    try:
        service = get_gmail_service()
        resultados = service.users().messages().list(
            userId='me', q=query, maxResults=max_resultados
        ).execute()
        mensajes = resultados.get('messages', [])

        lista_correos = []
        for msg in mensajes:
            detalle = service.users().messages().get(userId='me', id=msg['id']).execute()
            headers = detalle['payload']['headers']
            asunto = next((h['value'] for h in headers if h['name'] == 'Subject'), '(sin asunto)')
            remitente = next((h['value'] for h in headers if h['name'] == 'From'), '(desconocido)')
            destinatario = next((h['value'] for h in headers if h['name'] == 'To'), '(desconocido)')
            fecha = next((h['value'] for h in headers if h['name'] == 'Date'), '')
            lista_correos.append({
                'id': msg['id'],
                'asunto': asunto,
                'remitente': remitente,
                'destinatario': destinatario,
                'fecha': fecha,
                'snippet': detalle.get('snippet', '')
            })
        return lista_correos
    except HttpError as e:
        raise GmailNoDisponibleError(f"Error de la API de Gmail al buscar correos: {e}") from e
    except Exception as e:
        raise GmailNoDisponibleError(f"No se pudo conectar con Gmail: {e}") from e