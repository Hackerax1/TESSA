/**
 * Socket module - Handles WebSocket connections and fallback polling
 */
export default class SocketHandler {
    /**
     * Initialize socket connection
     * @param {Object} callbacks - Callback functions for socket events
     * @param {Function} callbacks.onVMUpdate - Callback for VM status updates
     * @param {Function} callbacks.onClusterUpdate - Callback for cluster status updates
     * @param {Function} callbacks.onNetworkDiagramUpdate - Callback for network diagram updates
     * @param {Function} callbacks.onError - Callback for connection errors
     */
    constructor(callbacks) {
        this.socket = io();
        this.callbacks = callbacks;
        this.pollingInterval = null;
        this.setupSocketHandlers();
    }

    /**
     * Set up socket event handlers
     */
    setupSocketHandlers() {
        this.socket.on('connect', () => {
            console.log('Connected to server');
            // Clear polling interval if it was set
            if (this.pollingInterval) {
                clearInterval(this.pollingInterval);
                this.pollingInterval = null;
            }
        });

        this.socket.on('connect_error', (error) => {
            console.error('Socket connection error:', error);
            // Fallback to polling if socket fails
            this.startPolling();
        });

        this.socket.on('vm_status_update', (data) => {
            if (this.callbacks.onVMUpdate) {
                this.callbacks.onVMUpdate(data);
            }
        });

        this.socket.on('cluster_status_update', (data) => {
            if (this.callbacks.onClusterUpdate) {
                this.callbacks.onClusterUpdate(data.status);
            }
        });

        this.socket.on('network_diagram_update', (data) => {
            if (this.callbacks.onNetworkDiagramUpdate) {
                this.callbacks.onNetworkDiagramUpdate(data.nodes, data.links);
            }
        });
    }

    /**
     * Start polling for updates if WebSocket fails
     */
    startPolling() {
        // Only start polling if not already polling
        if (this.pollingInterval) return;
        
        // Fallback to polling every 10 seconds if websocket fails
        this.pollingInterval = setInterval(async () => {
            try {
                const response = await fetch('/initial-status');
                const data = await response.json();
                
                if (data.success) {
                    if (this.callbacks.onVMUpdate) {
                        this.callbacks.onVMUpdate(data.vm_status);
                    }
                    
                    if (this.callbacks.onClusterUpdate) {
                        this.callbacks.onClusterUpdate(data.cluster_status.nodes);
                    }
                    
                    if (this.callbacks.onNetworkDiagramUpdate && data.network_diagram) {
                        this.callbacks.onNetworkDiagramUpdate(
                            data.network_diagram.nodes,
                            data.network_diagram.links
                        );
                    }
                } else {
                    console.error('Error in polling:', data.error);
                    if (this.callbacks.onError) {
                        this.callbacks.onError(data.error);
                    }
                }
            } catch (error) {
                console.error('Polling error:', error);
                if (this.callbacks.onError) {
                    this.callbacks.onError('Failed to poll for updates');
                }
            }
        }, 10000);
    }

    /**
     * Disconnect socket
     */
    disconnect() {
        if (this.socket) {
            this.socket.disconnect();
        }
        
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
        }
    }
}
