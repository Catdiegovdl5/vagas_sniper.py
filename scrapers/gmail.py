import os
import re
from bs4 import BeautifulSoup
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import base64

# Definimos que o robô só pode ler e-mails, para segurança
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def scrape(keyword, level="Todos", country="Brasil"):
    creds = None
    
    # O token armazena o acesso persistente do usuário.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        
    # Se não houver credencial válida, pede para o usuário logar
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('credentials.json'):
                print("ERRO: O arquivo credentials.json não foi encontrado. O Agente de Navegação não baixou?")
                return []
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
            
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    jobs = []
    try:
        service = build('gmail', 'v1', credentials=creds)
        
        # Busca usando a sintaxe nativa do Gmail
        query = 'subject:vaga OR subject:alert'
        results = service.users().messages().list(userId='me', q=query, maxResults=5).execute()
        messages = results.get('messages', [])

        for msg in messages:
            msg_data = service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
            
            payload = msg_data.get('payload', {})
            parts = payload.get('parts', [])
            
            body = ""
            if parts:
                for part in parts:
                    if part.get('mimeType') == 'text/html':
                        data = part['body'].get('data')
                        if data:
                            body = base64.urlsafe_b64decode(data).decode('utf-8')
                        break
            else:
                data = payload.get('body', {}).get('data')
                if data:
                    body = base64.urlsafe_b64decode(data).decode('utf-8')

            if not body:
                continue

            soup = BeautifulSoup(body, 'html.parser')
            links = soup.find_all('a')
            
            for a in links:
                href = a.get('href', '')
                text = a.text.strip()
                
                if ("jobs/view" in href or "viewjob" in href or "job-post" in href or "rc/clk" in href):
                    if len(text) > 4:
                        jobs.append({
                            "platform": "Gmail API",
                            "title": text,
                            "company": "Notificação por E-mail",
                            "budget": "A Combinar",
                            "link": href,
                            "job_type": "Diversos",
                            "profession": keyword,
                            "level": level,
                            "requirements": "Vaga coletada pela API Oficial do Google."
                        })

    except Exception as e:
        print(f"Erro no scraper Gmail API: {e}")

    unique_jobs = {j["link"]: j for j in jobs}
    return list(unique_jobs.values())[:20]
