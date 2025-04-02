/**
 * Resource Selection Step
 * Fourth step in the migration wizard for selecting resources to migrate
 */

import { apiRequest } from '../../api.js';
import { showToast } from '../../notifications.js';

export const ResourceSelectionStep = {
    /**
     * Render the resource selection step
     * @param {Object} data - Wizard data
     * @returns {string} HTML content
     */
    render: function(data) {
        if (!data.analysisComplete || !data.analysisResults) {
            return `
                <div class="alert alert-warning">
                    <i class="fas fa-exclamation-triangle"></i>
                    Please complete the analysis step first.
                </div>
                <button class="btn btn-primary" id="back-to-analysis-btn">
                    <i class="fas fa-arrow-left"></i> Back to Analysis
                </button>
            `;
        }

        const platform = data.platformDetails;
        const resources = data.analysisResults.resources || {};
        const selectedResources = data.selectedResources || {
            vms: [],
            containers: [],
            storage: [],
            networks: []
        };

        // Count total and selected resources
        const totalVMs = resources.vms ? resources.vms.length : 0;
        const totalContainers = resources.containers ? resources.containers.length : 0;
        const totalStorage = resources.storage ? resources.storage.length : 0;
        const totalNetworks = resources.networks ? resources.networks.length : 0;
        
        const selectedVMs = selectedResources.vms ? selectedResources.vms.length : 0;
        const selectedContainers = selectedResources.containers ? selectedResources.containers.length : 0;
        const selectedStorage = selectedResources.storage ? selectedResources.storage.length : 0;
        const selectedNetworks = selectedResources.networks ? selectedResources.networks.length : 0;

        return `
            <div class="resource-selection-step">
                <h4 class="mb-4">
                    <i class="fas ${platform.icon || 'fa-server'}"></i>
                    Select Resources to Migrate
                </h4>
                <p class="mb-4">
                    Select the resources you want to migrate from ${platform.name} to Proxmox.
                    You can select individual resources or use the bulk selection options.
                </p>
                
                <div class="row resource-summary mb-4">
                    <div class="col-md-3 col-sm-6 mb-3">
                        <div class="card text-center h-100">
                            <div class="card-body">
                                <h1 class="display-4">${selectedVMs}/${totalVMs}</h1>
                                <h5>Virtual Machines</h5>
                                <div class="progress mt-2">
                                    <div class="progress-bar bg-primary" role="progressbar" 
                                        style="width: ${totalVMs > 0 ? (selectedVMs / totalVMs * 100) : 0}%"></div>
                                </div>
                            </div>
                            <div class="card-footer">
                                <div class="btn-group btn-group-sm w-100">
                                    <button class="btn btn-outline-primary select-all-btn" data-type="vms">
                                        <i class="fas fa-check-square"></i> All
                                    </button>
                                    <button class="btn btn-outline-primary select-none-btn" data-type="vms">
                                        <i class="fas fa-square"></i> None
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3 col-sm-6 mb-3">
                        <div class="card text-center h-100">
                            <div class="card-body">
                                <h1 class="display-4">${selectedContainers}/${totalContainers}</h1>
                                <h5>Containers</h5>
                                <div class="progress mt-2">
                                    <div class="progress-bar bg-success" role="progressbar" 
                                        style="width: ${totalContainers > 0 ? (selectedContainers / totalContainers * 100) : 0}%"></div>
                                </div>
                            </div>
                            <div class="card-footer">
                                <div class="btn-group btn-group-sm w-100">
                                    <button class="btn btn-outline-success select-all-btn" data-type="containers">
                                        <i class="fas fa-check-square"></i> All
                                    </button>
                                    <button class="btn btn-outline-success select-none-btn" data-type="containers">
                                        <i class="fas fa-square"></i> None
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3 col-sm-6 mb-3">
                        <div class="card text-center h-100">
                            <div class="card-body">
                                <h1 class="display-4">${selectedStorage}/${totalStorage}</h1>
                                <h5>Storage Volumes</h5>
                                <div class="progress mt-2">
                                    <div class="progress-bar bg-info" role="progressbar" 
                                        style="width: ${totalStorage > 0 ? (selectedStorage / totalStorage * 100) : 0}%"></div>
                                </div>
                            </div>
                            <div class="card-footer">
                                <div class="btn-group btn-group-sm w-100">
                                    <button class="btn btn-outline-info select-all-btn" data-type="storage">
                                        <i class="fas fa-check-square"></i> All
                                    </button>
                                    <button class="btn btn-outline-info select-none-btn" data-type="storage">
                                        <i class="fas fa-square"></i> None
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3 col-sm-6 mb-3">
                        <div class="card text-center h-100">
                            <div class="card-body">
                                <h1 class="display-4">${selectedNetworks}/${totalNetworks}</h1>
                                <h5>Networks</h5>
                                <div class="progress mt-2">
                                    <div class="progress-bar bg-warning" role="progressbar" 
                                        style="width: ${totalNetworks > 0 ? (selectedNetworks / totalNetworks * 100) : 0}%"></div>
                                </div>
                            </div>
                            <div class="card-footer">
                                <div class="btn-group btn-group-sm w-100">
                                    <button class="btn btn-outline-warning select-all-btn" data-type="networks">
                                        <i class="fas fa-check-square"></i> All
                                    </button>
                                    <button class="btn btn-outline-warning select-none-btn" data-type="networks">
                                        <i class="fas fa-square"></i> None
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="resource-details mt-4">
                    <ul class="nav nav-tabs" id="resourceTabs" role="tablist">
                        <li class="nav-item" role="presentation">
                            <button class="nav-link active" id="vms-tab" data-bs-toggle="tab" 
                                data-bs-target="#vms-tab-pane" type="button" role="tab" 
                                aria-controls="vms-tab-pane" aria-selected="true">
                                Virtual Machines
                            </button>
                        </li>
                        <li class="nav-item" role="presentation">
                            <button class="nav-link" id="containers-tab" data-bs-toggle="tab" 
                                data-bs-target="#containers-tab-pane" type="button" role="tab" 
                                aria-controls="containers-tab-pane" aria-selected="false">
                                Containers
                            </button>
                        </li>
                        <li class="nav-item" role="presentation">
                            <button class="nav-link" id="storage-tab" data-bs-toggle="tab" 
                                data-bs-target="#storage-tab-pane" type="button" role="tab" 
                                aria-controls="storage-tab-pane" aria-selected="false">
                                Storage
                            </button>
                        </li>
                        <li class="nav-item" role="presentation">
                            <button class="nav-link" id="networks-tab" data-bs-toggle="tab" 
                                data-bs-target="#networks-tab-pane" type="button" role="tab" 
                                aria-controls="networks-tab-pane" aria-selected="false">
                                Networks
                            </button>
                        </li>
                    </ul>
                    <div class="tab-content p-3 border border-top-0 rounded-bottom" id="resourceTabsContent">
                        <div class="tab-pane fade show active" id="vms-tab-pane" role="tabpanel" 
                            aria-labelledby="vms-tab" tabindex="0">
                            ${this._renderResourceList(resources.vms || [], 'vm', selectedResources.vms || [])}
                        </div>
                        <div class="tab-pane fade" id="containers-tab-pane" role="tabpanel" 
                            aria-labelledby="containers-tab" tabindex="0">
                            ${this._renderResourceList(resources.containers || [], 'container', selectedResources.containers || [])}
                        </div>
                        <div class="tab-pane fade" id="storage-tab-pane" role="tabpanel" 
                            aria-labelledby="storage-tab" tabindex="0">
                            ${this._renderResourceList(resources.storage || [], 'storage', selectedResources.storage || [])}
                        </div>
                        <div class="tab-pane fade" id="networks-tab-pane" role="tabpanel" 
                            aria-labelledby="networks-tab" tabindex="0">
                            ${this._renderResourceList(resources.networks || [], 'network', selectedResources.networks || [])}
                        </div>
                    </div>
                </div>
                
                <div class="mt-4 d-flex justify-content-between">
                    <div>
                        <button class="btn btn-secondary" id="back-to-analysis-btn">
                            <i class="fas fa-arrow-left"></i> Back to Analysis
                        </button>
                    </div>
                    <div>
                        <button class="btn btn-primary" id="continue-to-target-btn">
                            <i class="fas fa-arrow-right"></i> Continue to Target Selection
                        </button>
                    </div>
                </div>
            </div>
        `;
    },

    /**
     * Initialize the resource selection step
     * @param {HTMLElement} container - Step container
     * @param {Object} data - Wizard data
     */
    init: function(container, data) {
        const backBtn = container.querySelector('#back-to-analysis-btn');
        if (backBtn) {
            backBtn.addEventListener('click', () => {
                window.migrationWizard.wizard.goToStep(2);
            });
        }

        const continueBtn = container.querySelector('#continue-to-target-btn');
        if (continueBtn) {
            continueBtn.addEventListener('click', () => {
                if (this._validateSelection(data)) {
                    window.migrationWizard.wizard.goToStep(4);
                }
            });
        }

        // Set up select all/none buttons
        const selectAllBtns = container.querySelectorAll('.select-all-btn');
        const selectNoneBtns = container.querySelectorAll('.select-none-btn');

        selectAllBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const type = btn.dataset.type;
                this._selectAll(container, data, type);
            });
        });

        selectNoneBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const type = btn.dataset.type;
                this._selectNone(container, data, type);
            });
        });

        // Set up resource checkboxes
        const checkboxes = container.querySelectorAll('.resource-checkbox');
        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', () => {
                this._updateSelection(checkbox, data);
            });
        });
    },

    /**
     * Validate the resource selection step
     * @param {Object} data - Wizard data
     * @returns {boolean} True if valid, false otherwise
     */
    validate: function(data) {
        return this._validateSelection(data);
    },

    /**
     * Process the resource selection step
     * @param {Object} data - Wizard data
     */
    process: function(data) {
        // Nothing to process here, just pass the selected resources to the next step
    },

    /**
     * Render resource list
     * @param {Array} resources - List of resources
     * @param {string} type - Resource type
     * @param {Array} selectedIds - List of selected resource IDs
     * @returns {string} HTML content
     * @private
     */
    _renderResourceList: function(resources, type, selectedIds) {
        if (!resources || resources.length === 0) {
            return `
                <div class="alert alert-info">
                    <i class="fas fa-info-circle"></i>
                    No ${type}s found in the source environment.
                </div>
            `;
        }

        const typeKey = `${type}s`; // Convert to plural
        const icon = this._getResourceIcon(type);

        return `
            <div class="table-responsive">
                <table class="table table-hover">
                    <thead>
                        <tr>
                            <th style="width: 40px;">
                                <div class="form-check">
                                    <input class="form-check-input select-all-checkbox" type="checkbox" 
                                        id="select-all-${typeKey}" data-type="${typeKey}"
                                        ${resources.length === selectedIds.length ? 'checked' : ''}>
                                </div>
                            </th>
                            <th>Name</th>
                            <th>Details</th>
                            <th>Status</th>
                            <th>Size</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${resources.map(resource => {
                            const isSelected = selectedIds.includes(resource.id);
                            return `
                                <tr class="${isSelected ? 'table-active' : ''}">
                                    <td>
                                        <div class="form-check">
                                            <input class="form-check-input resource-checkbox" type="checkbox" 
                                                id="${type}-${resource.id}" data-resource-id="${resource.id}" 
                                                data-resource-type="${type}" ${isSelected ? 'checked' : ''}>
                                        </div>
                                    </td>
                                    <td>
                                        <i class="${icon}"></i>
                                        ${resource.name || resource.id || 'Unnamed'}
                                    </td>
                                    <td>${this._getResourceDetails(resource, type)}</td>
                                    <td>${this._getResourceStatus(resource, type)}</td>
                                    <td>${this._getResourceSize(resource, type)}</td>
                                </tr>
                            `;
                        }).join('')}
                    </tbody>
                </table>
            </div>
        `;
    },

    /**
     * Get resource icon
     * @param {string} type - Resource type
     * @returns {string} Icon class
     * @private
     */
    _getResourceIcon: function(type) {
        switch (type) {
            case 'vm':
                return 'fas fa-desktop';
            case 'container':
                return 'fas fa-cube';
            case 'storage':
                return 'fas fa-hdd';
            case 'network':
                return 'fas fa-network-wired';
            default:
                return 'fas fa-cog';
        }
    },

    /**
     * Get resource details
     * @param {Object} resource - Resource object
     * @param {string} type - Resource type
     * @returns {string} HTML content
     * @private
     */
    _getResourceDetails: function(resource, type) {
        switch (type) {
            case 'vm':
                return resource.os || resource.description || '-';
            case 'container':
                return resource.image || resource.description || '-';
            case 'storage':
                return resource.type || resource.mountpoint || '-';
            case 'network':
                return resource.subnet || resource.type || '-';
            default:
                return '-';
        }
    },

    /**
     * Get resource status
     * @param {Object} resource - Resource object
     * @param {string} type - Resource type
     * @returns {string} HTML content
     * @private
     */
    _getResourceStatus: function(resource, type) {
        const status = resource.status || 'unknown';
        let badgeClass = 'bg-secondary';
        
        if (status === 'running' || status === 'online' || status === 'up') {
            badgeClass = 'bg-success';
        } else if (status === 'stopped' || status === 'offline' || status === 'down') {
            badgeClass = 'bg-danger';
        } else if (status === 'paused' || status === 'suspended') {
            badgeClass = 'bg-warning';
        }
        
        return `<span class="badge ${badgeClass}">${status}</span>`;
    },

    /**
     * Get resource size
     * @param {Object} resource - Resource object
     * @param {string} type - Resource type
     * @returns {string} Formatted size
     * @private
     */
    _getResourceSize: function(resource, type) {
        switch (type) {
            case 'vm':
                if (resource.disk_size) {
                    return this._formatSize(resource.disk_size);
                } else if (resource.memory) {
                    return this._formatMemory(resource.memory);
                }
                return '-';
            case 'container':
                if (resource.disk_size) {
                    return this._formatSize(resource.disk_size);
                } else if (resource.memory) {
                    return this._formatMemory(resource.memory);
                }
                return '-';
            case 'storage':
                return resource.size ? this._formatSize(resource.size) : '-';
            case 'network':
                return '-';
            default:
                return '-';
        }
    },

    /**
     * Format memory size
     * @param {number} size - Memory size in MB
     * @returns {string} Formatted size
     * @private
     */
    _formatMemory: function(size) {
        if (size >= 1024) {
            return `${(size / 1024).toFixed(1)} GB`;
        } else {
            return `${size} MB`;
        }
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
     * Select all resources of a type
     * @param {HTMLElement} container - Step container
     * @param {Object} data - Wizard data
     * @param {string} type - Resource type
     * @private
     */
    _selectAll: function(container, data, type) {
        const checkboxes = container.querySelectorAll(`.resource-checkbox[data-resource-type="${type.replace(/s$/, '')}"]`);
        const resources = data.analysisResults.resources[type] || [];
        const selectedResources = data.selectedResources || {
            vms: [],
            containers: [],
            storage: [],
            networks: []
        };
        
        // Update checkboxes
        checkboxes.forEach(checkbox => {
            checkbox.checked = true;
        });
        
        // Update selected resources
        selectedResources[type] = resources.map(resource => resource.id);
        
        // Update wizard data
        window.migrationWizard.wizard.setData({ selectedResources });
        
        // Update select all checkbox
        const selectAllCheckbox = container.querySelector(`#select-all-${type}`);
        if (selectAllCheckbox) {
            selectAllCheckbox.checked = true;
        }
        
        // Update summary
        this._updateSummary(container, data);
    },

    /**
     * Select no resources of a type
     * @param {HTMLElement} container - Step container
     * @param {Object} data - Wizard data
     * @param {string} type - Resource type
     * @private
     */
    _selectNone: function(container, data, type) {
        const checkboxes = container.querySelectorAll(`.resource-checkbox[data-resource-type="${type.replace(/s$/, '')}"]`);
        const selectedResources = data.selectedResources || {
            vms: [],
            containers: [],
            storage: [],
            networks: []
        };
        
        // Update checkboxes
        checkboxes.forEach(checkbox => {
            checkbox.checked = false;
        });
        
        // Update selected resources
        selectedResources[type] = [];
        
        // Update wizard data
        window.migrationWizard.wizard.setData({ selectedResources });
        
        // Update select all checkbox
        const selectAllCheckbox = container.querySelector(`#select-all-${type}`);
        if (selectAllCheckbox) {
            selectAllCheckbox.checked = false;
        }
        
        // Update summary
        this._updateSummary(container, data);
    },

    /**
     * Update selection based on checkbox change
     * @param {HTMLElement} checkbox - Checkbox element
     * @param {Object} data - Wizard data
     * @private
     */
    _updateSelection: function(checkbox, data) {
        const resourceId = checkbox.dataset.resourceId;
        const resourceType = checkbox.dataset.resourceType;
        const typeKey = `${resourceType}s`; // Convert to plural
        
        const selectedResources = data.selectedResources || {
            vms: [],
            containers: [],
            storage: [],
            networks: []
        };
        
        if (checkbox.checked) {
            // Add to selected resources if not already included
            if (!selectedResources[typeKey].includes(resourceId)) {
                selectedResources[typeKey].push(resourceId);
            }
        } else {
            // Remove from selected resources
            const index = selectedResources[typeKey].indexOf(resourceId);
            if (index !== -1) {
                selectedResources[typeKey].splice(index, 1);
            }
        }
        
        // Update wizard data
        window.migrationWizard.wizard.setData({ selectedResources });
        
        // Update row highlighting
        const row = checkbox.closest('tr');
        if (row) {
            if (checkbox.checked) {
                row.classList.add('table-active');
            } else {
                row.classList.remove('table-active');
            }
        }
        
        // Update select all checkbox
        this._updateSelectAllCheckbox(checkbox.closest('.tab-pane'), resourceType, data);
        
        // Update summary
        this._updateSummary(checkbox.closest('.resource-selection-step'), data);
    },

    /**
     * Update select all checkbox
     * @param {HTMLElement} container - Tab pane container
     * @param {string} type - Resource type
     * @param {Object} data - Wizard data
     * @private
     */
    _updateSelectAllCheckbox: function(container, type, data) {
        if (!container) return;
        
        const typeKey = `${type}s`; // Convert to plural
        const checkboxes = container.querySelectorAll(`.resource-checkbox[data-resource-type="${type}"]`);
        const selectAllCheckbox = container.querySelector(`.select-all-checkbox[data-type="${typeKey}"]`);
        
        if (!selectAllCheckbox) return;
        
        const allChecked = Array.from(checkboxes).every(cb => cb.checked);
        const noneChecked = Array.from(checkboxes).every(cb => !cb.checked);
        
        selectAllCheckbox.checked = allChecked;
        selectAllCheckbox.indeterminate = !allChecked && !noneChecked;
    },

    /**
     * Update resource summary
     * @param {HTMLElement} container - Step container
     * @param {Object} data - Wizard data
     * @private
     */
    _updateSummary: function(container, data) {
        const resources = data.analysisResults.resources || {};
        const selectedResources = data.selectedResources || {
            vms: [],
            containers: [],
            storage: [],
            networks: []
        };
        
        // Count total and selected resources
        const totalVMs = resources.vms ? resources.vms.length : 0;
        const totalContainers = resources.containers ? resources.containers.length : 0;
        const totalStorage = resources.storage ? resources.storage.length : 0;
        const totalNetworks = resources.networks ? resources.networks.length : 0;
        
        const selectedVMs = selectedResources.vms ? selectedResources.vms.length : 0;
        const selectedContainers = selectedResources.containers ? selectedResources.containers.length : 0;
        const selectedStorage = selectedResources.storage ? selectedResources.storage.length : 0;
        const selectedNetworks = selectedResources.networks ? selectedResources.networks.length : 0;
        
        // Update summary counts
        const vmCount = container.querySelector('.resource-summary .col-md-3:nth-child(1) .display-4');
        const containerCount = container.querySelector('.resource-summary .col-md-3:nth-child(2) .display-4');
        const storageCount = container.querySelector('.resource-summary .col-md-3:nth-child(3) .display-4');
        const networkCount = container.querySelector('.resource-summary .col-md-3:nth-child(4) .display-4');
        
        if (vmCount) vmCount.textContent = `${selectedVMs}/${totalVMs}`;
        if (containerCount) containerCount.textContent = `${selectedContainers}/${totalContainers}`;
        if (storageCount) storageCount.textContent = `${selectedStorage}/${totalStorage}`;
        if (networkCount) networkCount.textContent = `${selectedNetworks}/${totalNetworks}`;
        
        // Update progress bars
        const vmProgress = container.querySelector('.resource-summary .col-md-3:nth-child(1) .progress-bar');
        const containerProgress = container.querySelector('.resource-summary .col-md-3:nth-child(2) .progress-bar');
        const storageProgress = container.querySelector('.resource-summary .col-md-3:nth-child(3) .progress-bar');
        const networkProgress = container.querySelector('.resource-summary .col-md-3:nth-child(4) .progress-bar');
        
        if (vmProgress) vmProgress.style.width = `${totalVMs > 0 ? (selectedVMs / totalVMs * 100) : 0}%`;
        if (containerProgress) containerProgress.style.width = `${totalContainers > 0 ? (selectedContainers / totalContainers * 100) : 0}%`;
        if (storageProgress) storageProgress.style.width = `${totalStorage > 0 ? (selectedStorage / totalStorage * 100) : 0}%`;
        if (networkProgress) networkProgress.style.width = `${totalNetworks > 0 ? (selectedNetworks / totalNetworks * 100) : 0}%`;
    },

    /**
     * Validate resource selection
     * @param {Object} data - Wizard data
     * @returns {boolean} True if valid, false otherwise
     * @private
     */
    _validateSelection: function(data) {
        const selectedResources = data.selectedResources || {
            vms: [],
            containers: [],
            storage: [],
            networks: []
        };
        
        const totalSelected = 
            selectedResources.vms.length +
            selectedResources.containers.length +
            selectedResources.storage.length +
            selectedResources.networks.length;
        
        if (totalSelected === 0) {
            showToast('Please select at least one resource to migrate', 'warning');
            return false;
        }
        
        return true;
    }
};

export default ResourceSelectionStep;
