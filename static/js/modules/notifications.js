/**
 * Notifications module - Handles notification preferences and management
 */
import API from './api.js';

export default class Notifications {
    constructor() {
        this.notificationPreferences = [];
        this.pushSupported = 'serviceWorker' in navigator && 'PushManager' in window;
        this.pushSubscription = null;
        this.notificationContainer = document.getElementById('notificationContainer');
        this.serviceWorkerRegistration = null;
        this.vapidPublicKey = null;
        
        // Create notification container if it doesn't exist
        if (!this.notificationContainer) {
            this.notificationContainer = document.createElement('div');
            this.notificationContainer.id = 'notificationContainer';
            this.notificationContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
            document.body.appendChild(this.notificationContainer);
        }
    }

    /**
     * Initialize notifications system
     * @returns {Promise<void>}
     */
    async initialize() {
        // Load notification preferences
        await this.loadNotificationPreferences();
        
        // Check if push notifications are supported
        if (this.pushSupported) {
            // Get VAPID public key
            await this.getVapidPublicKey();
            
            // Register service worker for push notifications
            await this.registerServiceWorker();
            
            // Check permission status
            this.checkNotificationPermission();
            
            // Set up permission request button if it exists
            const permissionBtn = document.getElementById('request-notification-permission');
            if (permissionBtn) {
                permissionBtn.addEventListener('click', () => this.requestNotificationPermission());
            }
            
            // Set up test notification button if it exists
            const testBtn = document.getElementById('test-notification');
            if (testBtn) {
                testBtn.addEventListener('click', () => this.sendTestNotification());
            }
            
            // Listen for messages from service worker
            navigator.serviceWorker.addEventListener('message', (event) => {
                if (event.data && event.data.type === 'PUSH_NOTIFICATION') {
                    this.showLocalNotification(
                        event.data.title, 
                        event.data.message, 
                        event.data.data
                    );
                } else if (event.data && event.data.type === 'NOTIFICATION_CLICK') {
                    // Handle notification click
                    console.log('Notification clicked:', event.data);
                    // You can add custom handling here
                }
            });
        } else {
            console.log('Push notifications not supported in this browser');
            // Hide push notification options if not supported
            document.querySelectorAll('[data-method="push"]').forEach(element => {
                const parentCol = element.closest('.col-md-3');
                if (parentCol) {
                    parentCol.style.display = 'none';
                }
            });
        }
        
        // Set up notification preference toggles
        document.querySelectorAll('.notification-pref-toggle').forEach(toggle => {
            toggle.addEventListener('change', (e) => this.updateNotificationPreference(e.target));
        });
    }

    /**
     * Get VAPID public key from server
     * @returns {Promise<void>}
     */
    async getVapidPublicKey() {
        try {
            const response = await fetch('/api/push-public-key');
            const data = await response.json();
            
            if (data.success && data.publicKey) {
                this.vapidPublicKey = data.publicKey;
                return true;
            } else {
                console.error('Failed to get VAPID public key:', data.message || 'Unknown error');
                return false;
            }
        } catch (error) {
            console.error('Error getting VAPID public key:', error);
            return false;
        }
    }

    /**
     * Register service worker for push notifications
     * @returns {Promise<boolean>} - True if registration successful
     */
    async registerServiceWorker() {
        if (!this.pushSupported) {
            return false;
        }
        
        try {
            // Register service worker
            this.serviceWorkerRegistration = await navigator.serviceWorker.register('/static/js/service-worker.js');
            console.log('Service Worker registered successfully:', this.serviceWorkerRegistration);
            
            // Get existing push subscription if any
            this.pushSubscription = await this.serviceWorkerRegistration.pushManager.getSubscription();
            
            if (this.pushSubscription) {
                console.log('Existing push subscription found');
                // Save the subscription to server
                await this.saveSubscriptionToServer(this.pushSubscription);
            }
            
            return true;
        } catch (error) {
            console.error('Service Worker registration failed:', error);
            return false;
        }
    }

    /**
     * Check notification permission status
     * @returns {string} - Permission status: 'granted', 'denied', or 'default'
     */
    checkNotificationPermission() {
        if (!this.pushSupported) {
            return 'not-supported';
        }
        
        const permission = Notification.permission;
        
        // Update UI based on permission status
        const permissionStatus = document.getElementById('notification-permission-status');
        const permissionBtn = document.getElementById('request-notification-permission');
        
        if (permissionStatus) {
            if (permission === 'granted') {
                permissionStatus.textContent = 'Enabled';
                permissionStatus.className = 'badge bg-success';
                if (permissionBtn) permissionBtn.disabled = true;
            } else if (permission === 'denied') {
                permissionStatus.textContent = 'Blocked';
                permissionStatus.className = 'badge bg-danger';
                if (permissionBtn) permissionBtn.disabled = true;
            } else {
                permissionStatus.textContent = 'Not Enabled';
                permissionStatus.className = 'badge bg-warning';
                if (permissionBtn) permissionBtn.disabled = false;
            }
        }
        
        return permission;
    }

    /**
     * Request notification permission and subscribe to push
     * @returns {Promise<boolean>} - True if permission granted and subscribed
     */
    async requestNotificationPermission() {
        if (!this.pushSupported) {
            this.showLocalNotification('Error', 'Push notifications are not supported in this browser', null, 'error');
            return false;
        }
        
        try {
            // Request permission
            const permission = await Notification.requestPermission();
            
            // Update UI
            this.checkNotificationPermission();
            
            if (permission === 'granted') {
                // Subscribe to push notifications
                await this.subscribeToPushNotifications();
                return true;
            } else {
                console.log('Notification permission denied');
                return false;
            }
        } catch (error) {
            console.error('Error requesting notification permission:', error);
            return false;
        }
    }

    /**
     * Subscribe to push notifications
     * @returns {Promise<boolean>} - True if subscription successful
     */
    async subscribeToPushNotifications() {
        if (!this.pushSupported || !this.serviceWorkerRegistration || !this.vapidPublicKey) {
            return false;
        }
        
        try {
            // Convert VAPID public key to Uint8Array
            const applicationServerKey = this.urlBase64ToUint8Array(this.vapidPublicKey);
            
            // Subscribe to push
            this.pushSubscription = await this.serviceWorkerRegistration.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: applicationServerKey
            });
            
            console.log('Push subscription successful:', this.pushSubscription);
            
            // Save subscription to server
            await this.saveSubscriptionToServer(this.pushSubscription);
            
            // Show success notification
            this.showLocalNotification(
                'Notifications Enabled', 
                'You will now receive notifications for important events', 
                null, 
                'success'
            );
            
            return true;
        } catch (error) {
            console.error('Error subscribing to push notifications:', error);
            
            // Show error notification
            this.showLocalNotification(
                'Notification Error', 
                `Failed to enable notifications: ${error.message}`, 
                null, 
                'error'
            );
            
            return false;
        }
    }

    /**
     * Save push subscription to server
     * @param {PushSubscription} subscription - Push subscription object
     * @returns {Promise<boolean>} - True if saved successfully
     */
    async saveSubscriptionToServer(subscription) {
        if (!subscription) {
            return false;
        }
        
        const userId = localStorage.getItem('user_id') || 'default_user';
        
        try {
            const response = await fetch('/api/push-subscription', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    user_id: userId,
                    subscription: subscription
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                console.log('Push subscription saved to server');
                return true;
            } else {
                console.error('Failed to save push subscription:', data.message || 'Unknown error');
                return false;
            }
        } catch (error) {
            console.error('Error saving push subscription:', error);
            return false;
        }
    }

    /**
     * Send a test notification
     * @returns {Promise<boolean>} - True if test notification sent successfully
     */
    async sendTestNotification() {
        if (!this.pushSupported || !this.pushSubscription) {
            this.showLocalNotification(
                'Error', 
                'Push notifications are not enabled. Please enable notifications first.', 
                null, 
                'error'
            );
            return false;
        }
        
        const userId = localStorage.getItem('user_id') || 'default_user';
        
        try {
            const response = await API.fetchWithAuth(`/test-notification/${userId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    type: 'push',
                    subscription: this.pushSubscription
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showLocalNotification(
                    'Test Notification Sent', 
                    'If you don\'t receive a notification, please check your browser settings.', 
                    null, 
                    'info'
                );
                return true;
            } else {
                this.showLocalNotification(
                    'Error', 
                    `Failed to send test notification: ${data.message || 'Unknown error'}`, 
                    null, 
                    'error'
                );
                return false;
            }
        } catch (error) {
            console.error('Error sending test notification:', error);
            this.showLocalNotification(
                'Error', 
                `Failed to send test notification: ${error.message}`, 
                null, 
                'error'
            );
            return false;
        }
    }

    /**
     * Convert a base64 string to Uint8Array for push subscription
     * @param {string} base64String - Base64 encoded string
     * @returns {Uint8Array} - Uint8Array for push subscription
     */
    urlBase64ToUint8Array(base64String) {
        const padding = '='.repeat((4 - base64String.length % 4) % 4);
        const base64 = (base64String + padding)
            .replace(/-/g, '+')
            .replace(/_/g, '/');
            
        const rawData = window.atob(base64);
        const outputArray = new Uint8Array(rawData.length);
        
        for (let i = 0; i < rawData.length; ++i) {
            outputArray[i] = rawData.charCodeAt(i);
        }
        
        return outputArray;
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
        if (loadingElement) loadingElement.classList.remove('d-none');
        if (errorElement) errorElement.classList.add('d-none');
        if (containerElement) containerElement.classList.add('d-none');
        
        try {
            const response = await API.fetchWithAuth(`/notification-preferences/${userId}`);
            const data = await response.json();
            
            if (data.success) {
                this.notificationPreferences = data.preferences || [];
                
                if (containerElement) {
                    this.renderNotificationPreferences(data.grouped_preferences || {});
                    
                    // Hide loading, show container
                    if (loadingElement) loadingElement.classList.add('d-none');
                    containerElement.classList.remove('d-none');
                }
            } else {
                // Show error
                if (loadingElement) loadingElement.classList.add('d-none');
                if (errorElement) {
                    errorElement.classList.remove('d-none');
                    errorElement.textContent = data.message || 'Failed to load notification preferences';
                }
            }
        } catch (error) {
            console.error('Error loading notification preferences:', error);
            // Show error
            if (loadingElement) loadingElement.classList.add('d-none');
            if (errorElement) {
                errorElement.classList.remove('d-none');
                errorElement.textContent = `Error loading notification preferences: ${error.message}`;
            }
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
                
                // Hide push option if not supported
                if (method === 'push' && !this.pushSupported) {
                    return;
                }
                
                const methodCol = document.createElement('div');
                methodCol.className = 'col-md-3 col-6 mb-2';
                methodCol.innerHTML = `
                    <div class="form-check form-switch">
                        <input class="form-check-input notification-pref-toggle" 
                               type="checkbox" 
                               id="${eventType}_${method}" 
                               data-event-type="${eventType}" 
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
     * Update a notification preference
     * @param {HTMLElement} toggleElement - The toggle element that was changed
     * @returns {Promise<boolean>} - True if update successful
     */
    async updateNotificationPreference(toggleElement) {
        const eventType = toggleElement.dataset.eventType;
        const method = toggleElement.dataset.method;
        const enabled = toggleElement.checked;
        
        if (!eventType || !method) {
            console.error('Missing event type or method for notification preference');
            return false;
        }
        
        const userId = localStorage.getItem('user_id') || 'default_user';
        
        try {
            // Prepare request payload
            const payload = {
                event_type: eventType,
                method: method,
                enabled: enabled
            };
            
            // If this is a push notification and it's being enabled, add subscription
            if (method === 'push' && enabled && this.pushSubscription) {
                payload.subscription = this.pushSubscription;
            }
            
            // Send update to server
            const response = await API.fetchWithAuth(`/notification-preference/${userId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Update local preferences
                if (!this.notificationPreferences[eventType]) {
                    this.notificationPreferences[eventType] = {};
                }
                
                if (!this.notificationPreferences[eventType][method]) {
                    this.notificationPreferences[eventType][method] = {};
                }
                
                this.notificationPreferences[eventType][method].enabled = enabled;
                
                // Show success notification
                this.showLocalNotification(
                    'Preference Updated', 
                    `${method.charAt(0).toUpperCase() + method.slice(1)} notifications for ${eventType.replace(/_/g, ' ')} ${enabled ? 'enabled' : 'disabled'}`, 
                    null, 
                    'success'
                );
                
                return true;
            } else {
                // Show error notification
                this.showLocalNotification(
                    'Error', 
                    `Failed to update preference: ${data.message || 'Unknown error'}`, 
                    null, 
                    'error'
                );
                
                // Revert toggle
                toggleElement.checked = !enabled;
                
                return false;
            }
        } catch (error) {
            console.error('Error updating notification preference:', error);
            
            // Show error notification
            this.showLocalNotification(
                'Error', 
                `Failed to update preference: ${error.message}`, 
                null, 
                'error'
            );
            
            // Revert toggle
            toggleElement.checked = !enabled;
            
            return false;
        }
    }

    /**
     * Reset notification preferences to default
     * @returns {Promise<boolean>} - True if reset successful
     */
    async resetNotificationPreferences() {
        const userId = localStorage.getItem('user_id') || 'default_user';
        
        try {
            const response = await API.fetchWithAuth(`/initialize-notification-preferences/${userId}`, {
                method: 'POST'
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Update local preferences
                this.notificationPreferences = data.preferences || [];
                
                // Render updated preferences
                this.renderNotificationPreferences(data.grouped_preferences || {});
                
                // Show success notification
                this.showLocalNotification(
                    'Preferences Reset', 
                    'Notification preferences have been reset to default', 
                    null, 
                    'success'
                );
                
                return true;
            } else {
                // Show error notification
                this.showLocalNotification(
                    'Error', 
                    `Failed to reset preferences: ${data.message || 'Unknown error'}`, 
                    null, 
                    'error'
                );
                
                return false;
            }
        } catch (error) {
            console.error('Error resetting notification preferences:', error);
            
            // Show error notification
            this.showLocalNotification(
                'Error', 
                `Failed to reset preferences: ${error.message}`, 
                null, 
                'error'
            );
            
            return false;
        }
    }

    /**
     * Show a local notification
     * @param {string} title - Notification title
     * @param {string} message - Notification message
     * @param {object} data - Additional data for the notification
     * @param {string} type - Notification type (success, danger, warning, info)
     */
    showLocalNotification(title, message, data, type = 'info') {
        if (!this.notificationContainer) return;
        
        const toastId = 'toast-' + Date.now();
        
        const toastHTML = `
            <div class="toast" role="alert" aria-live="assertive" aria-atomic="true" id="${toastId}">
                <div class="toast-header bg-${type} text-white">
                    <strong class="me-auto">${title}</strong>
                    <small>${new Date().toLocaleTimeString()}</small>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
                <div class="toast-body">
                    ${message}
                </div>
            </div>
        `;
        
        this.notificationContainer.insertAdjacentHTML('beforeend', toastHTML);
        
        const toastElement = document.getElementById(toastId);
        const toast = new bootstrap.Toast(toastElement, { autohide: true, delay: 5000 });
        toast.show();
        
        // Remove toast from DOM after it's hidden
        toastElement.addEventListener('hidden.bs.toast', function() {
            toastElement.remove();
        });
    }
}
