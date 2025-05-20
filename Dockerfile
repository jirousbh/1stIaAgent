FROM ubuntu:22.04

# Evitar interações durante instalação
ENV DEBIAN_FRONTEND=noninteractive

# Instalar dependências básicas
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    python3-venv \
    git \
    ffmpeg \
    curl \
    wget \
    nodejs \
    npm \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Configurar diretório de trabalho
WORKDIR /app

# Copiar arquivos de requisitos primeiro para aproveitar o cache do Docker
COPY requirements.txt .

# Instalar dependências Python
RUN pip3 install --no-cache-dir -r requirements.txt

# Instalar Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# Copiar o código fonte
COPY . .

# Expor portas para FastAPI, Ollama e outros serviços
EXPOSE 8000 11434

# Comando para iniciar o serviço
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"] 