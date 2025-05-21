from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
import tempfile
import uuid
from pathlib import Path

# Serviços TTS
from app.services.tts import generate_tts_coqui, generate_tts_piper

router = APIRouter()

class TTSRequest(BaseModel):
    text: str
    voice: str = "pt_br_female"  # Voz padrão
    engine: str = "coqui"  # Engine: coqui ou piper
    speed: float = 1.0

@router.post("/generate")
async def generate_speech(request: TTSRequest, background_tasks: BackgroundTasks):
    """
    Gera áudio a partir de texto usando TTS
    """
    try:
        # Criar diretório temporário para armazenar áudios
        os.makedirs("app/static/audio", exist_ok=True)
        
        # Gerar nome de arquivo único
        file_id = str(uuid.uuid4())
        output_path = f"app/static/audio/{file_id}.wav"
        
        # Selecionar engine apropriada
        if request.engine.lower() == "coqui":
            success = await generate_tts_coqui(
                text=request.text,
                voice=request.voice,
                output_path=output_path,
                speed=request.speed
            )
        elif request.engine.lower() == "piper":
            success = await generate_tts_piper(
                text=request.text,
                voice=request.voice,
                output_path=output_path,
                speed=request.speed
            )
        else:
            raise HTTPException(status_code=400, detail=f"Engine TTS não suportada: {request.engine}")
        
        if not success:
            raise HTTPException(status_code=500, detail="Falha ao gerar áudio")
        
        # Configurar limpeza automática do arquivo após 1 hora
        background_tasks.add_task(cleanup_file, output_path, delay=3600)
        
        return {
            "success": True,
            "file_url": f"/static/audio/{file_id}.wav",
            "engine": request.engine,
            "voice": request.voice
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro: {str(e)}")

@router.get("/voices")
async def list_voices():
    """
    Lista as vozes disponíveis para TTS
    """
    voices = {
        "coqui": [
            "pt_br_female",
            "pt_br_male",
            "en_us_female",
            "en_us_male"
        ],
        "piper": [
            "pt_BR-16000",
            "en_US-22050"
        ]
    }
    
    return voices

async def cleanup_file(file_path: str, delay: int = 3600):
    """
    Remove um arquivo após um determinado tempo
    """
    import asyncio
    await asyncio.sleep(delay)
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except:
        pass 