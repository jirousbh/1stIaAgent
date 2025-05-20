from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import httpx
import os
import json
import asyncio

router = APIRouter()

class PromptRequest(BaseModel):
    prompt: str
    model: str = "tinyllama"  # Alterado para tinyllama como padrão
    system_prompt: str = "Você é um assistente útil e amigável."
    max_tokens: int = 1000
    temperature: float = 0.7

class PromptResponse(BaseModel):
    text: str
    model: str

@router.post("/generate", response_model=PromptResponse)
async def generate_text(request: PromptRequest):
    """
    Gera texto usando modelos LLM via Ollama
    """
    try:
        ollama_host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{ollama_host}/api/generate",
                json={
                    "model": request.model,
                    "prompt": request.prompt,
                    "system": request.system_prompt,
                    "options": {
                        "temperature": request.temperature,
                        "num_predict": request.max_tokens
                    }
                },
                headers={"Accept": "application/json"}
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="Erro ao chamar o Ollama API")
            
            # A resposta do Ollama é retornada como múltiplos objetos JSON
            # Vamos concatenar todas as respostas de texto
            full_response = ""
            
            # Dividir a resposta em linhas e processar cada objeto JSON
            try:
                lines = response.text.strip().split("\n")
                for line in lines:
                    if not line:
                        continue
                    
                    chunk = json.loads(line)
                    if "response" in chunk:
                        full_response += chunk["response"]
                        
                        # Se o modelo finalizou a geração, podemos parar
                        if chunk.get("done", False):
                            break
            except json.JSONDecodeError as e:
                # Em caso de erro no parsing JSON, retornar a resposta bruta
                return PromptResponse(text=f"Erro no parsing JSON: {str(e)}\nResposta bruta: {response.text[:100]}...", model=request.model)
            
            return PromptResponse(text=full_response, model=request.model)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro: {str(e)}")

@router.post("/stream")
async def stream_text(request: PromptRequest):
    """
    Gera texto usando modelos LLM via Ollama com streaming
    """
    async def generate_stream():
        try:
            ollama_host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
            
            # Criar um cliente com um timeout maior para streaming
            async with httpx.AsyncClient(timeout=300.0) as client:
                # Iniciar a requisição de streaming
                async with client.stream(
                    "POST",
                    f"{ollama_host}/api/generate",
                    json={
                        "model": request.model,
                        "prompt": request.prompt,
                        "system": request.system_prompt,
                        "stream": True,  # Ativar streaming
                        "options": {
                            "temperature": request.temperature,
                            "num_predict": request.max_tokens
                        }
                    },
                    headers={"Accept": "application/json"}
                ) as response:
                    if response.status_code != 200:
                        error_detail = await response.text()
                        error_msg = json.dumps({"error": f"Erro na API Ollama: {error_detail}"})
                        yield f"data: {error_msg}\n\n"
                        return
                    
                    # Processar cada chunk da resposta
                    async for chunk in response.aiter_text():
                        if not chunk.strip():
                            continue
                        
                        try:
                            # Cada linha é um objeto JSON separado
                            for line in chunk.strip().split("\n"):
                                if not line:
                                    continue
                                    
                                data = json.loads(line)
                                # Enviar apenas a parte da resposta
                                if "response" in data:
                                    # Formato SSE (Server-Sent Events)
                                    # Enviar apenas a parte da resposta atual
                                    yield f"data: {json.dumps({'text': data['response'], 'done': data.get('done', False)})}\n\n"
                                    
                                    # Se a geração foi concluída, finalizar o stream
                                    if data.get("done", False):
                                        break
                                        
                        except json.JSONDecodeError as e:
                            yield f"data: {json.dumps({'error': f'Erro no parsing JSON: {str(e)}'})}\n\n"
                    
                    # Sinalizar o fim do streaming
                    yield f"data: {json.dumps({'done': True})}\n\n"
                    
        except Exception as e:
            yield f"data: {json.dumps({'error': f'Erro: {str(e)}'})}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"
    
    # Retornar a resposta de streaming
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

@router.get("/models")
async def list_models():
    """
    Lista os modelos disponíveis no Ollama
    """
    try:
        ollama_host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{ollama_host}/api/tags")
            
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="Erro ao listar modelos do Ollama")
            
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro: {str(e)}")

@router.post("/pull/{model_name}")
async def pull_model(model_name: str):
    """
    Faz o download de um modelo do Ollama
    """
    try:
        ollama_host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        async with httpx.AsyncClient(timeout=600.0) as client:
            response = await client.post(
                f"{ollama_host}/api/pull",
                json={"name": model_name}
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="Erro ao baixar o modelo")
            
            return {"status": "success", "message": f"Modelo {model_name} baixado com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro: {str(e)}") 