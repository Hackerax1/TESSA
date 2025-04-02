/**
 * Voice Authentication Module
 * 
 * Handles voice authentication, registration, and management functionality.
 */
const VoiceAuth = (function() {
    // Private variables
    let audioContext;
    let recorder;
    let audioSamples = [];
    let isRecording = false;
    let visualizer;
    let currentUserID;
    
    // DOM elements cache
    let elements = {};
    
    /**
     * Initialize the audio context and request microphone permissions
     */
    async function initAudio() {
        try {
            // Create audio context
            audioContext = new (window.AudioContext || window.webkitAudioContext)();
            
            // Request microphone access
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            
            // Create audio recorder
            const audioSource = audioContext.createMediaStreamSource(stream);
            recorder = new Recorder(audioSource);
            
            // Initialize visualizer if canvas exists
            const canvas = document.getElementById('voice-waveform');
            if (canvas) {
                visualizer = new Visualizer(audioContext, audioSource, canvas);
            }
            
            return true;
        } catch (error) {
            console.error('Error initializing audio:', error);
            showError('Could not access microphone. Please check your permissions and try again.');
            return false;
        }
    }
    
    /**
     * Start recording audio
     */
    function startRecording() {
        if (!recorder) return;
        
        recorder.clear();
        recorder.record();
        isRecording = true;
        
        if (visualizer) {
            visualizer.start();
        }
    }
    
    /**
     * Stop recording audio and get the audio data
     */
    async function stopRecording() {
        if (!recorder || !isRecording) return null;
        
        recorder.stop();
        isRecording = false;
        
        if (visualizer) {
            visualizer.stop();
        }
        
        return new Promise(resolve => {
            recorder.exportWAV(blob => {
                const reader = new FileReader();
                reader.readAsDataURL(blob);
                reader.onloadend = function() {
                    const base64data = reader.result.split(',')[1];
                    resolve(base64data);
                };
            });
        });
    }
    
    /**
     * Show an error message
     * @param {string} message - The error message to display
     */
    function showError(message) {
        const alertElement = document.createElement('div');
        alertElement.className = 'alert alert-danger alert-dismissible fade show';
        alertElement.innerHTML = `
            <i class="fas fa-exclamation-circle me-2"></i> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        document.querySelector('.container').prepend(alertElement);
    }
    
    /**
     * Format date for display
     * @param {string} dateString - ISO date string
     * @returns {string} Formatted date string
     */
    function formatDate(dateString) {
        if (!dateString) return 'N/A';
        const date = new Date(dateString);
        return date.toLocaleString();
    }
    
    /**
     * Initialize the authentication page
     */
    async function initAuthenticationPage() {
        // Cache DOM elements
        elements = {
            startAuthBtn: document.getElementById('start-auth'),
            stopAuthBtn: document.getElementById('stop-auth'),
            authStatus: document.getElementById('voice-auth-status'),
            authResult: document.getElementById('auth-result'),
            authSuccess: document.getElementById('auth-success'),
            authSuccessMessage: document.getElementById('auth-success-message'),
            authFailure: document.getElementById('auth-failure'),
            authFailureMessage: document.getElementById('auth-failure-message'),
            tryAgainBtn: document.getElementById('try-again')
        };
        
        // Initialize audio
        const audioInitialized = await initAudio();
        if (!audioInitialized) return;
        
        // Add event listeners
        elements.startAuthBtn.addEventListener('click', async () => {
            elements.startAuthBtn.classList.add('d-none');
            elements.stopAuthBtn.classList.remove('d-none');
            elements.authStatus.textContent = 'Recording... Speak now.';
            elements.authStatus.className = 'alert alert-warning';
            elements.authResult.classList.add('d-none');
            
            startRecording();
        });
        
        elements.stopAuthBtn.addEventListener('click', async () => {
            elements.stopAuthBtn.classList.add('d-none');
            elements.startAuthBtn.classList.remove('d-none');
            elements.authStatus.textContent = 'Processing... Please wait.';
            
            const audioData = await stopRecording();
            if (!audioData) {
                elements.authStatus.textContent = 'Error recording audio. Please try again.';
                elements.authStatus.className = 'alert alert-danger';
                return;
            }
            
            // Authenticate with the server
            try {
                const response = await fetch('/api/voice-auth/authenticate', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        audio: audioData
                    })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    elements.authResult.classList.remove('d-none');
                    
                    if (result.authenticated) {
                        elements.authSuccess.classList.remove('d-none');
                        elements.authFailure.classList.add('d-none');
                        elements.authSuccessMessage.textContent = `Authentication successful! Welcome, ${result.user_id} (Confidence: ${Math.round(result.confidence * 100)}%)`;
                        elements.authStatus.textContent = 'Authentication complete.';
                        elements.authStatus.className = 'alert alert-success';
                    } else {
                        elements.authSuccess.classList.add('d-none');
                        elements.authFailure.classList.remove('d-none');
                        elements.authFailureMessage.textContent = `Authentication failed. Confidence: ${Math.round(result.confidence * 100)}%`;
                        elements.authStatus.textContent = 'Authentication failed.';
                        elements.authStatus.className = 'alert alert-danger';
                    }
                } else {
                    elements.authStatus.textContent = `Error: ${result.message}`;
                    elements.authStatus.className = 'alert alert-danger';
                }
            } catch (error) {
                console.error('Error authenticating:', error);
                elements.authStatus.textContent = 'Error communicating with the server. Please try again.';
                elements.authStatus.className = 'alert alert-danger';
            }
        });
        
        if (elements.tryAgainBtn) {
            elements.tryAgainBtn.addEventListener('click', () => {
                elements.authResult.classList.add('d-none');
                elements.authStatus.textContent = 'Ready to authenticate. Click the button below to start.';
                elements.authStatus.className = 'alert alert-info';
            });
        }
    }
    
    /**
     * Initialize the voice registration page
     */
    async function initRegistrationPage() {
        // Cache DOM elements
        elements = {
            userIdInput: document.getElementById('user-id'),
            passphraseInput: document.getElementById('passphrase'),
            startRecordingBtn: document.getElementById('start-recording'),
            stopRecordingBtn: document.getElementById('stop-recording'),
            registerStatus: document.getElementById('voice-register-status'),
            currentSampleSpan: document.getElementById('current-sample'),
            samplesProgressContainer: document.getElementById('samples-progress-container'),
            samplesProgress: document.getElementById('samples-progress'),
            registrationResult: document.getElementById('registration-result'),
            registrationSuccess: document.getElementById('registration-success'),
            registrationFailure: document.getElementById('registration-failure'),
            registrationErrorMessage: document.getElementById('registration-error-message'),
            tryAgainBtn: document.getElementById('try-again')
        };
        
        // Initialize audio
        const audioInitialized = await initAudio();
        if (!audioInitialized) return;
        
        // Reset samples
        audioSamples = [];
        
        // Add event listeners
        elements.startRecordingBtn.addEventListener('click', async () => {
            // Validate user ID
            const userId = elements.userIdInput.value.trim();
            if (!userId) {
                showError('Please enter a user ID.');
                return;
            }
            
            // Store current user ID
            currentUserID = userId;
            
            // Disable form while recording
            elements.userIdInput.disabled = true;
            elements.passphraseInput.disabled = true;
            
            // Update UI
            elements.startRecordingBtn.classList.add('d-none');
            elements.stopRecordingBtn.classList.remove('d-none');
            elements.registerStatus.textContent = `Recording sample ${audioSamples.length + 1} of 3... Speak now.`;
            elements.registerStatus.className = 'alert alert-warning';
            
            // Start recording
            startRecording();
        });
        
        elements.stopRecordingBtn.addEventListener('click', async () => {
            // Update UI
            elements.stopRecordingBtn.classList.add('d-none');
            elements.startRecordingBtn.classList.remove('d-none');
            elements.registerStatus.textContent = 'Processing... Please wait.';
            
            // Stop recording and get audio data
            const audioData = await stopRecording();
            if (!audioData) {
                elements.registerStatus.textContent = 'Error recording audio. Please try again.';
                elements.registerStatus.className = 'alert alert-danger';
                return;
            }
            
            // Add to samples
            audioSamples.push(audioData);
            
            // Update progress
            const progress = (audioSamples.length / 3) * 100;
            elements.samplesProgressContainer.classList.remove('d-none');
            elements.samplesProgress.style.width = `${progress}%`;
            elements.samplesProgress.textContent = `${Math.round(progress)}%`;
            elements.samplesProgress.setAttribute('aria-valuenow', progress);
            
            // Check if we have enough samples
            if (audioSamples.length < 3) {
                // Update UI for next sample
                elements.currentSampleSpan.textContent = audioSamples.length + 1;
                elements.registerStatus.textContent = `Sample ${audioSamples.length} recorded. Click the button to record sample ${audioSamples.length + 1} of 3.`;
                elements.registerStatus.className = 'alert alert-info';
            } else {
                // We have all samples, register with the server
                elements.registerStatus.textContent = 'Registering voice profile... Please wait.';
                
                try {
                    const response = await fetch('/api/voice-auth/register', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            user_id: currentUserID,
                            audio_samples: audioSamples,
                            phrase: elements.passphraseInput.value.trim() || null
                        })
                    });
                    
                    const result = await response.json();
                    
                    // Show result
                    elements.registrationResult.classList.remove('d-none');
                    
                    if (result.success) {
                        elements.registrationSuccess.classList.remove('d-none');
                        elements.registrationFailure.classList.add('d-none');
                        elements.registerStatus.textContent = 'Registration complete.';
                        elements.registerStatus.className = 'alert alert-success';
                    } else {
                        elements.registrationSuccess.classList.add('d-none');
                        elements.registrationFailure.classList.remove('d-none');
                        elements.registrationErrorMessage.textContent = result.message || 'Registration failed.';
                        elements.registerStatus.textContent = 'Registration failed.';
                        elements.registerStatus.className = 'alert alert-danger';
                    }
                } catch (error) {
                    console.error('Error registering voice:', error);
                    elements.registrationSuccess.classList.add('d-none');
                    elements.registrationFailure.classList.remove('d-none');
                    elements.registrationErrorMessage.textContent = 'Error communicating with the server. Please try again.';
                    elements.registerStatus.textContent = 'Registration failed.';
                    elements.registerStatus.className = 'alert alert-danger';
                }
                
                // Reset form
                elements.userIdInput.disabled = false;
                elements.passphraseInput.disabled = false;
            }
        });
        
        if (elements.tryAgainBtn) {
            elements.tryAgainBtn.addEventListener('click', () => {
                // Reset samples and UI
                audioSamples = [];
                elements.registrationResult.classList.add('d-none');
                elements.currentSampleSpan.textContent = '1';
                elements.samplesProgressContainer.classList.add('d-none');
                elements.samplesProgress.style.width = '0%';
                elements.samplesProgress.textContent = '0%';
                elements.samplesProgress.setAttribute('aria-valuenow', 0);
                elements.registerStatus.textContent = 'Ready to record. Click the button below to start recording sample 1 of 3.';
                elements.registerStatus.className = 'alert alert-info';
                elements.userIdInput.disabled = false;
                elements.passphraseInput.disabled = false;
            });
        }
    }
    
    /**
     * Initialize the voice management page
     */
    async function initManagementPage() {
        // Cache DOM elements
        elements = {
            loadingProfiles: document.getElementById('loading-profiles'),
            noProfiles: document.getElementById('no-profiles'),
            profilesContainer: document.getElementById('profiles-container'),
            profilesTableBody: document.getElementById('profiles-table-body'),
            updateUserIdSelect: document.getElementById('update-user-id'),
            passphraseUserIdSelect: document.getElementById('passphrase-user-id'),
            startUpdateBtn: document.getElementById('start-update'),
            stopUpdateBtn: document.getElementById('stop-update'),
            updateStatus: document.getElementById('update-status'),
            updateResult: document.getElementById('update-result'),
            updateSuccess: document.getElementById('update-success'),
            updateFailure: document.getElementById('update-failure'),
            updateErrorMessage: document.getElementById('update-error-message'),
            newPassphraseInput: document.getElementById('new-passphrase'),
            savePassphraseBtn: document.getElementById('save-passphrase'),
            passphraseResult: document.getElementById('passphrase-result'),
            passphraseSuccess: document.getElementById('passphrase-success'),
            passphraseFailure: document.getElementById('passphrase-failure'),
            passphraseErrorMessage: document.getElementById('passphrase-error-message'),
            deleteConfirmModal: new bootstrap.Modal(document.getElementById('delete-confirm-modal')),
            deleteUserIdSpan: document.getElementById('delete-user-id'),
            confirmDeleteBtn: document.getElementById('confirm-delete')
        };
        
        // Initialize audio
        const audioInitialized = await initAudio();
        if (!audioInitialized) {
            elements.loadingProfiles.innerHTML = '<div class="alert alert-danger">Could not access microphone. Voice recording features will not work.</div>';
        }
        
        // Load profiles
        await loadProfiles();
        
        // Add event listeners for update profile
        elements.updateUserIdSelect.addEventListener('change', () => {
            elements.startUpdateBtn.disabled = !elements.updateUserIdSelect.value;
        });
        
        elements.startUpdateBtn.addEventListener('click', async () => {
            // Store current user ID
            currentUserID = elements.updateUserIdSelect.value;
            
            // Update UI
            elements.startUpdateBtn.classList.add('d-none');
            elements.stopUpdateBtn.classList.remove('d-none');
            elements.updateStatus.textContent = 'Recording... Speak now.';
            elements.updateStatus.className = 'alert alert-warning';
            elements.updateResult.classList.add('d-none');
            
            // Start recording
            startRecording();
        });
        
        elements.stopUpdateBtn.addEventListener('click', async () => {
            // Update UI
            elements.stopUpdateBtn.classList.add('d-none');
            elements.startUpdateBtn.classList.remove('d-none');
            elements.updateStatus.textContent = 'Processing... Please wait.';
            
            // Stop recording and get audio data
            const audioData = await stopRecording();
            if (!audioData) {
                elements.updateStatus.textContent = 'Error recording audio. Please try again.';
                elements.updateStatus.className = 'alert alert-danger';
                return;
            }
            
            // Update profile with the server
            try {
                const response = await fetch('/api/voice-auth/update', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        user_id: currentUserID,
                        audio: audioData
                    })
                });
                
                const result = await response.json();
                
                // Show result
                elements.updateResult.classList.remove('d-none');
                
                if (result.success) {
                    elements.updateSuccess.classList.remove('d-none');
                    elements.updateFailure.classList.add('d-none');
                    elements.updateStatus.textContent = 'Update complete.';
                    elements.updateStatus.className = 'alert alert-success';
                } else {
                    elements.updateSuccess.classList.add('d-none');
                    elements.updateFailure.classList.remove('d-none');
                    elements.updateErrorMessage.textContent = result.message || 'Update failed.';
                    elements.updateStatus.textContent = 'Update failed.';
                    elements.updateStatus.className = 'alert alert-danger';
                }
            } catch (error) {
                console.error('Error updating voice profile:', error);
                elements.updateSuccess.classList.add('d-none');
                elements.updateFailure.classList.remove('d-none');
                elements.updateErrorMessage.textContent = 'Error communicating with the server. Please try again.';
                elements.updateStatus.textContent = 'Update failed.';
                elements.updateStatus.className = 'alert alert-danger';
            }
        });
        
        // Add event listeners for passphrase update
        elements.passphraseUserIdSelect.addEventListener('change', () => {
            elements.savePassphraseBtn.disabled = !elements.passphraseUserIdSelect.value;
        });
        
        elements.savePassphraseBtn.addEventListener('click', async (e) => {
            e.preventDefault();
            
            const userId = elements.passphraseUserIdSelect.value;
            const passphrase = elements.newPassphraseInput.value.trim();
            
            if (!userId || !passphrase) {
                showError('Please select a user ID and enter a passphrase.');
                return;
            }
            
            // Update passphrase with the server
            try {
                const response = await fetch('/api/voice-auth/passphrase', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        user_id: userId,
                        passphrase: passphrase
                    })
                });
                
                const result = await response.json();
                
                // Show result
                elements.passphraseResult.classList.remove('d-none');
                
                if (result.success) {
                    elements.passphraseSuccess.classList.remove('d-none');
                    elements.passphraseFailure.classList.add('d-none');
                    elements.newPassphraseInput.value = '';
                } else {
                    elements.passphraseSuccess.classList.add('d-none');
                    elements.passphraseFailure.classList.remove('d-none');
                    elements.passphraseErrorMessage.textContent = result.message || 'Failed to update passphrase.';
                }
            } catch (error) {
                console.error('Error updating passphrase:', error);
                elements.passphraseSuccess.classList.add('d-none');
                elements.passphraseFailure.classList.remove('d-none');
                elements.passphraseErrorMessage.textContent = 'Error communicating with the server. Please try again.';
            }
        });
        
        // Add event listener for delete confirmation
        elements.confirmDeleteBtn.addEventListener('click', async () => {
            const userId = elements.deleteUserIdSpan.textContent;
            
            try {
                const response = await fetch(`/api/voice-auth/delete/${userId}`, {
                    method: 'DELETE'
                });
                
                const result = await response.json();
                
                if (result.success) {
                    // Close modal and reload profiles
                    elements.deleteConfirmModal.hide();
                    await loadProfiles();
                    
                    // Show success message
                    const alertElement = document.createElement('div');
                    alertElement.className = 'alert alert-success alert-dismissible fade show';
                    alertElement.innerHTML = `
                        <i class="fas fa-check-circle me-2"></i> Voice profile deleted successfully.
                        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                    `;
                    document.querySelector('.container').prepend(alertElement);
                } else {
                    showError(result.message || 'Failed to delete voice profile.');
                }
            } catch (error) {
                console.error('Error deleting voice profile:', error);
                showError('Error communicating with the server. Please try again.');
            }
        });
    }
    
    /**
     * Load voice profiles from the server
     */
    async function loadProfiles() {
        try {
            const response = await fetch('/api/voice-auth/users');
            const result = await response.json();
            
            // Hide loading indicator
            elements.loadingProfiles.classList.add('d-none');
            
            if (result.success && result.users && result.users.length > 0) {
                // Show profiles container
                elements.profilesContainer.classList.remove('d-none');
                elements.noProfiles.classList.add('d-none');
                
                // Clear table body
                elements.profilesTableBody.innerHTML = '';
                
                // Clear select options
                elements.updateUserIdSelect.innerHTML = '<option value="" selected disabled>Select a user ID</option>';
                elements.passphraseUserIdSelect.innerHTML = '<option value="" selected disabled>Select a user ID</option>';
                
                // Add profiles to table
                result.users.forEach(user => {
                    // Add to table
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${user.user_id}</td>
                        <td>${formatDate(user.created_at)}</td>
                        <td>${formatDate(user.updated_at)}</td>
                        <td>${user.has_passphrase ? '<i class="fas fa-check-circle text-success"></i> Yes' : '<i class="fas fa-times-circle text-muted"></i> No'}</td>
                        <td>
                            <button class="btn btn-sm btn-danger delete-profile" data-user-id="${user.user_id}">
                                <i class="fas fa-trash"></i> Delete
                            </button>
                        </td>
                    `;
                    elements.profilesTableBody.appendChild(row);
                    
                    // Add to select options
                    const updateOption = document.createElement('option');
                    updateOption.value = user.user_id;
                    updateOption.textContent = user.user_id;
                    elements.updateUserIdSelect.appendChild(updateOption);
                    
                    const passphraseOption = document.createElement('option');
                    passphraseOption.value = user.user_id;
                    passphraseOption.textContent = user.user_id;
                    elements.passphraseUserIdSelect.appendChild(passphraseOption);
                });
                
                // Add event listeners for delete buttons
                document.querySelectorAll('.delete-profile').forEach(button => {
                    button.addEventListener('click', () => {
                        const userId = button.getAttribute('data-user-id');
                        elements.deleteUserIdSpan.textContent = userId;
                        elements.deleteConfirmModal.show();
                    });
                });
            } else {
                // Show no profiles message
                elements.noProfiles.classList.remove('d-none');
                elements.profilesContainer.classList.add('d-none');
            }
        } catch (error) {
            console.error('Error loading profiles:', error);
            elements.loadingProfiles.innerHTML = '<div class="alert alert-danger">Error loading voice profiles. Please refresh the page to try again.</div>';
        }
    }
    
    // Public API
    return {
        initAuthenticationPage,
        initRegistrationPage,
        initManagementPage
    };
})();

/**
 * Audio Visualizer Class
 */
class Visualizer {
    constructor(audioContext, source, canvas) {
        this.audioContext = audioContext;
        this.source = source;
        this.canvas = canvas;
        this.canvasCtx = canvas.getContext('2d');
        this.analyser = audioContext.createAnalyser();
        this.analyser.fftSize = 256;
        this.bufferLength = this.analyser.frequencyBinCount;
        this.dataArray = new Uint8Array(this.bufferLength);
        this.source.connect(this.analyser);
        this.animationFrame = null;
        
        // Set canvas width and height
        this.canvas.width = this.canvas.clientWidth;
        this.canvas.height = this.canvas.clientHeight;
    }
    
    start() {
        this.draw();
    }
    
    stop() {
        if (this.animationFrame) {
            cancelAnimationFrame(this.animationFrame);
            this.animationFrame = null;
            
            // Clear canvas
            this.canvasCtx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        }
    }
    
    draw() {
        this.animationFrame = requestAnimationFrame(() => this.draw());
        
        this.analyser.getByteFrequencyData(this.dataArray);
        
        this.canvasCtx.fillStyle = 'rgb(240, 240, 240)';
        this.canvasCtx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        const barWidth = (this.canvas.width / this.bufferLength) * 2.5;
        let barHeight;
        let x = 0;
        
        for (let i = 0; i < this.bufferLength; i++) {
            barHeight = this.dataArray[i] / 2;
            
            this.canvasCtx.fillStyle = `rgb(${barHeight + 100}, 50, 50)`;
            this.canvasCtx.fillRect(x, this.canvas.height - barHeight, barWidth, barHeight);
            
            x += barWidth + 1;
        }
    }
}
