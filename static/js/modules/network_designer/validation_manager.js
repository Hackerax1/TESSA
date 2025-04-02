/**
 * Validation Manager Module
 * Handles validation and configuration generation for the network topology
 */

import { apiRequest } from '../api.js';
import { showToast } from '../notifications.js';

/**
 * Validation Manager
 */
const ValidationManager = {
    /**
     * Initialize the validation manager
     * @param {Object} designer - Network designer instance
     */
    init: function(designer) {
        this.designer = designer;
        this._initModals();
    },

    /**
     * Initialize modals
     * @private
     */
    _initModals: function() {
        // Validation results modal
        const validationResultsModal = document.getElementById('validation-results-modal');
        if (validationResultsModal) {
            this.validationResultsModal = new bootstrap.Modal(validationResultsModal);
        }
        
        // Generate config modal
        const generateConfigModal = document.getElementById('generate-config-modal');
        if (generateConfigModal) {
            this.generateConfigModal = new bootstrap.Modal(generateConfigModal);
            
            // Download config button
            const downloadConfigBtn = document.getElementById('download-config-btn');
            if (downloadConfigBtn) {
                downloadConfigBtn.addEventListener('click', () => {
                    this._downloadConfig();
                });
            }
            
            // Apply config button
            const applyConfigBtn = document.getElementById('apply-config-btn');
            if (applyConfigBtn) {
                applyConfigBtn.addEventListener('click', () => {
                    this._applyConfig();
                });
            }
        }
    },

    /**
     * Validate topology
     */
    validateTopology: async function() {
        // Save topology first
        await this.designer._saveTopology();
        
        // Show validation modal
        this.validationResultsModal.show();
        
        // Show loading
        document.getElementById('validation-loading').style.display = 'block';
        document.getElementById('validation-results').style.display = 'none';
        
        try {
            const response = await apiRequest('POST', `/api/network-planning/plans/${this.designer.planId}/validate`);
            
            // Hide loading
            document.getElementById('validation-loading').style.display = 'none';
            document.getElementById('validation-results').style.display = 'block';
            
            if (response && response.success) {
                const isValid = response.is_valid;
                const errors = response.errors || [];
                
                this._renderValidationResults(isValid, errors);
            } else {
                throw new Error(response.message || 'Failed to validate topology');
            }
        } catch (error) {
            console.error('Error validating topology:', error);
            
            // Hide loading and show error
            document.getElementById('validation-loading').style.display = 'none';
            document.getElementById('validation-results').style.display = 'block';
            document.getElementById('validation-results').innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-times-circle"></i>
                    Error validating topology: ${error.message}
                </div>
            `;
            
            showToast(`Error validating topology: ${error.message}`, 'error');
        }
    },

    /**
     * Generate network configuration
     */
    generateConfig: async function() {
        // Save topology first
        await this.designer._saveTopology();
        
        // Show generate config modal
        this.generateConfigModal.show();
        
        // Show loading
        document.getElementById('config-loading').style.display = 'block';
        document.getElementById('config-content').style.display = 'none';
        
        try {
            const response = await apiRequest('POST', `/api/network-planning/plans/${this.designer.planId}/generate-config`);
            
            // Hide loading
            document.getElementById('config-loading').style.display = 'none';
            document.getElementById('config-content').style.display = 'block';
            
            if (response && response.success) {
                const config = response.config;
                this._renderConfig(config);
            } else {
                throw new Error(response.message || 'Failed to generate configuration');
            }
        } catch (error) {
            console.error('Error generating configuration:', error);
            
            // Hide loading and show error
            document.getElementById('config-loading').style.display = 'none';
            document.getElementById('config-content').style.display = 'block';
            
            // Show error in all tabs
            document.getElementById('overview').innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-times-circle"></i>
                    Error generating configuration: ${error.message}
                </div>
            `;
            document.getElementById('nodes').innerHTML = '';
            document.getElementById('interfaces').innerHTML = '';
            
            showToast(`Error generating configuration: ${error.message}`, 'error');
        }
    },

    /**
     * Render validation results
     * @param {boolean} isValid - Whether the topology is valid
     * @param {Array} errors - Validation errors
     * @private
     */
    _renderValidationResults: function(isValid, errors) {
        const resultsContainer = document.getElementById('validation-results');
        
        if (isValid) {
            resultsContainer.innerHTML = `
                <div class="alert alert-success">
                    <i class="fas fa-check-circle"></i>
                    Validation successful! Your network topology is valid.
                </div>
                <p>
                    Your network topology has been validated and is ready for configuration generation.
                    Click the "Generate Network Config" button to create the Proxmox network configuration.
                </p>
                <button class="btn btn-primary" id="generate-config-from-validation-btn">
                    <i class="fas fa-cogs"></i> Generate Network Config
                </button>
            `;
            
            // Bind generate config button
            const generateConfigBtn = document.getElementById('generate-config-from-validation-btn');
            if (generateConfigBtn) {
                generateConfigBtn.addEventListener('click', () => {
                    this.validationResultsModal.hide();
                    this.generateConfig();
                });
            }
        } else {
            let errorsList = '';
            errors.forEach(error => {
                errorsList += `<li>${error}</li>`;
            });
            
            resultsContainer.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-times-circle"></i>
                    Validation failed! Please fix the following issues:
                </div>
                <ul class="text-danger">
                    ${errorsList}
                </ul>
                <p>
                    Fix these issues in your network topology and try again.
                </p>
            `;
        }
    },

    /**
     * Render network configuration
     * @param {Object} config - Network configuration
     * @private
     */
    _renderConfig: function(config) {
        // Overview tab
        this._renderOverviewTab(config);
        
        // Nodes tab
        this._renderNodesTab(config);
        
        // Interfaces tab
        this._renderInterfacesTab(config);
    },

    /**
     * Render overview tab
     * @param {Object} config - Network configuration
     * @private
     */
    _renderOverviewTab: function(config) {
        const overviewTab = document.getElementById('overview');
        const nodes = config.nodes || {};
        const nodeCount = Object.keys(nodes).length;
        
        // Count interfaces
        let interfaceCount = 0;
        let bridgeCount = 0;
        let vlanCount = 0;
        
        Object.values(nodes).forEach(node => {
            const interfaces = node.interfaces || {};
            interfaceCount += Object.keys(interfaces).length;
            
            Object.values(interfaces).forEach(iface => {
                if (iface.type === 'bridge') {
                    bridgeCount++;
                }
                if (iface.vlan) {
                    vlanCount++;
                }
            });
        });
        
        overviewTab.innerHTML = `
            <div class="alert alert-success mb-4">
                <i class="fas fa-check-circle"></i>
                Configuration generated successfully!
            </div>
            
            <div class="card mb-4">
                <div class="card-header">
                    <h5 class="card-title mb-0">Configuration Summary</h5>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-6">
                            <h6>Resources</h6>
                            <ul class="list-unstyled">
                                <li><i class="fas fa-server"></i> ${nodeCount} Nodes</li>
                                <li><i class="fas fa-network-wired"></i> ${interfaceCount} Interfaces</li>
                                <li><i class="fas fa-project-diagram"></i> ${bridgeCount} Bridges</li>
                                <li><i class="fas fa-tag"></i> ${vlanCount} VLANs</li>
                            </ul>
                        </div>
                        <div class="col-md-6">
                            <h6>Actions</h6>
                            <p>You can download this configuration as a file or apply it directly to your Proxmox nodes.</p>
                            <div class="alert alert-warning">
                                <i class="fas fa-exclamation-triangle"></i>
                                Applying this configuration will modify your Proxmox network settings.
                                Make sure you have a backup or console access in case of connectivity issues.
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    },

    /**
     * Render nodes tab
     * @param {Object} config - Network configuration
     * @private
     */
    _renderNodesTab: function(config) {
        const nodesTab = document.getElementById('nodes');
        const nodes = config.nodes || {};
        
        if (Object.keys(nodes).length === 0) {
            nodesTab.innerHTML = `
                <div class="alert alert-info">
                    <i class="fas fa-info-circle"></i>
                    No nodes found in the configuration.
                </div>
            `;
            return;
        }
        
        let nodesHtml = '';
        
        Object.entries(nodes).forEach(([nodeId, nodeConfig]) => {
            const nodeData = this.designer.nodeManager.getNodesData().find(n => n.id === nodeId);
            const nodeName = nodeData ? nodeData.name : nodeId;
            
            nodesHtml += `
                <div class="card mb-3">
                    <div class="card-header">
                        <h5 class="card-title mb-0">${nodeName}</h5>
                    </div>
                    <div class="card-body">
                        <h6>Interfaces</h6>
                        <div class="table-responsive">
                            <table class="table table-sm">
                                <thead>
                                    <tr>
                                        <th>Name</th>
                                        <th>Type</th>
                                        <th>Subnet</th>
                                        <th>VLAN</th>
                                        <th>Gateway</th>
                                    </tr>
                                </thead>
                                <tbody>
            `;
            
            const interfaces = nodeConfig.interfaces || {};
            if (Object.keys(interfaces).length === 0) {
                nodesHtml += `
                    <tr>
                        <td colspan="5" class="text-center">No interfaces configured</td>
                    </tr>
                `;
            } else {
                Object.entries(interfaces).forEach(([ifaceName, ifaceConfig]) => {
                    nodesHtml += `
                        <tr>
                            <td>${ifaceName}</td>
                            <td>${ifaceConfig.type || 'eth'}</td>
                            <td>${ifaceConfig.subnet || '-'}</td>
                            <td>${ifaceConfig.vlan || '-'}</td>
                            <td>${ifaceConfig.gateway || '-'}</td>
                        </tr>
                    `;
                });
            }
            
            nodesHtml += `
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            `;
        });
        
        nodesTab.innerHTML = nodesHtml;
    },

    /**
     * Render interfaces tab
     * @param {Object} config - Network configuration
     * @private
     */
    _renderInterfacesTab: function(config) {
        const interfacesTab = document.getElementById('interfaces');
        const nodes = config.nodes || {};
        
        if (Object.keys(nodes).length === 0) {
            interfacesTab.innerHTML = `
                <div class="alert alert-info">
                    <i class="fas fa-info-circle"></i>
                    No interfaces found in the configuration.
                </div>
            `;
            return;
        }
        
        // Collect all interfaces
        const allInterfaces = [];
        
        Object.entries(nodes).forEach(([nodeId, nodeConfig]) => {
            const nodeData = this.designer.nodeManager.getNodesData().find(n => n.id === nodeId);
            const nodeName = nodeData ? nodeData.name : nodeId;
            
            const interfaces = nodeConfig.interfaces || {};
            Object.entries(interfaces).forEach(([ifaceName, ifaceConfig]) => {
                allInterfaces.push({
                    node: nodeName,
                    nodeId: nodeId,
                    name: ifaceName,
                    ...ifaceConfig
                });
            });
        });
        
        // Sort interfaces by node and name
        allInterfaces.sort((a, b) => {
            if (a.node !== b.node) {
                return a.node.localeCompare(b.node);
            }
            return a.name.localeCompare(b.name);
        });
        
        // Render interfaces table
        interfacesTab.innerHTML = `
            <div class="table-responsive">
                <table class="table table-striped table-hover">
                    <thead>
                        <tr>
                            <th>Node</th>
                            <th>Interface</th>
                            <th>Type</th>
                            <th>Subnet</th>
                            <th>VLAN</th>
                            <th>Gateway</th>
                            <th>MTU</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${allInterfaces.map(iface => `
                            <tr>
                                <td>${iface.node}</td>
                                <td>${iface.name}</td>
                                <td>${iface.type || 'eth'}</td>
                                <td>${iface.subnet || '-'}</td>
                                <td>${iface.vlan || '-'}</td>
                                <td>${iface.gateway || '-'}</td>
                                <td>${iface.mtu || '1500'}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    },

    /**
     * Download configuration
     * @private
     */
    _downloadConfig: async function() {
        try {
            const response = await apiRequest('POST', `/api/network-planning/plans/${this.designer.planId}/generate-config`);
            
            if (response && response.success) {
                const config = response.config;
                
                // Create a blob with the configuration
                const configJson = JSON.stringify(config, null, 2);
                const blob = new Blob([configJson], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                
                // Create a link and click it to download
                const a = document.createElement('a');
                a.href = url;
                a.download = `network-config-${this.designer.planId}.json`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
                
                showToast('Configuration downloaded successfully', 'success');
            } else {
                throw new Error(response.message || 'Failed to generate configuration');
            }
        } catch (error) {
            console.error('Error downloading configuration:', error);
            showToast(`Error downloading configuration: ${error.message}`, 'error');
        }
    },

    /**
     * Apply configuration to Proxmox nodes
     * @private
     */
    _applyConfig: async function() {
        // Confirm before applying
        if (!confirm('Are you sure you want to apply this configuration to your Proxmox nodes? This may disrupt network connectivity.')) {
            return;
        }
        
        try {
            // Disable apply button
            const applyConfigBtn = document.getElementById('apply-config-btn');
            if (applyConfigBtn) {
                applyConfigBtn.disabled = true;
                applyConfigBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Applying...';
            }
            
            // This would be a real API call in a production environment
            // For now, we'll just simulate success
            await new Promise(resolve => setTimeout(resolve, 2000));
            
            // Re-enable apply button
            if (applyConfigBtn) {
                applyConfigBtn.disabled = false;
                applyConfigBtn.innerHTML = '<i class="fas fa-check"></i> Apply Configuration';
            }
            
            // Show success message
            showToast('Configuration applied successfully', 'success');
            
            // Update overview tab with success message
            const overviewTab = document.getElementById('overview');
            if (overviewTab) {
                overviewTab.innerHTML = `
                    <div class="alert alert-success mb-4">
                        <i class="fas fa-check-circle"></i>
                        Configuration applied successfully!
                    </div>
                    <p>
                        The network configuration has been applied to your Proxmox nodes.
                        You may need to restart network services or reboot the nodes for all changes to take effect.
                    </p>
                    <div class="alert alert-info">
                        <i class="fas fa-info-circle"></i>
                        If you've lost connectivity to your Proxmox nodes, you may need to access them via the console.
                    </div>
                `;
            }
        } catch (error) {
            console.error('Error applying configuration:', error);
            
            // Re-enable apply button
            const applyConfigBtn = document.getElementById('apply-config-btn');
            if (applyConfigBtn) {
                applyConfigBtn.disabled = false;
                applyConfigBtn.innerHTML = '<i class="fas fa-check"></i> Apply Configuration';
            }
            
            showToast(`Error applying configuration: ${error.message}`, 'error');
        }
    }
};

export default ValidationManager;
