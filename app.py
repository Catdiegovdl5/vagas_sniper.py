from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from database import get_jobs, insert_jobs, init_db
import uvicorn
import os
import asyncio
import logging
from logging.handlers import RotatingFileHandler

app = FastAPI()

# Configuração do Logger Segura (Limpa arquivos maiores que 1MB, guarda apenas 1 backup)
log_path = "C:\\Users\\99196\\OneDrive\\Documentos\\vagas_bot\\system.log"
logger = logging.getLogger("SniperBot")
logger.setLevel(logging.INFO)
handler = RotatingFileHandler(log_path, maxBytes=1000000, backupCount=1, encoding='utf-8')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
handler.setFormatter(formatter)
logger.addHandler(handler)

logger.info("Sistema de Logs Iniciado com Sucesso.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializa o banco de dados caso nao exista
init_db()

STATIC_DIR = "C:\\Users\\99196\\OneDrive\\Documentos\\vagas_bot\\static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/", response_class=HTMLResponse)
def serve_dashboard():
    with open(os.path.join(STATIC_DIR, "index.html"), "r", encoding="utf-8") as f:
        return f.read()

@app.get("/api/jobs")
def api_get_jobs():
    return {"jobs": get_jobs()}

import importlib

@app.post("/api/webhook/n8n")
async def n8n_webhook(request: Request):
    """ Webhook chamado pelo n8n a cada 24h contendo as vagas raspadas """
    data = await request.json()
    jobs = data.get("jobs", [])
    inserted = insert_jobs(jobs)
    return {"status": "success", "inserted": inserted, "total_received": len(jobs)}

@app.post("/api/trigger")
async def trigger_scrapers(request: Request):
    """ Chamado pelo botão 'Hunt Now' do App """
    data = await request.json()
    platforms = data.get("platforms", [])
    keyword = data.get("keyword", "Python")
    level = data.get("level", "Todos")
    
    logger.info(f"Recebida ordem de Varredura! Plataformas: {platforms} | Keyword: {keyword} | Nível: {level}")
    
    all_jobs = []
    
    for plat in platforms:
        try:
            logger.info(f"[{plat.upper()}] Inicializando Scraper...")
            module = importlib.import_module(f"scrapers.{plat}")
            jobs = await asyncio.to_thread(module.scrape, keyword=keyword, level=level)
            all_jobs.extend(jobs)
            logger.info(f"[{plat.upper()}] Sucesso! {len(jobs)} vagas capturadas.")
        except Exception as e:
            logger.error(f"[{plat.upper()}] ERRO CRÍTICO no scraper: {str(e)}")
            
    try:
        inserted = await asyncio.to_thread(insert_jobs, all_jobs)
        logger.info(f"Varredura Finalizada! {len(all_jobs)} vagas totais recebidas. {inserted} novas vagas gravadas no banco de dados.")
        return {"status": "success", "inserted": inserted, "total_found": len(all_jobs)}
    except Exception as e:
        logger.error(f"ERRO DE BANCO DE DADOS ao inserir vagas: {str(e)}")
        return {"status": "error", "message": "Falha no DB"}

@app.get("/api/logs")
def get_logs():
    """ Retorna as últimas 100 linhas de log """
    try:
        if not os.path.exists(log_path):
            return {"logs": ["Nenhum log encontrado ainda."]}
            
        with open(log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        # Pega as ultimas 100 linhas para o frontend
        last_lines = lines[-100:]
        return {"logs": last_lines}
    except Exception as e:
        return {"logs": [f"Erro ao ler log: {str(e)}"]}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
