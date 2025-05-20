import os
import asyncio
from pathlib import Path
import tempfile
import shutil

async def generate_tts_coqui(text: str, voice: str, output_path: str, speed: float = 1.0) -> bool:
    """
    Gera áudio a partir de texto usando Coqui TTS
    
    Args:
        text: Texto para conversão
        voice: Modelo de voz a ser usado
        output_path: Caminho para salvar o arquivo de áudio
        speed: Velocidade da fala (1.0 é normal)
    
    Returns:
        bool: True se gerado com sucesso, False caso contrário
    """
    try:
        # Importar TTS apenas quando necessário para evitar carregar modelos em memória desnecessariamente
        from TTS.api import TTS
        
        # Mapeamento de vozes para modelos (simplificado)
        voice_models = {
            "pt_br_female": "tts_models/pt/cv/vits",
            "pt_br_male": "tts_models/pt/cv/vits",
            "en_us_female": "tts_models/en/ljspeech/tacotron2-DDC",
            "en_us_male": "tts_models/en/vctk/vits"
        }
        
        # Verificar se a voz existe
        if voice not in voice_models:
            print(f"Voz {voice} não encontrada, usando pt_br_female como padrão")
            model_name = voice_models["pt_br_female"]
        else:
            model_name = voice_models[voice]
        
        # Inicializar TTS em uma thread separada para não bloquear o event loop
        def _generate():
            tts = TTS(model_name=model_name)
            tts.tts_to_file(text=text, file_path=output_path, speed=speed)
            return True
        
        # Executar em um ThreadPool pois TTS não é async-friendly
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, _generate)
        
        return os.path.exists(output_path)
    except Exception as e:
        print(f"Erro ao gerar TTS com Coqui: {str(e)}")
        return False

async def generate_tts_piper(text: str, voice: str, output_path: str, speed: float = 1.0) -> bool:
    """
    Gera áudio a partir de texto usando Piper TTS
    
    Args:
        text: Texto para conversão
        voice: Modelo de voz a ser usado
        output_path: Caminho para salvar o arquivo de áudio
        speed: Velocidade da fala (1.0 é normal)
    
    Returns:
        bool: True se gerado com sucesso, False caso contrário
    """
    try:
        # Mapeamento de vozes para modelos do Piper (simplificado)
        voice_models = {
            "pt_BR-22050": "pt_BR-bahiana-medium.onnx",
            "en_US-22050": "en_US-lessac-medium.onnx"
        }
        
        # Verificar se a voz existe
        if voice not in voice_models:
            print(f"Voz {voice} não encontrada, usando pt_BR-22050 como padrão")
            voice_model = voice_models["pt_BR-22050"]
        else:
            voice_model = voice_models[voice]
        
        # Criar diretório temporário para texto
        temp_dir = tempfile.mkdtemp()
        text_file = os.path.join(temp_dir, "input.txt")
        
        # Salvar texto em arquivo
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write(text)
        
        # Configurar caminho para modelo
        model_path = f"/app/models/piper/{voice_model}"
        
        # Preparar comando, ajustando a velocidade
        command = f"piper --model {model_path} --output_file {output_path} --text_file {text_file}"
        
        if speed != 1.0:
            command += f" --speaker-speed {speed}"
        
        # Executar comando em um subprocesso
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        # Limpar arquivo temporário
        shutil.rmtree(temp_dir)
        
        if process.returncode != 0:
            print(f"Erro no Piper TTS: {stderr.decode()}")
            return False
            
        return os.path.exists(output_path)
    except Exception as e:
        print(f"Erro ao gerar TTS com Piper: {str(e)}")
        if 'temp_dir' in locals():
            shutil.rmtree(temp_dir)
        return False 