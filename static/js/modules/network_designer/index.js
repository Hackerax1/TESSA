/**
 * Network Designer Module
 * Main module for the network topology designer
 */

import NodeManager from './node_manager.js';
import ConnectionManager from './connection_manager.js';
import PropertyManager from './property_manager.js';
import ValidationManager from './validation_manager.js';
import TemplatesManager from './templates_manager.js';
import { apiRequest } from '../api.js';
import { showToast } from '../notifications.js';

/**
 * Network Designer
 */
const NetworkDesigner = {
    /**
     * Initialize the network designer
     * @param {string} containerId - Container element ID
     * @param {string} planId - Network plan ID
     */
    init: async function(containerId, planId) {
        this.container = document.getElementById(containerId);
        this.planId = planId;
        this.plan = null;
        this.jsPlumbInstance = null;
        
        // Initialize sub-modules
        NodeManager.init(this);
        ConnectionManager.init(this);
        PropertyManager.init(this);
        ValidationManager.init(this);
        TemplatesManager.init(this);
        
        // Initialize UI
        this._initUI();
        
        // Load plan data
        await this._loadPlanData();
        
        // Initialize jsPlumb
        this._initJsPlumb();
        
        // Render topology
        this._renderTopology();
    },
    
    /**
     * Initialize UI
     * @private
     */
    _initUI: function() {
        // Initialize toolbar buttons
        this._initToolbar();
        
        // Initialize canvas
        this._initCanvas();
    },
    
    /**
     * Initialize toolbar
     * @private
     */
    _initToolbar: function() {
        // Add node button
        const addNodeBtn = document.getElementById('add-node-btn');
        if (addNodeBtn) {
            addNodeBtn.addEventListener('click', () => {
                NodeManager.showAddNodeModal();
            });
        }
        
        // Save button
        const saveBtn = document.getElementById('save-topology-btn');
        if (saveBtn) {
            saveBtn.addEventListener('click', () => {
                this._saveTopology();
            });
        }
        
        // Validate button
        const validateBtn = document.getElementById('validate-topology-btn');
        if (validateBtn) {
            validateBtn.addEventListener('click', () => {
                ValidationManager.validateTopology();
            });
        }
        
        // Generate config button
        const generateConfigBtn = document.getElementById('generate-config-btn');
        if (generateConfigBtn) {
            generateConfigBtn.addEventListener('click', () => {
                ValidationManager.generateProxmoxConfig();
            });
        }
        
        // VLAN templates button
        const vlanTemplatesBtn = document.getElementById('vlan-templates-btn');
        if (vlanTemplatesBtn) {
            vlanTemplatesBtn.addEventListener('click', () => {
                TemplatesManager.showVlanTemplatesModal();
            });
        }
        
        // Subnet templates button
        const subnetTemplatesBtn = document.getElementById('subnet-templates-btn');
        if (subnetTemplatesBtn) {
            subnetTemplatesBtn.addEventListener('click', () => {
                TemplatesManager.showSubnetTemplatesModal();
            });
        }
    },
    
    /**
     * Initialize canvas
     * @private
     */
    _initCanvas: function() {
        // Create canvas element
        const canvas = document.createElement('div');
        canvas.id = 'network-canvas';
        canvas.className = 'network-canvas';
        
        // Append to container
        this.container.appendChild(canvas);
        
        // Store reference
        this.canvas = canvas;
    },
    
    /**
     * Initialize jsPlumb
     * @private
     */
    _initJsPlumb: function() {
        // Create jsPlumb instance
        this.jsPlumbInstance = jsPlumb.getInstance({
            Endpoint: ["Dot", { radius: 2 }],
            Connector: ["Bezier", { curviness: 50 }],
            HoverPaintStyle: { stroke: "#1e8151", strokeWidth: 2 },
            ConnectionOverlays: [
                ["Arrow", { location: 1, width: 10, length: 10, id: "arrow" }],
                ["Label", { 
                    label: "", 
                    id: "label", 
                    cssClass: "connection-label" 
                }]
            ],
            Container: this.canvas.id
        });
        
        // Make nodes draggable
        this.jsPlumbInstance.draggable(this.canvas, {
            filter: ".node",
            containment: true,
            grid: [10, 10],
            stop: (event) => {
                // Update node position in plan data
                const nodeId = event.el.getAttribute('data-node-id');
                const node = this.plan.nodes.find(n => n.id === nodeId);
                if (node) {
                    const position = this.jsPlumbInstance.getOffset(event.el);
                    node.position = {
                        x: position.left,
                        y: position.top
                    };
                }
            }
        });
        
        // Setup connection events
        this.jsPlumbInstance.bind("connection", (info) => {
            ConnectionManager.handleConnection(info);
        });
        
        this.jsPlumbInstance.bind("connectionDetached", (info) => {
            ConnectionManager.handleDisconnection(info);
        });
    },
    
    /**
     * Load plan data
     * @private
     */
    _loadPlanData: async function() {
        try {
            const response = await apiRequest('GET', `/api/network-planning/plans/${this.planId}`);
            
            if (response && response.success) {
                this.plan = response.plan;
                
                // Update plan name in UI
                const planNameElement = document.getElementById('plan-name');
                if (planNameElement) {
                    planNameElement.textContent = this.plan.name;
                }
                
                return this.plan;
            } else {
                throw new Error(response.message || 'Failed to load plan data');
            }
        } catch (error) {
            console.error('Error loading plan data:', error);
            showToast(`Error loading plan data: ${error.message}`, 'error');
            return null;
        }
    },
    
    /**
     * Render topology
     * @private
     */
    _renderTopology: function() {
        // Clear canvas
        this._clearCanvas();
        
        // Render nodes
        this.plan.nodes.forEach(node => {
            NodeManager.renderNode(node);
        });
        
        // Render connections
        this.plan.connections.forEach(connection => {
            ConnectionManager.renderConnection(connection);
        });
    },
    
    /**
     * Clear canvas
     * @private
     */
    _clearCanvas: function() {
        // Clear jsPlumb
        if (this.jsPlumbInstance) {
            this.jsPlumbInstance.reset();
        }
        
        // Clear canvas
        this.canvas.innerHTML = '';
        
        // Re-initialize jsPlumb
        this._initJsPlumb();
    },
    
    /**
     * Save topology
     * @private
     */
    _saveTopology: async function() {
        try {
            const response = await apiRequest('PUT', `/api/network-planning/plans/${this.planId}`, this.plan);
            
            if (response && response.success) {
                showToast('Topology saved successfully', 'success');
            } else {
                throw new Error(response.message || 'Failed to save topology');
            }
        } catch (error) {
            console.error('Error saving topology:', error);
            showToast(`Error saving topology: ${error.message}`, 'error');
        }
    }
};

// Initialize the module when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const containerId = 'network-designer-container';
    const planId = 'plan-id';
    NetworkDesigner.init(containerId, planId);
});

export default NetworkDesigner;
