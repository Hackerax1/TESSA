/**
 * Connection Manager Module
 * Handles connections between nodes in the network topology designer
 */

import { showToast } from '../notifications.js';

/**
 * Connection Manager
 */
const ConnectionManager = {
    /**
     * Initialize the connection manager
     * @param {Object} designer - Network designer instance
     */
    init: function(designer) {
        this.designer = designer;
        this.connections = [];
        this.nextConnectionId = 1;
        this._bindEvents();
    },

    /**
     * Bind events
     * @private
     */
    _bindEvents: function() {
        // Listen for connection events
        this.designer.jsPlumb.bind('connection', (info) => {
            this._handleConnection(info);
        });
        
        // Listen for connection detached events
        this.designer.jsPlumb.bind('connectionDetached', (info) => {
            this._handleConnectionDetached(info);
        });
        
        // Listen for connection click events
        this.designer.jsPlumb.bind('click', (connection) => {
            this._handleConnectionClick(connection);
        });
    },

    /**
     * Handle new connection
     * @param {Object} info - Connection info
     * @private
     */
    _handleConnection: function(info) {
        // Check if this is a connection being loaded (already has an id)
        if (info.connection.id && info.connection.id.startsWith('connection-')) {
            return;
        }
        
        // Generate connection ID
        const connectionId = `connection-${this.nextConnectionId++}`;
        info.connection.id = connectionId;
        
        // Get source and target node IDs
        const sourceId = info.source.id;
        const targetId = info.target.id;
        
        // Validate connection
        if (!this._validateConnection(sourceId, targetId)) {
            this.designer.jsPlumb.deleteConnection(info.connection);
            return;
        }
        
        // Create connection data
        const connectionData = {
            id: connectionId,
            source: sourceId,
            target: targetId,
            interface: this._getDefaultInterfaceName(sourceId, targetId),
            type: 'ethernet',
            speed: 'auto'
        };
        
        // Add connection to connections array
        this.connections.push(connectionData);
        
        // Update plan data
        if (!this.designer.plan.connections) {
            this.designer.plan.connections = [];
        }
        this.designer.plan.connections.push(connectionData);
        
        // Style the connection
        this._styleConnection(info.connection, connectionData);
        
        // Show properties modal for new connection
        this._editConnectionProperties(connectionId);
    },

    /**
     * Handle connection detached
     * @param {Object} info - Connection info
     * @private
     */
    _handleConnectionDetached: function(info) {
        const connectionId = info.connection.id;
        
        // Remove from connections array
        this.connections = this.connections.filter(c => c.id !== connectionId);
        
        // Remove from plan data
        if (this.designer.plan.connections) {
            this.designer.plan.connections = this.designer.plan.connections.filter(c => c.id !== connectionId);
        }
        
        // Clear properties if this connection was selected
        if (this.designer.selectedElement && this.designer.selectedElement.type === 'connection' && this.designer.selectedElement.id === connectionId) {
            this.designer.selectedElement = null;
            this.designer.propertyManager.clearProperties();
        }
    },

    /**
     * Handle connection click
     * @param {Object} connection - Connection object
     * @private
     */
    _handleConnectionClick: function(connection) {
        if (this.designer.mode === 'delete') {
            // Delete mode - delete the connection
            this.designer.jsPlumb.deleteConnection(connection);
            return;
        }
        
        // Select connection
        this._selectConnection(connection);
    },

    /**
     * Select a connection
     * @param {Object} connection - Connection object
     * @private
     */
    _selectConnection: function(connection) {
        // Deselect all nodes
        document.querySelectorAll('.node').forEach(n => {
            n.classList.remove('selected');
        });
        
        // Set selected element
        this.designer.selectedElement = {
            type: 'connection',
            id: connection.id
        };
        
        // Show properties
        const connectionData = this._getConnectionDataById(connection.id);
        if (connectionData) {
            this.designer.propertyManager.showConnectionProperties(connectionData);
        }
    },

    /**
     * Edit connection properties
     * @param {string} connectionId - Connection ID
     * @private
     */
    _editConnectionProperties: function(connectionId) {
        const connectionData = this._getConnectionDataById(connectionId);
        if (!connectionData) return;
        
        // Show connection properties modal
        this.designer.propertyManager.showConnectionPropertiesModal(connectionData);
    },

    /**
     * Validate connection
     * @param {string} sourceId - Source node ID
     * @param {string} targetId - Target node ID
     * @returns {boolean} True if valid, false otherwise
     * @private
     */
    _validateConnection: function(sourceId, targetId) {
        const sourceNode = document.getElementById(sourceId);
        const targetNode = document.getElementById(targetId);
        
        if (!sourceNode || !targetNode) {
            showToast('Invalid connection: Node not found', 'error');
            return false;
        }
        
        const sourceType = sourceNode.dataset.nodeType;
        const targetType = targetNode.dataset.nodeType;
        
        // Check if source is a network
        if (sourceType === 'network') {
            showToast('Networks cannot be connection sources', 'error');
            return false;
        }
        
        // Check for existing connections between these nodes
        const existingConnection = this.connections.find(c => 
            (c.source === sourceId && c.target === targetId) || 
            (c.source === targetId && c.target === sourceId)
        );
        
        if (existingConnection) {
            showToast('Connection already exists between these nodes', 'error');
            return false;
        }
        
        return true;
    },

    /**
     * Style a connection
     * @param {Object} connection - jsPlumb connection object
     * @param {Object} connectionData - Connection data
     * @private
     */
    _styleConnection: function(connection, connectionData) {
        // Style based on connection type
        switch (connectionData.type) {
            case 'bridge':
                connection.setPaintStyle({ stroke: '#6f42c1', strokeWidth: 3, dashstyle: '4 2' });
                break;
            case 'bond':
                connection.setPaintStyle({ stroke: '#fd7e14', strokeWidth: 4 });
                break;
            default: // ethernet
                connection.setPaintStyle({ stroke: '#0d6efd', strokeWidth: 2 });
        }
        
        // Add label
        connection.setLabel({
            label: connectionData.interface || '',
            cssClass: 'connection-label',
            location: 0.5
        });
    },

    /**
     * Get default interface name
     * @param {string} sourceId - Source node ID
     * @param {string} targetId - Target node ID
     * @returns {string} Default interface name
     * @private
     */
    _getDefaultInterfaceName: function(sourceId, targetId) {
        const sourceNode = document.getElementById(sourceId);
        const targetNode = document.getElementById(targetId);
        
        if (!sourceNode || !targetNode) return 'eth0';
        
        const sourceType = sourceNode.dataset.nodeType;
        const targetType = targetNode.dataset.nodeType;
        
        // Count existing connections for this source
        const existingConnections = this.connections.filter(c => c.source === sourceId);
        const interfaceIndex = existingConnections.length;
        
        // Generate interface name based on node types
        if (targetType === 'network') {
            const networkType = targetNode.dataset.networkType;
            
            if (networkType === 'vlan') {
                // For VLANs, use eth0.X format
                const vlanId = this._getVlanIdForNetwork(targetId) || 10;
                return `eth${interfaceIndex}.${vlanId}`;
            } else if (networkType === 'wan') {
                return 'wan0';
            }
        }
        
        return `eth${interfaceIndex}`;
    },

    /**
     * Get VLAN ID for a network
     * @param {string} networkId - Network node ID
     * @returns {number|null} VLAN ID or null if not found
     * @private
     */
    _getVlanIdForNetwork: function(networkId) {
        // Find network in nodes
        const networkNode = this.designer.nodeManager.getNodesData().find(n => n.id === networkId);
        if (networkNode && networkNode.vlan) {
            return networkNode.vlan;
        }
        return null;
    },

    /**
     * Get connection data by ID
     * @param {string} connectionId - Connection ID
     * @returns {Object|null} Connection data or null if not found
     * @private
     */
    _getConnectionDataById: function(connectionId) {
        return this.connections.find(c => c.id === connectionId) || null;
    },

    /**
     * Render connections
     * @param {Array} connections - Connections data
     */
    renderConnections: function(connections) {
        this.connections = [...connections];
        
        // Find the highest connection ID to set nextConnectionId
        let highestId = 0;
        connections.forEach(connection => {
            if (connection.id.startsWith('connection-')) {
                const idNum = parseInt(connection.id.substring(11));
                if (idNum > highestId) {
                    highestId = idNum;
                }
            }
        });
        this.nextConnectionId = highestId + 1;
        
        // Render each connection
        connections.forEach(connectionData => {
            this._createConnection(connectionData);
        });
    },

    /**
     * Create a connection
     * @param {Object} connectionData - Connection data
     * @private
     */
    _createConnection: function(connectionData) {
        // Check if source and target nodes exist
        const sourceNode = document.getElementById(connectionData.source);
        const targetNode = document.getElementById(connectionData.target);
        
        if (!sourceNode || !targetNode) {
            console.warn(`Cannot create connection: Node not found (${connectionData.source} -> ${connectionData.target})`);
            return;
        }
        
        // Create connection
        const connection = this.designer.jsPlumb.connect({
            source: connectionData.source,
            target: connectionData.target,
            id: connectionData.id
        });
        
        if (connection) {
            // Style the connection
            this._styleConnection(connection, connectionData);
        }
    },

    /**
     * Get connections data
     * @returns {Array} Connections data
     */
    getConnectionsData: function() {
        return this.connections;
    },

    /**
     * Update connection
     * @param {string} connectionId - Connection ID
     * @param {Object} data - Updated connection data
     */
    updateConnection: function(connectionId, data) {
        // Update connection data
        const connectionData = this._getConnectionDataById(connectionId);
        if (!connectionData) return;
        
        // Update data
        Object.assign(connectionData, data);
        
        // Update connection element
        const connection = this.designer.jsPlumb.getConnections().find(c => c.id === connectionId);
        if (connection) {
            // Update label
            connection.setLabel({
                label: data.interface || '',
                cssClass: 'connection-label',
                location: 0.5
            });
            
            // Update style if type changed
            if (data.type) {
                this._styleConnection(connection, connectionData);
            }
        }
        
        // Update plan data
        if (this.designer.plan.connections) {
            const planConnectionIndex = this.designer.plan.connections.findIndex(c => c.id === connectionId);
            if (planConnectionIndex !== -1) {
                this.designer.plan.connections[planConnectionIndex] = connectionData;
            }
        }
    },

    /**
     * Delete connections for a node
     * @param {string} nodeId - Node ID
     */
    deleteConnectionsForNode: function(nodeId) {
        // Find connections for this node
        const nodeConnections = this.connections.filter(c => c.source === nodeId || c.target === nodeId);
        
        // Delete each connection
        nodeConnections.forEach(connection => {
            const jsPlumbConnection = this.designer.jsPlumb.getConnections().find(c => c.id === connection.id);
            if (jsPlumbConnection) {
                this.designer.jsPlumb.deleteConnection(jsPlumbConnection);
            }
        });
    }
};

export default ConnectionManager;
