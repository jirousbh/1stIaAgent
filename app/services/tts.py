import os
import asyncio
from pathlib import Path
import tempfile
import shutil
import logging
import subprocess

# Lista de modelos Piper para download
PIPER_MODELS = {
    "pt_BR-edresson-low.onnx": "https://huggingface.co/rhasspy/piper-voices/resolve/main/pt/pt_BR/edresson/low/pt_BR-edresson-low.onnx",
    "pt_BR-edresson-low.onnx.json": "https://huggingface.co/rhasspy/piper-voices/resolve/main/pt/pt_BR/edresson/low/pt_BR-edresson-low.onnx.json",
    "en_US-lessac-medium.onnx": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx",
    "en_US-lessac-medium.onnx.json": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json"
}

def ensure_directories():
    """Garante que os diretórios necessários existam"""
    os.makedirs("app/models/piper", exist_ok=True)
    os.makedirs("app/static/audio", exist_ok=True)

def download_piper_models():
    """Baixa os modelos Piper TTS se não existirem"""
    ensure_directories()
    
    import requests
    
    models_dir = Path("app/models/piper")
    
    for model_file, model_url in PIPER_MODELS.items():
        model_path = models_dir / model_file
        if not model_path.exists():
            try:
                logging.info(f"Baixando modelo {model_file}...")
                response = requests.get(model_url, stream=True)
                response.raise_for_status()  # Verificar se o download foi bem-sucedido
                
                # Salvar o arquivo
                with open(model_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                logging.info(f"Modelo {model_file} baixado com sucesso")
            except Exception as e:
                logging.error(f"Erro ao baixar modelo {model_file}: {str(e)}")

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
        # Garantir que o diretório de saída existe
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Importar TTS apenas quando necessário para evitar carregar modelos em memória desnecessariamente
        from TTS.api import TTS
        
        # Mapeamento de vozes para modelos (simplificado)
        voice_models = {
            "pt_br_female": "tts_models/pt/cv/vits",   # Modelo português - mesmo para masculino e feminino
            "pt_br_male": "tts_models/pt/cv/vits",     # Vamos diferenciar no frontend apenas
            "en_us_female": "tts_models/en/ljspeech/tacotron2-DDC",
            "en_us_male": "tts_models/en/vctk/vits"
        }
        
        # Verificar se a voz existe
        if voice not in voice_models:
            logging.warning(f"Voz {voice} não encontrada, usando pt_br_female como padrão")
            model_name = voice_models["pt_br_female"]
        else:
            model_name = voice_models[voice]
        
        logging.info(f"Iniciando geração de TTS com o modelo Coqui: {model_name}")
        
        # Inicializar TTS em uma thread separada para não bloquear o event loop
        def _generate():
            try:
                # Carregar o modelo de TTS
                tts = TTS(model_name=model_name)
                
                # Verificar se o modelo suporta múltiplos speakers
                if hasattr(tts, "speakers") and tts.speakers and "en/vctk" in model_name:
                    logging.info(f"Modelo {model_name} suporta múltiplos speakers: {tts.speakers}")
                    
                    # Apenas para o modelo VCTK inglês
                    if voice == "en_us_female" and "p282" in tts.speakers:
                        selected_speaker = "p282"  # Feminino
                    else:
                        selected_speaker = "p299"  # Masculino
                        
                    logging.info(f"Usando speaker {selected_speaker} para {voice}")
                    tts.tts_to_file(text=text, file_path=output_path, speed=speed, 
                                    speaker=selected_speaker)
                else:
                    # Modelo sem múltiplos speakers ou não é VCTK
                    logging.info(f"Modelo {model_name} não suporta múltiplos speakers ou não é VCTK")
                    tts.tts_to_file(text=text, file_path=output_path, speed=speed)
                
                return True
            except Exception as e:
                logging.error(f"Erro interno ao gerar TTS com Coqui: {str(e)}")
                
                # Tentar com um modelo alternativo conhecido por ser estável
                try:
                    fallback_model = "tts_models/en/ljspeech/tacotron2-DDC"
                    logging.info(f"Tentando gerar com modelo alternativo: {fallback_model}")
                    fallback_tts = TTS(model_name=fallback_model)
                    fallback_tts.tts_to_file(text=text, file_path=output_path, speed=speed)
                    return True
                except Exception as fallback_error:
                    logging.error(f"Erro também com modelo alternativo: {str(fallback_error)}")
                    return False
        
        # Executar em um ThreadPool pois TTS não é async-friendly
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, _generate)
        
        success = os.path.exists(output_path) and os.path.getsize(output_path) > 0
        if success:
            logging.info(f"Áudio TTS Coqui gerado com sucesso: {output_path}")
        else:
            logging.error(f"Falha ao gerar áudio TTS Coqui: arquivo não existe ou está vazio - {output_path}")
            
        return success
    except Exception as e:
        logging.error(f"Erro ao gerar TTS com Coqui: {str(e)}")
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
        # Garantir que o diretório de saída existe
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Mapeamento de vozes para modelos do Piper (simplificado)
        voice_models = {
            "pt_BR-16000": "pt_BR-edresson-low.onnx",
            "en_US-22050": "en_US-lessac-medium.onnx"
        }
        
        # Verificar se a voz existe
        if voice not in voice_models:
            logging.warning(f"Voz {voice} não encontrada, usando pt_BR-16000 como padrão")
            voice_model = voice_models["pt_BR-16000"]
        else:
            voice_model = voice_models[voice]
        
        # Garantir que o diretório de modelos existe
        ensure_directories()
        
        # Configurar caminho para modelo
        model_path = f"/app/app/models/piper/{voice_model}"
        
        # Verificar se o modelo existe
        if not os.path.exists(model_path):
            download_piper_models()
            
            # Verificar novamente após tentativa de download
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Modelo {voice_model} não encontrado após tentativa de download")
        
        logging.info(f"Gerando áudio com Piper TTS usando modelo: {model_path}")
        
        # Usar a biblioteca Python piper-tts em vez do comando de linha
        def _generate():
            try:
                # Importar apenas quando necessário para evitar sobrecarga
                import wave
                from piper.voice import PiperVoice
                
                # Carregar voz do modelo
                voice = PiperVoice.load(model_path)
                
                # Abrir arquivo WAV para escrita
                wav_file = wave.open(output_path, "w")
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(voice.config.sample_rate)  # Taxa de amostragem do modelo
                
                # Gerar áudio
                voice.synthesize(text, wav_file)
                
                # Fechar o arquivo
                wav_file.close()
                
                return True
            except Exception as e:
                logging.error(f"Erro interno na geração TTS com Piper: {str(e)}")
                return False
        
        # Executar em um ThreadPool pois pode não ser async-friendly
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, _generate)
        
        success = os.path.exists(output_path)
        if success:
            logging.info(f"Áudio TTS Piper gerado com sucesso: {output_path}")
        else:
            logging.error(f"Falha ao gerar áudio TTS Piper: arquivo não existe - {output_path}")
            
        return success
    except Exception as e:
        logging.error(f"Erro ao gerar TTS com Piper: {str(e)}")
        return False 