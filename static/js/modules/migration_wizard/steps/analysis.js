/**
 * Analysis Step
 * Third step in the migration wizard for analyzing the source environment
 */

import { apiRequest } from '../../api.js';
import { showToast } from '../../notifications.js';

export const AnalysisStep = {
    /**
     * Render the analysis step
     * @param {Object} data - Wizard data
     * @returns {string} HTML content
     */
    render: function(data) {
        if (!data.selectedPlatform || !data.credentials || !data.credentialsValidated) {
            return `
                <div class="alert alert-warning">
                    <i class="fas fa-exclamation-triangle"></i>
                    Please complete the previous steps first.
                </div>
                <button class="btn btn-primary" id="back-to-credentials-btn">
                    <i class="fas fa-arrow-left"></i> Back to Credentials
                </button>
            `;
        }

        // If analysis is already complete, show results
        if (data.analysisComplete && data.analysisResults) {
            return this._renderAnalysisResults(data);
        }

        const platform = data.platformDetails;

        return `
            <div class="analysis-step">
                <h4 class="mb-4">
                    <i class="fas ${platform.icon || 'fa-server'}"></i>
                    Analyzing ${platform.name} Environment
                </h4>
                <p class="mb-4">
                    We need to analyze your ${platform.name} environment to discover resources that can be migrated.
                    This process may take a few minutes depending on the size of your environment.
                </p>
                
                <div class="card mb-4">
                    <div class="card-header">
                        <h5 class="card-title mb-0">Connection Details</h5>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-6">
                                <p><strong>Platform:</strong> ${platform.name}</p>
                                <p><strong>Host:</strong> ${data.credentials.host}</p>
                                ${data.credentials.port ? `<p><strong>Port:</strong> ${data.credentials.port}</p>` : ''}
                            </div>
                            <div class="col-md-6">
                                ${data.credentials.username ? `<p><strong>Username:</strong> ${data.credentials.username}</p>` : ''}
                                ${data.credentials.use_https !== undefined ? `<p><strong>HTTPS:</strong> ${data.credentials.use_https ? 'Yes' : 'No'}</p>` : ''}
                            </div>
                        </div>
                    </div>
                </div>
                
                <div id="analysis-controls">
                    <button class="btn btn-primary" id="start-analysis-btn">
                        <i class="fas fa-search"></i> Start Analysis
                    </button>
                </div>
                
                <div id="analysis-progress" style="display: none;">
                    <div class="progress mb-3">
                        <div class="progress-bar progress-bar-striped progress-bar-animated" 
                            role="progressbar" style="width: 100%"></div>
                    </div>
                    <p class="text-center" id="analysis-status">Connecting to ${platform.name}...</p>
                </div>
                
                <div id="analysis-result" class="mt-4" style="display: none;"></div>
            </div>
        `;
    },

    /**
     * Initialize the analysis step
     * @param {HTMLElement} container - Step container
     * @param {Object} data - Wizard data
     */
    init: function(container, data) {
        const backBtn = container.querySelector('#back-to-credentials-btn');
        if (backBtn) {
            backBtn.addEventListener('click', () => {
                window.migrationWizard.wizard.goToStep(1);
            });
            return;
        }

        // If analysis is already complete, set up resource cards
        if (data.analysisComplete && data.analysisResults) {
            this._setupResourceCards(container, data);
            return;
        }

        const startBtn = container.querySelector('#start-analysis-btn');
        if (startBtn) {
            startBtn.addEventListener('click', () => {
                this._startAnalysis(container, data);
            });
        }
    },

    /**
     * Validate the analysis step
     * @param {Object} data - Wizard data
     * @returns {boolean} True if valid, false otherwise
     */
    validate: function(data) {
        if (!data.analysisComplete || !data.analysisResults) {
            showToast('Please complete the analysis first', 'warning');
            return false;
        }
        return true;
    },

    /**
     * Process the analysis step
     * @param {Object} data - Wizard data
     */
    process: function(data) {
        // Nothing to process here, just pass the analysis results to the next step
    },

    /**
     * Start the analysis process
     * @param {HTMLElement} container - Step container
     * @param {Object} data - Wizard data
     * @private
     */
    _startAnalysis: async function(container, data) {
        const controlsEl = container.querySelector('#analysis-controls');
        const progressEl = container.querySelector('#analysis-progress');
        const statusEl = container.querySelector('#analysis-status');
        const resultEl = container.querySelector('#analysis-result');
        
        if (!controlsEl || !progressEl || !statusEl || !resultEl) return;
        
        // Show progress and hide controls
        controlsEl.style.display = 'none';
        progressEl.style.display = 'block';
        resultEl.style.display = 'none';
        
        try {
            // Update status
            statusEl.textContent = `Connecting to ${data.platformDetails.name}...`;
            
            // Start analysis
            const response = await apiRequest('POST', `/api/migration/${data.selectedPlatform}/analyze`, {
                credentials: data.credentials
            });
            
            // Hide progress
            progressEl.style.display = 'none';
            resultEl.style.display = 'block';
            
            if (response && response.success) {
                // Show success message
                resultEl.innerHTML = this._renderAnalysisSuccess(response);
                
                // Update wizard data
                window.migrationWizard.wizard.setData({
                    analysisComplete: true,
                    analysisResults: response,
                    activeMigrationId: response.migration_id
                });
                
                // Set active migration ID in wizard
                window.migrationWizard.setActiveMigrationId(response.migration_id);
                
                // Set up resource cards
                this._setupResourceCards(container, {
                    ...data,
                    analysisComplete: true,
                    analysisResults: response
                });
                
                showToast('Analysis completed successfully', 'success');
            } else {
                // Show error message
                resultEl.innerHTML = `
                    <div class="alert alert-danger">
                        <i class="fas fa-times-circle"></i>
                        ${response.message || 'Failed to analyze environment'}
                    </div>
                    <button class="btn btn-primary" id="retry-analysis-btn">
                        <i class="fas fa-sync"></i> Retry Analysis
                    </button>
                `;
                
                // Set up retry button
                const retryBtn = resultEl.querySelector('#retry-analysis-btn');
                if (retryBtn) {
                    retryBtn.addEventListener('click', () => {
                        this._startAnalysis(container, data);
                    });
                }
                
                showToast('Failed to analyze environment', 'error');
            }
        } catch (error) {
            console.error('Error analyzing environment:', error);
            
            // Hide progress and show controls
            progressEl.style.display = 'none';
            resultEl.style.display = 'block';
            
            // Show error message
            resultEl.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-times-circle"></i>
                    Error analyzing environment: ${error.message}
                </div>
                <button class="btn btn-primary" id="retry-analysis-btn">
                    <i class="fas fa-sync"></i> Retry Analysis
                </button>
            `;
            
            // Set up retry button
            const retryBtn = resultEl.querySelector('#retry-analysis-btn');
            if (retryBtn) {
                retryBtn.addEventListener('click', () => {
                    this._startAnalysis(container, data);
                });
            }
            
            showToast(`Error analyzing environment: ${error.message}`, 'error');
        }
    },

    /**
     * Render analysis success message
     * @param {Object} results - Analysis results
     * @returns {string} HTML content
     * @private
     */
    _renderAnalysisSuccess: function(results) {
        const resources = results.resources || {};
        const vms = resources.vms || [];
        const containers = resources.containers || [];
        const storage = resources.storage || [];
        const networks = resources.networks || [];
        
        return `
            <div class="alert alert-success mb-4">
                <i class="fas fa-check-circle"></i>
                Analysis completed successfully! We found the following resources:
            </div>
            
            <div class="row resource-summary mb-4">
                <div class="col-md-3 col-sm-6">
                    <div class="card text-center">
                        <div class="card-body">
                            <h1 class="display-4">${vms.length}</h1>
                            <h5>Virtual Machines</h5>
                        </div>
                    </div>
                </div>
                <div class="col-md-3 col-sm-6">
                    <div class="card text-center">
                        <div class="card-body">
                            <h1 class="display-4">${containers.length}</h1>
                            <h5>Containers</h5>
                        </div>
                    </div>
                </div>
                <div class="col-md-3 col-sm-6">
                    <div class="card text-center">
                        <div class="card-body">
                            <h1 class="display-4">${storage.length}</h1>
                            <h5>Storage Volumes</h5>
                        </div>
                    </div>
                </div>
                <div class="col-md-3 col-sm-6">
                    <div class="card text-center">
                        <div class="card-body">
                            <h1 class="display-4">${networks.length}</h1>
                            <h5>Networks</h5>
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
                        ${this._renderResourceCards(vms, 'vm')}
                    </div>
                    <div class="tab-pane fade" id="containers-tab-pane" role="tabpanel" 
                        aria-labelledby="containers-tab" tabindex="0">
                        ${this._renderResourceCards(containers, 'container')}
                    </div>
                    <div class="tab-pane fade" id="storage-tab-pane" role="tabpanel" 
                        aria-labelledby="storage-tab" tabindex="0">
                        ${this._renderResourceCards(storage, 'storage')}
                    </div>
                    <div class="tab-pane fade" id="networks-tab-pane" role="tabpanel" 
                        aria-labelledby="networks-tab" tabindex="0">
                        ${this._renderResourceCards(networks, 'network')}
                    </div>
                </div>
            </div>
            
            <div class="mt-4">
                <button class="btn btn-primary" id="continue-to-selection-btn">
                    <i class="fas fa-arrow-right"></i> Continue to Resource Selection
                </button>
            </div>
        `;
    },

    /**
     * Render resource cards
     * @param {Array} resources - List of resources
     * @param {string} type - Resource type
     * @returns {string} HTML content
     * @private
     */
    _renderResourceCards: function(resources, type) {
        if (!resources || resources.length === 0) {
            return `
                <div class="alert alert-info">
                    <i class="fas fa-info-circle"></i>
                    No ${type}s found in the source environment.
                </div>
            `;
        }

        let html = `<div class="row resource-cards">`;

        resources.forEach(resource => {
            const icon = this._getResourceIcon(type);
            const title = resource.name || resource.id || 'Unnamed';
            const details = this._getResourceDetails(resource, type);

            html += `
                <div class="col-md-4 col-sm-6 mb-4">
                    <div class="card resource-card" data-resource-id="${resource.id}" data-resource-type="${type}">
                        <div class="card-header d-flex justify-content-between align-items-center">
                            <h5 class="card-title mb-0">
                                <i class="${icon}"></i>
                                ${title}
                            </h5>
                            <div class="form-check">
                                <input class="form-check-input resource-checkbox" type="checkbox" 
                                    id="${type}-${resource.id}" data-resource-id="${resource.id}" 
                                    data-resource-type="${type}" checked>
                            </div>
                        </div>
                        <div class="card-body">
                            <ul class="list-unstyled">
                                ${details}
                            </ul>
                        </div>
                    </div>
                </div>
            `;
        });

        html += `</div>`;
        return html;
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
        let details = '';

        switch (type) {
            case 'vm':
                details += resource.status ? `<li><strong>Status:</strong> ${resource.status}</li>` : '';
                details += resource.vcpus ? `<li><strong>vCPUs:</strong> ${resource.vcpus}</li>` : '';
                details += resource.memory ? `<li><strong>Memory:</strong> ${this._formatMemory(resource.memory)}</li>` : '';
                details += resource.disk_size ? `<li><strong>Disk:</strong> ${this._formatSize(resource.disk_size)}</li>` : '';
                details += resource.os ? `<li><strong>OS:</strong> ${resource.os}</li>` : '';
                break;
            case 'container':
                details += resource.status ? `<li><strong>Status:</strong> ${resource.status}</li>` : '';
                details += resource.image ? `<li><strong>Image:</strong> ${resource.image}</li>` : '';
                details += resource.vcpus ? `<li><strong>vCPUs:</strong> ${resource.vcpus}</li>` : '';
                details += resource.memory ? `<li><strong>Memory:</strong> ${this._formatMemory(resource.memory)}</li>` : '';
                details += resource.disk_size ? `<li><strong>Disk:</strong> ${this._formatSize(resource.disk_size)}</li>` : '';
                break;
            case 'storage':
                details += resource.type ? `<li><strong>Type:</strong> ${resource.type}</li>` : '';
                details += resource.size ? `<li><strong>Size:</strong> ${this._formatSize(resource.size)}</li>` : '';
                details += resource.used ? `<li><strong>Used:</strong> ${this._formatSize(resource.used)} (${Math.round(resource.used / resource.size * 100)}%)</li>` : '';
                details += resource.mountpoint ? `<li><strong>Mount:</strong> ${resource.mountpoint}</li>` : '';
                break;
            case 'network':
                details += resource.type ? `<li><strong>Type:</strong> ${resource.type}</li>` : '';
                details += resource.vlan_id ? `<li><strong>VLAN ID:</strong> ${resource.vlan_id}</li>` : '';
                details += resource.subnet ? `<li><strong>Subnet:</strong> ${resource.subnet}</li>` : '';
                details += resource.gateway ? `<li><strong>Gateway:</strong> ${resource.gateway}</li>` : '';
                break;
        }

        return details;
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
     * Render analysis results
     * @param {Object} data - Wizard data
     * @returns {string} HTML content
     * @private
     */
    _renderAnalysisResults: function(data) {
        const results = data.analysisResults;
        const platform = data.platformDetails;

        return `
            <div class="analysis-step">
                <h4 class="mb-4">
                    <i class="fas ${platform.icon || 'fa-server'}"></i>
                    ${platform.name} Environment Analysis
                </h4>
                
                <div class="alert alert-success mb-4">
                    <i class="fas fa-check-circle"></i>
                    Analysis completed successfully! Review the discovered resources below.
                </div>
                
                ${this._renderAnalysisSuccess(results)}
            </div>
        `;
    },

    /**
     * Set up resource cards
     * @param {HTMLElement} container - Step container
     * @param {Object} data - Wizard data
     * @private
     */
    _setupResourceCards: function(container, data) {
        // Set up continue button
        const continueBtn = container.querySelector('#continue-to-selection-btn');
        if (continueBtn) {
            continueBtn.addEventListener('click', () => {
                window.migrationWizard.wizard.goToStep(3);
            });
        }

        // Set up resource checkboxes
        const checkboxes = container.querySelectorAll('.resource-checkbox');
        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', () => {
                const resourceId = checkbox.dataset.resourceId;
                const resourceType = checkbox.dataset.resourceType;
                
                // Update selected resources in wizard data
                const selectedResources = data.selectedResources || {
                    vms: [],
                    containers: [],
                    storage: [],
                    networks: []
                };
                
                const typeKey = `${resourceType}s`; // Convert to plural
                
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
            });
        });

        // Initialize selected resources in wizard data
        const resources = data.analysisResults.resources || {};
        const selectedResources = {
            vms: resources.vms ? resources.vms.map(vm => vm.id) : [],
            containers: resources.containers ? resources.containers.map(container => container.id) : [],
            storage: resources.storage ? resources.storage.map(storage => storage.id) : [],
            networks: resources.networks ? resources.networks.map(network => network.id) : []
        };
        
        // Update wizard data
        window.migrationWizard.wizard.setData({ selectedResources });
    }
};

export default AnalysisStep;
