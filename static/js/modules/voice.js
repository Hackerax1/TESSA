/**
 * Voice module - Handles voice recording, speech-to-text, and text-to-speech functionality
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
                        body: JSON.stringify({ audio: base64Audio })
                    });
                    const data = await response.json();
                    if (data.success) {
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
     * @returns {Promise<void>}
     */
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
}
