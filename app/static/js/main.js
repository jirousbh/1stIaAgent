document.addEventListener('DOMContentLoaded', function() {
    // Elementos da navegação por abas
    const tabButtons = document.querySelectorAll('.tabs button');
    const tabContents = document.querySelectorAll('.tab-content');

    // Função para alternar entre abas
    function switchTab(tabId) {
        // Ocultar todos os conteúdos
        tabContents.forEach(content => {
            content.classList.remove('active');
        });
        
        // Desmarcar todos os botões
        tabButtons.forEach(button => {
            button.classList.remove('active');
        });
        
        // Mostrar conteúdo da aba selecionada
        document.getElementById(tabId).classList.add('active');
        
        // Marcar botão selecionado
        document.querySelector(`button[data-tab="${tabId}"]`).classList.add('active');
    }

    // Adicionar evento de clique aos botões das abas
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            const tabId = this.getAttribute('data-tab');
            switchTab(tabId);
        });
    });

    // Iniciar com a primeira aba ativa
    if (tabButtons.length > 0) {
        const firstTabId = tabButtons[0].getAttribute('data-tab');
        switchTab(firstTabId);
    }

    // ===== Funções para API LLM =====
    const llmForm = document.getElementById('llm-form');
    const llmPrompt = document.getElementById('llm-prompt');
    const llmResults = document.getElementById('llm-results');
    const llmLoading = document.getElementById('llm-loading');

    if (llmForm) {
        llmForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const prompt = llmPrompt.value.trim();
            if (!prompt) return;
            
            // Mostrar loading
            llmLoading.style.display = 'block';
            llmResults.textContent = '';
            
            try {
                const response = await fetch('/api/llm/generate', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ prompt: prompt })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    llmResults.textContent = data.response || data.text || data.result || JSON.stringify(data);
                } else {
                    throw new Error(data.detail || 'Erro ao processar requisição');
                }
            } catch (error) {
                showError(llmResults, error.message);
            } finally {
                llmLoading.style.display = 'none';
            }
        });
    }

    // ===== Funções para API TTS =====
    const ttsForm = document.getElementById('tts-form');
    const ttsText = document.getElementById('tts-text');
    const ttsVoice = document.getElementById('tts-voice');
    const ttsEngine = document.getElementById('tts-engine');
    const ttsAudioPlayer = document.getElementById('tts-audio');
    const ttsLoading = document.getElementById('tts-loading');
    
    // Carregar lista de vozes da API
    async function loadVoices() {
        try {
            const response = await fetch('/api/tts/voices');
            if (response.ok) {
                const voices = await response.json();
                return voices;
            }
        } catch (error) {
            console.error('Erro ao carregar vozes:', error);
        }
        return null;
    }
    
    // Atualizar seletor de vozes com base no engine selecionado
    async function updateVoiceOptions() {
        const voices = await loadVoices();
        if (!voices) return;
        
        const engine = ttsEngine.value;
        const engineVoices = voices[engine] || [];
        
        // Limpar opções atuais
        ttsVoice.innerHTML = '';
        
        // Adicionar novas opções com base no engine
        if (engine === 'coqui') {
            // Adicionar vozes Coqui com nomes amigáveis
            const voiceLabels = {
                'pt_br_female': 'Português (BR) - Feminina',
                'pt_br_male': 'Português (BR) - Masculina',
                'en_us_female': 'Inglês (US) - Feminina',
                'en_us_male': 'Inglês (US) - Masculina'
            };
            
            engineVoices.forEach(voice => {
                const option = document.createElement('option');
                option.value = voice;
                option.textContent = voiceLabels[voice] || voice;
                ttsVoice.appendChild(option);
            });
        } else if (engine === 'piper') {
            // Adicionar vozes Piper com nomes amigáveis
            const voiceLabels = {
                'pt_BR-16000': 'Português (BR) - Piper',
                'en_US-22050': 'Inglês (US) - Piper'
            };
            
            engineVoices.forEach(voice => {
                const option = document.createElement('option');
                option.value = voice;
                option.textContent = voiceLabels[voice] || voice;
                ttsVoice.appendChild(option);
            });
        }
    }
    
    // Inicializar vozes quando a página carrega
    updateVoiceOptions();
    
    // Atualizar vozes quando o engine muda
    if (ttsEngine) {
        ttsEngine.addEventListener('change', updateVoiceOptions);
    }

    if (ttsForm) {
        ttsForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const text = ttsText.value.trim();
            if (!text) return;
            
            // Mostrar loading
            ttsLoading.style.display = 'block';
            ttsAudioPlayer.style.display = 'none';
            
            try {
                const response = await fetch('/api/tts/generate', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        text: text,
                        voice: ttsVoice ? ttsVoice.value : undefined,
                        engine: ttsEngine ? ttsEngine.value : 'coqui',
                        speed: document.getElementById('tts-speed') ? parseFloat(document.getElementById('tts-speed').value) : 1.0
                    })
                });
                
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || 'Erro ao converter texto para fala');
                }
                
                // Para áudio, precisamos criar uma URL do blob
                const audioBlob = await response.blob();
                const audioUrl = URL.createObjectURL(audioBlob);
                ttsAudioPlayer.src = audioUrl;
                ttsAudioPlayer.style.display = 'block';
                ttsAudioPlayer.play();
            } catch (error) {
                showError(document.querySelector('#tts-tab .error-message') || ttsForm, error.message);
            } finally {
                ttsLoading.style.display = 'none';
            }
        });
    }

    // ===== Funções para API STT =====
    const sttForm = document.getElementById('stt-form');
    const sttFileInput = document.getElementById('stt-file');
    const sttRecordButton = document.getElementById('stt-record');
    const sttStopButton = document.getElementById('stt-stop');
    const sttResults = document.getElementById('stt-results');
    const sttLoading = document.getElementById('stt-loading');
    
    let mediaRecorder = null;
    let audioChunks = [];

    if (sttRecordButton && sttStopButton) {
        sttRecordButton.addEventListener('click', async function() {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                mediaRecorder = new MediaRecorder(stream);
                audioChunks = [];
                
                mediaRecorder.addEventListener('dataavailable', function(e) {
                    audioChunks.push(e.data);
                });
                
                mediaRecorder.start();
                sttRecordButton.style.display = 'none';
                sttStopButton.style.display = 'inline-block';
            } catch (error) {
                showError(sttResults, 'Erro ao acessar microfone: ' + error.message);
            }
        });
        
        sttStopButton.addEventListener('click', function() {
            if (mediaRecorder) {
                mediaRecorder.stop();
                
                mediaRecorder.addEventListener('stop', async function() {
                    const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                    
                    // Enviar áudio para a API
                    const formData = new FormData();
                    formData.append('audio', audioBlob, 'recording.wav');
                    
                    sttLoading.style.display = 'block';
                    
                    try {
                        const response = await fetch('/api/stt/transcribe', {
                            method: 'POST',
                            body: formData
                        });
                        
                        const data = await response.json();
                        
                        if (response.ok) {
                            sttResults.textContent = data.text || data.transcription || JSON.stringify(data);
                        } else {
                            throw new Error(data.detail || 'Erro ao transcrever áudio');
                        }
                    } catch (error) {
                        showError(sttResults, error.message);
                    } finally {
                        sttLoading.style.display = 'none';
                        sttRecordButton.style.display = 'inline-block';
                        sttStopButton.style.display = 'none';
                    }
                });
            }
        });
    }

    if (sttForm) {
        sttForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            if (!sttFileInput.files.length) {
                showError(sttResults, 'Por favor, selecione um arquivo de áudio.');
                return;
            }
            
            const formData = new FormData();
            formData.append('audio', sttFileInput.files[0]);
            
            sttLoading.style.display = 'block';
            sttResults.textContent = '';
            
            try {
                const response = await fetch('/api/stt/transcribe', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    sttResults.textContent = data.text || data.transcription || JSON.stringify(data);
                } else {
                    throw new Error(data.detail || 'Erro ao transcrever áudio');
                }
            } catch (error) {
                showError(sttResults, error.message);
            } finally {
                sttLoading.style.display = 'none';
            }
        });
    }

    // ===== Funções para API Vision =====
    const visionForm = document.getElementById('vision-form');
    const visionFileInput = document.getElementById('vision-file');
    const visionPrompt = document.getElementById('vision-prompt');
    const visionImagePreview = document.getElementById('vision-image-preview');
    const visionResults = document.getElementById('vision-results');
    const visionLoading = document.getElementById('vision-loading');

    if (visionFileInput) {
        visionFileInput.addEventListener('change', function() {
            if (this.files && this.files[0]) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    visionImagePreview.src = e.target.result;
                    visionImagePreview.style.display = 'block';
                };
                reader.readAsDataURL(this.files[0]);
            }
        });
    }

    if (visionForm) {
        visionForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            if (!visionFileInput.files.length) {
                showError(visionResults, 'Por favor, selecione uma imagem.');
                return;
            }
            
            const formData = new FormData();
            formData.append('image', visionFileInput.files[0]);
            
            if (visionPrompt && visionPrompt.value.trim()) {
                formData.append('prompt', visionPrompt.value.trim());
            }
            
            visionLoading.style.display = 'block';
            visionResults.textContent = '';
            
            try {
                const response = await fetch('/api/vision/analyze', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    visionResults.textContent = data.description || data.analysis || data.result || JSON.stringify(data);
                } else {
                    throw new Error(data.detail || 'Erro ao analisar imagem');
                }
            } catch (error) {
                showError(visionResults, error.message);
            } finally {
                visionLoading.style.display = 'none';
            }
        });
    }

    // Função auxiliar para mostrar mensagens de erro
    function showError(container, message) {
        const errorElement = document.createElement('div');
        errorElement.className = 'error-message';
        errorElement.textContent = message;
        
        // Se o container já for um elemento de erro, atualizar o texto
        if (container.classList.contains('error-message')) {
            container.textContent = message;
        } else {
            // Limpar mensagens de erro anteriores
            const previousErrors = container.querySelectorAll('.error-message');
            previousErrors.forEach(err => err.remove());
            
            container.appendChild(errorElement);
        }
    }
}); 