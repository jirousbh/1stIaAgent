from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
import os
import tempfile
import shutil
from pathlib import Path
import uuid

# Serviço Whisper
from app.services.stt import transcribe_audio

router = APIRouter()

class TranscriptionResponse(BaseModel):
    text: str
    language: str
    model: str

@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_speech(
    file: UploadFile = File(...),
    model: str = Form("base"),  # tiny, base, small, medium, large
    language: str = Form(None)  # Código do idioma (pt, en, etc.) ou None para auto-detecção
):
    """
    Transcreve áudio para texto usando Whisper
    """
    try:
        # Verificar extensão do arquivo
        allowed_extensions = [".mp3", ".wav", ".ogg", ".flac", ".m4a"]
        file_extension = os.path.splitext(file.filename)[1].lower()
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"Tipo de arquivo não suportado. Use: {', '.join(allowed_extensions)}"
            )
        
        # Salvar arquivo temporariamente
        temp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(temp_dir, f"audio{file_extension}")
        
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Transcrever áudio
        result = await transcribe_audio(
            audio_path=temp_file_path,
            model_name=model,
            language=language
        )
        
        # Limpar arquivos temporários
        shutil.rmtree(temp_dir)
        
        if not result:
            raise HTTPException(status_code=500, detail="Falha na transcrição")
        
        return TranscriptionResponse(
            text=result["text"],
            language=result["language"],
            model=model
        )
    except Exception as e:
        # Garantir limpeza em caso de erro
        if 'temp_dir' in locals():
            shutil.rmtree(temp_dir)
        raise HTTPException(status_code=500, detail=f"Erro: {str(e)}")

@router.get("/models")
async def list_models():
    """
    Lista os modelos disponíveis do Whisper
    """
    models = [
        {"name": "tiny", "description": "Muito rápido, baixa precisão"},
        {"name": "base", "description": "Rápido, precisão moderada"},
        {"name": "small", "description": "Equilíbrio entre velocidade e precisão"},
        {"name": "medium", "description": "Mais preciso, moderadamente lento"},
        {"name": "large", "description": "Mais preciso de todos, lento"}
    ]
    
    return models 