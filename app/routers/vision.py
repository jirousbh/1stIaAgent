from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
import os
import tempfile
import shutil
from pathlib import Path
import uuid
from typing import List, Optional

# Serviços de visão computacional
from app.services.vision import (
    generate_image_caption,
    extract_image_features,
    classify_image,
    search_similar_images
)

router = APIRouter()

class CaptionResponse(BaseModel):
    caption: str
    model: str

class ClassificationResponse(BaseModel):
    categories: List[dict]
    model: str

class FeatureResponse(BaseModel):
    success: bool
    feature_id: str
    model: str

@router.post("/caption", response_model=CaptionResponse)
async def get_image_caption(
    file: UploadFile = File(...),
    model: str = Form("blip2")
):
    """
    Gera uma descrição para a imagem usando BLIP-2
    """
    try:
        # Verificar extensão do arquivo
        allowed_extensions = [".jpg", ".jpeg", ".png", ".webp"]
        file_extension = os.path.splitext(file.filename)[1].lower()
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"Tipo de arquivo não suportado. Use: {', '.join(allowed_extensions)}"
            )
        
        # Salvar arquivo temporariamente
        temp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(temp_dir, f"image{file_extension}")
        
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Gerar legenda para a imagem
        caption = await generate_image_caption(
            image_path=temp_file_path,
            model_name=model
        )
        
        # Limpar arquivos temporários
        shutil.rmtree(temp_dir)
        
        if not caption:
            raise HTTPException(status_code=500, detail="Falha ao gerar legenda")
        
        return CaptionResponse(
            caption=caption,
            model=model
        )
    except Exception as e:
        # Garantir limpeza em caso de erro
        if 'temp_dir' in locals():
            shutil.rmtree(temp_dir)
        raise HTTPException(status_code=500, detail=f"Erro: {str(e)}")

@router.post("/classify", response_model=ClassificationResponse)
async def classify_image_endpoint(
    file: UploadFile = File(...),
    model: str = Form("clip"),
    num_categories: int = Form(5)
):
    """
    Classifica uma imagem em categorias usando CLIP
    """
    try:
        # Verificar extensão do arquivo
        allowed_extensions = [".jpg", ".jpeg", ".png", ".webp"]
        file_extension = os.path.splitext(file.filename)[1].lower()
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"Tipo de arquivo não suportado. Use: {', '.join(allowed_extensions)}"
            )
        
        # Salvar arquivo temporariamente
        temp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(temp_dir, f"image{file_extension}")
        
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Classificar a imagem
        categories = await classify_image(
            image_path=temp_file_path,
            model_name=model,
            top_k=num_categories
        )
        
        # Limpar arquivos temporários
        shutil.rmtree(temp_dir)
        
        if not categories:
            raise HTTPException(status_code=500, detail="Falha ao classificar imagem")
        
        return ClassificationResponse(
            categories=categories,
            model=model
        )
    except Exception as e:
        # Garantir limpeza em caso de erro
        if 'temp_dir' in locals():
            shutil.rmtree(temp_dir)
        raise HTTPException(status_code=500, detail=f"Erro: {str(e)}")

@router.post("/extract-features", response_model=FeatureResponse)
async def extract_features(
    file: UploadFile = File(...),
    model: str = Form("clip"),
):
    """
    Extrai características de uma imagem usando CLIP e armazena para uso posterior
    """
    try:
        # Verificar extensão do arquivo
        allowed_extensions = [".jpg", ".jpeg", ".png", ".webp"]
        file_extension = os.path.splitext(file.filename)[1].lower()
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"Tipo de arquivo não suportado. Use: {', '.join(allowed_extensions)}"
            )
        
        # Salvar arquivo temporariamente
        temp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(temp_dir, f"image{file_extension}")
        
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Extrair características da imagem
        feature_id = await extract_image_features(
            image_path=temp_file_path,
            model_name=model
        )
        
        # Limpar arquivos temporários
        shutil.rmtree(temp_dir)
        
        if not feature_id:
            raise HTTPException(status_code=500, detail="Falha ao extrair características")
        
        return FeatureResponse(
            success=True,
            feature_id=feature_id,
            model=model
        )
    except Exception as e:
        # Garantir limpeza em caso de erro
        if 'temp_dir' in locals():
            shutil.rmtree(temp_dir)
        raise HTTPException(status_code=500, detail=f"Erro: {str(e)}")

@router.post("/search-similar")
async def search_similar(
    file: UploadFile = File(...),
    model: str = Form("clip"),
    top_k: int = Form(5)
):
    """
    Busca imagens similares a partir de uma imagem de consulta
    """
    try:
        # Verificar extensão do arquivo
        allowed_extensions = [".jpg", ".jpeg", ".png", ".webp"]
        file_extension = os.path.splitext(file.filename)[1].lower()
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"Tipo de arquivo não suportado. Use: {', '.join(allowed_extensions)}"
            )
        
        # Salvar arquivo temporariamente
        temp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(temp_dir, f"image{file_extension}")
        
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Buscar imagens similares
        results = await search_similar_images(
            query_image_path=temp_file_path,
            model_name=model,
            top_k=top_k
        )
        
        # Limpar arquivos temporários
        shutil.rmtree(temp_dir)
        
        if results is None:
            raise HTTPException(status_code=500, detail="Falha ao buscar imagens similares")
        
        return {
            "results": results,
            "model": model
        }
    except Exception as e:
        # Garantir limpeza em caso de erro
        if 'temp_dir' in locals():
            shutil.rmtree(temp_dir)
        raise HTTPException(status_code=500, detail=f"Erro: {str(e)}")

@router.get("/models")
async def list_models():
    """
    Lista os modelos disponíveis para processamento de imagem
    """
    models = {
        "caption": [
            {"name": "blip2", "description": "Modelo BLIP-2 para geração de legendas"}
        ],
        "classification": [
            {"name": "clip", "description": "Modelo CLIP para classificação de imagens"}
        ]
    }
    
    return models 