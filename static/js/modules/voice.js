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
     * @returns {Promise<boolean>} - Success status
     */
    async startAmbientMode(onWakeWordDetected) {
        try {
            const response = await API.fetchWithAuth('/voice-ambient-mode', {
                method: 'POST',
                body: JSON.stringify({ action: 'start' })
            });
            
            const data = await response.json();
            if (data.success) {
                this.ambientModeActive = true;
                
                // Set up polling for wake word detection
                this.ambientModeTimer = setInterval(async () => {
                    const statusResponse = await API.fetchWithAuth('/voice-ambient-status');
                    const statusData = await statusResponse.json();
                    
                    if (statusData.wake_word_detected) {
                        if (onWakeWordDetected) {
                            onWakeWordDetected(statusData.wake_word);
                        }
                        
                        // Automatically stop ambient mode once wake word is detected
                        this.wakeWordDetected = true;
                        await this.stopAmbientMode();
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
     * Add or update a wake word
     * @param {string} wakeWord - Wake word or phrase
     * @param {number} sensitivity - Detection sensitivity (0-1)
     * @returns {Promise<boolean>} - Success status
     */
    async addWakeWord(wakeWord, sensitivity = 0.7) {
        try {
            const response = await API.fetchWithAuth('/voice-wake-words', {
                method: 'POST',
                body: JSON.stringify({
                    wake_word: wakeWord,
                    sensitivity
                })
            });
            
            return (await response.json()).success;
        } catch (error) {
            console.error('Error adding wake word:', error);
            return false;
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
            
            return (await response.json()).success;
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
}
