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
        this.networkDiagram = new NetworkDiagram('network-diagram-container');
        
        // Voice settings
        this.voiceProfile = 'tessa_default';
        this.personalityEnabled = true;
        this.personalityLevel = 0.2; // Default 20%
        
        // Initialize UI
        this.initializeEventListeners();
        this.setupSocketHandlers();
        this.setupMediaRecorder();
        this.loadInitialData();
        this.loadVoiceProfiles();
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

        this.socket.on('network_diagram_update', (data) => {
            this.networkDiagram.update(data.nodes, data.links);
        });
    }

    initializeEventListeners() {
        // Existing event listeners
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
                
                if (document.getElementById('enable-personality') && 
                    document.getElementById('enable-personality').checked) {
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

        // Event listener for experience level change
        document.getElementById('experienceLevel').addEventListener('change', (event) => {
            const level = event.target.value;
            this.adjustUIForExperienceLevel(level);
            
            // Update voice profile based on experience level
            this.setVoiceForExperienceLevel(level);
        });

        // New voice settings event listeners
        const saveVoiceSettings = document.getElementById('save-voice-settings');
        if (saveVoiceSettings) {
            saveVoiceSettings.addEventListener('click', () => {
                this.saveVoiceSettings();
            });
        }
        
        const testVoice = document.getElementById('test-voice');
        if (testVoice) {
            testVoice.addEventListener('click', () => {
                this.testVoiceSettings();
            });
        }
        
        const voiceProfile = document.getElementById('voice-profile');
        if (voiceProfile) {
            voiceProfile.addEventListener('change', (e) => {
                this.updateVoiceSettingsUI(e.target.value);
            });
        }

        // Event listener for setup wizard steps
        document.getElementById('deploy-button').addEventListener('click', () => {
            this.deployServices();
        });
    }

    // New method to load voice profiles from the server
    async loadVoiceProfiles() {
        try {
            const response = await fetch('/voice-profiles');
            const data = await response.json();
            
            if (data.success) {
                const selectElement = document.getElementById('voice-profile');
                
                // Clear existing options except default ones
                const defaultOptions = Array.from(selectElement.options).slice(0, 3);
                selectElement.innerHTML = '';
                
                // Add default options back
                defaultOptions.forEach(option => {
                    selectElement.appendChild(option);
                });
                
                // Add additional profiles
                data.profiles.forEach(profile => {
                    if (!['tessa_default', 'tessa_warm', 'tessa_professional'].includes(profile)) {
                        const option = document.createElement('option');
                        option.value = profile;
                        option.textContent = profile.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
                        selectElement.appendChild(option);
                    }
                });
                
                // Set active profile
                if (data.active) {
                    this.voiceProfile = data.active;
                    selectElement.value = data.active;
                    this.updateVoiceSettingsUI(data.active);
                }
            }
        } catch (error) {
            console.error('Error loading voice profiles:', error);
        }
    }
    
    // New method to update UI based on selected voice profile
    async updateVoiceSettingsUI(profileName) {
        try {
            const response = await fetch(`/voice-profile/${profileName}`);
            const data = await response.json();
            
            if (data.success) {
                const profile = data.profile;
                
                // Update UI elements
                if (document.getElementById('voice-accent')) {
                    document.getElementById('voice-accent').value = profile.tld || 'com';
                }
                
                if (document.getElementById('voice-speed')) {
                    document.getElementById('voice-speed').value = profile.slow ? 'true' : 'false';
                }
                
                if (document.getElementById('voice-style')) {
                    document.getElementById('voice-style').value = profile.tone_style || 'friendly';
                }
            }
        } catch (error) {
            console.error('Error fetching voice profile:', error);
        }
    }
    
    // New method to save voice settings
    async saveVoiceSettings() {
        try {
            const profileName = document.getElementById('voice-profile').value;
            const accent = document.getElementById('voice-accent').value;
            const speed = document.getElementById('voice-speed').value === 'true';
            const style = document.getElementById('voice-style').value;
            const personalityLevel = document.getElementById('personality-level').value / 100;
            const personalityEnabled = document.getElementById('enable-personality').checked;
            
            // Save settings
            const response = await fetch('/voice-settings', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    profile_name: profileName,
                    accent: accent,
                    slow: speed,
                    tone_style: style,
                    personality_level: personalityLevel,
                    personality_enabled: personalityEnabled
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Show success message
                this.addMessage('Voice settings updated successfully!', 'system');
                this.voiceProfile = profileName;
                this.personalityEnabled = personalityEnabled;
                this.personalityLevel = personalityLevel;
            } else {
                this.addMessage('Error updating voice settings: ' + data.error, 'system');
            }
        } catch (error) {
            console.error('Error saving voice settings:', error);
            this.addMessage('Error saving voice settings', 'system');
        }
    }
    
    // New method to test voice settings
    async testVoiceSettings() {
        const testText = "Hello! This is a test of the TESSA voice system. I'm using the voice profile you've selected.";
        
        try {
            const profileName = document.getElementById('voice-profile').value;
            const accent = document.getElementById('voice-accent').value;
            const speed = document.getElementById('voice-speed').value === 'true';
            const style = document.getElementById('voice-style').value;
            const personalityLevel = document.getElementById('personality-level').value / 100;
            const personalityEnabled = document.getElementById('enable-personality').checked;
            
            // Test voice with current settings
            const response = await fetch('/test-voice', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    text: testText,
                    profile_name: profileName,
                    accent: accent,
                    slow: speed,
                    tone_style: style,
                    personality_level: personalityLevel,
                    personality_enabled: personalityEnabled
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                const audio = new Audio(data.audio);
                await audio.play();
                
                // If the text was modified with personality, show it
                if (data.text !== testText) {
                    this.addMessage(`Voice test (with personality): "${data.text}"`, 'system');
                }
            } else {
                this.addMessage('Error testing voice: ' + data.error, 'system');
            }
        } catch (error) {
            console.error('Error testing voice:', error);
            this.addMessage('Error testing voice settings', 'system');
        }
    }
    
    // New method to adapt voice based on experience level
    setVoiceForExperienceLevel(level) {
        let experienceLevel = 0;
        
        switch (level) {
            case 'beginner':
                experienceLevel = 0.0;
                break;
            case 'intermediate':
                experienceLevel = 0.5;
                break;
            case 'advanced':
                experienceLevel = 1.0;
                break;
        }
        
        // Call API to adapt voice to experience level
        fetch('/adapt-voice', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                experience_level: experienceLevel
            })
        }).then(response => response.json())
          .then(data => {
              if (data.success && data.profile) {
                  // Update UI if profile changed
                  const voiceProfile = document.getElementById('voice-profile');
                  if (voiceProfile && voiceProfile.value !== data.profile) {
                      voiceProfile.value = data.profile;
                      this.updateVoiceSettingsUI(data.profile);
                  }
              }
          })
          .catch(error => {
              console.error('Error adapting voice:', error);
          });
    }

    // Enhanced TTS playback with voice profile
    async playTextToSpeech(text) {
        try {
            const response = await fetch('/tts', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    text: text,
                    profile: this.voiceProfile,
                    add_personality: this.personalityEnabled,
                    personality_level: this.personalityLevel
                })
            });
            
            const data = await response.json();
            if (data.success) {
                const audio = new Audio(data.audio);
                await audio.play();
                
                // If the text was modified with personality and different from original
                if (data.text && data.text !== text) {
                    console.log('TESSA added personality:', data.text);
                }
            } else {
                console.error('TTS Error:', data.error);
            }
        } catch (error) {
            console.error('Error playing TTS:', error);
        }
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

    adjustUIForExperienceLevel(level) {
        const advancedTab = document.getElementById('advanced-tab');
        if (level === 'beginner') {
            advancedTab.style.display = 'none';
        } else {
            advancedTab.style.display = 'block';
        }
    }

    deployServices() {
        // Collect selected goals
        const selectedGoals = Array.from(document.querySelectorAll('#step1 input[type="checkbox"]:checked')).map(checkbox => checkbox.value);
        const otherGoals = document.getElementById('otherGoals').value;

        // Collect resource information
        const resources = {
            cpuCores: document.getElementById('cpuCores').value,
            ramSize: document.getElementById('ramSize').value,
            diskSize: document.getElementById('diskSize').value,
            networkSpeed: document.getElementById('networkSpeed').value
        };

        // Collect recommended services
        const recommendedServices = Array.from(document.querySelectorAll('#recommended-services input[type="checkbox"]:checked')).map(checkbox => checkbox.value);

        // Display summary
        document.getElementById('summary-goals').innerHTML = selectedGoals.join(', ') + (otherGoals ? ', ' + otherGoals : '');
        document.getElementById('summary-resources').innerHTML = `CPU Cores: ${resources.cpuCores}, RAM: ${resources.ramSize} GB, Disk: ${resources.diskSize} GB, Network: ${resources.networkSpeed} Mbps`;
        document.getElementById('summary-services').innerHTML = recommendedServices.join(', ');

        // Send deployment request to the server
        fetch('/deploy', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ goals: selectedGoals, otherGoals, resources, services: recommendedServices })
        }).then(response => response.json()).then(data => {
            if (data.success) {
                alert('Services deployed successfully!');
            } else {
                alert('Error deploying services: ' + data.error);
            }
        }).catch(error => {
            console.error('Error deploying services:', error);
            alert('Error deploying services: ' + error.message);
        });
    }
}

// Initialize the application when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new ProxmoxNLI();
});