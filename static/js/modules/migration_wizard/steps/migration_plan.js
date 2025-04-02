/**
 * Migration Plan Step
 * Sixth step in the migration wizard for reviewing the migration plan
 */

import { apiRequest } from '../../api.js';
import { showToast } from '../../notifications.js';

export const MigrationPlanStep = {
    /**
     * Render the migration plan step
     * @param {Object} data - Wizard data
     * @returns {string} HTML content
     */
    render: function(data) {
        if (!data.targetNode || !data.targetStorage) {
            return `
                <div class="alert alert-warning">
                    <i class="fas fa-exclamation-triangle"></i>
                    Please complete the target selection step first.
                </div>
                <button class="btn btn-primary" id="back-to-target-btn">
                    <i class="fas fa-arrow-left"></i> Back to Target Selection
                </button>
            `;
        }

        // If plan is already generated, show it
        if (data.migrationPlan) {
            return this._renderMigrationPlan(data);
        }

        const platform = data.platformDetails;

        return `
            <div class="migration-plan-step">
                <h4 class="mb-4">
                    <i class="fas ${platform.icon || 'fa-server'}"></i>
                    Generate Migration Plan
                </h4>
                <p class="mb-4">
                    We need to generate a migration plan based on your selections.
                    This will analyze the resources and create a detailed plan for migration.
                </p>
                
                <div class="card mb-4">
                    <div class="card-header">
                        <h5 class="card-title mb-0">Migration Summary</h5>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-6">
                                <h6>Source Environment</h6>
                                <p><strong>Platform:</strong> ${platform.name}</p>
                                <p><strong>Host:</strong> ${data.credentials.host}</p>
                                ${this._renderResourceSummary(data)}
                            </div>
                            <div class="col-md-6">
                                <h6>Target Environment</h6>
                                <p><strong>Node:</strong> ${data.targetNode}</p>
                                <p><strong>Storage:</strong> ${data.targetStorage}</p>
                                ${data.backupStorage ? `<p><strong>Backup Storage:</strong> ${data.backupStorage}</p>` : ''}
                                <h6 class="mt-3">Options</h6>
                                <ul class="list-unstyled">
                                    <li>
                                        <i class="fas ${data.createBackups ? 'fa-check-circle text-success' : 'fa-times-circle text-danger'}"></i>
                                        Create backups before migration
                                    </li>
                                    <li>
                                        <i class="fas ${data.shutdownSource ? 'fa-check-circle text-success' : 'fa-times-circle text-danger'}"></i>
                                        Shutdown source resources
                                    </li>
                                    <li>
                                        <i class="fas ${data.startAfterMigration !== false ? 'fa-check-circle text-success' : 'fa-times-circle text-danger'}"></i>
                                        Start resources after migration
                                    </li>
                                    <li>
                                        <i class="fas ${data.verifyMigration !== false ? 'fa-check-circle text-success' : 'fa-times-circle text-danger'}"></i>
                                        Verify migration
                                    </li>
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div id="plan-controls">
                    <button class="btn btn-primary" id="generate-plan-btn">
                        <i class="fas fa-cogs"></i> Generate Migration Plan
                    </button>
                </div>
                
                <div id="plan-progress" style="display: none;">
                    <div class="progress mb-3">
                        <div class="progress-bar progress-bar-striped progress-bar-animated" 
                            role="progressbar" style="width: 100%"></div>
                    </div>
                    <p class="text-center" id="plan-status">Generating migration plan...</p>
                </div>
                
                <div id="plan-result" class="mt-4" style="display: none;"></div>
                
                <div class="mt-4 d-flex justify-content-between">
                    <div>
                        <button class="btn btn-secondary" id="back-to-target-btn">
                            <i class="fas fa-arrow-left"></i> Back to Target Selection
                        </button>
                    </div>
                </div>
            </div>
        `;
    },

    /**
     * Initialize the migration plan step
     * @param {HTMLElement} container - Step container
     * @param {Object} data - Wizard data
     */
    init: function(container, data) {
        const backBtn = container.querySelector('#back-to-target-btn');
        if (backBtn) {
            backBtn.addEventListener('click', () => {
                window.migrationWizard.wizard.goToStep(4);
            });
        }

        // If plan is already generated, set up continue button
        if (data.migrationPlan) {
            const continueBtn = container.querySelector('#continue-to-execution-btn');
            if (continueBtn) {
                continueBtn.addEventListener('click', () => {
                    window.migrationWizard.wizard.goToStep(6);
                });
            }
            return;
        }

        const generateBtn = container.querySelector('#generate-plan-btn');
        if (generateBtn) {
            generateBtn.addEventListener('click', () => {
                this._generatePlan(container, data);
            });
        }
    },

    /**
     * Validate the migration plan step
     * @param {Object} data - Wizard data
     * @returns {boolean} True if valid, false otherwise
     */
    validate: function(data) {
        if (!data.migrationPlan) {
            showToast('Please generate a migration plan first', 'warning');
            return false;
        }
        return true;
    },

    /**
     * Process the migration plan step
     * @param {Object} data - Wizard data
     */
    process: function(data) {
        // Nothing to process here, just pass the migration plan to the next step
    },

    /**
     * Generate migration plan
     * @param {HTMLElement} container - Step container
     * @param {Object} data - Wizard data
     * @private
     */
    _generatePlan: async function(container, data) {
        const controlsEl = container.querySelector('#plan-controls');
        const progressEl = container.querySelector('#plan-progress');
        const statusEl = container.querySelector('#plan-status');
        const resultEl = container.querySelector('#plan-result');
        
        if (!controlsEl || !progressEl || !statusEl || !resultEl) return;
        
        // Show progress and hide controls
        controlsEl.style.display = 'none';
        progressEl.style.display = 'block';
        resultEl.style.display = 'none';
        
        try {
            // Update status
            statusEl.textContent = 'Generating migration plan...';
            
            // Prepare request data
            const requestData = {
                migration_id: data.activeMigrationId,
                source_resources: {
                    vms: data.selectedResources.vms,
                    containers: data.selectedResources.containers,
                    storage: data.selectedResources.storage,
                    networks: data.selectedResources.networks
                },
                target_node: data.targetNode
            };
            
            // Generate plan
            const response = await apiRequest('POST', '/api/migration/plan', requestData);
            
            // Hide progress
            progressEl.style.display = 'none';
            resultEl.style.display = 'block';
            
            if (response && response.success) {
                // Update wizard data
                window.migrationWizard.wizard.setData({
                    migrationPlan: response.plan
                });
                
                // Show success message
                resultEl.innerHTML = this._renderPlanResult(response.plan, data);
                
                showToast('Migration plan generated successfully', 'success');
            } else {
                // Show error message
                resultEl.innerHTML = `
                    <div class="alert alert-danger">
                        <i class="fas fa-times-circle"></i>
                        ${response.message || 'Failed to generate migration plan'}
                    </div>
                    <button class="btn btn-primary" id="retry-plan-btn">
                        <i class="fas fa-sync"></i> Retry
                    </button>
                `;
                
                // Set up retry button
                const retryBtn = resultEl.querySelector('#retry-plan-btn');
                if (retryBtn) {
                    retryBtn.addEventListener('click', () => {
                        this._generatePlan(container, data);
                    });
                }
                
                showToast('Failed to generate migration plan', 'error');
            }
        } catch (error) {
            console.error('Error generating migration plan:', error);
            
            // Hide progress and show controls
            progressEl.style.display = 'none';
            resultEl.style.display = 'block';
            
            // Show error message
            resultEl.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-times-circle"></i>
                    Error generating migration plan: ${error.message}
                </div>
                <button class="btn btn-primary" id="retry-plan-btn">
                    <i class="fas fa-sync"></i> Retry
                </button>
            `;
            
            // Set up retry button
            const retryBtn = resultEl.querySelector('#retry-plan-btn');
            if (retryBtn) {
                retryBtn.addEventListener('click', () => {
                    this._generatePlan(container, data);
                });
            }
            
            showToast(`Error generating migration plan: ${error.message}`, 'error');
        }
    },

    /**
     * Render resource summary
     * @param {Object} data - Wizard data
     * @returns {string} HTML content
     * @private
     */
    _renderResourceSummary: function(data) {
        const selectedResources = data.selectedResources || {
            vms: [],
            containers: [],
            storage: [],
            networks: []
        };
        
        return `
            <h6 class="mt-3">Selected Resources</h6>
            <ul class="list-unstyled">
                <li>
                    <i class="fas fa-desktop"></i>
                    ${selectedResources.vms.length} Virtual Machines
                </li>
                <li>
                    <i class="fas fa-cube"></i>
                    ${selectedResources.containers.length} Containers
                </li>
                <li>
                    <i class="fas fa-hdd"></i>
                    ${selectedResources.storage.length} Storage Volumes
                </li>
                <li>
                    <i class="fas fa-network-wired"></i>
                    ${selectedResources.networks.length} Networks
                </li>
            </ul>
        `;
    },

    /**
     * Render plan result
     * @param {Object} plan - Migration plan
     * @param {Object} data - Wizard data
     * @returns {string} HTML content
     * @private
     */
    _renderPlanResult: function(plan, data) {
        return `
            <div class="alert alert-success mb-4">
                <i class="fas fa-check-circle"></i>
                Migration plan generated successfully! Review the details below.
            </div>
            
            <div class="card mb-4">
                <div class="card-header">
                    <h5 class="card-title mb-0">Migration Plan</h5>
                </div>
                <div class="card-body">
                    <div class="row mb-4">
                        <div class="col-md-6">
                            <h6>Resources to Migrate</h6>
                            <ul class="list-unstyled">
                                <li>
                                    <i class="fas fa-desktop"></i>
                                    ${plan.resources.vms.length} Virtual Machines
                                </li>
                                <li>
                                    <i class="fas fa-cube"></i>
                                    ${plan.resources.containers.length} Containers
                                </li>
                                <li>
                                    <i class="fas fa-hdd"></i>
                                    ${plan.resources.storage.length} Storage Volumes
                                </li>
                                <li>
                                    <i class="fas fa-network-wired"></i>
                                    ${plan.resources.networks.length} Networks
                                </li>
                            </ul>
                        </div>
                        <div class="col-md-6">
                            <h6>Estimated Resources</h6>
                            <ul class="list-unstyled">
                                <li>
                                    <i class="fas fa-memory"></i>
                                    Memory: ${this._formatMemory(plan.estimates.memory_required_mb)}
                                </li>
                                <li>
                                    <i class="fas fa-hdd"></i>
                                    Storage: ${this._formatSize(plan.estimates.storage_required_bytes)}
                                </li>
                                <li>
                                    <i class="fas fa-microchip"></i>
                                    vCPUs: ${plan.estimates.vcpus_required}
                                </li>
                                <li>
                                    <i class="fas fa-clock"></i>
                                    Estimated Time: ${this._formatDuration(plan.estimates.estimated_migration_time_seconds)}
                                </li>
                            </ul>
                        </div>
                    </div>
                    
                    <div class="row">
                        <div class="col-12">
                            <h6>Migration Steps</h6>
                            <ol class="list-group list-group-numbered mb-3">
                                ${plan.steps.map(step => `
                                    <li class="list-group-item">
                                        <div class="ms-2 me-auto">
                                            <div class="fw-bold">${step.title}</div>
                                            ${step.description}
                                        </div>
                                    </li>
                                `).join('')}
                            </ol>
                            
                            ${plan.warnings && plan.warnings.length > 0 ? `
                                <div class="alert alert-warning">
                                    <h6><i class="fas fa-exclamation-triangle"></i> Warnings</h6>
                                    <ul>
                                        ${plan.warnings.map(warning => `<li>${warning}</li>`).join('')}
                                    </ul>
                                </div>
                            ` : ''}
                            
                            ${plan.notes ? `
                                <div class="alert alert-info">
                                    <h6><i class="fas fa-info-circle"></i> Notes</h6>
                                    <p>${plan.notes}</p>
                                </div>
                            ` : ''}
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="mt-4 d-flex justify-content-between">
                <div>
                    <button class="btn btn-secondary" id="back-to-target-btn">
                        <i class="fas fa-arrow-left"></i> Back to Target Selection
                    </button>
                </div>
                <div>
                    <button class="btn btn-primary" id="continue-to-execution-btn">
                        <i class="fas fa-arrow-right"></i> Continue to Execution
                    </button>
                </div>
            </div>
        `;
    },

    /**
     * Render migration plan
     * @param {Object} data - Wizard data
     * @returns {string} HTML content
     * @private
     */
    _renderMigrationPlan: function(data) {
        const platform = data.platformDetails;
        const plan = data.migrationPlan;

        return `
            <div class="migration-plan-step">
                <h4 class="mb-4">
                    <i class="fas ${platform.icon || 'fa-server'}"></i>
                    Migration Plan
                </h4>
                <p class="mb-4">
                    Review the migration plan below. If everything looks good, proceed to execution.
                </p>
                
                ${this._renderPlanResult(plan, data)}
            </div>
        `;
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
     * Format duration in seconds to human-readable format
     * @param {number} seconds - Duration in seconds
     * @returns {string} Formatted duration
     * @private
     */
    _formatDuration: function(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);
        
        return `${hours}h ${minutes}m ${secs}s`;
    }
};

export default MigrationPlanStep;
