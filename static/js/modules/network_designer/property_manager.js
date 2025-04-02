/**
 * Property Manager Module
 * Handles property display and editing for nodes and connections
 */

import { showToast } from '../notifications.js';

/**
 * Property Manager
 */
const PropertyManager = {
    /**
     * Initialize the property manager
     * @param {Object} designer - Network designer instance
     */
    init: function(designer) {
        this.designer = designer;
        this.propertiesPanel = document.getElementById('properties-panel');
        this._initModals();
    },

    /**
     * Initialize modals
     * @private
     */
    _initModals: function() {
        // Node properties modal
        const nodePropertiesModal = document.getElementById('node-properties-modal');
        if (nodePropertiesModal) {
            this.nodePropertiesModal = new bootstrap.Modal(nodePropertiesModal);
            
            // Save button
            const saveNodePropertiesBtn = document.getElementById('save-node-properties');
            if (saveNodePropertiesBtn) {
                saveNodePropertiesBtn.addEventListener('click', () => {
                    this._saveNodeProperties();
                });
            }
            
            // Node type change event
            const nodeTypeSelect = document.getElementById('node-type');
            if (nodeTypeSelect) {
                nodeTypeSelect.addEventListener('change', () => {
                    this._updateNodePropertiesForm(nodeTypeSelect.value);
                });
            }
            
            // Network type change event
            const networkTypeSelect = document.getElementById('network-type');
            if (networkTypeSelect) {
                networkTypeSelect.addEventListener('change', () => {
                    this._updateNetworkPropertiesForm(networkTypeSelect.value);
                });
            }
        }
        
        // Connection properties modal
        const connectionPropertiesModal = document.getElementById('connection-properties-modal');
        if (connectionPropertiesModal) {
            this.connectionPropertiesModal = new bootstrap.Modal(connectionPropertiesModal);
            
            // Save button
            const saveConnectionPropertiesBtn = document.getElementById('save-connection-properties');
            if (saveConnectionPropertiesBtn) {
                saveConnectionPropertiesBtn.addEventListener('click', () => {
                    this._saveConnectionProperties();
                });
            }
        }
    },

    /**
     * Clear properties panel
     */
    clearProperties: function() {
        if (this.propertiesPanel) {
            this.propertiesPanel.innerHTML = `
                <div class="text-center py-3">
                    <p class="text-muted">Select an element to view its properties</p>
                </div>
            `;
        }
    },

    /**
     * Show node properties in the properties panel
     * @param {Object} nodeData - Node data
     */
    showNodeProperties: function(nodeData) {
        if (!this.propertiesPanel) return;
        
        let propertiesHtml = `
            <div class="mb-3">
                <h6>${nodeData.name}</h6>
                <p class="text-muted">Type: ${this._formatNodeType(nodeData.type, nodeData.networkType)}</p>
            </div>
            <div class="mb-3">
                <button class="btn btn-sm btn-primary edit-properties-btn" data-node-id="${nodeData.id}">
                    <i class="fas fa-edit"></i> Edit Properties
                </button>
            </div>
            <hr>
        `;
        
        // Add type-specific properties
        switch (nodeData.type) {
            case 'server':
                propertiesHtml += this._renderServerProperties(nodeData);
                break;
            case 'router':
                propertiesHtml += this._renderRouterProperties(nodeData);
                break;
            case 'switch':
                propertiesHtml += this._renderSwitchProperties(nodeData);
                break;
            case 'network':
                propertiesHtml += this._renderNetworkProperties(nodeData);
                break;
        }
        
        this.propertiesPanel.innerHTML = propertiesHtml;
        
        // Bind edit button
        const editBtn = this.propertiesPanel.querySelector('.edit-properties-btn');
        if (editBtn) {
            editBtn.addEventListener('click', () => {
                this.showNodePropertiesModal(nodeData);
            });
        }
    },

    /**
     * Show connection properties in the properties panel
     * @param {Object} connectionData - Connection data
     */
    showConnectionProperties: function(connectionData) {
        if (!this.propertiesPanel) return;
        
        // Get source and target node names
        const sourceNode = this.designer.nodeManager.getNodesData().find(n => n.id === connectionData.source);
        const targetNode = this.designer.nodeManager.getNodesData().find(n => n.id === connectionData.target);
        
        const sourceName = sourceNode ? sourceNode.name : 'Unknown';
        const targetName = targetNode ? targetNode.name : 'Unknown';
        
        let propertiesHtml = `
            <div class="mb-3">
                <h6>Connection</h6>
                <p class="text-muted">Interface: ${connectionData.interface || 'Not set'}</p>
            </div>
            <div class="mb-3">
                <button class="btn btn-sm btn-primary edit-properties-btn" data-connection-id="${connectionData.id}">
                    <i class="fas fa-edit"></i> Edit Properties
                </button>
            </div>
            <hr>
            <div class="mb-3">
                <p><strong>Source:</strong> ${sourceName}</p>
                <p><strong>Target:</strong> ${targetName}</p>
                <p><strong>Type:</strong> ${this._formatConnectionType(connectionData.type)}</p>
                <p><strong>Speed:</strong> ${this._formatConnectionSpeed(connectionData.speed)}</p>
            </div>
        `;
        
        this.propertiesPanel.innerHTML = propertiesHtml;
        
        // Bind edit button
        const editBtn = this.propertiesPanel.querySelector('.edit-properties-btn');
        if (editBtn) {
            editBtn.addEventListener('click', () => {
                this.showConnectionPropertiesModal(connectionData);
            });
        }
    },

    /**
     * Show node properties modal
     * @param {Object} nodeData - Node data
     */
    showNodePropertiesModal: function(nodeData) {
        // Set form values
        document.getElementById('node-id').value = nodeData.id;
        document.getElementById('node-name').value = nodeData.name;
        document.getElementById('node-type').value = nodeData.type;
        
        // Hide all type-specific property sections
        document.querySelectorAll('.node-type-properties').forEach(section => {
            section.style.display = 'none';
        });
        
        // Show type-specific property section
        switch (nodeData.type) {
            case 'server':
                document.getElementById('server-properties').style.display = 'block';
                document.getElementById('server-hostname').value = nodeData.hostname || '';
                document.getElementById('server-ip').value = nodeData.ip || '';
                break;
            case 'router':
                document.getElementById('router-properties').style.display = 'block';
                document.getElementById('router-model').value = nodeData.model || '';
                document.getElementById('router-is-gateway').checked = nodeData.isGateway || false;
                break;
            case 'switch':
                document.getElementById('switch-properties').style.display = 'block';
                document.getElementById('switch-model').value = nodeData.model || '';
                document.getElementById('switch-managed').checked = nodeData.managed || false;
                break;
            case 'network':
                document.getElementById('network-properties').style.display = 'block';
                document.getElementById('network-type').value = nodeData.networkType || 'lan';
                document.getElementById('network-subnet').value = nodeData.subnet || '';
                document.getElementById('network-vlan-id').value = nodeData.vlan || '';
                document.getElementById('network-gateway').value = nodeData.gateway || '';
                
                // Update network form based on network type
                this._updateNetworkPropertiesForm(nodeData.networkType || 'lan');
                break;
        }
        
        // Show modal
        this.nodePropertiesModal.show();
    },

    /**
     * Show connection properties modal
     * @param {Object} connectionData - Connection data
     */
    showConnectionPropertiesModal: function(connectionData) {
        // Get source and target node names
        const sourceNode = this.designer.nodeManager.getNodesData().find(n => n.id === connectionData.source);
        const targetNode = this.designer.nodeManager.getNodesData().find(n => n.id === connectionData.target);
        
        const sourceName = sourceNode ? sourceNode.name : 'Unknown';
        const targetName = targetNode ? targetNode.name : 'Unknown';
        
        // Set form values
        document.getElementById('connection-id').value = connectionData.id;
        document.getElementById('connection-source').value = sourceName;
        document.getElementById('connection-target').value = targetName;
        document.getElementById('connection-interface').value = connectionData.interface || '';
        document.getElementById('connection-type').value = connectionData.type || 'ethernet';
        document.getElementById('connection-speed').value = connectionData.speed || 'auto';
        
        // Show modal
        this.connectionPropertiesModal.show();
    },

    /**
     * Save node properties
     * @private
     */
    _saveNodeProperties: function() {
        const nodeId = document.getElementById('node-id').value;
        const nodeType = document.getElementById('node-type').value;
        
        // Basic properties
        const data = {
            name: document.getElementById('node-name').value
        };
        
        // Type-specific properties
        switch (nodeType) {
            case 'server':
                data.hostname = document.getElementById('server-hostname').value;
                data.ip = document.getElementById('server-ip').value;
                break;
            case 'router':
                data.model = document.getElementById('router-model').value;
                data.isGateway = document.getElementById('router-is-gateway').checked;
                break;
            case 'switch':
                data.model = document.getElementById('switch-model').value;
                data.managed = document.getElementById('switch-managed').checked;
                break;
            case 'network':
                data.networkType = document.getElementById('network-type').value;
                data.subnet = document.getElementById('network-subnet').value;
                data.vlan = document.getElementById('network-vlan-id').value ? parseInt(document.getElementById('network-vlan-id').value) : null;
                data.gateway = document.getElementById('network-gateway').value;
                break;
        }
        
        // Update node
        this.designer.nodeManager.updateNode(nodeId, data);
        
        // Update properties panel if this node is selected
        if (this.designer.selectedElement && this.designer.selectedElement.type === 'node' && this.designer.selectedElement.id === nodeId) {
            const nodeData = this.designer.nodeManager.getNodesData().find(n => n.id === nodeId);
            if (nodeData) {
                this.showNodeProperties(nodeData);
            }
        }
        
        // Hide modal
        this.nodePropertiesModal.hide();
        
        showToast('Node properties updated', 'success');
    },

    /**
     * Save connection properties
     * @private
     */
    _saveConnectionProperties: function() {
        const connectionId = document.getElementById('connection-id').value;
        
        // Get form values
        const data = {
            interface: document.getElementById('connection-interface').value,
            type: document.getElementById('connection-type').value,
            speed: document.getElementById('connection-speed').value
        };
        
        // Update connection
        this.designer.connectionManager.updateConnection(connectionId, data);
        
        // Update properties panel if this connection is selected
        if (this.designer.selectedElement && this.designer.selectedElement.type === 'connection' && this.designer.selectedElement.id === connectionId) {
            const connectionData = this.designer.connectionManager.getConnectionsData().find(c => c.id === connectionId);
            if (connectionData) {
                this.showConnectionProperties(connectionData);
            }
        }
        
        // Hide modal
        this.connectionPropertiesModal.hide();
        
        showToast('Connection properties updated', 'success');
    },

    /**
     * Update node properties form based on node type
     * @param {string} nodeType - Node type
     * @private
     */
    _updateNodePropertiesForm: function(nodeType) {
        // Hide all type-specific property sections
        document.querySelectorAll('.node-type-properties').forEach(section => {
            section.style.display = 'none';
        });
        
        // Show type-specific property section
        switch (nodeType) {
            case 'server':
                document.getElementById('server-properties').style.display = 'block';
                break;
            case 'router':
                document.getElementById('router-properties').style.display = 'block';
                break;
            case 'switch':
                document.getElementById('switch-properties').style.display = 'block';
                break;
            case 'network':
                document.getElementById('network-properties').style.display = 'block';
                break;
        }
    },

    /**
     * Update network properties form based on network type
     * @param {string} networkType - Network type
     * @private
     */
    _updateNetworkPropertiesForm: function(networkType) {
        const vlanIdField = document.getElementById('network-vlan-id');
        const vlanIdContainer = vlanIdField.closest('.mb-3');
        
        // Show/hide VLAN ID field based on network type
        if (networkType === 'vlan') {
            vlanIdContainer.style.display = 'block';
        } else {
            vlanIdContainer.style.display = 'none';
        }
    },

    /**
     * Format node type for display
     * @param {string} type - Node type
     * @param {string} networkType - Network type
     * @returns {string} Formatted node type
     * @private
     */
    _formatNodeType: function(type, networkType) {
        switch (type) {
            case 'server':
                return 'Server';
            case 'router':
                return 'Router';
            case 'switch':
                return 'Switch';
            case 'firewall':
                return 'Firewall';
            case 'network':
                if (networkType === 'wan') {
                    return 'WAN Network';
                } else if (networkType === 'vlan') {
                    return 'VLAN Network';
                } else {
                    return 'LAN Network';
                }
            default:
                return type.charAt(0).toUpperCase() + type.slice(1);
        }
    },

    /**
     * Format connection type for display
     * @param {string} type - Connection type
     * @returns {string} Formatted connection type
     * @private
     */
    _formatConnectionType: function(type) {
        switch (type) {
            case 'ethernet':
                return 'Ethernet';
            case 'bridge':
                return 'Bridge';
            case 'bond':
                return 'Bond';
            default:
                return type.charAt(0).toUpperCase() + type.slice(1);
        }
    },

    /**
     * Format connection speed for display
     * @param {string} speed - Connection speed
     * @returns {string} Formatted connection speed
     * @private
     */
    _formatConnectionSpeed: function(speed) {
        if (speed === 'auto') {
            return 'Auto';
        } else {
            return `${speed} Mbps`;
        }
    },

    /**
     * Render server properties
     * @param {Object} nodeData - Node data
     * @returns {string} HTML content
     * @private
     */
    _renderServerProperties: function(nodeData) {
        return `
            <div class="mb-3">
                <p><strong>Hostname:</strong> ${nodeData.hostname || 'Not set'}</p>
                <p><strong>IP Address:</strong> ${nodeData.ip || 'Not set'}</p>
            </div>
        `;
    },

    /**
     * Render router properties
     * @param {Object} nodeData - Node data
     * @returns {string} HTML content
     * @private
     */
    _renderRouterProperties: function(nodeData) {
        return `
            <div class="mb-3">
                <p><strong>Model:</strong> ${nodeData.model || 'Not set'}</p>
                <p><strong>Default Gateway:</strong> ${nodeData.isGateway ? 'Yes' : 'No'}</p>
            </div>
        `;
    },

    /**
     * Render switch properties
     * @param {Object} nodeData - Node data
     * @returns {string} HTML content
     * @private
     */
    _renderSwitchProperties: function(nodeData) {
        return `
            <div class="mb-3">
                <p><strong>Model:</strong> ${nodeData.model || 'Not set'}</p>
                <p><strong>Managed:</strong> ${nodeData.managed ? 'Yes' : 'No'}</p>
            </div>
        `;
    },

    /**
     * Render network properties
     * @param {Object} nodeData - Node data
     * @returns {string} HTML content
     * @private
     */
    _renderNetworkProperties: function(nodeData) {
        let html = `
            <div class="mb-3">
                <p><strong>Network Type:</strong> ${this._formatNetworkType(nodeData.networkType)}</p>
                <p><strong>Subnet:</strong> ${nodeData.subnet || 'Not set'}</p>
        `;
        
        if (nodeData.networkType === 'vlan') {
            html += `<p><strong>VLAN ID:</strong> ${nodeData.vlan || 'Not set'}</p>`;
        }
        
        html += `
                <p><strong>Gateway:</strong> ${nodeData.gateway || 'Not set'}</p>
            </div>
        `;
        
        return html;
    },

    /**
     * Format network type for display
     * @param {string} type - Network type
     * @returns {string} Formatted network type
     * @private
     */
    _formatNetworkType: function(type) {
        switch (type) {
            case 'lan':
                return 'LAN';
            case 'vlan':
                return 'VLAN';
            case 'wan':
                return 'WAN';
            default:
                return type.toUpperCase();
        }
    }
};

export default PropertyManager;
