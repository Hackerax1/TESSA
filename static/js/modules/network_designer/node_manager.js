/**
 * Node Manager Module
 * Handles node creation, movement, and deletion in the network topology designer
 */

import { showToast } from '../notifications.js';

/**
 * Node Manager
 */
const NodeManager = {
    /**
     * Initialize the node manager
     * @param {Object} designer - Network designer instance
     */
    init: function(designer) {
        this.designer = designer;
        this.nodes = [];
        this.nextNodeId = 1;
        this._bindEvents();
    },

    /**
     * Bind events
     * @private
     */
    _bindEvents: function() {
        // Bind drag and drop events for toolbox items
        const nodeItems = document.querySelectorAll('.node-item');
        nodeItems.forEach(item => {
            item.addEventListener('dragstart', (e) => this._handleDragStart(e));
        });
        
        // Bind drop events for canvas
        const canvas = this.designer.canvas;
        if (canvas) {
            canvas.addEventListener('dragover', (e) => this._handleDragOver(e));
            canvas.addEventListener('drop', (e) => this._handleDrop(e));
        }
    },

    /**
     * Handle drag start event
     * @param {Event} e - Drag event
     * @private
     */
    _handleDragStart: function(e) {
        const nodeType = e.target.dataset.nodeType;
        const networkType = e.target.dataset.networkType;
        
        e.dataTransfer.setData('nodeType', nodeType);
        if (networkType) {
            e.dataTransfer.setData('networkType', networkType);
        }
        
        // Set drag image
        const dragIcon = document.createElement('div');
        dragIcon.classList.add('node-drag-image');
        dragIcon.innerHTML = `<i class="${e.target.querySelector('i').className}"></i>`;
        document.body.appendChild(dragIcon);
        e.dataTransfer.setDragImage(dragIcon, 25, 25);
        
        // Remove drag image after drag
        setTimeout(() => {
            document.body.removeChild(dragIcon);
        }, 0);
    },

    /**
     * Handle drag over event
     * @param {Event} e - Drag event
     * @private
     */
    _handleDragOver: function(e) {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'copy';
    },

    /**
     * Handle drop event
     * @param {Event} e - Drop event
     * @private
     */
    _handleDrop: function(e) {
        e.preventDefault();
        
        const nodeType = e.dataTransfer.getData('nodeType');
        if (!nodeType) return;
        
        // Get drop position relative to canvas
        const canvasRect = this.designer.canvas.getBoundingClientRect();
        const x = (e.clientX - canvasRect.left) / this.designer.scale;
        const y = (e.clientY - canvasRect.top) / this.designer.scale;
        
        // Create node
        const networkType = e.dataTransfer.getData('networkType') || null;
        this._createNode(nodeType, x, y, networkType);
    },

    /**
     * Create a node
     * @param {string} type - Node type
     * @param {number} x - X position
     * @param {number} y - Y position
     * @param {string} networkType - Network type (for network nodes)
     * @private
     */
    _createNode: function(type, x, y, networkType = null) {
        const nodeId = `node-${this.nextNodeId++}`;
        
        // Create node data
        const nodeData = {
            id: nodeId,
            name: this._getDefaultNodeName(type, networkType),
            type: type,
            x: x,
            y: y
        };
        
        // Add network-specific properties
        if (type === 'network') {
            nodeData.networkType = networkType || 'lan';
            nodeData.subnet = this._getDefaultSubnet(networkType);
            nodeData.vlan = type === 'vlan' ? 10 : null;
        }
        
        // Add node to nodes array
        this.nodes.push(nodeData);
        
        // Create node element
        this._createNodeElement(nodeData);
        
        // Update plan data
        if (!this.designer.plan.nodes) {
            this.designer.plan.nodes = [];
        }
        this.designer.plan.nodes.push(nodeData);
    },

    /**
     * Create a node element
     * @param {Object} nodeData - Node data
     * @private
     */
    _createNodeElement: function(nodeData) {
        const node = document.createElement('div');
        node.id = nodeData.id;
        node.className = 'node';
        node.dataset.nodeType = nodeData.type;
        if (nodeData.networkType) {
            node.dataset.networkType = nodeData.networkType;
        }
        
        // Set position
        node.style.left = `${nodeData.x}px`;
        node.style.top = `${nodeData.y}px`;
        
        // Set content
        node.innerHTML = `
            <i class="${this._getNodeIcon(nodeData.type, nodeData.networkType)}"></i>
            <div class="node-label">${nodeData.name}</div>
        `;
        
        // Add to canvas
        this.designer.canvas.appendChild(node);
        
        // Make node draggable
        this._makeNodeDraggable(node);
        
        // Add click event
        node.addEventListener('click', (e) => {
            e.stopPropagation();
            this._handleNodeClick(node);
        });
        
        // Add double click event for editing
        node.addEventListener('dblclick', (e) => {
            e.stopPropagation();
            this._editNodeProperties(nodeData.id);
        });
        
        // Make node a jsPlumb source and target
        this._makeNodeConnectable(node, nodeData.type);
    },

    /**
     * Make a node draggable
     * @param {HTMLElement} node - Node element
     * @private
     */
    _makeNodeDraggable: function(node) {
        this.designer.jsPlumb.draggable(node, {
            grid: [10, 10],
            containment: true,
            stop: (e) => {
                // Update node position in data
                const nodeData = this._getNodeDataById(node.id);
                if (nodeData) {
                    nodeData.x = parseInt(node.style.left);
                    nodeData.y = parseInt(node.style.top);
                }
            }
        });
    },

    /**
     * Make a node connectable
     * @param {HTMLElement} node - Node element
     * @param {string} nodeType - Node type
     * @private
     */
    _makeNodeConnectable: function(node, nodeType) {
        // Different endpoint configurations based on node type
        if (nodeType === 'network') {
            // Networks can only be targets
            this.designer.jsPlumb.makeTarget(node, {
                dropOptions: { hoverClass: 'dragHover' },
                anchor: 'Continuous',
                maxConnections: -1
            });
        } else {
            // Devices can be both sources and targets
            this.designer.jsPlumb.makeSource(node, {
                filter: '.ep',
                anchor: 'Continuous',
                connectorStyle: { stroke: '#5c96bc', strokeWidth: 2 },
                connectionType: 'basic',
                maxConnections: -1,
                onMaxConnections: function(info, e) {
                    showToast('Maximum connections reached', 'warning');
                }
            });
            
            this.designer.jsPlumb.makeTarget(node, {
                dropOptions: { hoverClass: 'dragHover' },
                anchor: 'Continuous',
                maxConnections: -1
            });
        }
    },

    /**
     * Handle node click
     * @param {HTMLElement} node - Node element
     * @private
     */
    _handleNodeClick: function(node) {
        if (this.designer.mode === 'delete') {
            // Delete mode - delete the node
            this._deleteNode(node.id);
            return;
        }
        
        // Select node
        this._selectNode(node);
    },

    /**
     * Select a node
     * @param {HTMLElement} node - Node element
     * @private
     */
    _selectNode: function(node) {
        // Deselect all nodes
        document.querySelectorAll('.node').forEach(n => {
            n.classList.remove('selected');
        });
        
        // Select this node
        node.classList.add('selected');
        
        // Set selected element
        this.designer.selectedElement = {
            type: 'node',
            id: node.id
        };
        
        // Show properties
        const nodeData = this._getNodeDataById(node.id);
        if (nodeData) {
            this.designer.propertyManager.showNodeProperties(nodeData);
        }
    },

    /**
     * Delete a node
     * @param {string} nodeId - Node ID
     * @private
     */
    _deleteNode: function(nodeId) {
        // Remove connections
        this.designer.connectionManager.deleteConnectionsForNode(nodeId);
        
        // Remove node element
        const node = document.getElementById(nodeId);
        if (node) {
            this.designer.jsPlumb.remove(node);
        }
        
        // Remove from nodes array
        this.nodes = this.nodes.filter(n => n.id !== nodeId);
        
        // Remove from plan data
        if (this.designer.plan.nodes) {
            this.designer.plan.nodes = this.designer.plan.nodes.filter(n => n.id !== nodeId);
        }
        
        // Clear properties if this node was selected
        if (this.designer.selectedElement && this.designer.selectedElement.type === 'node' && this.designer.selectedElement.id === nodeId) {
            this.designer.selectedElement = null;
            this.designer.propertyManager.clearProperties();
        }
        
        showToast('Node deleted', 'success');
    },

    /**
     * Edit node properties
     * @param {string} nodeId - Node ID
     * @private
     */
    _editNodeProperties: function(nodeId) {
        const nodeData = this._getNodeDataById(nodeId);
        if (!nodeData) return;
        
        // Show node properties modal
        this.designer.propertyManager.showNodePropertiesModal(nodeData);
    },

    /**
     * Get node data by ID
     * @param {string} nodeId - Node ID
     * @returns {Object|null} Node data or null if not found
     * @private
     */
    _getNodeDataById: function(nodeId) {
        return this.nodes.find(n => n.id === nodeId) || null;
    },

    /**
     * Get default node name
     * @param {string} type - Node type
     * @param {string} networkType - Network type
     * @returns {string} Default node name
     * @private
     */
    _getDefaultNodeName: function(type, networkType) {
        switch (type) {
            case 'server':
                return `Server ${this._countNodesByType('server') + 1}`;
            case 'router':
                return `Router ${this._countNodesByType('router') + 1}`;
            case 'switch':
                return `Switch ${this._countNodesByType('switch') + 1}`;
            case 'firewall':
                return `Firewall ${this._countNodesByType('firewall') + 1}`;
            case 'network':
                if (networkType === 'wan') {
                    return 'WAN';
                } else if (networkType === 'vlan') {
                    return `VLAN ${this._countNodesByType('network', 'vlan') + 1}`;
                } else {
                    return `LAN ${this._countNodesByType('network', 'lan') + 1}`;
                }
            default:
                return `Node ${this.nextNodeId}`;
        }
    },

    /**
     * Get node icon
     * @param {string} type - Node type
     * @param {string} networkType - Network type
     * @returns {string} Icon class
     * @private
     */
    _getNodeIcon: function(type, networkType) {
        switch (type) {
            case 'server':
                return 'fas fa-server';
            case 'router':
                return 'fas fa-router';
            case 'switch':
                return 'fas fa-network-wired';
            case 'firewall':
                return 'fas fa-shield-alt';
            case 'network':
                if (networkType === 'wan') {
                    return 'fas fa-cloud';
                } else if (networkType === 'vlan') {
                    return 'fas fa-tag';
                } else {
                    return 'fas fa-globe';
                }
            default:
                return 'fas fa-question-circle';
        }
    },

    /**
     * Get default subnet
     * @param {string} networkType - Network type
     * @returns {string} Default subnet
     * @private
     */
    _getDefaultSubnet: function(networkType) {
        if (networkType === 'wan') {
            return '192.168.1.0/24';
        } else if (networkType === 'vlan') {
            const vlanCount = this._countNodesByType('network', 'vlan');
            return `10.0.${vlanCount + 1}.0/24`;
        } else {
            const lanCount = this._countNodesByType('network', 'lan');
            return `192.168.${lanCount + 1}.0/24`;
        }
    },

    /**
     * Count nodes by type
     * @param {string} type - Node type
     * @param {string} networkType - Network type (optional)
     * @returns {number} Node count
     * @private
     */
    _countNodesByType: function(type, networkType = null) {
        if (networkType) {
            return this.nodes.filter(n => n.type === type && n.networkType === networkType).length;
        } else {
            return this.nodes.filter(n => n.type === type).length;
        }
    },

    /**
     * Render nodes
     * @param {Array} nodes - Nodes data
     */
    renderNodes: function(nodes) {
        this.nodes = [...nodes];
        
        // Find the highest node ID to set nextNodeId
        let highestId = 0;
        nodes.forEach(node => {
            if (node.id.startsWith('node-')) {
                const idNum = parseInt(node.id.substring(5));
                if (idNum > highestId) {
                    highestId = idNum;
                }
            }
        });
        this.nextNodeId = highestId + 1;
        
        // Render each node
        nodes.forEach(nodeData => {
            this._createNodeElement(nodeData);
        });
    },

    /**
     * Get nodes data
     * @returns {Array} Nodes data
     */
    getNodesData: function() {
        return this.nodes;
    },

    /**
     * Update node
     * @param {string} nodeId - Node ID
     * @param {Object} data - Updated node data
     */
    updateNode: function(nodeId, data) {
        // Update node data
        const nodeData = this._getNodeDataById(nodeId);
        if (!nodeData) return;
        
        // Update data
        Object.assign(nodeData, data);
        
        // Update node element
        const node = document.getElementById(nodeId);
        if (node) {
            // Update label
            const label = node.querySelector('.node-label');
            if (label) {
                label.textContent = data.name;
            }
            
            // Update network type if changed
            if (data.networkType && node.dataset.networkType !== data.networkType) {
                node.dataset.networkType = data.networkType;
                
                // Update icon
                const icon = node.querySelector('i');
                if (icon) {
                    icon.className = this._getNodeIcon(nodeData.type, data.networkType);
                }
            }
        }
        
        // Update plan data
        if (this.designer.plan.nodes) {
            const planNodeIndex = this.designer.plan.nodes.findIndex(n => n.id === nodeId);
            if (planNodeIndex !== -1) {
                this.designer.plan.nodes[planNodeIndex] = nodeData;
            }
        }
    }
};

export default NodeManager;
