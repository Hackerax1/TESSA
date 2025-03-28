/**
 * Voice module - Handles voice recording, speech-to-text, and text-to-speech functionality
 * Includes ambient mode, voice authentication, command sequences, and shortcuts
 */
import API from './api.js';

export default class Voice {
    constructor() {
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.isRecording = false;
        
        // Voice settings
        this.voiceProfile = 'tessa_default';
        this.personalityEnabled = true;
        this.personalityLevel = 0.2; // Default 20%
        this.currentLanguage = 'en';
        
        // Ambient mode settings
        this.ambientModeActive = false;
        this.wakeWordDetected = false;
        this.ambientModeTimer = null;
        this.ambientModeStatus = {
            energyThreshold: 4000,
            dynamicAdjustment: true,
            useOfflineDetection: false,
            pauseAfterDetection: 5,
            batteryFriendly: true
        };
        this.lastWakeWordTime = null;
        this.wakeWordVisualFeedbackTimeout = null;
        
        // Authentication settings
        this.isAuthenticated = false;
        this.authenticatedUser = null;
        this.authenticationSamples = [];
        
        // Voice shortcuts
        this.shortcuts = [];
        
        // Command sequences
        this.activeSequence = null;
        
        // Available languages
        this.availableLanguages = {};
    }

    /**
     * Set up the media recorder for voice input
     * @returns {Promise<void>}
     */
    async setupMediaRecorder() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            this.mediaRecorder = new MediaRecorder(stream);
        } catch (error) {
            console.error('Error accessing microphone:', error);
            throw new Error('Could not access microphone');
        }
    }

    /**
     * Configure media recorder event handlers
     * @param {Function} onSpeechRecognized - Callback when speech is recognized
     * @param {Function} onError - Callback for errors
     */
    configureMediaRecorder(onSpeechRecognized, onError) {
        if (!this.mediaRecorder) {
            onError('Microphone not available');
            return;
        }
        
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
                    const response = await API.fetchWithAuth('/stt', {
                        method: 'POST',
                        body: JSON.stringify({ 
                            audio: base64Audio,
                            language: this.currentLanguage
                        })
                    });
                    const data = await response.json();
                    if (data.success) {
                        // Handle authentication response
                        if (data.authenticated === true) {
                            this.isAuthenticated = true;
                            this.authenticatedUser = data.user_id;
                            onSpeechRecognized(`Authentication successful. Welcome, ${data.user_id}!`);
                            return;
                        } else if (data.authenticated === false) {
                            this.isAuthenticated = false;
                            onSpeechRecognized('Voice authentication failed. Please try again.');
                            return;
                        }
                        
                        // Handle wake word detection
                        if (data.wake_word) {
                            this.wakeWordDetected = true;
                            onSpeechRecognized(`Wake word detected: ${data.wake_word}`);
                            return;
                        }
                        
                        // Handle shortcuts
                        if (data.shortcut) {
                            onSpeechRecognized(`Executing shortcut: ${data.shortcut.description}`);
                            // Execute the shortcut command
                            this.executeVoiceShortcut(data.shortcut);
                            return;
                        }
                        
                        onSpeechRecognized(data.text);
                    } else {
                        onError('Error: ' + data.error);
                    }
                } catch (error) {
                    console.error('Error:', error);
                    onError('Error processing voice input');
                }
                this.audioChunks = [];
            };
        };
    }

    /**
     * Toggle recording state
     * @returns {boolean} - New recording state
     */
    toggleRecording() {
        if (this.isRecording) {
            this.mediaRecorder.stop();
        } else {
            this.audioChunks = [];
            this.mediaRecorder.start();
        }
        this.isRecording = !this.isRecording;
        return this.isRecording;
    }

    /**
     * Play text using text-to-speech
     * @param {string} text - Text to speak
     * @param {string} language - Optional language override
     * @returns {Promise<boolean>} - Success status
     */
    async playTextToSpeech(text, language = null) {
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
                    personality_level: this.personalityLevel,
                    language: language || this.currentLanguage
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
                return true;
            } else {
                console.error('TTS Error:', data.error);
                return false;
            }
        } catch (error) {
            console.error('Error playing TTS:', error);
            return false;
        }
    }

    /**
     * Save voice settings to server
     * @param {Object} settings - Voice settings
     * @returns {Promise<Object>} - Response data
     */
    async saveVoiceSettings(settings) {
        try {
            const response = await API.fetchWithAuth('/voice-settings', {
                method: 'POST',
                body: JSON.stringify(settings)
            });
            return await response.json();
        } catch (error) {
            console.error('Error saving voice settings:', error);
            throw error;
        }
    }

    /**
     * Load voice profiles from server
     * @returns {Promise<Array>} - List of voice profiles
     */
    async loadVoiceProfiles() {
        try {
            const response = await API.fetchWithAuth('/voice-profiles');
            const data = await response.json();
            return data.profiles || [];
        } catch (error) {
            console.error('Error loading voice profiles:', error);
            return [];
        }
    }

    /**
     * Load available languages for voice recognition and synthesis
     * @returns {Promise<Object>} - Available languages
     */
    async loadAvailableLanguages() {
        try {
            const response = await API.fetchWithAuth('/voice-languages');
            const data = await response.json();
            if (data.success) {
                this.availableLanguages = data.languages || {};
            }
            return this.availableLanguages;
        } catch (error) {
            console.error('Error loading languages:', error);
            return {};
        }
    }

    /**
     * Set current language for voice recognition and synthesis
     * @param {string} languageCode - Language code (e.g., 'en', 'es')
     */
    setLanguage(languageCode) {
        if (languageCode && this.availableLanguages[languageCode]) {
            this.currentLanguage = languageCode;
            return true;
        }
        return false;
    }

    /**
     * Toggle ambient mode for wake word detection
     * @param {Function} onWakeWordDetected - Callback when wake word is detected
     * @returns {Promise<boolean>} - Success status
     */
    async toggleAmbientMode(onWakeWordDetected) {
        if (this.ambientModeActive) {
            return this.stopAmbientMode();
        } else {
            return this.startAmbientMode(onWakeWordDetected);
        }
    }

    /**
     * Start ambient mode for wake word detection
     * @param {Function} onWakeWordDetected - Callback when wake word is detected
     * @param {Object} options - Optional ambient mode options
     * @returns {Promise<boolean>} - Success status
     */
    async startAmbientMode(onWakeWordDetected, options = {}) {
        try {
            // Configure ambient mode parameters from options or defaults
            const params = {
                action: 'start',
                energy_threshold: options.energyThreshold || this.ambientModeStatus.energyThreshold,
                use_offline: options.useOfflineDetection !== undefined ? 
                    options.useOfflineDetection : this.ambientModeStatus.useOfflineDetection,
                dynamic_adjustment: options.dynamicAdjustment !== undefined ? 
                    options.dynamicAdjustment : this.ambientModeStatus.dynamicAdjustment
            };
            
            const response = await API.fetchWithAuth('/voice-ambient-mode', {
                method: 'POST',
                body: JSON.stringify(params)
            });
            
            const data = await response.json();
            if (data.success) {
                this.ambientModeActive = true;
                
                // Show ambient mode indicator
                this.showAmbientModeIndicator(true);
                
                // Set up polling for wake word detection
                this.ambientModeTimer = setInterval(async () => {
                    try {
                        const statusResponse = await API.fetchWithAuth('/voice-ambient-status');
                        const statusData = await statusResponse.json();
                        
                        if (statusData.wake_word_detected) {
                            // Update last detection time
                            this.lastWakeWordTime = new Date();
                            
                            // Show visual feedback
                            this.showWakeWordVisualFeedback(statusData.wake_word);
                            
                            if (onWakeWordDetected) {
                                onWakeWordDetected(statusData.wake_word);
                            }
                            
                            this.wakeWordDetected = true;
                            
                            // Don't automatically stop ambient mode - this is now configurable
                            if (!options.keepListening) {
                                await this.stopAmbientMode();
                            }
                        }
                        
                        // Update ambient mode status
                        if (statusData.ambient_status) {
                            this.updateAmbientModeStatus(statusData.ambient_status);
                        }
                        
                    } catch (err) {
                        console.warn('Error checking ambient mode status:', err);
                    }
                }, 1000); // Check every second
                
                return true;
            }
            return false;
        } catch (error) {
            console.error('Error starting ambient mode:', error);
            return false;
        }
    }

    /**
     * Stop ambient mode
     * @returns {Promise<boolean>} - Success status
     */
    async stopAmbientMode() {
        try {
            if (this.ambientModeTimer) {
                clearInterval(this.ambientModeTimer);
                this.ambientModeTimer = null;
            }
            
            const response = await API.fetchWithAuth('/voice-ambient-mode', {
                method: 'POST',
                body: JSON.stringify({ action: 'stop' })
            });
            
            // Hide ambient mode indicator
            this.showAmbientModeIndicator(false);
            
            const data = await response.json();
            if (data.success) {
                this.ambientModeActive = false;
                return true;
            }
            return false;
        } catch (error) {
            console.error('Error stopping ambient mode:', error);
            this.ambientModeActive = false;
            return false;
        }
    }
    
    /**
     * Show ambient mode indicator in the UI
     * @param {boolean} active - Whether ambient mode is active
     */
    showAmbientModeIndicator(active) {
        const indicator = document.getElementById('ambient-mode-indicator');
        if (indicator) {
            indicator.style.display = active ? 'block' : 'none';
            
            // Update indicator text
            if (active) {
                indicator.innerHTML = '<i class="fas fa-assistive-listening-systems"></i> Listening for wake word';
                indicator.classList.add('active');
            } else {
                indicator.classList.remove('active');
            }
        } else if (active) {
            // Create indicator if it doesn't exist
            const newIndicator = document.createElement('div');
            newIndicator.id = 'ambient-mode-indicator';
            newIndicator.innerHTML = '<i class="fas fa-assistive-listening-systems"></i> Listening for wake word';
            newIndicator.className = 'ambient-indicator active';
            document.body.appendChild(newIndicator);
            
            // Add CSS if not already present
            if (!document.getElementById('ambient-mode-css')) {
                const style = document.createElement('style');
                style.id = 'ambient-mode-css';
                style.textContent = `
                    .ambient-indicator {
                        position: fixed;
                        bottom: 20px;
                        right: 20px;
                        background: rgba(0, 0, 0, 0.7);
                        color: #fff;
                        padding: 10px 15px;
                        border-radius: 20px;
                        font-size: 14px;
                        z-index: 9999;
                        display: none;
                        transition: all 0.3s ease;
                    }
                    .ambient-indicator.active {
                        background: rgba(76, 175, 80, 0.8);
                    }
                    .ambient-indicator.wake-word-detected {
                        background: rgba(33, 150, 243, 0.9);
                        transform: scale(1.1);
                    }
                    .ambient-indicator i {
                        margin-right: 5px;
                    }
                `;
                document.head.appendChild(style);
            }
        }
    }
    
    /**
     * Show visual feedback when wake word is detected
     * @param {string} wakeWord - Detected wake word
     */
    showWakeWordVisualFeedback(wakeWord) {
        const indicator = document.getElementById('ambient-mode-indicator');
        if (indicator) {
            // Clear any existing timeout
            if (this.wakeWordVisualFeedbackTimeout) {
                clearTimeout(this.wakeWordVisualFeedbackTimeout);
            }
            
            // Show detected wake word
            indicator.innerHTML = `<i class="fas fa-volume-up"></i> Wake word detected: "${wakeWord}"`;
            indicator.classList.add('wake-word-detected');
            
            // Reset after 3 seconds
            this.wakeWordVisualFeedbackTimeout = setTimeout(() => {
                if (this.ambientModeActive) {
                    indicator.innerHTML = '<i class="fas fa-assistive-listening-systems"></i> Listening for wake word';
                    indicator.classList.remove('wake-word-detected');
                }
            }, 3000);
        }
    }
    
    /**
     * Update ambient mode status from backend
     * @param {Object} status - Status data from backend
     */
    updateAmbientModeStatus(status) {
        this.ambientModeStatus = {
            energyThreshold: status.energy_threshold || this.ambientModeStatus.energyThreshold,
            dynamicAdjustment: status.dynamic_adjustment !== undefined ? 
                status.dynamic_adjustment : this.ambientModeStatus.dynamicAdjustment,
            useOfflineDetection: status.offline_detection !== undefined ? 
                status.offline_detection : this.ambientModeStatus.useOfflineDetection,
            pauseAfterDetection: status.pause_after_detection || this.ambientModeStatus.pauseAfterDetection
        };
        
        // Update UI if we have a settings panel
        this.updateAmbientModeSettingsUI();
    }
    
    /**
     * Update ambient mode settings UI if available
     */
    updateAmbientModeSettingsUI() {
        const thresholdSlider = document.getElementById('ambient-threshold-slider');
        if (thresholdSlider) {
            thresholdSlider.value = this.ambientModeStatus.energyThreshold;
            const thresholdValue = document.getElementById('ambient-threshold-value');
            if (thresholdValue) {
                thresholdValue.textContent = this.ambientModeStatus.energyThreshold;
            }
        }
        
        const dynamicCheckbox = document.getElementById('ambient-dynamic-adjustment');
        if (dynamicCheckbox) {
            dynamicCheckbox.checked = this.ambientModeStatus.dynamicAdjustment;
        }
        
        const offlineCheckbox = document.getElementById('ambient-offline-detection');
        if (offlineCheckbox) {
            offlineCheckbox.checked = this.ambientModeStatus.useOfflineDetection;
        }
    }
    
    /**
     * Configure ambient mode settings
     * @param {Object} settings - Settings to configure
     * @returns {Promise<Object>} - Current ambient mode settings
     */
    async configureAmbientMode(settings = {}) {
        try {
            const params = {};
            
            if (settings.energyThreshold !== undefined) {
                params.energy_threshold = settings.energyThreshold;
            }
            
            if (settings.dynamicAdjustment !== undefined) {
                params.dynamic_adjustment = settings.dynamicAdjustment;
            }
            
            if (settings.useOfflineDetection !== undefined) {
                params.offline_detection = settings.useOfflineDetection;
            }
            
            if (settings.pauseAfterDetection !== undefined) {
                params.pause_after_detection = settings.pauseAfterDetection;
            }
            
            const response = await API.fetchWithAuth('/voice-ambient-config', {
                method: 'POST',
                body: JSON.stringify(params)
            });
            
            const data = await response.json();
            if (data.success && data.settings) {
                this.updateAmbientModeStatus(data.settings);
                return this.ambientModeStatus;
            }
            
            return this.ambientModeStatus;
        } catch (error) {
            console.error('Error configuring ambient mode:', error);
            return this.ambientModeStatus;
        }
    }

    /**
     * Add or update a wake word
     * @param {string} wakeWord - Wake word or phrase
     * @param {number} sensitivity - Detection sensitivity (0-1)
     * @returns {Promise<boolean>} - Success status
     */
    async addWakeWord(wakeWord, sensitivity = 0.7) {
        try {
            // Validate wake word
            if (!wakeWord || wakeWord.trim() === '') {
                console.error('Wake word cannot be empty');
                return false;
            }
            
            // Check for common assistant names to avoid conflicts
            const commonAssistants = ['alexa', 'siri', 'hey google', 'ok google', 'cortana', 'hey cortana'];
            if (commonAssistants.some(name => wakeWord.toLowerCase().includes(name))) {
                console.error('Wake word contains a common assistant name that may cause conflicts');
                return {
                    success: false, 
                    error: 'Wake word contains a common assistant name that may cause conflicts'
                };
            }
            
            const response = await API.fetchWithAuth('/voice-wake-words', {
                method: 'POST',
                body: JSON.stringify({
                    wake_word: wakeWord,
                    sensitivity
                })
            });
            
            const data = await response.json();
            if (data.success) {
                // Refresh wake word list in UI
                this.refreshWakeWordUI();
                return true;
            }
            
            return false;
        } catch (error) {
            console.error('Error adding wake word:', error);
            return false;
        }
    }
    
    /**
     * Refresh wake word UI elements if they exist
     */
    async refreshWakeWordUI() {
        const wakeWordList = document.getElementById('wake-word-list');
        if (wakeWordList) {
            const words = await this.getWakeWords();
            
            // Clear existing list
            wakeWordList.innerHTML = '';
            
            // Add each wake word
            words.forEach(word => {
                const item = document.createElement('div');
                item.className = 'wake-word-item';
                item.innerHTML = `
                    <span>${word}</span>
                    <button class="delete-wake-word" data-word="${word}">
                        <i class="fas fa-trash"></i>
                    </button>
                `;
                wakeWordList.appendChild(item);
            });
            
            // Add event listeners to delete buttons
            document.querySelectorAll('.delete-wake-word').forEach(button => {
                button.addEventListener('click', async (e) => {
                    const word = e.target.closest('button').dataset.word;
                    if (await this.removeWakeWord(word)) {
                        e.target.closest('.wake-word-item').remove();
                    }
                });
            });
        }
    }
    
    /**
     * Test a wake word by simulating wake word detection
     * @param {string} wakeWord - Wake word to test
     * @returns {Promise<boolean>} - Success status
     */
    async testWakeWord(wakeWord) {
        try {
            // First check if the wake word exists
            const words = await this.getWakeWords();
            if (!words.includes(wakeWord)) {
                console.error('Wake word does not exist');
                return false;
            }
            
            // Simulate wake word detection
            await this.playTextToSpeech(`Testing wake word detection for: ${wakeWord}`);
            
            // Show visual feedback
            this.showWakeWordVisualFeedback(wakeWord);
            
            return true;
        } catch (error) {
            console.error('Error testing wake word:', error);
            return false;
        }
    }

    /**
     * Get ambient mode status (whether active and settings)
     * @returns {Promise<Object>} - Ambient mode status
     */
    async getAmbientModeStatus() {
        try {
            const response = await API.fetchWithAuth('/voice-ambient-status');
            const data = await response.json();
            
            if (data.ambient_status) {
                this.updateAmbientModeStatus(data.ambient_status);
            }
            
            return {
                active: this.ambientModeActive,
                settings: this.ambientModeStatus,
                wakeWordDetected: this.wakeWordDetected,
                lastDetectionTime: this.lastWakeWordTime
            };
        } catch (error) {
            console.error('Error getting ambient mode status:', error);
            return {
                active: this.ambientModeActive,
                settings: this.ambientModeStatus,
                error: 'Failed to get status from server'
            };
        }
    }

    /**
     * Add a voice sample for authentication
     * @param {string} audioBase64 - Base64 encoded audio data
     */
    addAuthenticationSample(audioBase64) {
        if (this.authenticationSamples.length < 5) {
            this.authenticationSamples.push(audioBase64);
            return this.authenticationSamples.length;
        }
        return -1;
    }

    /**
     * Register voice for authentication
     * @param {string} userId - User ID
     * @returns {Promise<boolean>} - Success status
     */
    async registerVoice(userId) {
        if (this.authenticationSamples.length < 3) {
            console.error('Not enough voice samples for registration');
            return false;
        }
        
        try {
            const response = await API.fetchWithAuth('/voice-register', {
                method: 'POST',
                body: JSON.stringify({
                    user_id: userId,
                    audio_samples: this.authenticationSamples
                })
            });
            
            const data = await response.json();
            if (data.success) {
                // Clear samples after successful registration
                this.authenticationSamples = [];
                return true;
            }
            return false;
        } catch (error) {
            console.error('Error registering voice:', error);
            return false;
        }
    }

    /**
     * Authenticate voice
     * @param {string} audioBase64 - Base64 encoded audio data
     * @returns {Promise<Object>} - Authentication result
     */
    async authenticateVoice(audioBase64) {
        try {
            const response = await API.fetchWithAuth('/voice-authenticate', {
                method: 'POST',
                body: JSON.stringify({ audio: audioBase64 })
            });
            
            const data = await response.json();
            if (data.success && data.user_id) {
                this.isAuthenticated = true;
                this.authenticatedUser = data.user_id;
            } else {
                this.isAuthenticated = false;
                this.authenticatedUser = null;
            }
            
            return data;
        } catch (error) {
            console.error('Error authenticating voice:', error);
            return { success: false, error: 'Authentication failed' };
        }
    }

    /**
     * Load voice shortcuts
     * @returns {Promise<Array>} - List of shortcuts
     */
    async loadVoiceShortcuts() {
        try {
            const response = await API.fetchWithAuth('/voice-shortcuts');
            const data = await response.json();
            if (data.success) {
                this.shortcuts = data.shortcuts || [];
                return this.shortcuts;
            }
            return [];
        } catch (error) {
            console.error('Error loading shortcuts:', error);
            return [];
        }
    }

    /**
     * Create a new voice shortcut
     * @param {string} phrase - Trigger phrase
     * @param {string} command - Command to execute
     * @param {string} description - Shortcut description
     * @returns {Promise<Object>} - New shortcut data
     */
    async createVoiceShortcut(phrase, command, description) {
        try {
            const response = await API.fetchWithAuth('/voice-shortcuts', {
                method: 'POST',
                body: JSON.stringify({
                    phrase,
                    command,
                    description
                })
            });
            
            const data = await response.json();
            if (data.success) {
                // Reload shortcuts
                await this.loadVoiceShortcuts();
            }
            return data;
        } catch (error) {
            console.error('Error creating shortcut:', error);
            return { success: false, error: 'Failed to create shortcut' };
        }
    }

    /**
     * Delete a voice shortcut
     * @param {string} shortcutId - Shortcut ID
     * @returns {Promise<boolean>} - Success status
     */
    async deleteVoiceShortcut(shortcutId) {
        try {
            const response = await API.fetchWithAuth(`/voice-shortcuts/${shortcutId}`, {
                method: 'DELETE'
            });
            
            const data = await response.json();
            if (data.success) {
                // Reload shortcuts
                await this.loadVoiceShortcuts();
                return true;
            }
            return false;
        } catch (error) {
            console.error('Error deleting shortcut:', error);
            return false;
        }
    }

    /**
     * Execute a voice shortcut
     * @param {Object} shortcut - Shortcut object
     * @returns {Promise<boolean>} - Success status
     */
    async executeVoiceShortcut(shortcut) {
        try {
            // For security, send the shortcut ID rather than the command
            const response = await API.fetchWithAuth('/execute-shortcut', {
                method: 'POST',
                body: JSON.stringify({
                    shortcut_id: shortcut.id || shortcut.phrase
                })
            });
            
            return await response.json();
        } catch (error) {
            console.error('Error executing shortcut:', error);
            return { success: false, error: 'Failed to execute shortcut' };
        }
    }

    /**
     * Remove a wake word
     * @param {string} wakeWord - Wake word to remove
     * @returns {Promise<boolean>} - Success status
     */
    async removeWakeWord(wakeWord) {
        try {
            const response = await API.fetchWithAuth('/voice-wake-words', {
                method: 'DELETE',
                body: JSON.stringify({
                    wake_word: wakeWord
                })
            });
            
            const data = await response.json();
            if (data.success) {
                // Refresh wake word list in UI if needed
                this.refreshWakeWordUI();
                return true;
            }
            return false;
        } catch (error) {
            console.error('Error removing wake word:', error);
            return false;
        }
    }

    /**
     * Get list of wake words
     * @returns {Promise<Array<string>>} - List of wake words
     */
    async getWakeWords() {
        try {
            const response = await API.fetchWithAuth('/voice-wake-words');
            const data = await response.json();
            return data.wake_words || [];
        } catch (error) {
            console.error('Error getting wake words:', error);
            return [];
        }
    }

    /**
     * Load command sequences
     * @returns {Promise<Array>} - List of command sequences
     */
    async loadCommandSequences() {
        try {
            const response = await API.fetchWithAuth('/voice-sequences');
            const data = await response.json();
            return data.sequences || [];
        } catch (error) {
            console.error('Error loading command sequences:', error);
            return [];
        }
    }

    /**
     * Create a new command sequence
     * @param {string} name - Sequence name
     * @param {Array<string>} triggers - Trigger phrases
     * @param {Array<string>} steps - Command steps
     * @param {Object} contextRequirements - Context requirements
     * @returns {Promise<Object>} - New sequence data
     */
    async createCommandSequence(name, triggers, steps, contextRequirements = {}) {
        try {
            const response = await API.fetchWithAuth('/voice-sequences', {
                method: 'POST',
                body: JSON.stringify({
                    name,
                    triggers,
                    steps,
                    context_requirements: contextRequirements
                })
            });
            
            return await response.json();
        } catch (error) {
            console.error('Error creating sequence:', error);
            return { success: false, error: 'Failed to create sequence' };
        }
    }

    /**
     * Delete a command sequence
     * @param {string} sequenceId - Sequence ID
     * @returns {Promise<boolean>} - Success status
     */
    async deleteCommandSequence(sequenceId) {
        try {
            const response = await API.fetchWithAuth(`/voice-sequences/${sequenceId}`, {
                method: 'DELETE'
            });
            
            return (await response.json()).success;
        } catch (error) {
            console.error('Error deleting sequence:', error);
            return false;
        }
    }

    /**
     * Get wake word statistics and performance metrics
     * @returns {Promise<Object>} - Wake word performance data
     */
    async getWakeWordPerformanceStats() {
        try {
            const response = await API.fetchWithAuth('/voice-wake-word-stats');
            return await response.json();
        } catch (error) {
            console.error('Error getting wake word stats:', error);
            return { success: false, error: 'Failed to get wake word statistics' };
        }
    }

    /**
     * Check microphone and audio system health
     * @returns {Promise<Object>} - Audio system health data
     */
    async checkAudioSystemHealth() {
        try {
            // First check if microphone is available
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                return {
                    success: false,
                    microphone: false,
                    error: 'Media devices API not available in this browser'
                };
            }

            // Try to access the microphone
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                const audioTracks = stream.getAudioTracks();
                
                // Check if we got any audio tracks
                if (audioTracks.length === 0) {
                    return {
                        success: false,
                        microphone: false,
                        error: 'No audio tracks available'
                    };
                }
                
                // Get information about the microphone
                const track = audioTracks[0];
                const settings = track.getSettings();
                
                // Clean up by stopping all tracks
                audioTracks.forEach(track => track.stop());
                
                // Check audio output devices
                const devices = await navigator.mediaDevices.enumerateDevices();
                const outputDevices = devices.filter(device => device.kind === 'audiooutput');
                
                return {
                    success: true,
                    microphone: true,
                    microphoneLabel: track.label,
                    sampleRate: settings.sampleRate,
                    channelCount: settings.channelCount,
                    outputDevices: outputDevices.length,
                    audioOutputAvailable: outputDevices.length > 0
                };
            } catch (err) {
                return {
                    success: false,
                    microphone: false,
                    error: `Error accessing microphone: ${err.message}`
                };
            }
        } catch (error) {
            console.error('Error checking audio system health:', error);
            return { 
                success: false, 
                error: 'Failed to check audio system health',
                details: error.message
            };
        }
    }

    /**
     * Create a voice settings UI panel
     * @param {HTMLElement} container - Container element to append UI
     */
    createVoiceSettingsUI(container) {
        if (!container) return;
        
        // Create settings panel
        const panel = document.createElement('div');
        panel.className = 'voice-settings-panel';
        
        // Add ambient mode section
        panel.innerHTML = `
            <div class="settings-section">
                <h3>Ambient Mode Settings</h3>
                
                <div class="setting-item">
                    <label for="ambient-mode-toggle">Ambient Mode</label>
                    <div class="toggle-switch">
                        <input type="checkbox" id="ambient-mode-toggle" ${this.ambientModeActive ? 'checked' : ''}>
                        <span class="toggle-slider"></span>
                    </div>
                </div>
                
                <div class="setting-item">
                    <label for="ambient-threshold-slider">Detection Sensitivity</label>
                    <input type="range" id="ambient-threshold-slider" min="1000" max="8000" step="100" 
                        value="${this.ambientModeStatus.energyThreshold}">
                    <span id="ambient-threshold-value">${this.ambientModeStatus.energyThreshold}</span>
                </div>
                
                <div class="setting-item">
                    <label for="ambient-dynamic-adjustment">Dynamic Adjustment</label>
                    <div class="toggle-switch">
                        <input type="checkbox" id="ambient-dynamic-adjustment" 
                            ${this.ambientModeStatus.dynamicAdjustment ? 'checked' : ''}>
                        <span class="toggle-slider"></span>
                    </div>
                </div>
                
                <div class="setting-item">
                    <label for="ambient-offline-detection">Offline Detection</label>
                    <div class="toggle-switch">
                        <input type="checkbox" id="ambient-offline-detection" 
                            ${this.ambientModeStatus.useOfflineDetection ? 'checked' : ''}>
                        <span class="toggle-slider"></span>
                    </div>
                </div>
            </div>
            
            <div class="settings-section">
                <h3>Wake Words</h3>
                <div class="wake-word-manager">
                    <div class="wake-word-add">
                        <input type="text" id="new-wake-word" placeholder="Enter new wake word">
                        <button id="add-wake-word-btn">Add</button>
                    </div>
                    <div id="wake-word-list" class="wake-word-list">
                        <!-- Wake words will be added here -->
                    </div>
                </div>
            </div>
            
            <div class="settings-section">
                <h3>Voice Profile</h3>
                <div class="setting-item">
                    <label for="voice-profile-select">Profile</label>
                    <select id="voice-profile-select">
                        <!-- Voice profiles will be added here -->
                    </select>
                </div>
                
                <div class="setting-item">
                    <label for="personality-toggle">Personality</label>
                    <div class="toggle-switch">
                        <input type="checkbox" id="personality-toggle" ${this.personalityEnabled ? 'checked' : ''}>
                        <span class="toggle-slider"></span>
                    </div>
                </div>
                
                <div class="setting-item">
                    <label for="personality-level-slider">Personality Level</label>
                    <input type="range" id="personality-level-slider" min="0" max="1" step="0.1" 
                        value="${this.personalityLevel}">
                    <span id="personality-level-value">${Math.round(this.personalityLevel * 100)}%</span>
                </div>
                
                <div class="setting-item">
                    <label for="language-select">Language</label>
                    <select id="language-select">
                        <!-- Languages will be added here -->
                    </select>
                </div>
            </div>
        `;
        
        container.appendChild(panel);
        
        // Add CSS if not already present
        if (!document.getElementById('voice-settings-css')) {
            const style = document.createElement('style');
            style.id = 'voice-settings-css';
            style.textContent = `
                .voice-settings-panel {
                    padding: 15px;
                    background: #f5f5f5;
                    border-radius: 8px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                }
                
                .settings-section {
                    margin-bottom: 20px;
                }
                
                .settings-section h3 {
                    margin-top: 0;
                    margin-bottom: 15px;
                    border-bottom: 1px solid #ddd;
                    padding-bottom: 5px;
                }
                
                .setting-item {
                    display: flex;
                    align-items: center;
                    margin-bottom: 10px;
                }
                
                .setting-item label {
                    flex: 1;
                    margin-right: 10px;
                }
                
                .toggle-switch {
                    position: relative;
                    display: inline-block;
                    width: 50px;
                    height: 24px;
                }
                
                .toggle-switch input {
                    opacity: 0;
                    width: 0;
                    height: 0;
                }
                
                .toggle-slider {
                    position: absolute;
                    cursor: pointer;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background-color: #ccc;
                    transition: .4s;
                    border-radius: 24px;
                }
                
                .toggle-slider:before {
                    position: absolute;
                    content: "";
                    height: 16px;
                    width: 16px;
                    left: 4px;
                    bottom: 4px;
                    background-color: white;
                    transition: .4s;
                    border-radius: 50%;
                }
                
                input:checked + .toggle-slider {
                    background-color: #2196F3;
                }
                
                input:checked + .toggle-slider:before {
                    transform: translateX(26px);
                }
                
                .wake-word-manager {
                    margin-top: 10px;
                }
                
                .wake-word-add {
                    display: flex;
                    margin-bottom: 10px;
                }
                
                .wake-word-add input {
                    flex: 1;
                    padding: 8px;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    margin-right: 10px;
                }
                
                .wake-word-add button {
                    padding: 8px 15px;
                    background: #2196F3;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                }
                
                .wake-word-list {
                    max-height: 150px;
                    overflow-y: auto;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    padding: 5px;
                }
                
                .wake-word-item {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 5px;
                    border-bottom: 1px solid #eee;
                }
                
                .wake-word-item:last-child {
                    border-bottom: none;
                }
                
                .delete-wake-word {
                    background: transparent;
                    border: none;
                    color: #f44336;
                    cursor: pointer;
                }
                
                select, input[type="range"] {
                    width: 150px;
                }
            `;
            document.head.appendChild(style);
        }
        
        // Populate lists and add event listeners
        this.populateVoiceSettingsUI();
    }
    
    /**
     * Populate voice settings UI with data and attach event handlers
     */
    async populateVoiceSettingsUI() {
        // Populate wake word list
        await this.refreshWakeWordUI();
        
        // Populate voice profiles dropdown
        const profileSelect = document.getElementById('voice-profile-select');
        if (profileSelect) {
            const profiles = await this.loadVoiceProfiles();
            profileSelect.innerHTML = '';
            
            profiles.forEach(profile => {
                const option = document.createElement('option');
                option.value = profile.id || profile.name.toLowerCase().replace(/\s+/g, '_');
                option.textContent = profile.name;
                option.selected = (option.value === this.voiceProfile);
                profileSelect.appendChild(option);
            });
            
            profileSelect.addEventListener('change', (e) => {
                this.voiceProfile = e.target.value;
                this.saveVoiceSettings({ profile: this.voiceProfile });
            });
        }
        
        // Populate language dropdown
        const languageSelect = document.getElementById('language-select');
        if (languageSelect) {
            const languages = await this.loadAvailableLanguages();
            languageSelect.innerHTML = '';
            
            Object.entries(languages).forEach(([code, info]) => {
                const option = document.createElement('option');
                option.value = code;
                option.textContent = info.name;
                option.selected = (code === this.currentLanguage);
                languageSelect.appendChild(option);
            });
            
            languageSelect.addEventListener('change', (e) => {
                this.setLanguage(e.target.value);
                this.saveVoiceSettings({ language: this.currentLanguage });
            });
        }
        
        // Set up event listeners for ambient mode toggle
        const ambientToggle = document.getElementById('ambient-mode-toggle');
        if (ambientToggle) {
            ambientToggle.addEventListener('change', async (e) => {
                if (e.target.checked) {
                    await this.startAmbientMode((wakeWord) => {
                        console.log(`Wake word detected in settings UI: ${wakeWord}`);
                    });
                } else {
                    await this.stopAmbientMode();
                }
            });
        }
        
        // Set up threshold slider
        const thresholdSlider = document.getElementById('ambient-threshold-slider');
        const thresholdValue = document.getElementById('ambient-threshold-value');
        if (thresholdSlider && thresholdValue) {
            thresholdSlider.addEventListener('input', (e) => {
                thresholdValue.textContent = e.target.value;
            });
            
            thresholdSlider.addEventListener('change', async (e) => {
                await this.configureAmbientMode({ energyThreshold: parseInt(e.target.value) });
            });
        }
        
        // Set up dynamic adjustment toggle
        const dynamicAdjustment = document.getElementById('ambient-dynamic-adjustment');
        if (dynamicAdjustment) {
            dynamicAdjustment.addEventListener('change', async (e) => {
                await this.configureAmbientMode({ dynamicAdjustment: e.target.checked });
            });
        }
        
        // Set up offline detection toggle
        const offlineDetection = document.getElementById('ambient-offline-detection');
        if (offlineDetection) {
            offlineDetection.addEventListener('change', async (e) => {
                await this.configureAmbientMode({ useOfflineDetection: e.target.checked });
            });
        }
        
        // Set up personality toggle
        const personalityToggle = document.getElementById('personality-toggle');
        if (personalityToggle) {
            personalityToggle.addEventListener('change', async (e) => {
                this.personalityEnabled = e.target.checked;
                await this.saveVoiceSettings({ personality_enabled: this.personalityEnabled });
            });
        }
        
        // Set up personality level slider
        const personalitySlider = document.getElementById('personality-level-slider');
        const personalityValue = document.getElementById('personality-level-value');
        if (personalitySlider && personalityValue) {
            personalitySlider.addEventListener('input', (e) => {
                personalityValue.textContent = `${Math.round(e.target.value * 100)}%`;
            });
            
            personalitySlider.addEventListener('change', async (e) => {
                this.personalityLevel = parseFloat(e.target.value);
                await this.saveVoiceSettings({ personality_level: this.personalityLevel });
            });
        }
        
        // Set up add wake word button
        const addWakeWordBtn = document.getElementById('add-wake-word-btn');
        const newWakeWordInput = document.getElementById('new-wake-word');
        if (addWakeWordBtn && newWakeWordInput) {
            addWakeWordBtn.addEventListener('click', async () => {
                const wakeWord = newWakeWordInput.value.trim();
                if (wakeWord) {
                    const result = await this.addWakeWord(wakeWord);
                    if (result === true) {
                        newWakeWordInput.value = '';
                        await this.refreshWakeWordUI();
                    } else if (result.error) {
                        alert(`Error adding wake word: ${result.error}`);
                    }
                }
            });
            
            newWakeWordInput.addEventListener('keypress', async (e) => {
                if (e.key === 'Enter') {
                    addWakeWordBtn.click();
                }
            });
        }
    }
}
