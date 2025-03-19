/**
 * Notifications module - Handles notification preferences and management
 */
import API from './api.js';

export default class Notifications {
    constructor() {
        this.notificationPreferences = [];
    }

    /**
     * Load notification preferences from the server
     * @returns {Promise<void>}
     */
    async loadNotificationPreferences() {
        const userId = localStorage.getItem('user_id') || 'default_user';
        const loadingElement = document.getElementById('notification-preferences-loading');
        const errorElement = document.getElementById('notification-preferences-error');
        const containerElement = document.getElementById('notification-preferences-container');
        
        // Show loading state
        loadingElement.classList.remove('d-none');
        errorElement.classList.add('d-none');
        containerElement.classList.add('d-none');
        
        try {
            const response = await API.fetchWithAuth(`/notification-preferences/${userId}`);
            const data = await response.json();
            
            if (data.success) {
                this.notificationPreferences = data.preferences || [];
                this.renderNotificationPreferences(data.grouped_preferences || {});
                
                // Hide loading, show container
                loadingElement.classList.add('d-none');
                containerElement.classList.remove('d-none');
            } else {
                // Show error
                loadingElement.classList.add('d-none');
                errorElement.classList.remove('d-none');
                errorElement.textContent = data.message || 'Failed to load notification preferences';
            }
        } catch (error) {
            console.error('Error loading notification preferences:', error);
            // Show error
            loadingElement.classList.add('d-none');
            errorElement.classList.remove('d-none');
            errorElement.textContent = `Error loading notification preferences: ${error.message}`;
        }
    }
    
    /**
     * Render notification preferences in the UI
     * @param {Object} groupedPreferences - Grouped notification preferences
     * @returns {void}
     */
    renderNotificationPreferences(groupedPreferences) {
        // Define event type categories and their containers
        const categories = {
            'vm_': { 
                container: document.getElementById('vm-events-prefs'),
                title: 'Virtual Machine Events',
                events: {
                    'vm_state_change': 'VM State Changes (start/stop/restart)',
                    'vm_creation': 'VM Creation',
                    'vm_deletion': 'VM Deletion',
                    'vm_error': 'VM Errors'
                }
            },
            'backup_': { 
                container: document.getElementById('backup-events-prefs'),
                title: 'Backup Events',
                events: {
                    'backup_start': 'Backup Started',
                    'backup_complete': 'Backup Completed',
                    'backup_error': 'Backup Errors'
                }
            },
            'security_': { 
                container: document.getElementById('security-events-prefs'),
                title: 'Security Events',
                events: {
                    'security_alert': 'Security Alerts',
                    'login_failure': 'Login Failures',
                    'login_success': 'Login Success'
                }
            },
            'system_': { 
                container: document.getElementById('system-events-prefs'),
                title: 'System Events',
                events: {
                    'system_update': 'System Updates',
                    'resource_warning': 'Resource Warnings',
                    'disk_space_low': 'Low Disk Space'
                }
            },
            'service_': { 
                container: document.getElementById('service-events-prefs'),
                title: 'Service Events',
                events: {
                    'service_start': 'Service Started',
                    'service_stop': 'Service Stopped',
                    'service_error': 'Service Errors'
                }
            }
        };
        
        // Clear all containers
        for (const category of Object.values(categories)) {
            if (category.container) {
                category.container.innerHTML = '';
            }
        }
        
        // If no preferences, show message in all containers
        if (Object.keys(groupedPreferences).length === 0) {
            for (const category of Object.values(categories)) {
                if (category.container) {
                    category.container.innerHTML = `
                        <div class="alert alert-info">
                            No notification preferences set. Click "Reset to Default" to initialize.
                        </div>
                    `;
                }
            }
            return;
        }
        
        // Process each event type and add to corresponding category
        for (const [eventType, prefs] of Object.entries(groupedPreferences)) {
            // Find the category this event belongs to
            let categoryKey = null;
            for (const key of Object.keys(categories)) {
                if (eventType.startsWith(key)) {
                    categoryKey = key;
                    break;
                }
            }
            
            if (!categoryKey || !categories[categoryKey].container) continue;
            
            const container = categories[categoryKey].container;
            const eventName = categories[categoryKey].events[eventType] || eventType;
            
            // Create preference controls for this event type
            const prefDiv = document.createElement('div');
            prefDiv.className = 'mb-3 border-bottom pb-3';
            
            const titleRow = document.createElement('div');
            titleRow.className = 'row mb-2';
            titleRow.innerHTML = `
                <div class="col-12">
                    <h6>${eventName}</h6>
                </div>
            `;
            prefDiv.appendChild(titleRow);
            
            // Add notification method toggles
            const methodsRow = document.createElement('div');
            methodsRow.className = 'row';
            
            const methods = ['email', 'sms', 'push', 'webhook'];
            const methodLabels = {
                'email': 'Email',
                'sms': 'SMS',
                'push': 'Push',
                'webhook': 'Webhook'
            };
            
            methods.forEach(method => {
                const isEnabled = prefs[method]?.enabled || false;
                
                const methodCol = document.createElement('div');
                methodCol.className = 'col-md-3 col-6 mb-2';
                methodCol.innerHTML = `
                    <div class="form-check form-switch">
                        <input class="form-check-input notification-pref-toggle" 
                               type="checkbox" 
                               id="${eventType}_${method}" 
                               data-event="${eventType}" 
                               data-method="${method}"
                               ${isEnabled ? 'checked' : ''}>
                        <label class="form-check-label" for="${eventType}_${method}">
                            ${methodLabels[method]}
                        </label>
                    </div>
                `;
                methodsRow.appendChild(methodCol);
            });
            
            prefDiv.appendChild(methodsRow);
            container.appendChild(prefDiv);
        }
    }
    
    /**
     * Initialize notification preferences with default values
     * @returns {Promise<void>}
     */
    async initializeNotificationPreferences() {
        if (!confirm('This will reset all notification preferences to default values. Continue?')) {
            return;
        }
        
        const userId = localStorage.getItem('user_id') || 'default_user';
        const loadingElement = document.getElementById('notification-preferences-loading');
        const errorElement = document.getElementById('notification-preferences-error');
        const containerElement = document.getElementById('notification-preferences-container');
        
        // Show loading state
        loadingElement.classList.remove('d-none');
        errorElement.classList.add('d-none');
        containerElement.classList.add('d-none');
        
        try {
            const response = await API.fetchWithAuth(`/notification-preferences/${userId}/initialize`, {
                method: 'POST'
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.notificationPreferences = data.preferences || [];
                this.renderNotificationPreferences(data.grouped_preferences || {});
                
                // Hide loading, show container
                loadingElement.classList.add('d-none');
                containerElement.classList.remove('d-none');
                
                alert('Notification preferences have been initialized with default values.');
            } else {
                // Show error
                loadingElement.classList.add('d-none');
                errorElement.classList.remove('d-none');
                errorElement.textContent = data.message || 'Failed to initialize notification preferences';
            }
        } catch (error) {
            console.error('Error initializing notification preferences:', error);
            // Show error
            loadingElement.classList.add('d-none');
            errorElement.classList.remove('d-none');
            errorElement.textContent = `Error initializing notification preferences: ${error.message}`;
        }
    }
    
    /**
     * Save notification preferences to the server
     * @returns {Promise<void>}
     */
    async saveNotificationPreferences() {
        const userId = localStorage.getItem('user_id') || 'default_user';
        
        // Collect all notification preference toggles
        const toggles = document.querySelectorAll('.notification-pref-toggle');
        const preferences = {};
        
        toggles.forEach(toggle => {
            const eventType = toggle.dataset.event;
            const method = toggle.dataset.method;
            const enabled = toggle.checked;
            
            if (!preferences[eventType]) {
                preferences[eventType] = {};
            }
            
            if (!preferences[eventType][method]) {
                preferences[eventType][method] = {};
            }
            
            preferences[eventType][method].enabled = enabled;
        });
        
        try {
            const response = await API.fetchWithAuth(`/notification-preferences/${userId}`, {
                method: 'POST',
                body: JSON.stringify({ preferences })
            });
            
            const data = await response.json();
            
            if (data.success) {
                alert('Notification preferences saved successfully.');
            } else {
                alert(`Failed to save notification preferences: ${data.message || 'Unknown error'}`);
            }
        } catch (error) {
            console.error('Error saving notification preferences:', error);
            alert(`Error saving notification preferences: ${error.message}`);
        }
    }
}
