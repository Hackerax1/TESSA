/**
 * Main application entry point
 * This file coordinates all the modules and initializes the application
 */
import API from './modules/api.js';
import UI from './modules/ui.js';
import Data from './modules/data.js';
import SocketHandler from './modules/socket.js';
import ErrorHandler from './modules/error_handler.js';

// Core modules loaded immediately
const core = {
    API,
    UI,
    Data,
    SocketHandler,
    ErrorHandler
};

class ProxmoxNLI {
    constructor() {
        // DOM elements
        this.chatForm = document.getElementById('chat-form');
        this.userInput = document.getElementById('user-input');
        this.chatBody = document.getElementById('chat-body');
        this.micButton = document.getElementById('mic-button');
        this.vmList = document.getElementById('vm-list');
        this.clusterStatus = document.getElementById('cluster-status');
        this.auditLog = document.getElementById('audit-log');
        
        // Initialize core modules
        this.ui = new UI();
        this.data = new Data();
        
        // Initialize error handler
        ErrorHandler.initialize();
        
        // Add global error handler
        ErrorHandler.addListener((error) => {
            console.log('Global error handler:', error);
            if (this.ui) {
                this.ui.showError(error.userMessage);
            }
        });
        
        // Make error handler globally available
        window.ErrorHandler = ErrorHandler;
        
        // Modules to be lazy-loaded
        this.voice = null;
        this.wizard = null;
        this.notifications = null;
        this.commands = null;
        this.shortcuts = null;
        this.dashboards = null;
        this.qrcode = null;
        this.networkDiagram = null;
        
        // Initialize socket with callbacks
        this.socket = new SocketHandler({
            onVMUpdate: (data) => this.handleVMUpdate(data),
            onClusterUpdate: (data) => this.handleClusterUpdate(data),
            onNetworkDiagramUpdate: (nodes, links) => this.handleNetworkDiagramUpdate(nodes, links),
            onError: (error) => ErrorHandler.handleError(error)
        });
        
        // Initialize UI
        this.initializeEventListeners();
        this.initializeApplication();
    }

    /**
     * Initialize application by loading initial data
     */
    async initializeApplication() {
        try {
            // Load initial data
            await Data.loadInitialData(
                (vmData) => this.handleVMUpdate(vmData),
                (clusterData) => this.handleClusterUpdate(clusterData),
                (error) => ErrorHandler.handleError(error)
            );
            
            // Load audit logs
            await Data.loadAuditLogs(this.auditLog);
            
            // Set up periodic audit log updates
            setInterval(() => Data.loadAuditLogs(this.auditLog), 30000);
            
            // Initialize core modules
            await this.ui.initialize();
            
            // Lazy load additional modules as needed
            this.lazyLoadModules();
            
            // Register service worker for offline support and caching
            this.registerServiceWorker();
        } catch (error) {
            ErrorHandler.handleError(error);
        }
    }
    
    /**
     * Lazy load non-critical modules
     */
    async lazyLoadModules() {
        // Start loading modules in the background
        this.loadVoiceModule();
        this.loadWizardModule();
        this.loadNotificationsModule();
        
        // Load other modules when user is idle or on demand
        if ('requestIdleCallback' in window) {
            requestIdleCallback(() => {
                this.loadRemainingModules();
            });
        } else {
            // Fallback for browsers without requestIdleCallback
            setTimeout(() => {
                this.loadRemainingModules();
            }, 1000);
        }
    }
    
    /**
     * Load voice module when needed
     */
    async loadVoiceModule() {
        if (this.micButton) {
            try {
                const { default: Voice } = await import('./modules/voice.js');
                this.voice = new Voice();
                
                // Set up voice input
                await this.voice.setupMediaRecorder();
                this.voice.configureMediaRecorder(
                    (text) => {
                        this.userInput.value = text;
                        this.chatForm.dispatchEvent(new Event('submit'));
                    },
                    (error) => ErrorHandler.handleError(error)
                );
                
                // Load voice profiles
                await this.loadVoiceProfiles();
                
                // Enable mic button
                this.micButton.disabled = false;
            } catch (error) {
                ErrorHandler.handleError(error);
            }
        }
    }
    
    /**
     * Load wizard module when needed
     */
    async loadWizardModule() {
        if (document.querySelector('.wizard-container')) {
            try {
                const { default: Wizard } = await import('./modules/wizard.js');
                this.wizard = new Wizard();
                await this.wizard.initialize();
                this.setupWizard();
            } catch (error) {
                ErrorHandler.handleError(error);
            }
        }
    }
    
    /**
     * Load notifications module when needed
     */
    async loadNotificationsModule() {
        try {
            const { default: Notifications } = await import('./modules/notifications.js');
            this.notifications = new Notifications();
            await this.notifications.initialize();
        } catch (error) {
            ErrorHandler.handleError(error);
        }
    }
    
    /**
     * Load remaining non-critical modules
     */
    async loadRemainingModules() {
        try {
            // Load commands module
            const { default: Commands } = await import('./modules/commands.js');
            this.commands = new Commands();
            await this.commands.initialize();
            
            // Load shortcuts module
            const { default: Shortcuts } = await import('./modules/shortcuts.js');
            this.shortcuts = new Shortcuts();
            await this.shortcuts.initialize();
            
            // Load dashboards module if dashboard container exists
            if (document.getElementById('dashboard-container')) {
                const { default: Dashboards } = await import('./modules/dashboards.js');
                this.dashboards = new Dashboards();
                await this.dashboards.initialize();
            }
            
            // Load QR code module if QR container exists
            if (document.querySelector('.qr-code-container')) {
                const { default: QRCode } = await import('./modules/qrcode.js');
                this.qrcode = new QRCode();
            }
            
            // Load network diagram if container exists
            if (document.getElementById('network-diagram-container')) {
                const { default: NetworkDiagram } = await import('./network_diagram.js');
                this.networkDiagram = new NetworkDiagram('network-diagram-container');
            }
        } catch (error) {
            ErrorHandler.handleError(error);
        }
    }

    /**
     * Register service worker for offline support and caching
     */
    registerServiceWorker() {
        if ('serviceWorker' in navigator) {
            window.addEventListener('load', () => {
                navigator.serviceWorker.register('/static/js/service-worker.js')
                    .then(registration => {
                        console.log('ServiceWorker registration successful with scope: ', registration.scope);
                    })
                    .catch(error => {
                        ErrorHandler.handleError(error);
                    });
            });
        }
    }

    /**
     * Initialize event listeners
     */
    initializeEventListeners() {
        // Chat form submission
        this.chatForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const query = this.userInput.value.trim();
            if (!query) return;

            UI.addMessage(query, 'user', this.chatBody);
            this.userInput.value = '';

            try {
                // Add command to history
                await this.commands.addCommandToHistory(query);
                
                // Send query to server
                const response = await API.fetchWithAuth('/query', {
                    method: 'POST',
                    body: JSON.stringify({ query: query })
                });
                const data = await response.json();
                
                const responseText = data.error ? 'Error: ' + data.error : data.response;
                UI.addMessage(responseText, 'system', this.chatBody);
                
                // Play text-to-speech if enabled
                if (document.getElementById('enable-personality') && 
                    document.getElementById('enable-personality').checked) {
                    await this.voice.playTextToSpeech(responseText);
                }
            } catch (error) {
                ErrorHandler.handleError(error);
            }
        });

        // Microphone button
        this.micButton.addEventListener('click', () => {
            if (!this.voice.mediaRecorder) {
                UI.addMessage('Error: Microphone not available', 'system', this.chatBody);
                return;
            }

            const isRecording = this.voice.toggleRecording();
            if (isRecording) {
                this.micButton.classList.add('recording');
                UI.addMessage('Listening... Click the microphone again to stop.', 'system', this.chatBody);
            } else {
                this.micButton.classList.remove('recording');
            }
        });

        // Experience level change
        document.getElementById('experienceLevel').addEventListener('change', (event) => {
            const level = event.target.value;
            UI.adjustUIForExperienceLevel(level);
            this.setVoiceForExperienceLevel(level);
        });

        // Voice settings
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

        // Setup wizard
        document.getElementById('deploy-button').addEventListener('click', () => {
            this.wizard.deployServices()
                .then(success => {
                    if (success) {
                        UI.addMessage('I\'ve successfully deployed the services you requested based on your goals. You can now interact with them through natural language commands.', 'system', this.chatBody);
                    }
                });
        });
        
        // Goal selection checkboxes
        const goalCheckboxes = document.querySelectorAll('#step1 input[type="checkbox"]');
        goalCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', () => {
                this.wizard.updateCloudServicesOptions();
            });
        });

        // Command history tab
        const commandHistoryTab = document.getElementById('command-history-tab');
        if (commandHistoryTab) {
            commandHistoryTab.addEventListener('shown.bs.tab', () => {
                Data.loadCommandHistory(document.getElementById('history'), false);
            });
        }

        // Favorite commands tab
        const favoriteCommandsTab = document.getElementById('favorites-tab');
        if (favoriteCommandsTab) {
            favoriteCommandsTab.addEventListener('shown.bs.tab', () => {
                Data.loadFavoriteCommands(document.getElementById('favorites'));
            });
        }
        
        // Notification preferences tab
        const notificationPrefTab = document.getElementById('notification-pref-tab');
        if (notificationPrefTab) {
            notificationPrefTab.addEventListener('shown.bs.tab', () => {
                this.notifications.loadNotificationPreferences();
            });
        }
        
        // Notification preferences buttons
        const initNotificationPrefsBtn = document.getElementById('initialize-notification-prefs');
        if (initNotificationPrefsBtn) {
            initNotificationPrefsBtn.addEventListener('click', () => {
                this.notifications.initializeNotificationPreferences();
            });
        }
        
        const saveNotificationPrefsBtn = document.getElementById('save-notification-prefs');
        if (saveNotificationPrefsBtn) {
            saveNotificationPrefsBtn.addEventListener('click', () => {
                this.notifications.saveNotificationPreferences();
            });
        }
        
        // Show only successful commands toggle
        const successfulCommandsOnly = document.getElementById('successfulCommandsOnly');
        if (successfulCommandsOnly) {
            successfulCommandsOnly.addEventListener('change', (e) => {
                Data.loadCommandHistory(document.getElementById('history'), e.target.checked);
            });
        }
        
        // Add favorite button
        const addFavoriteBtn = document.getElementById('addFavoriteBtn');
        if (addFavoriteBtn) {
            addFavoriteBtn.addEventListener('click', () => {
                const modal = new bootstrap.Modal(document.getElementById('favoriteCommandModal'));
                document.getElementById('favorite-command-text').value = '';
                document.getElementById('favorite-command-description').value = '';
                modal.show();
            });
        }
        
        // Add event delegation for command history and favorites
        document.addEventListener('click', (e) => {
            // Run command from history or favorites
            if (e.target.closest('.run-command')) {
                const button = e.target.closest('.run-command');
                const command = button.dataset.command;
                if (command) {
                    this.userInput.value = command;
                    this.chatForm.dispatchEvent(new Event('submit'));
                }
            }
            
            // Add to favorites from history
            if (e.target.closest('.add-favorite')) {
                const button = e.target.closest('.add-favorite');
                const command = button.dataset.command;
                if (command) {
                    // Show modal to add description
                    const modal = new bootstrap.Modal(document.getElementById('favoriteCommandModal'));
                    document.getElementById('favorite-command-text').value = command;
                    modal.show();
                }
            }
            
            // Remove from favorites
            if (e.target.closest('.remove-favorite')) {
                const button = e.target.closest('.remove-favorite');
                const id = button.dataset.id;
                if (id) {
                    this.commands.removeFavoriteCommand(id)
                        .then(success => {
                            if (success) {
                                UI.addMessage('Command removed from favorites.', 'system', this.chatBody);
                                Data.loadFavoriteCommands(document.getElementById('favorites'));
                            }
                        });
                }
            }
            
            // Clear history
            if (e.target.closest('#clear-history-btn')) {
                this.commands.clearCommandHistory()
                    .then(success => {
                        if (success) {
                            UI.addMessage('Command history cleared.', 'system', this.chatBody);
                            Data.loadCommandHistory(document.getElementById('history'), false);
                        }
                    });
            }
        });
        
        // Save favorite command
        const saveFavoriteBtn = document.getElementById('save-favorite-command');
        if (saveFavoriteBtn) {
            saveFavoriteBtn.addEventListener('click', () => {
                const command = document.getElementById('favorite-command-text').value;
                const description = document.getElementById('favorite-command-description').value;
                
                this.commands.addToFavorites(command, description)
                    .then(success => {
                        if (success) {
                            UI.addMessage('Command added to favorites.', 'system', this.chatBody);
                            Data.loadFavoriteCommands(document.getElementById('favorites'));
                            
                            // Close modal
                            const modal = bootstrap.Modal.getInstance(document.getElementById('favoriteCommandModal'));
                            modal.hide();
                        }
                    });
            });
        }
        
        // Setup event listeners for the shortcuts modal
        document.getElementById('shortcutsModal').addEventListener('show.bs.modal', async () => {
            await this.shortcuts.loadShortcuts(document.getElementById('shortcuts-list'));
        });

        // Setup event listeners for common commands in the shortcuts modal
        document.querySelectorAll('.list-group-item[data-command]').forEach(item => {
            item.addEventListener('click', () => {
                const command = item.getAttribute('data-command');
                this.userInput.value = command;
                this.chatForm.dispatchEvent(new Event('submit'));
                
                // Close the modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('shortcutsModal'));
                modal.hide();
            });
        });
    }

    /**
     * Set up the setup wizard
     */
    setupWizard() {
        this.wizard.setupCloudServicesSection();
        
        // Set up event listeners for wizard navigation
        document.getElementById('step1-next').addEventListener('click', () => {
            this.wizard.processGoalSelections();
        });
        
        // Detect system resources when step 2 is shown
        document.getElementById('step2-tab').addEventListener('shown.bs.tab', () => {
            this.wizard.detectSystemResources();
        });
    }

    /**
     * Load voice profiles from server
     */
    async loadVoiceProfiles() {
        const profiles = await this.voice.loadVoiceProfiles();
        
        // Populate voice profile dropdown
        const voiceProfileSelect = document.getElementById('voice-profile');
        if (voiceProfileSelect && profiles.length > 0) {
            voiceProfileSelect.innerHTML = '';
            profiles.forEach(profile => {
                const option = document.createElement('option');
                option.value = profile.id;
                option.textContent = profile.name;
                voiceProfileSelect.appendChild(option);
            });
            
            // Set default profile
            voiceProfileSelect.value = this.voice.voiceProfile;
            this.updateVoiceSettingsUI(this.voice.voiceProfile);
        }
    }

    /**
     * Update voice settings UI based on selected profile
     * @param {string} profileId - Voice profile ID
     */
    updateVoiceSettingsUI(profileId) {
        // This would typically load profile-specific settings from the server
        // For now, just update the UI with default values
        this.voice.voiceProfile = profileId;
        
        // Update UI elements
        const personalitySlider = document.getElementById('personality-level');
        if (personalitySlider) {
            personalitySlider.value = this.voice.personalityLevel * 100;
            document.getElementById('personality-level-value').textContent = `${Math.round(this.voice.personalityLevel * 100)}%`;
        }
        
        const enablePersonality = document.getElementById('enable-personality');
        if (enablePersonality) {
            enablePersonality.checked = this.voice.personalityEnabled;
        }
    }

    /**
     * Save voice settings
     */
    async saveVoiceSettings() {
        // Get values from UI
        const profileId = document.getElementById('voice-profile').value;
        const enablePersonality = document.getElementById('enable-personality').checked;
        const personalityLevel = parseInt(document.getElementById('personality-level').value) / 100;
        
        // Update local settings
        this.voice.voiceProfile = profileId;
        this.voice.personalityEnabled = enablePersonality;
        this.voice.personalityLevel = personalityLevel;
        
        // Save to server
        try {
            const result = await this.voice.saveVoiceSettings({
                profile: profileId,
                add_personality: enablePersonality,
                personality_level: personalityLevel
            });
            
            if (result.success) {
                alert('Voice settings saved successfully!');
            } else {
                alert('Error saving voice settings: ' + result.error);
            }
        } catch (error) {
            ErrorHandler.handleError(error);
        }
    }

    /**
     * Test voice settings
     */
    async testVoiceSettings() {
        // Get values from UI
        const profileId = document.getElementById('voice-profile').value;
        const enablePersonality = document.getElementById('enable-personality').checked;
        const personalityLevel = parseInt(document.getElementById('personality-level').value) / 100;
        
        // Create test instance with current settings
        const testVoice = new Voice();
        testVoice.voiceProfile = profileId;
        testVoice.personalityEnabled = enablePersonality;
        testVoice.personalityLevel = personalityLevel;
        
        // Play test message
        await testVoice.playTextToSpeech('This is a test of the voice settings. How do I sound?');
    }

    /**
     * Set voice profile based on experience level
     * @param {string} experienceLevel - User experience level
     */
    async setVoiceForExperienceLevel(experienceLevel) {
        try {
            const response = await fetch('/adapt-voice', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    experience_level: experienceLevel
                })
            });
            
            const data = await response.json();
            
            if (data.success && data.profile) {
                // Update UI if profile changed
                const voiceProfile = document.getElementById('voice-profile');
                if (voiceProfile && voiceProfile.value !== data.profile) {
                    voiceProfile.value = data.profile;
                    this.updateVoiceSettingsUI(data.profile);
                }
            }
        } catch (error) {
            ErrorHandler.handleError(error);
        }
    }

    /**
     * Handle VM status update
     * @param {Object} data - VM status data
     */
    handleVMUpdate(data) {
        UI.updateVMList(data, this.vmList);
    }

    /**
     * Handle cluster status update
     * @param {Object} data - Cluster status data
     */
    handleClusterUpdate(data) {
        UI.updateClusterStatus(data, this.clusterStatus);
    }

    /**
     * Handle network diagram update
     * @param {Array} nodes - Network diagram nodes
     * @param {Array} links - Network diagram links
     */
    handleNetworkDiagramUpdate(nodes, links) {
        this.networkDiagram.update(nodes, links);
    }

    /**
     * Handle socket error
     * @param {string} error - Error message
     */
    handleSocketError(error) {
        ErrorHandler.handleError(error);
    }
}

// Initialize the application when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.proxyApp = new ProxmoxNLI();
});
