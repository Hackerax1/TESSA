/**
 * Target Selection Step
 * Fifth step in the migration wizard for selecting target Proxmox node and storage
 */

import { apiRequest } from '../../api.js';
import { showToast } from '../../notifications.js';

export const TargetSelectionStep = {
    /**
     * Render the target selection step
     * @param {Object} data - Wizard data
     * @returns {string} HTML content
     */
    render: function(data) {
        if (!data.selectedResources) {
            return `
                <div class="alert alert-warning">
                    <i class="fas fa-exclamation-triangle"></i>
                    Please complete the resource selection step first.
                </div>
                <button class="btn btn-primary" id="back-to-resources-btn">
                    <i class="fas fa-arrow-left"></i> Back to Resource Selection
                </button>
            `;
        }

        return `
            <div class="target-selection-step">
                <h4 class="mb-4">Select Target Environment</h4>
                <p class="mb-4">
                    Select the target Proxmox node and storage for migration.
                    The resources will be migrated to the selected node and storage.
                </p>
                
                <div class="row">
                    <div class="col-md-6">
                        <div class="card mb-4">
                            <div class="card-header">
                                <h5 class="card-title mb-0">Target Node</h5>
                            </div>
                            <div class="card-body">
                                <div class="mb-3">
                                    <label for="target-node" class="form-label">Proxmox Node</label>
                                    <select class="form-select" id="target-node" required>
                                        <option value="" selected disabled>Select a node...</option>
                                        ${data.targetNodes ? data.targetNodes.map(node => 
                                            `<option value="${node.node}" ${data.targetNode === node.node ? 'selected' : ''}>
                                                ${node.node} (${node.status})
                                            </option>`
                                        ).join('') : ''}
                                    </select>
                                    <div class="form-text">
                                        Select the Proxmox node where resources will be migrated.
                                    </div>
                                </div>
                                
                                <div id="node-details" class="mt-3" style="display: ${data.targetNode ? 'block' : 'none'}">
                                    <div class="alert alert-info">
                                        <div class="d-flex align-items-center">
                                            <div class="spinner-border spinner-border-sm me-2" role="status" id="node-loading-spinner">
                                                <span class="visually-hidden">Loading...</span>
                                            </div>
                                            <div>Loading node details...</div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="col-md-6">
                        <div class="card mb-4">
                            <div class="card-header">
                                <h5 class="card-title mb-0">Target Storage</h5>
                            </div>
                            <div class="card-body">
                                <div class="mb-3">
                                    <label for="target-storage" class="form-label">Primary Storage</label>
                                    <select class="form-select" id="target-storage" required ${!data.targetNode ? 'disabled' : ''}>
                                        <option value="" selected disabled>Select storage...</option>
                                        ${data.targetStorages ? data.targetStorages.map(storage => 
                                            `<option value="${storage.storage}" ${data.targetStorage === storage.storage ? 'selected' : ''}>
                                                ${storage.storage} (${storage.type})
                                            </option>`
                                        ).join('') : ''}
                                    </select>
                                    <div class="form-text">
                                        Select the primary storage for VM disks and containers.
                                    </div>
                                </div>
                                
                                <div class="mb-3">
                                    <label for="backup-storage" class="form-label">Backup Storage (Optional)</label>
                                    <select class="form-select" id="backup-storage" ${!data.targetNode ? 'disabled' : ''}>
                                        <option value="">None</option>
                                        ${data.targetStorages ? data.targetStorages.filter(storage => 
                                            storage.content && storage.content.includes('backup')
                                        ).map(storage => 
                                            `<option value="${storage.storage}" ${data.backupStorage === storage.storage ? 'selected' : ''}>
                                                ${storage.storage} (${storage.type})
                                            </option>`
                                        ).join('') : ''}
                                    </select>
                                    <div class="form-text">
                                        Select a storage for backups (optional).
                                    </div>
                                </div>
                                
                                <div id="storage-details" class="mt-3" style="display: ${data.targetStorage ? 'block' : 'none'}">
                                    <div class="alert alert-info">
                                        <div class="d-flex align-items-center">
                                            <div class="spinner-border spinner-border-sm me-2" role="status" id="storage-loading-spinner">
                                                <span class="visually-hidden">Loading...</span>
                                            </div>
                                            <div>Loading storage details...</div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="card mb-4">
                    <div class="card-header">
                        <h5 class="card-title mb-0">Migration Options</h5>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-6">
                                <div class="mb-3 form-check">
                                    <input type="checkbox" class="form-check-input" id="create-backups" 
                                        ${data.createBackups ? 'checked' : ''}>
                                    <label class="form-check-label" for="create-backups">
                                        Create backups before migration
                                    </label>
                                    <div class="form-text">
                                        Create backups of source resources before migration.
                                    </div>
                                </div>
                                
                                <div class="mb-3 form-check">
                                    <input type="checkbox" class="form-check-input" id="shutdown-source" 
                                        ${data.shutdownSource ? 'checked' : ''}>
                                    <label class="form-check-label" for="shutdown-source">
                                        Shutdown source resources
                                    </label>
                                    <div class="form-text">
                                        Shutdown source VMs and containers before migration.
                                    </div>
                                </div>
                            </div>
                            
                            <div class="col-md-6">
                                <div class="mb-3 form-check">
                                    <input type="checkbox" class="form-check-input" id="start-after-migration" 
                                        ${data.startAfterMigration !== false ? 'checked' : ''}>
                                    <label class="form-check-label" for="start-after-migration">
                                        Start resources after migration
                                    </label>
                                    <div class="form-text">
                                        Start VMs and containers after migration is complete.
                                    </div>
                                </div>
                                
                                <div class="mb-3 form-check">
                                    <input type="checkbox" class="form-check-input" id="verify-migration" 
                                        ${data.verifyMigration !== false ? 'checked' : ''}>
                                    <label class="form-check-label" for="verify-migration">
                                        Verify migration
                                    </label>
                                    <div class="form-text">
                                        Verify resources after migration is complete.
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="mt-4 d-flex justify-content-between">
                    <div>
                        <button class="btn btn-secondary" id="back-to-resources-btn">
                            <i class="fas fa-arrow-left"></i> Back to Resource Selection
                        </button>
                    </div>
                    <div>
                        <button class="btn btn-primary" id="continue-to-plan-btn">
                            <i class="fas fa-arrow-right"></i> Continue to Migration Plan
                        </button>
                    </div>
                </div>
            </div>
        `;
    },

    /**
     * Initialize the target selection step
     * @param {HTMLElement} container - Step container
     * @param {Object} data - Wizard data
     */
    init: function(container, data) {
        const backBtn = container.querySelector('#back-to-resources-btn');
        if (backBtn) {
            backBtn.addEventListener('click', () => {
                window.migrationWizard.wizard.goToStep(3);
            });
        }

        const continueBtn = container.querySelector('#continue-to-plan-btn');
        if (continueBtn) {
            continueBtn.addEventListener('click', () => {
                if (this._validateSelection(container, data)) {
                    this._saveOptions(container, data);
                    window.migrationWizard.wizard.goToStep(5);
                }
            });
        }

        // Load nodes if not already loaded
        if (!data.targetNodes) {
            this._loadNodes(container, data);
        }

        // Set up node selection
        const nodeSelect = container.querySelector('#target-node');
        if (nodeSelect) {
            nodeSelect.addEventListener('change', () => {
                const selectedNode = nodeSelect.value;
                if (selectedNode) {
                    // Update wizard data
                    window.migrationWizard.wizard.setData({ targetNode: selectedNode });
                    
                    // Load node details and storages
                    this._loadNodeDetails(container, selectedNode, data);
                    this._loadStorages(container, selectedNode, data);
                }
            });
        }

        // Set up storage selection
        const storageSelect = container.querySelector('#target-storage');
        if (storageSelect) {
            storageSelect.addEventListener('change', () => {
                const selectedStorage = storageSelect.value;
                if (selectedStorage) {
                    // Update wizard data
                    window.migrationWizard.wizard.setData({ targetStorage: selectedStorage });
                    
                    // Load storage details
                    this._loadStorageDetails(container, data.targetNode, selectedStorage, data);
                }
            });
        }

        // Set up backup storage selection
        const backupStorageSelect = container.querySelector('#backup-storage');
        if (backupStorageSelect) {
            backupStorageSelect.addEventListener('change', () => {
                const selectedBackupStorage = backupStorageSelect.value;
                // Update wizard data
                window.migrationWizard.wizard.setData({ backupStorage: selectedBackupStorage });
            });
        }

        // If node is already selected, load details and storages
        if (data.targetNode) {
            this._loadNodeDetails(container, data.targetNode, data);
            
            // If storages not loaded yet
            if (!data.targetStorages) {
                this._loadStorages(container, data.targetNode, data);
            }
            
            // If storage is already selected, load details
            if (data.targetStorage) {
                this._loadStorageDetails(container, data.targetNode, data.targetStorage, data);
            }
        }
    },

    /**
     * Validate the target selection step
     * @param {Object} data - Wizard data
     * @returns {boolean} True if valid, false otherwise
     */
    validate: function(data) {
        if (!data.targetNode) {
            showToast('Please select a target node', 'warning');
            return false;
        }
        
        if (!data.targetStorage) {
            showToast('Please select a target storage', 'warning');
            return false;
        }
        
        return true;
    },

    /**
     * Process the target selection step
     * @param {Object} data - Wizard data
     */
    process: function(data) {
        // Nothing to process here, just pass the target selection to the next step
    },

    /**
     * Load Proxmox nodes
     * @param {HTMLElement} container - Step container
     * @param {Object} data - Wizard data
     * @private
     */
    _loadNodes: async function(container, data) {
        try {
            const response = await apiRequest('GET', '/api/nodes');
            
            if (response && response.success && response.data) {
                // Update wizard data
                window.migrationWizard.wizard.setData({ targetNodes: response.data });
                
                // Update node select
                const nodeSelect = container.querySelector('#target-node');
                if (nodeSelect) {
                    nodeSelect.innerHTML = '<option value="" selected disabled>Select a node...</option>';
                    
                    response.data.forEach(node => {
                        const option = document.createElement('option');
                        option.value = node.node;
                        option.textContent = `${node.node} (${node.status})`;
                        nodeSelect.appendChild(option);
                    });
                }
            } else {
                throw new Error(response.message || 'Failed to load nodes');
            }
        } catch (error) {
            console.error('Error loading nodes:', error);
            showToast(`Error loading nodes: ${error.message}`, 'error');
        }
    },

    /**
     * Load node details
     * @param {HTMLElement} container - Step container
     * @param {string} node - Node name
     * @param {Object} data - Wizard data
     * @private
     */
    _loadNodeDetails: async function(container, node, data) {
        const nodeDetailsEl = container.querySelector('#node-details');
        const spinnerEl = container.querySelector('#node-loading-spinner');
        
        if (!nodeDetailsEl) return;
        
        // Show loading
        nodeDetailsEl.style.display = 'block';
        if (spinnerEl) spinnerEl.style.display = 'inline-block';
        
        try {
            const response = await apiRequest('GET', `/api/nodes/${node}/status`);
            
            if (response && response.success && response.data) {
                const nodeDetails = response.data;
                
                // Update wizard data
                window.migrationWizard.wizard.setData({ targetNodeDetails: nodeDetails });
                
                // Update node details
                nodeDetailsEl.innerHTML = this._renderNodeDetails(nodeDetails);
            } else {
                throw new Error(response.message || 'Failed to load node details');
            }
        } catch (error) {
            console.error('Error loading node details:', error);
            nodeDetailsEl.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-times-circle"></i>
                    Error loading node details: ${error.message}
                </div>
            `;
        }
    },

    /**
     * Load storages for a node
     * @param {HTMLElement} container - Step container
     * @param {string} node - Node name
     * @param {Object} data - Wizard data
     * @private
     */
    _loadStorages: async function(container, node, data) {
        const storageSelect = container.querySelector('#target-storage');
        const backupStorageSelect = container.querySelector('#backup-storage');
        
        if (!storageSelect || !backupStorageSelect) return;
        
        // Enable selects
        storageSelect.disabled = true;
        backupStorageSelect.disabled = true;
        
        // Show loading
        storageSelect.innerHTML = '<option value="" selected disabled>Loading storages...</option>';
        backupStorageSelect.innerHTML = '<option value="" selected disabled>Loading storages...</option>';
        
        try {
            const response = await apiRequest('GET', `/api/nodes/${node}/storage`);
            
            if (response && response.success && response.data) {
                const storages = response.data;
                
                // Update wizard data
                window.migrationWizard.wizard.setData({ targetStorages: storages });
                
                // Update storage select
                storageSelect.innerHTML = '<option value="" selected disabled>Select storage...</option>';
                storages.forEach(storage => {
                    const option = document.createElement('option');
                    option.value = storage.storage;
                    option.textContent = `${storage.storage} (${storage.type})`;
                    storageSelect.appendChild(option);
                });
                
                // Update backup storage select
                backupStorageSelect.innerHTML = '<option value="">None</option>';
                storages.filter(storage => 
                    storage.content && storage.content.includes('backup')
                ).forEach(storage => {
                    const option = document.createElement('option');
                    option.value = storage.storage;
                    option.textContent = `${storage.storage} (${storage.type})`;
                    backupStorageSelect.appendChild(option);
                });
                
                // Enable selects
                storageSelect.disabled = false;
                backupStorageSelect.disabled = false;
                
                // Select previously selected storage if available
                if (data.targetStorage) {
                    storageSelect.value = data.targetStorage;
                }
                
                // Select previously selected backup storage if available
                if (data.backupStorage) {
                    backupStorageSelect.value = data.backupStorage;
                }
            } else {
                throw new Error(response.message || 'Failed to load storages');
            }
        } catch (error) {
            console.error('Error loading storages:', error);
            storageSelect.innerHTML = '<option value="" selected disabled>Error loading storages</option>';
            backupStorageSelect.innerHTML = '<option value="" selected disabled>Error loading storages</option>';
            showToast(`Error loading storages: ${error.message}`, 'error');
        }
    },

    /**
     * Load storage details
     * @param {HTMLElement} container - Step container
     * @param {string} node - Node name
     * @param {string} storage - Storage name
     * @param {Object} data - Wizard data
     * @private
     */
    _loadStorageDetails: async function(container, node, storage, data) {
        const storageDetailsEl = container.querySelector('#storage-details');
        const spinnerEl = container.querySelector('#storage-loading-spinner');
        
        if (!storageDetailsEl) return;
        
        // Show loading
        storageDetailsEl.style.display = 'block';
        if (spinnerEl) spinnerEl.style.display = 'inline-block';
        
        try {
            const response = await apiRequest('GET', `/api/nodes/${node}/storage/${storage}/status`);
            
            if (response && response.success && response.data) {
                const storageDetails = response.data;
                
                // Update wizard data
                window.migrationWizard.wizard.setData({ targetStorageDetails: storageDetails });
                
                // Update storage details
                storageDetailsEl.innerHTML = this._renderStorageDetails(storageDetails);
            } else {
                throw new Error(response.message || 'Failed to load storage details');
            }
        } catch (error) {
            console.error('Error loading storage details:', error);
            storageDetailsEl.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-times-circle"></i>
                    Error loading storage details: ${error.message}
                </div>
            `;
        }
    },

    /**
     * Render node details
     * @param {Object} nodeDetails - Node details
     * @returns {string} HTML content
     * @private
     */
    _renderNodeDetails: function(nodeDetails) {
        const cpuUsage = nodeDetails.cpu * 100;
        const memoryTotal = this._formatMemory(nodeDetails.memory.total);
        const memoryUsed = this._formatMemory(nodeDetails.memory.used);
        const memoryUsage = (nodeDetails.memory.used / nodeDetails.memory.total) * 100;
        
        return `
            <div class="card">
                <div class="card-body">
                    <h6 class="card-subtitle mb-2 text-muted">Node Resources</h6>
                    <div class="row">
                        <div class="col-md-6">
                            <p><strong>Status:</strong> <span class="badge bg-success">Online</span></p>
                            <p><strong>CPU:</strong> ${nodeDetails.cpuinfo.cores} cores</p>
                            <p><strong>Memory:</strong> ${memoryUsed} / ${memoryTotal}</p>
                        </div>
                        <div class="col-md-6">
                            <p><strong>CPU Usage:</strong></p>
                            <div class="progress mb-3">
                                <div class="progress-bar ${cpuUsage > 80 ? 'bg-danger' : cpuUsage > 60 ? 'bg-warning' : 'bg-success'}" 
                                    role="progressbar" style="width: ${cpuUsage}%" 
                                    aria-valuenow="${cpuUsage}" aria-valuemin="0" aria-valuemax="100">
                                    ${cpuUsage.toFixed(1)}%
                                </div>
                            </div>
                            <p><strong>Memory Usage:</strong></p>
                            <div class="progress">
                                <div class="progress-bar ${memoryUsage > 80 ? 'bg-danger' : memoryUsage > 60 ? 'bg-warning' : 'bg-success'}" 
                                    role="progressbar" style="width: ${memoryUsage}%" 
                                    aria-valuenow="${memoryUsage}" aria-valuemin="0" aria-valuemax="100">
                                    ${memoryUsage.toFixed(1)}%
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    },

    /**
     * Render storage details
     * @param {Object} storageDetails - Storage details
     * @returns {string} HTML content
     * @private
     */
    _renderStorageDetails: function(storageDetails) {
        const total = this._formatSize(storageDetails.total);
        const used = this._formatSize(storageDetails.used);
        const available = this._formatSize(storageDetails.avail);
        const usagePercent = (storageDetails.used / storageDetails.total) * 100;
        
        return `
            <div class="card">
                <div class="card-body">
                    <h6 class="card-subtitle mb-2 text-muted">Storage Resources</h6>
                    <div class="row">
                        <div class="col-md-6">
                            <p><strong>Type:</strong> ${storageDetails.type}</p>
                            <p><strong>Total:</strong> ${total}</p>
                            <p><strong>Available:</strong> ${available}</p>
                        </div>
                        <div class="col-md-6">
                            <p><strong>Usage:</strong> ${used} / ${total}</p>
                            <div class="progress">
                                <div class="progress-bar ${usagePercent > 80 ? 'bg-danger' : usagePercent > 60 ? 'bg-warning' : 'bg-success'}" 
                                    role="progressbar" style="width: ${usagePercent}%" 
                                    aria-valuenow="${usagePercent}" aria-valuemin="0" aria-valuemax="100">
                                    ${usagePercent.toFixed(1)}%
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    },

    /**
     * Format memory size
     * @param {number} size - Memory size in bytes
     * @returns {string} Formatted size
     * @private
     */
    _formatMemory: function(size) {
        const gb = size / (1024 * 1024 * 1024);
        return `${gb.toFixed(2)} GB`;
    },

    /**
     * Format storage size
     * @param {number} size - Storage size in bytes
     * @returns {string} Formatted size
     * @private
     */
    _formatSize: function(size) {
        const units = ['B', 'KB', 'MB', 'GB', 'TB'];
        let unitIndex = 0;
        let scaledSize = size;

        while (scaledSize >= 1024 && unitIndex < units.length - 1) {
            unitIndex++;
            scaledSize /= 1024;
        }

        return `${scaledSize.toFixed(1)} ${units[unitIndex]}`;
    },

    /**
     * Validate target selection
     * @param {HTMLElement} container - Step container
     * @param {Object} data - Wizard data
     * @returns {boolean} True if valid, false otherwise
     * @private
     */
    _validateSelection: function(container, data) {
        const nodeSelect = container.querySelector('#target-node');
        const storageSelect = container.querySelector('#target-storage');
        
        if (!nodeSelect.value) {
            showToast('Please select a target node', 'warning');
            nodeSelect.focus();
            return false;
        }
        
        if (!storageSelect.value) {
            showToast('Please select a target storage', 'warning');
            storageSelect.focus();
            return false;
        }
        
        return true;
    },

    /**
     * Save migration options
     * @param {HTMLElement} container - Step container
     * @param {Object} data - Wizard data
     * @private
     */
    _saveOptions: function(container, data) {
        const createBackups = container.querySelector('#create-backups').checked;
        const shutdownSource = container.querySelector('#shutdown-source').checked;
        const startAfterMigration = container.querySelector('#start-after-migration').checked;
        const verifyMigration = container.querySelector('#verify-migration').checked;
        
        // Update wizard data
        window.migrationWizard.wizard.setData({
            createBackups,
            shutdownSource,
            startAfterMigration,
            verifyMigration
        });
    }
};

export default TargetSelectionStep;
