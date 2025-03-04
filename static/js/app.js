class ProxmoxNLI {
    constructor() {
        this.chatForm = document.getElementById('chat-form');
        this.userInput = document.getElementById('user-input');
        this.chatBody = document.getElementById('chat-body');
        this.micButton = document.getElementById('mic-button');
        this.vmList = document.getElementById('vm-list');
        this.clusterStatus = document.getElementById('cluster-status');
        this.auditLog = document.getElementById('audit-log');
        this.isRecording = false;
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.socket = io();

        this.initializeEventListeners();
        this.setupSocketHandlers();
        this.setupMediaRecorder();
        this.loadInitialData();
    }

    async setupMediaRecorder() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            this.mediaRecorder = new MediaRecorder(stream);
            
            this.mediaRecorder.ondataavailable = (event) => {
                this.audioChunks.push(event.data);
            };
            
            this.mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(this.audioChunks, { type: 'audio/wav' });
                const reader = new FileReader();
                reader.readAsDataURL(audioBlob);
                reader.onloadend = async () => {
                    const base64Audio = reader.result;
                    try {
                        const response = await fetch('/stt', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({ audio: base64Audio })
                        });
                        const data = await response.json();
                        if (data.success) {
                            this.userInput.value = data.text;
                            this.chatForm.dispatchEvent(new Event('submit'));
                        } else {
                            this.addMessage('Error: ' + data.error, 'system');
                        }
                    } catch (error) {
                        console.error('Error:', error);
                        this.addMessage('Error processing voice input', 'system');
                    }
                    this.audioChunks = [];
                };
            };
        } catch (error) {
            console.error('Error accessing microphone:', error);
            this.addMessage('Error: Could not access microphone', 'system');
        }
    }

    setupSocketHandlers() {
        this.socket.on('connect', () => {
            console.log('Connected to server');
        });

        this.socket.on('vm_status_update', (data) => {
            this.updateVMList(data.vms);
        });

        this.socket.on('cluster_status_update', (data) => {
            this.updateClusterStatus(data.status);
        });
    }

    initializeEventListeners() {
        this.chatForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const query = this.userInput.value.trim();
            if (!query) return;

            this.addMessage(query, 'user');
            this.userInput.value = '';

            try {
                const response = await fetch('/query', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ query: query })
                });
                const data = await response.json();
                
                const responseText = data.error ? 'Error: ' + data.error : data.response;
                this.addMessage(responseText, 'system');
                
                if (this.isRecording) {
                    await this.playTextToSpeech(responseText);
                }
            } catch (error) {
                console.error('Error:', error);
                this.addMessage('Sorry, there was an error processing your request.', 'system');
            }
        });

        this.micButton.addEventListener('click', () => {
            if (!this.mediaRecorder) {
                this.addMessage('Error: Microphone not available', 'system');
                return;
            }

            if (this.isRecording) {
                this.mediaRecorder.stop();
                this.micButton.classList.remove('recording');
            } else {
                this.audioChunks = [];
                this.mediaRecorder.start();
                this.micButton.classList.add('recording');
                this.addMessage('Listening... Click the microphone again to stop.', 'system');
            }
            this.isRecording = !this.isRecording;
        });
    }

    updateVMList(vms) {
        this.vmList.innerHTML = '';
        vms.forEach(vm => {
            const card = document.createElement('div');
            card.className = `card vm-card ${vm.status === 'running' ? 'border-success' : 'border-danger'}`;
            card.innerHTML = `
                <div class="card-body">
                    <h5 class="card-title">VM ${vm.id} - ${vm.name}</h5>
                    <p class="card-text">
                        Status: <span class="badge bg-${vm.status === 'running' ? 'success' : 'danger'}">${vm.status}</span><br>
                        CPU: ${vm.cpu} cores | Memory: ${vm.memory.toFixed(1)} MB | Disk: ${vm.disk.toFixed(1)} GB
                    </p>
                </div>
            `;
            this.vmList.appendChild(card);
        });
    }

    updateClusterStatus(nodes) {
        this.clusterStatus.innerHTML = '';
        nodes.forEach(node => {
            const nodeElement = document.createElement('div');
            nodeElement.className = 'mb-2';
            nodeElement.innerHTML = `
                <strong>${node.name}</strong>
                <span class="badge bg-${node.status === 'online' ? 'success' : 'danger'} ms-2">${node.status}</span>
            `;
            this.clusterStatus.appendChild(nodeElement);
        });
    }

    async loadAuditLogs() {
        try {
            const response = await fetch('/audit-logs');
            const data = await response.json();
            this.auditLog.innerHTML = '';
            data.logs.forEach(log => {
                const entry = document.createElement('div');
                entry.className = 'audit-entry';
                entry.innerHTML = `
                    <div class="timestamp">${new Date(log.timestamp).toLocaleString()}</div>
                    <div class="user">${log.user || 'anonymous'}</div>
                    <div class="query">${log.query}</div>
                    <div class="result ${log.success ? 'text-success' : 'text-danger'}">
                        ${log.success ? 'Success' : 'Failed'}
                    </div>
                `;
                this.auditLog.appendChild(entry);
            });
        } catch (error) {
            console.error('Error loading audit logs:', error);
        }
    }

    async playTextToSpeech(text) {
        try {
            const response = await fetch('/tts', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ text: text })
            });
            const data = await response.json();
            if (data.success) {
                const audio = new Audio(data.audio);
                await audio.play();
            } else {
                console.error('TTS Error:', data.error);
            }
        } catch (error) {
            console.error('Error playing TTS:', error);
        }
    }

    addMessage(text, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        messageDiv.textContent = text;
        this.chatBody.appendChild(messageDiv);
        this.chatBody.scrollTop = this.chatBody.scrollHeight;
    }

    loadInitialData() {
        this.loadAuditLogs();
        setInterval(() => this.loadAuditLogs(), 30000);
    }
}

// Initialize the application when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new ProxmoxNLI();
});