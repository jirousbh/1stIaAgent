import os
import asyncio
import tempfile
import uuid
import json
import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any, Union
import numpy as np

# Diretório para armazenar features extraídas
FEATURES_DIR = "app/models/features"
os.makedirs(FEATURES_DIR, exist_ok=True)

async def generate_image_caption(
    image_path: str, 
    model_name: str = "blip2"
) -> Optional[str]:
    """
    Gera uma descrição para a imagem usando BLIP-2
    
    Args:
        image_path: Caminho para o arquivo de imagem
        model_name: Nome do modelo (blip2)
    
    Returns:
        String com a descrição da imagem ou None se falhar
    """
    try:
        # Importar bibliotecas apenas quando necessário
        from transformers import BlipProcessor, BlipForConditionalGeneration
        from PIL import Image
        import torch
        
        # Função para carregar modelo e gerar caption (não assíncrona)
        def _generate_caption():
            # Carregar modelo e processador
            processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-large")
            model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-large")
            
            # Mover para GPU se disponível
            device = "cuda" if torch.cuda.is_available() else "cpu"
            model = model.to(device)
            
            # Carregar e processar imagem
            image = Image.open(image_path).convert('RGB')
            inputs = processor(image, return_tensors="pt").to(device)
            
            # Gerar descrição
            output = model.generate(**inputs, max_new_tokens=100)
            caption = processor.decode(output[0], skip_special_tokens=True)
            
            return caption
        
        # Executar em um ThreadPool pois os modelos PyTorch não são async-friendly
        loop = asyncio.get_event_loop()
        caption = await loop.run_in_executor(None, _generate_caption)
        
        return caption
    except Exception as e:
        print(f"Erro ao gerar caption: {str(e)}")
        return None

async def classify_image(
    image_path: str, 
    model_name: str = "clip",
    top_k: int = 5,
    categories: Optional[List[str]] = None
) -> Optional[List[Dict[str, Union[str, float]]]]:
    """
    Classifica uma imagem em categorias usando CLIP
    
    Args:
        image_path: Caminho para o arquivo de imagem
        model_name: Nome do modelo (clip)
        top_k: Número de categorias para retornar
        categories: Lista opcional de categorias para classificação
                   Se None, usa categorias predefinidas
    
    Returns:
        Lista de dicionários com categorias e scores ou None se falhar
    """
    try:
        # Importar bibliotecas apenas quando necessário
        import torch
        from transformers import CLIPProcessor, CLIPModel
        from PIL import Image
        
        # Se não foram fornecidas categorias, usar algumas predefinidas
        if categories is None:
            # Lista básica de categorias em português
            categories = [
                "foto", "desenho", "paisagem", "retrato", "animal", 
                "comida", "prédio", "planta", "veículo", "pessoa",
                "esporte", "arte", "tecnologia", "natureza", "urbano",
                "interior", "exterior", "dia", "noite", "água",
                "montanha", "praia", "floresta", "deserto", "neve"
            ]
        
        # Função para classificar imagem (não assíncrona)
        def _classify():
            # Carregar modelo e processador
            model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
            processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
            
            # Mover para GPU se disponível
            device = "cuda" if torch.cuda.is_available() else "cpu"
            model = model.to(device)
            
            # Carregar e processar imagem
            image = Image.open(image_path).convert('RGB')
            
            # Preparar texto com as categorias
            text_inputs = processor(
                text=categories, 
                images=image, 
                return_tensors="pt", 
                padding=True
            ).to(device)
            
            # Calcular similaridade
            with torch.no_grad():
                outputs = model(**text_inputs)
                logits_per_image = outputs.logits_per_image
                probs = logits_per_image.softmax(dim=1)[0].cpu().numpy()
            
            # Organizar resultados
            results = []
            for category, score in zip(categories, probs):
                results.append({
                    "category": category,
                    "score": float(score)
                })
            
            # Ordenar por score e pegar os top_k
            results = sorted(results, key=lambda x: x["score"], reverse=True)[:top_k]
            
            return results
        
        # Executar em um ThreadPool
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(None, _classify)
        
        return results
    except Exception as e:
        print(f"Erro ao classificar imagem: {str(e)}")
        return None

async def extract_image_features(
    image_path: str, 
    model_name: str = "clip"
) -> Optional[str]:
    """
    Extrai características de uma imagem usando CLIP e armazena para uso posterior
    
    Args:
        image_path: Caminho para o arquivo de imagem
        model_name: Nome do modelo (clip)
    
    Returns:
        ID único para as características extraídas ou None se falhar
    """
    try:
        # Importar bibliotecas apenas quando necessário
        import torch
        from transformers import CLIPProcessor, CLIPModel
        from PIL import Image
        
        # Função para extrair características (não assíncrona)
        def _extract_features():
            # Carregar modelo e processador
            model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
            processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
            
            # Mover para GPU se disponível
            device = "cuda" if torch.cuda.is_available() else "cpu"
            model = model.to(device)
            
            # Carregar e processar imagem
            image = Image.open(image_path).convert('RGB')
            inputs = processor(images=image, return_tensors="pt").to(device)
            
            # Extrair características
            with torch.no_grad():
                image_features = model.get_image_features(**inputs)
                
            # Converter para numpy e normalizar
            features = image_features[0].cpu().numpy()
            normalized_features = features / np.linalg.norm(features)
            
            # Gerar ID único
            feature_id = str(uuid.uuid4())
            
            # Salvar características como arquivo numpy
            feature_path = os.path.join(FEATURES_DIR, f"{feature_id}.npz")
            np.savez_compressed(feature_path, features=normalized_features)
            
            # Salvar metadados básicos
            metadata_path = os.path.join(FEATURES_DIR, f"{feature_id}.json")
            metadata = {
                "id": feature_id,
                "model": model_name,
                "created_at": str(datetime.datetime.now()),
                "original_image": os.path.basename(image_path)
            }
            
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f)
            
            return feature_id
        
        # Executar em um ThreadPool
        loop = asyncio.get_event_loop()
        feature_id = await loop.run_in_executor(None, _extract_features)
        
        return feature_id
    except Exception as e:
        print(f"Erro ao extrair características: {str(e)}")
        return None

async def search_similar_images(
    query_image_path: str, 
    model_name: str = "clip",
    top_k: int = 5
) -> Optional[List[Dict[str, Any]]]:
    """
    Busca imagens similares com base em características extraídas
    
    Args:
        query_image_path: Caminho para a imagem de consulta
        model_name: Nome do modelo (clip)
        top_k: Número máximo de resultados
    
    Returns:
        Lista de resultados ou None se falhar
    """
    try:
        # Primeiro, extrair características da imagem de consulta
        query_feature_id = await extract_image_features(query_image_path, model_name)
        
        if not query_feature_id:
            return None
        
        # Importar bibliotecas
        import numpy as np
        from glob import glob
        
        # Função para buscar imagens similares (não assíncrona)
        def _search_similar():
            # Carregar características da consulta
            query_feature_path = os.path.join(FEATURES_DIR, f"{query_feature_id}.npz")
            query_features = np.load(query_feature_path)["features"]
            
            # Listar todos os arquivos de características
            feature_files = glob(os.path.join(FEATURES_DIR, "*.npz"))
            
            # Calcular similaridade com todas as características armazenadas
            results = []
            
            for feature_file in feature_files:
                # Pular a própria imagem de consulta
                feature_id = os.path.basename(feature_file).replace(".npz", "")
                if feature_id == query_feature_id:
                    continue
                
                # Carregar características e calcular similaridade
                features = np.load(feature_file)["features"]
                similarity = np.dot(query_features, features)
                
                # Carregar metadados, se disponíveis
                metadata_file = feature_file.replace(".npz", ".json")
                metadata = {}
                
                if os.path.exists(metadata_file):
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                
                # Adicionar à lista de resultados
                results.append({
                    "id": feature_id,
                    "similarity": float(similarity),
                    "metadata": metadata
                })
            
            # Ordenar por similaridade e retornar os top_k
            results = sorted(results, key=lambda x: x["similarity"], reverse=True)[:top_k]
            
            return results
        
        # Executar em um ThreadPool
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(None, _search_similar)
        
        return results
    except Exception as e:
        print(f"Erro ao buscar imagens similares: {str(e)}")
        return None 