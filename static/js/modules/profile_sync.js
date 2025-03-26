/**
 * Profile synchronization module for cross-device support
 */
export default class ProfileSync {
    constructor() {
        this.syncEnabled = false;
        this.deviceName = '';
        this.lastSync = null;
        this.setupEventListeners();
    }
    
    /**
     * Initialize profile sync
     */
    async initialize() {
        try {
            const response = await fetch('/api/profile/sync/status');
            const data = await response.json();
            
            if (data.success) {
                this.syncEnabled = data.sync_enabled;
                this.deviceName = data.device_name;
                this.lastSync = data.last_sync;
                
                // Update UI
                this.updateSyncStatus();
                
                if (this.syncEnabled) {
                    // Start sync service if enabled
                    this.startSyncService();
                }
            }
        } catch (error) {
            console.error('Error initializing profile sync:', error);
        }
    }
    
    /**
     * Set up event listeners for sync UI
     */
    setupEventListeners() {
        // Sync toggle switch
        const syncToggle = document.getElementById('sync-toggle');
        if (syncToggle) {
            syncToggle.addEventListener('change', async () => {
                try {
                    const response = await fetch('/api/profile/sync/enable', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            enabled: syncToggle.checked
                        })
                    });
                    
                    const data = await response.json();
                    if (data.success) {
                        this.syncEnabled = syncToggle.checked;
                        if (this.syncEnabled) {
                            this.startSyncService();
                        } else {
                            this.stopSyncService();
                        }
                    }
                } catch (error) {
                    console.error('Error toggling sync:', error);
                    syncToggle.checked = !syncToggle.checked;
                }
            });
        }
        
        // Device name input
        const deviceNameInput = document.getElementById('device-name');
        if (deviceNameInput) {
            deviceNameInput.addEventListener('change', async () => {
                try {
                    const response = await fetch('/api/profile/sync/device', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            device_name: deviceNameInput.value
                        })
                    });
                    
                    const data = await response.json();
                    if (data.success) {
                        this.deviceName = deviceNameInput.value;
                    }
                } catch (error) {
                    console.error('Error updating device name:', error);
                    deviceNameInput.value = this.deviceName;
                }
            });
        }
        
        // Manual sync button
        const syncButton = document.getElementById('sync-now');
        if (syncButton) {
            syncButton.addEventListener('click', () => this.syncNow());
        }
    }
    
    /**
     * Start the sync service
     */
    startSyncService() {
        // Set up WebSocket connection for real-time sync
        this.setupWebSocket();
        
        // Initial sync
        this.syncNow();
        
        // Set up periodic sync
        this.syncInterval = setInterval(() => this.syncNow(), 5 * 60 * 1000);  // Every 5 minutes
    }
    
    /**
     * Stop the sync service
     */
    stopSyncService() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
        
        if (this.syncInterval) {
            clearInterval(this.syncInterval);
            this.syncInterval = null;
        }
    }
    
    /**
     * Set up WebSocket connection for real-time sync
     */
    setupWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        this.ws = new WebSocket(`${protocol}//${window.location.host}/ws/sync`);
        
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'sync_update') {
                this.handleSyncUpdate(data);
            }
        };
        
        this.ws.onclose = () => {
            // Attempt to reconnect after 5 seconds
            setTimeout(() => {
                if (this.syncEnabled) {
                    this.setupWebSocket();
                }
            }, 5000);
        };
    }
    
    /**
     * Handle incoming sync updates
     */
    handleSyncUpdate(data) {
        if (data.dashboards) {
            // Update dashboards
            window.dashboards.syncDashboards(data.dashboards);
        }
        
        if (data.preferences) {
            // Update user preferences
            window.userPreferences.syncPreferences(data.preferences);
        }
        
        this.lastSync = new Date().toISOString();
        this.updateSyncStatus();
    }
    
    /**
     * Perform immediate sync
     */
    async syncNow() {
        try {
            const response = await fetch('/api/profile/sync/now', {
                method: 'POST'
            });
            
            const data = await response.json();
            if (data.success) {
                this.handleSyncUpdate(data);
            }
        } catch (error) {
            console.error('Error performing sync:', error);
        }
    }
    
    /**
     * Update sync status in UI
     */
    updateSyncStatus() {
        const statusElement = document.getElementById('sync-status');
        if (statusElement) {
            if (this.syncEnabled) {
                const lastSyncDate = this.lastSync ? new Date(this.lastSync) : null;
                const lastSyncText = lastSyncDate 
                    ? `Last synced ${lastSyncDate.toLocaleString()}`
                    : 'Never synced';
                    
                statusElement.innerHTML = `
                    <span class="text-success">
                        <i class="bi bi-check-circle"></i> Sync enabled
                    </span>
                    <br>
                    <small class="text-muted">${lastSyncText}</small>
                `;
            } else {
                statusElement.innerHTML = `
                    <span class="text-muted">
                        <i class="bi bi-pause-circle"></i> Sync disabled
                    </span>
                `;
            }
        }
        
        // Update device name input
        const deviceNameInput = document.getElementById('device-name');
        if (deviceNameInput) {
            deviceNameInput.value = this.deviceName;
        }
        
        // Update sync toggle
        const syncToggle = document.getElementById('sync-toggle');
        if (syncToggle) {
            syncToggle.checked = this.syncEnabled;
        }
    }
}