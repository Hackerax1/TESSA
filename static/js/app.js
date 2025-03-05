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
        this.socket = io({
            auth: {
                token: this.getToken()
            }
        });

        this.initializeEventListeners();
        this.setupSocketHandlers();
        this.setupMediaRecorder();
        this.checkAuthentication();
    }

    async checkAuthentication() {
        const token = this.getToken();
        if (!token) {
            this.showLoginForm();
        } else {
            await this.loadInitialData();
        }
    }

    getToken() {
        return localStorage.getItem('jwt_token');
    }

    setToken(token) {
        localStorage.setItem('jwt_token', token);
    }

    removeToken() {
        localStorage.removeItem('jwt_token');
    }

    showLoginForm() {
        this.chatBody.innerHTML = `
            <div class="login-form">
                <h3>Login</h3>
                <form id="login-form">
                    <div class="form-group">
                        <input type="text" id="username" class="form-control" placeholder="Username" required>
                    </div>
                    <div class="form-group">
                        <input type="password" id="password" class="form-control" placeholder="Password" required>
                    </div>
                    <button type="submit" class="btn btn-primary">Login</button>
                </form>
            </div>
        `;

        document.getElementById('login-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            
            try {
                const response = await fetch('/auth/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ username, password })
                });
                
                const data = await response.json();
                if (data.token) {
                    this.setToken(data.token);
                    this.socket.auth = { token: data.token };
                    this.socket.connect();
                    await this.loadInitialData();
                } else {
                    this.addMessage('Login failed: ' + (data.error || 'Unknown error'), 'system');
                }
            } catch (error) {
                this.addMessage('Login failed: ' + error, 'system');
            }
        });
    }

    async fetchWithAuth(url, options = {}) {
        const token = this.getToken();
        if (!token) {
            this.showLoginForm();
            throw new Error('Not authenticated');
        }

        const headers = {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
            ...(options.headers || {})
        };

        const response = await fetch(url, { ...options, headers });
        
        if (response.status === 401) {
            this.removeToken();
            this.showLoginForm();
            throw new Error('Authentication expired');
        }

        return response;
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
                        const response = await this.fetchWithAuth('/stt', {
                            method: 'POST',
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
            this.updateVMList(data);
        });

        this.socket.on('cluster_status_update', (data) => {
            this.updateClusterStatus(data);
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
                const response = await this.fetchWithAuth('/query', {
                    method: 'POST',
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

    updateVMList(data) {
        this.vmList.innerHTML = '';
        if (data.error) {
            this.vmList.innerHTML = `
                <div class="alert alert-danger" role="alert">
                    ${data.error}
                </div>`;
            return;
        }
        
        if (!data.vms || data.vms.length === 0) {
            this.vmList.innerHTML = `
                <div class="alert alert-info" role="alert">
                    No virtual machines found
                </div>`;
            return;
        }

        data.vms.forEach(vm => {
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

    updateClusterStatus(data) {
        this.clusterStatus.innerHTML = '';
        if (data.error) {
            this.clusterStatus.innerHTML = `
                <div class="alert alert-danger" role="alert">
                    ${data.error}
                </div>`;
            return;
        }

        if (!data.status || data.status.length === 0) {
            this.clusterStatus.innerHTML = `
                <div class="alert alert-info" role="alert">
                    No cluster nodes found
                </div>`;
            return;
        }

        data.status.forEach(node => {
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
            const response = await this.fetchWithAuth('/audit-logs');
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
            const response = await this.fetchWithAuth('/tts', {
                method: 'POST',
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

    async loadInitialData() {
        try {
            const response = await this.fetchWithAuth('/query', {
                method: 'POST',
                body: JSON.stringify({ query: 'list vms' })
            });
            const data = await response.json();
            if (data.error) {
                this.addMessage('Error: ' + data.error, 'system');
            }
            await this.loadAuditLogs();
        } catch (error) {
            console.error('Error loading initial data:', error);
        }
    }
}

// Initialize the application when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new ProxmoxNLI();
});