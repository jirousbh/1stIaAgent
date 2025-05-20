# IA Agent

Um agente de IA completo com múltiplas capacidades: LLM, TTS, STT e processamento de imagens.

## Stack Tecnológica

- **Interface**: FastAPI com UI Web
- **Orquestrador**: Python com FastAPI (assíncrono)
- **LLM**: Llama 3 e Mistral 7B via Ollama
- **Imagem**: BLIP-2 + CLIP
- **STT**: Whisper local
- **TTS**: Coqui TTS e Piper
- **Middleware**: LangChain
- **Containerização**: Docker com Ubuntu

## Requisitos

- Docker
- Docker Compose

## Instalação e Execução

1. Clone o repositório:

```bash
git clone https://seu-repositorio/ia-agent.git
cd ia-agent
```

2. Inicie os contêineres com Docker Compose:

```bash
docker-compose up -d
```

3. Acesse a aplicação:
   - Interface Web: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## Modelos Recomendados para Download

Para começar a usar o sistema, recomenda-se baixar os seguintes modelos:

### LLM (via Ollama):

```bash
docker exec -it ia-agent_app_1 ollama pull llama3
docker exec -it ia-agent_app_1 ollama pull mistral
```

### Outros modelos:

Os modelos para as funções de BLIP-2, CLIP, Whisper, Coqui TTS e Piper serão baixados automaticamente na primeira utilização.

## Funcionalidades

### LLM (Modelos de Linguagem)
- Geração de texto com modelos como Llama 3 e Mistral 7B
- Controle de parâmetros como temperatura e tokens máximos
- Prompts de sistema personalizáveis

### TTS (Text-to-Speech)
- Conversão de texto para fala usando Coqui TTS e Piper
- Suporte a múltiplas vozes em português e inglês
- Controle de velocidade da fala

### STT (Speech-to-Text)
- Transcrição de áudio para texto usando Whisper
- Suporte a diferentes tamanhos de modelo (tiny, base, small, medium)
- Detecção automática de idioma ou seleção manual

### Visão Computacional
- Geração de descrições de imagens usando BLIP-2
- Classificação de imagens em categorias usando CLIP
- Extração de características para busca por similaridade

## Estrutura do Projeto

```
.
├── app/
│   ├── main.py             # Aplicação FastAPI principal
│   ├── routers/            # Rotas da API
│   ├── services/           # Serviços para cada funcionalidade
│   ├── models/             # Armazenamento de modelos e features
│   ├── static/             # Arquivos estáticos
│   └── templates/          # Templates HTML
├── docker-compose.yml      # Configuração do Docker Compose
├── Dockerfile              # Configuração do container
└── requirements.txt        # Dependências Python
```

## API Endpoints

A documentação completa da API está disponível em http://localhost:8000/docs após iniciar a aplicação.

## Contribuição

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou pull requests.

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo LICENSE para detalhes. 