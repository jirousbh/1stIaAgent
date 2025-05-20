import os
import asyncio
from pathlib import Path
import tempfile
import shutil
from typing import Dict, Optional, Union

async def transcribe_audio(
    audio_path: str,
    model_name: str = "base", 
    language: Optional[str] = None
) -> Optional[Dict[str, str]]:
    """
    Transcreve áudio para texto usando Whisper
    
    Args:
        audio_path: Caminho para o arquivo de áudio
        model_name: Nome do modelo Whisper (tiny, base, small, medium, large)
        language: Código do idioma (pt, en, etc.) ou None para auto-detecção
    
    Returns:
        Dict com texto transcrito e idioma detectado, ou None em caso de erro
    """
    try:
        # Importar Whisper apenas quando necessário
        import whisper
        
        # Validar modelo
        valid_models = ["tiny", "base", "small", "medium", "large"]
        if model_name not in valid_models:
            print(f"Modelo {model_name} não é válido, usando 'base'")
            model_name = "base"
        
        # Função para carregar modelo e fazer transcrição (não assíncrona)
        def _transcribe():
            # Carregar modelo
            model = whisper.load_model(model_name)
            
            # Configurar opções de transcrição
            options = {}
            if language:
                options["language"] = language
            
            # Transcerver o áudio
            if language:
                result = model.transcribe(audio_path, language=language)
            else:
                result = model.transcribe(audio_path)
            
            return {
                "text": result["text"],
                "language": result["language"]
            }
        
        # Executar em um ThreadPool, pois Whisper não é async-friendly
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, _transcribe)
        
        return result
    except Exception as e:
        print(f"Erro na transcrição com Whisper: {str(e)}")
        return None 