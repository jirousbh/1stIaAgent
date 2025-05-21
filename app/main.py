import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Importar routers
from app.routers import llm, tts, stt, vision

# Importar funções para inicialização dos modelos TTS
from app.services.tts import ensure_directories, download_piper_models

# Criar aplicação FastAPI
app = FastAPI(
    title="AI Agent",
    description="Um agente de IA com múltiplas capacidades: LLM, STT, TTS e processamento de imagens",
    version="0.1.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar arquivos estáticos e configurar templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Incluir routers
app.include_router(llm.router, prefix="/api/llm", tags=["LLM"])
app.include_router(tts.router, prefix="/api/tts", tags=["TTS"])
app.include_router(stt.router, prefix="/api/stt", tags=["STT"])
app.include_router(vision.router, prefix="/api/vision", tags=["Vision"])

@app.on_event("startup")
async def startup_event():
    """Executado na inicialização do aplicativo"""
    logging.info("Iniciando a aplicação...")
    
    # Garantir que os diretórios necessários existam
    ensure_directories()
    
    # Baixar modelos TTS se não existirem
    download_piper_models()
    
    logging.info("Aplicação inicializada com sucesso")

@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 