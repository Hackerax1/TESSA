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
        this.setupWizard();
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

        this.socket.on('connect_error', (error) => {
            console.error('Socket connection error:', error);
            // Fallback to polling if socket fails
            this.startPolling();
        });

        this.socket.on('vm_status_update', (data) => {
            this.updateVMList(data);
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
                const response = await this.fetchWithAuth('/query', {
                    method: 'POST',
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
        
        // Add event listeners for goal selection checkboxes
        const goalCheckboxes = document.querySelectorAll('#step1 input[type="checkbox"]');
        goalCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', () => {
                this.updateCloudServicesOptions();
            });
        });
    }

    deployServices() {
        // Collect selected goals
        const selectedGoals = Array.from(document.querySelectorAll('#step1 input[type="checkbox"]:checked')).map(checkbox => checkbox.value);
        const otherGoals = document.getElementById('otherGoals').value;

        // Collect cloud services to replace
        const cloudServices = Array.from(document.querySelectorAll('#cloud-services-container input[type="checkbox"]:checked')).map(checkbox => checkbox.value);

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
            body: JSON.stringify({ 
                goals: selectedGoals, 
                otherGoals, 
                cloudServices,
                resources, 
                services: recommendedServices 
            })
        }).then(response => response.json()).then(data => {
            if (data.success) {
                alert('Services deployed successfully!');
                // Close the modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('setupWizardModal'));
                modal.hide();
                // Add a message to the chat
                this.addMessage('I\'ve successfully deployed the services you requested based on your goals. You can now interact with them through natural language commands.', 'system');
            } else {
                alert('Error deploying services: ' + data.error);
            }
        }).catch(error => {
            console.error('Error deploying services:', error);
            alert('Error deploying services: ' + error.message);
        });
    }
    
    setupWizard() {
        // Add cloud services replacement section to step 1
        this.setupCloudServicesSection();
        
        // Set up event listeners for wizard navigation
        document.getElementById('step1-next').addEventListener('click', () => {
            this.processGoalSelections();
        });
        
        // Detect system resources when step 2 is shown
        document.getElementById('step2-tab').addEventListener('shown.bs.tab', () => {
            this.detectSystemResources();
        });
    }
    
    setupCloudServicesSection() {
        const step1 = document.getElementById('step1');
        
        // Create cloud services section if it doesn't exist
        if (!document.getElementById('cloud-services-container')) {
            const cloudServicesContainer = document.createElement('div');
            cloudServicesContainer.id = 'cloud-services-container';
            cloudServicesContainer.className = 'mt-4';
            
            const cloudServicesTitle = document.createElement('h5');
            cloudServicesTitle.textContent = 'What cloud services would you like to replace?';
            
            const cloudServicesDescription = document.createElement('p');
            cloudServicesDescription.className = 'text-muted';
            cloudServicesDescription.textContent = 'Select the cloud services you\'d like to replace with self-hosted alternatives';
            
            cloudServicesContainer.appendChild(cloudServicesTitle);
            cloudServicesContainer.appendChild(cloudServicesDescription);
            
            // Create the services grid
            const servicesGrid = document.createElement('div');
            servicesGrid.className = 'row mt-3';
            servicesGrid.id = 'cloud-services-grid';
            
            // Define cloud services to replace
            const cloudServices = [
                { id: 'google_photos', name: 'Google Photos', icon: 'bi-images' },
                { id: 'google_drive', name: 'Google Drive', icon: 'bi-cloud' },
                { id: 'dropbox', name: 'Dropbox', icon: 'bi-folder' },
                { id: 'netflix', name: 'Netflix', icon: 'bi-film' },
                { id: 'spotify', name: 'Spotify', icon: 'bi-music-note-beamed' },
                { id: 'lastpass', name: 'LastPass/1Password', icon: 'bi-key' },
                { id: 'github', name: 'GitHub', icon: 'bi-code-square' },
                { id: 'google_calendar', name: 'Google Calendar', icon: 'bi-calendar' },
                { id: 'google_docs', name: 'Google Docs', icon: 'bi-file-text' }
            ];
            
            // Create two columns for the services
            const col1 = document.createElement('div');
            col1.className = 'col-md-6';
            
            const col2 = document.createElement('div');
            col2.className = 'col-md-6';
            
            // Add services to columns
            cloudServices.forEach((service, index) => {
                const serviceCheck = document.createElement('div');
                serviceCheck.className = 'form-check mb-3';
                serviceCheck.innerHTML = `
                    <input class="form-check-input" type="checkbox" value="${service.id}" id="cloud${service.id}">
                    <label class="form-check-label" for="cloud${service.id}">
                        <i class="bi ${service.icon}"></i> ${service.name}
                    </label>
                `;
                
                // Add to appropriate column
                if (index < cloudServices.length / 2) {
                    col1.appendChild(serviceCheck);
                } else {
                    col2.appendChild(serviceCheck);
                }
            });
            
            servicesGrid.appendChild(col1);
            servicesGrid.appendChild(col2);
            cloudServicesContainer.appendChild(servicesGrid);
            
            // Add to step 1 before the "Other goals" section
            const otherGoalsSection = document.querySelector('#step1 .mt-4:last-child');
            step1.insertBefore(cloudServicesContainer, otherGoalsSection);
        }
    }
    
    updateCloudServicesOptions() {
        const selectedGoals = Array.from(document.querySelectorAll('#step1 input[type="checkbox"]:checked')).map(checkbox => checkbox.value);
        
        // Show/hide relevant cloud services based on goals
        const cloudServiceMappings = {
            'media': ['netflix', 'spotify'],
            'files': ['google_photos', 'google_drive', 'dropbox'],
            'webhosting': ['github'],
            'productivity': ['google_calendar', 'google_docs', 'lastpass']
        };
        
        // Get all cloud service checkboxes
        const cloudServiceCheckboxes = document.querySelectorAll('#cloud-services-grid input[type="checkbox"]');
        
        // First, hide all cloud services
        cloudServiceCheckboxes.forEach(checkbox => {
            checkbox.closest('.form-check').style.display = 'none';
        });
        
        // Then show only the relevant ones
        if (selectedGoals.length > 0) {
            document.getElementById('cloud-services-container').style.display = 'block';
            
            // For each selected goal, show the relevant cloud services
            selectedGoals.forEach(goal => {
                if (cloudServiceMappings[goal]) {
                    cloudServiceMappings[goal].forEach(serviceId => {
                        const checkbox = document.getElementById(`cloud${serviceId}`);
                        if (checkbox) {
                            checkbox.closest('.form-check').style.display = 'block';
                        }
                    });
                }
            });
        } else {
            // If no goals selected, hide the cloud services section
            document.getElementById('cloud-services-container').style.display = 'none';
        }
    }
    
    processGoalSelections() {
        // Get selected goals and cloud services
        const selectedGoals = Array.from(document.querySelectorAll('#step1 input[type="checkbox"]:checked')).map(checkbox => checkbox.value);
        const cloudServices = Array.from(document.querySelectorAll('#cloud-services-container input[type="checkbox"]:checked')).map(checkbox => checkbox.value);
        
        // Show loading indicator
        const recommendedServices = document.getElementById('recommended-services');
        recommendedServices.innerHTML = `
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading recommendations...</span>
            </div>
            <span class="ms-2">Getting service recommendations...</span>
        `;
        
        // Get recommendations from the server
        fetch('/recommend-services', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ goals: selectedGoals, cloudServices })
        }).then(response => response.json()).then(data => {
            if (data.success) {
                this.displayRecommendedServices(data.recommendations, data.total_resources);
                
                // Update resource requirements in step 2
                if (data.total_resources) {
                    document.getElementById('cpuCores').value = Math.max(2, Math.ceil(data.total_resources.cpu_cores));
                    document.getElementById('ramSize').value = Math.max(4, Math.ceil(data.total_resources.memory_mb / 1024));
                    document.getElementById('diskSize').value = Math.max(20, Math.ceil(data.total_resources.storage_gb));
                }
                
                // Proceed to next step
                const step2Tab = document.getElementById('step2-tab');
                bootstrap.Tab.getInstance(step2Tab).show();
            } else {
                recommendedServices.innerHTML = `<div class="alert alert-danger">Error: ${data.error}</div>`;
            }
        }).catch(error => {
            console.error('Error getting recommendations:', error);
            recommendedServices.innerHTML = `<div class="alert alert-danger">Error: ${error.message}</div>`;
        });
    }
    
    displayRecommendedServices(recommendations, totalResources) {
        const recommendedServices = document.getElementById('recommended-services');
        recommendedServices.innerHTML = '';
        
        if (recommendations.length === 0) {
            recommendedServices.innerHTML = `
                <div class="alert alert-info">
                    No services recommended based on your selections. Please select different goals or cloud services.
                </div>
            `;
            return;
        }
        
        // Group recommendations by goal/replacement
        const goalGroups = {};
        const replacementGroups = {};
        
        recommendations.forEach(service => {
            if (service.goal) {
                if (!goalGroups[service.goal]) {
                    goalGroups[service.goal] = {
                        description: service.goal_description,
                        services: []
                    };
                }
                goalGroups[service.goal].services.push(service);
            }
            
            if (service.replaces) {
                if (!replacementGroups[service.replaces]) {
                    replacementGroups[service.replaces] = {
                        description: service.replacement_description,
                        services: []
                    };
                }
                replacementGroups[service.replaces].services.push(service);
            }
        });
        
        // First show replacement recommendations
        if (Object.keys(replacementGroups).length > 0) {
            const replacementsSection = document.createElement('div');
            replacementsSection.className = 'mb-4';
            
            const replacementsTitle = document.createElement('h5');
            replacementsTitle.textContent = 'Recommended Cloud Service Replacements';
            replacementsSection.appendChild(replacementsTitle);
            
            for (const [replacementId, group] of Object.entries(replacementGroups)) {
                const groupCard = document.createElement('div');
                groupCard.className = 'card mb-3';
                
                const cardHeader = document.createElement('div');
                cardHeader.className = 'card-header';
                cardHeader.innerHTML = `<h6 class="mb-0">Replace: ${replacementId.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}</h6>`;
                
                const cardBody = document.createElement('div');
                cardBody.className = 'card-body';
                
                const description = document.createElement('p');
                description.className = 'text-muted';
                description.textContent = group.description;
                cardBody.appendChild(description);
                
                const servicesList = document.createElement('div');
                servicesList.className = 'list-group';
                
                group.services.forEach(service => {
                    const serviceItem = document.createElement('div');
                    serviceItem.className = 'list-group-item';
                    serviceItem.innerHTML = `
                        <div class="form-check">
                            <input class="form-check-input" type="checkbox" value="${service.id}" id="service${service.id}" checked>
                            <label class="form-check-label" for="service${service.id}">
                                <strong>${service.name}</strong>
                            </label>
                            <p class="mb-0 text-muted">${service.description}</p>
                            <small class="text-muted">Resources: ${service.resources.cpu_cores || 1} CPU, ${Math.ceil((service.resources.memory_mb || 512) / 1024)} GB RAM, ${service.resources.storage_gb || 5} GB Storage</small>
                        </div>
                    `;
                    servicesList.appendChild(serviceItem);
                });
                
                cardBody.appendChild(servicesList);
                groupCard.appendChild(cardHeader);
                groupCard.appendChild(cardBody);
                replacementsSection.appendChild(groupCard);
            }
            
            recommendedServices.appendChild(replacementsSection);
        }
        
        // Then show goal-based recommendations
        if (Object.keys(goalGroups).length > 0) {
            const goalsSection = document.createElement('div');
            goalsSection.className = 'mb-4';
            
            const goalsTitle = document.createElement('h5');
            goalsTitle.textContent = 'Recommended Services Based on Your Goals';
            goalsSection.appendChild(goalsTitle);
            
            for (const [goalId, group] of Object.entries(goalGroups)) {
                const groupCard = document.createElement('div');
                groupCard.className = 'card mb-3';
                
                const cardHeader = document.createElement('div');
                cardHeader.className = 'card-header';
                cardHeader.innerHTML = `<h6 class="mb-0">Goal: ${goalId.replace(/\b\w/g, c => c.toUpperCase())}</h6>`;
                
                const cardBody = document.createElement('div');
                cardBody.className = 'card-body';
                
                const description = document.createElement('p');
                description.className = 'text-muted';
                description.textContent = group.description;
                cardBody.appendChild(description);
                
                const servicesList = document.createElement('div');
                servicesList.className = 'list-group';
                
                group.services.forEach(service => {
                    // Skip services already shown in replacements
                    if (service.replaces) return;
                    
                    const serviceItem = document.createElement('div');
                    serviceItem.className = 'list-group-item';
                    serviceItem.innerHTML = `
                        <div class="form-check">
                            <input class="form-check-input" type="checkbox" value="${service.id}" id="service${service.id}" checked>
                            <label class="form-check-label" for="service${service.id}">
                                <strong>${service.name}</strong>
                            </label>
                            <p class="mb-0 text-muted">${service.description}</p>
                            <small class="text-muted">Resources: ${service.resources.cpu_cores || 1} CPU, ${Math.ceil((service.resources.memory_mb || 512) / 1024)} GB RAM, ${service.resources.storage_gb || 5} GB Storage</small>
                        </div>
                    `;
                    servicesList.appendChild(serviceItem);
                });
                
                // Only add the card if there are services to show
                if (servicesList.children.length > 0) {
                    cardBody.appendChild(servicesList);
                    groupCard.appendChild(cardHeader);
                    groupCard.appendChild(cardBody);
                    goalsSection.appendChild(groupCard);
                }
            }
            
            // Only add the section if there are cards to show
            if (goalsSection.querySelectorAll('.card').length > 0) {
                recommendedServices.appendChild(goalsSection);
            }
        }
        
        // Add total resource requirements
        if (totalResources) {
            const resourcesSection = document.createElement('div');
            resourcesSection.className = 'alert alert-info mt-3';
            resourcesSection.innerHTML = `
                <h6>Estimated Total Resource Requirements:</h6>
                <ul>
                    <li>CPU: ${Math.ceil(totalResources.cpu_cores)} cores</li>
                    <li>Memory: ${Math.ceil(totalResources.memory_mb / 1024)} GB RAM</li>
                    <li>Storage: ${Math.ceil(totalResources.storage_gb)} GB</li>
                </ul>
            `;
            recommendedServices.appendChild(resourcesSection);
        }
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

    addMessage(text, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        messageDiv.textContent = text;
        this.chatBody.appendChild(messageDiv);
        this.chatBody.scrollTop = this.chatBody.scrollHeight;
    }

    async loadInitialData() {
        try {
            // Fetch initial status data
            const response = await fetch('/initial-status');
            const data = await response.json();
            
            if (data.success) {
                // Update VM list and cluster status with initial data
                this.updateVMList(data.vm_status);
                this.updateClusterStatus(data.cluster_status.nodes);
            } else {
                throw new Error(data.error || 'Failed to load initial status');
            }

            // Load audit logs
            await this.loadAuditLogs();
            
            // Set up periodic audit log updates
            setInterval(() => this.loadAuditLogs(), 30000);
        } catch (error) {
            console.error('Error loading initial data:', error);
            this.showError('Failed to load system status. Please refresh the page or contact support.');
        }
    }

    showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'alert alert-danger';
        errorDiv.textContent = message;
        
        // Insert error message in both status containers
        ['cluster-status', 'vm-list'].forEach(containerId => {
            const container = document.getElementById(containerId);
            container.innerHTML = '';
            container.appendChild(errorDiv.cloneNode(true));
        });
    }

    startPolling() {
        // Fallback to polling every 10 seconds if websocket fails
        setInterval(async () => {
            try {
                const response = await fetch('/initial-status');
                const data = await response.json();
                
                if (data.success) {
                    this.updateVMList(data.vm_status);
                    this.updateClusterStatus(data.cluster_status.nodes);
                }
            } catch (error) {
                console.error('Error polling status:', error);
            }
        }, 10000);
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

        // Collect cloud services to replace
        const cloudServices = Array.from(document.querySelectorAll('#cloud-services-container input[type="checkbox"]:checked')).map(checkbox => checkbox.value);

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
            body: JSON.stringify({ 
                goals: selectedGoals, 
                otherGoals, 
                cloudServices,
                resources, 
                services: recommendedServices 
            })
        }).then(response => response.json()).then(data => {
            if (data.success) {
                alert('Services deployed successfully!');
                // Close the modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('setupWizardModal'));
                modal.hide();
                // Add a message to the chat
                this.addMessage('I\'ve successfully deployed the services you requested based on your goals. You can now interact with them through natural language commands.', 'system');
            } else {
                alert('Error deploying services: ' + data.error);
            }
        }).catch(error => {
            console.error('Error deploying services:', error);
            alert('Error deploying services: ' + error.message);
        });
    }
    
    // New method to detect system resources
    detectSystemResources() {
        const resourcesContainer = document.getElementById('detected-resources');
        
        // Show loading indicator
        resourcesContainer.innerHTML = `
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Detecting resources...</span>
            </div>
            <span class="ms-2">Detecting system resources...</span>
        `;
        
        // Call the server to detect resources
        fetch('/detect-resources')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const resources = data.resources;
                    
                    // Update the UI with detected resources
                    document.getElementById('cpuCores').value = resources.cpu_cores;
                    document.getElementById('ramSize').value = resources.ram_gb;
                    document.getElementById('diskSize').value = resources.disk_gb;
                    document.getElementById('networkSpeed').value = resources.network_speed;
                    
                    // Show success message
                    resourcesContainer.innerHTML = `
                        <div class="alert alert-success">
                            <i class="bi bi-check-circle-fill me-2"></i>
                            System resources detected successfully!
                        </div>
                        <div class="mb-3">
                            <small class="text-muted">You can adjust these values if needed.</small>
                        </div>
                    `;
                } else {
                    // Show error message
                    resourcesContainer.innerHTML = `
                        <div class="alert alert-warning">
                            <i class="bi bi-exclamation-triangle-fill me-2"></i>
                            Could not detect system resources automatically: ${data.error}
                        </div>
                        <div class="mb-3">
                            <small class="text-muted">Please enter your system resources manually.</small>
                        </div>
                    `;
                }
            })
            .catch(error => {
                console.error('Error detecting resources:', error);
                resourcesContainer.innerHTML = `
                    <div class="alert alert-danger">
                        <i class="bi bi-exclamation-triangle-fill me-2"></i>
                        Error detecting system resources: ${error.message}
                    </div>
                    <div class="mb-3">
                        <small class="text-muted">Please enter your system resources manually.</small>
                    </div>
                `;
            });
    }

}

// Initialize the application when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new ProxmoxNLI();
});