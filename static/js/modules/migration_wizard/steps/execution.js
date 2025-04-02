/**
 * Execution Step
 * Seventh step in the migration wizard for executing the migration
 */

import { apiRequest } from '../../api.js';
import { showToast } from '../../notifications.js';

export const ExecutionStep = {
    /**
     * Render the execution step
     * @param {Object} data - Wizard data
     * @returns {string} HTML content
     */
    render: function(data) {
        if (!data.migrationPlan) {
            return `
                <div class="alert alert-warning">
                    <i class="fas fa-exclamation-triangle"></i>
                    Please complete the migration plan step first.
                </div>
                <button class="btn btn-primary" id="back-to-plan-btn">
                    <i class="fas fa-arrow-left"></i> Back to Migration Plan
                </button>
            `;
        }

        const platform = data.platformDetails;
        const migrationStatus = data.migrationStatus || {};
        const isRunning = migrationStatus.status === 'running';
        const isCompleted = migrationStatus.status === 'completed';
        const isFailed = migrationStatus.status === 'failed';
        const isPaused = migrationStatus.status === 'paused';
        const isCancelled = migrationStatus.status === 'cancelled';
        const hasStarted = isRunning || isCompleted || isFailed || isPaused || isCancelled;

        return `
            <div class="execution-step">
                <h4 class="mb-4">
                    <i class="fas ${platform.icon || 'fa-server'}"></i>
                    Migration Execution
                </h4>
                <p class="mb-4">
                    ${hasStarted 
                        ? 'Your migration is in progress. You can monitor the status below.'
                        : 'Execute the migration plan. This will start the migration process.'}
                </p>
                
                <div class="card mb-4">
                    <div class="card-header">
                        <h5 class="card-title mb-0">Migration Status</h5>
                    </div>
                    <div class="card-body">
                        <div id="migration-status-container">
                            ${hasStarted 
                                ? this._renderMigrationStatus(migrationStatus)
                                : `
                                    <div class="alert alert-info">
                                        <i class="fas fa-info-circle"></i>
                                        Migration has not started yet. Click the "Start Migration" button to begin.
                                    </div>
                                `
                            }
                        </div>
                    </div>
                </div>
                
                <div id="execution-controls" class="mb-4">
                    ${!hasStarted ? `
                        <button class="btn btn-primary" id="start-migration-btn">
                            <i class="fas fa-play"></i> Start Migration
                        </button>
                    ` : ''}
                    
                    ${isRunning ? `
                        <button class="btn btn-warning" id="pause-migration-btn">
                            <i class="fas fa-pause"></i> Pause Migration
                        </button>
                        <button class="btn btn-danger" id="cancel-migration-btn">
                            <i class="fas fa-times"></i> Cancel Migration
                        </button>
                    ` : ''}
                    
                    ${isPaused ? `
                        <button class="btn btn-primary" id="resume-migration-btn">
                            <i class="fas fa-play"></i> Resume Migration
                        </button>
                        <button class="btn btn-danger" id="cancel-migration-btn">
                            <i class="fas fa-times"></i> Cancel Migration
                        </button>
                    ` : ''}
                    
                    ${(isCompleted || isFailed || isCancelled) ? `
                        <button class="btn btn-primary" id="view-report-btn">
                            <i class="fas fa-file-alt"></i> View Migration Report
                        </button>
                    ` : ''}
                </div>
                
                <div class="mt-4 d-flex justify-content-between">
                    <div>
                        <button class="btn btn-secondary" id="back-to-plan-btn" ${isRunning ? 'disabled' : ''}>
                            <i class="fas fa-arrow-left"></i> Back to Migration Plan
                        </button>
                    </div>
                    <div>
                        ${(isCompleted || isFailed || isCancelled) ? `
                            <button class="btn btn-primary" id="continue-to-summary-btn">
                                <i class="fas fa-arrow-right"></i> Continue to Summary
                            </button>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;
    },

    /**
     * Initialize the execution step
     * @param {HTMLElement} container - Step container
     * @param {Object} data - Wizard data
     */
    init: function(container, data) {
        const backBtn = container.querySelector('#back-to-plan-btn');
        if (backBtn) {
            backBtn.addEventListener('click', () => {
                window.migrationWizard.wizard.goToStep(5);
            });
        }

        const continueBtn = container.querySelector('#continue-to-summary-btn');
        if (continueBtn) {
            continueBtn.addEventListener('click', () => {
                window.migrationWizard.wizard.goToStep(7);
            });
        }

        // Start migration button
        const startBtn = container.querySelector('#start-migration-btn');
        if (startBtn) {
            startBtn.addEventListener('click', () => {
                this._startMigration(container, data);
            });
        }

        // Pause migration button
        const pauseBtn = container.querySelector('#pause-migration-btn');
        if (pauseBtn) {
            pauseBtn.addEventListener('click', () => {
                this._pauseMigration(container, data);
            });
        }

        // Resume migration button
        const resumeBtn = container.querySelector('#resume-migration-btn');
        if (resumeBtn) {
            resumeBtn.addEventListener('click', () => {
                this._resumeMigration(container, data);
            });
        }

        // Cancel migration button
        const cancelBtn = container.querySelector('#cancel-migration-btn');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => {
                this._cancelMigration(container, data);
            });
        }

        // View report button
        const reportBtn = container.querySelector('#view-report-btn');
        if (reportBtn) {
            reportBtn.addEventListener('click', () => {
                this._viewMigrationReport(data);
            });
        }

        // Start status polling if migration is running
        if (data.migrationStatus && data.migrationStatus.status === 'running') {
            this._startStatusPolling(container, data);
        }
    },

    /**
     * Validate the execution step
     * @param {Object} data - Wizard data
     * @returns {boolean} True if valid, false otherwise
     */
    validate: function(data) {
        if (!data.migrationStatus || 
            (data.migrationStatus.status !== 'completed' && 
             data.migrationStatus.status !== 'failed' &&
             data.migrationStatus.status !== 'cancelled')) {
            showToast('Migration must be completed, failed, or cancelled to proceed', 'warning');
            return false;
        }
        return true;
    },

    /**
     * Process the execution step
     * @param {Object} data - Wizard data
     */
    process: function(data) {
        // Nothing to process here, just pass the migration status to the next step
    },

    /**
     * Start migration
     * @param {HTMLElement} container - Step container
     * @param {Object} data - Wizard data
     * @private
     */
    _startMigration: async function(container, data) {
        try {
            const requestData = {
                migration_id: data.activeMigrationId,
                plan_id: data.migrationPlan.plan_id,
                options: {
                    create_backups: data.createBackups || false,
                    shutdown_source: data.shutdownSource || false,
                    start_after_migration: data.startAfterMigration !== false,
                    verify_migration: data.verifyMigration !== false
                }
            };
            
            const response = await apiRequest('POST', '/api/migration/execute', requestData);
            
            if (response && response.success) {
                // Update wizard data
                window.migrationWizard.wizard.setData({
                    migrationStatus: response.status
                });
                
                // Refresh the UI
                container.innerHTML = this.render(window.migrationWizard.wizard.getData());
                this.init(container, window.migrationWizard.wizard.getData());
                
                // Start polling for status updates
                this._startStatusPolling(container, window.migrationWizard.wizard.getData());
                
                showToast('Migration started successfully', 'success');
            } else {
                throw new Error(response.message || 'Failed to start migration');
            }
        } catch (error) {
            console.error('Error starting migration:', error);
            showToast(`Error starting migration: ${error.message}`, 'error');
        }
    },

    /**
     * Pause migration
     * @param {HTMLElement} container - Step container
     * @param {Object} data - Wizard data
     * @private
     */
    _pauseMigration: async function(container, data) {
        try {
            const response = await apiRequest('POST', `/api/migration/${data.activeMigrationId}/pause`);
            
            if (response && response.success) {
                // Update wizard data
                window.migrationWizard.wizard.setData({
                    migrationStatus: response.status
                });
                
                // Refresh the UI
                container.innerHTML = this.render(window.migrationWizard.wizard.getData());
                this.init(container, window.migrationWizard.wizard.getData());
                
                showToast('Migration paused successfully', 'success');
            } else {
                throw new Error(response.message || 'Failed to pause migration');
            }
        } catch (error) {
            console.error('Error pausing migration:', error);
            showToast(`Error pausing migration: ${error.message}`, 'error');
        }
    },

    /**
     * Resume migration
     * @param {HTMLElement} container - Step container
     * @param {Object} data - Wizard data
     * @private
     */
    _resumeMigration: async function(container, data) {
        try {
            const response = await apiRequest('POST', `/api/migration/${data.activeMigrationId}/resume`);
            
            if (response && response.success) {
                // Update wizard data
                window.migrationWizard.wizard.setData({
                    migrationStatus: response.status
                });
                
                // Refresh the UI
                container.innerHTML = this.render(window.migrationWizard.wizard.getData());
                this.init(container, window.migrationWizard.wizard.getData());
                
                // Start polling for status updates
                this._startStatusPolling(container, window.migrationWizard.wizard.getData());
                
                showToast('Migration resumed successfully', 'success');
            } else {
                throw new Error(response.message || 'Failed to resume migration');
            }
        } catch (error) {
            console.error('Error resuming migration:', error);
            showToast(`Error resuming migration: ${error.message}`, 'error');
        }
    },

    /**
     * Cancel migration
     * @param {HTMLElement} container - Step container
     * @param {Object} data - Wizard data
     * @private
     */
    _cancelMigration: async function(container, data) {
        // Confirm cancellation
        if (!confirm('Are you sure you want to cancel the migration? This action cannot be undone.')) {
            return;
        }
        
        try {
            const response = await apiRequest('POST', `/api/migration/${data.activeMigrationId}/cancel`);
            
            if (response && response.success) {
                // Update wizard data
                window.migrationWizard.wizard.setData({
                    migrationStatus: response.status
                });
                
                // Refresh the UI
                container.innerHTML = this.render(window.migrationWizard.wizard.getData());
                this.init(container, window.migrationWizard.wizard.getData());
                
                showToast('Migration cancelled successfully', 'success');
            } else {
                throw new Error(response.message || 'Failed to cancel migration');
            }
        } catch (error) {
            console.error('Error cancelling migration:', error);
            showToast(`Error cancelling migration: ${error.message}`, 'error');
        }
    },

    /**
     * View migration report
     * @param {Object} data - Wizard data
     * @private
     */
    _viewMigrationReport: function(data) {
        // Open migration report in a new tab
        window.open(`/migration/report/${data.activeMigrationId}`, '_blank');
    },

    /**
     * Start polling for migration status updates
     * @param {HTMLElement} container - Step container
     * @param {Object} data - Wizard data
     * @private
     */
    _startStatusPolling: function(container, data) {
        // Clear existing interval if any
        if (this.statusInterval) {
            clearInterval(this.statusInterval);
        }
        
        // Set up polling interval
        this.statusInterval = setInterval(async () => {
            try {
                const response = await apiRequest('GET', `/api/migration/${data.activeMigrationId}/status`);
                
                if (response && response.success) {
                    const currentStatus = data.migrationStatus ? data.migrationStatus.status : null;
                    const newStatus = response.status.status;
                    
                    // Update wizard data
                    window.migrationWizard.wizard.setData({
                        migrationStatus: response.status
                    });
                    
                    // Update status container
                    const statusContainer = container.querySelector('#migration-status-container');
                    if (statusContainer) {
                        statusContainer.innerHTML = this._renderMigrationStatus(response.status);
                    }
                    
                    // If status changed, refresh the UI
                    if (currentStatus !== newStatus) {
                        container.innerHTML = this.render(window.migrationWizard.wizard.getData());
                        this.init(container, window.migrationWizard.wizard.getData());
                        
                        // Show toast for status change
                        if (newStatus === 'completed') {
                            showToast('Migration completed successfully', 'success');
                            clearInterval(this.statusInterval);
                        } else if (newStatus === 'failed') {
                            showToast('Migration failed', 'error');
                            clearInterval(this.statusInterval);
                        } else if (newStatus === 'cancelled') {
                            showToast('Migration cancelled', 'warning');
                            clearInterval(this.statusInterval);
                        } else if (newStatus === 'paused') {
                            showToast('Migration paused', 'warning');
                            clearInterval(this.statusInterval);
                        }
                    }
                } else {
                    throw new Error(response.message || 'Failed to get migration status');
                }
            } catch (error) {
                console.error('Error getting migration status:', error);
                // Don't show a toast for every error to avoid spamming the user
            }
        }, 5000); // Poll every 5 seconds
    },

    /**
     * Render migration status
     * @param {Object} status - Migration status
     * @returns {string} HTML content
     * @private
     */
    _renderMigrationStatus: function(status) {
        if (!status) {
            return `
                <div class="alert alert-warning">
                    <i class="fas fa-exclamation-triangle"></i>
                    No migration status available.
                </div>
            `;
        }
        
        const statusClass = this._getStatusClass(status.status);
        const statusIcon = this._getStatusIcon(status.status);
        const statusText = this._getStatusText(status.status);
        const progress = status.progress || 0;
        const currentStep = status.current_step || {};
        const completedSteps = status.completed_steps || [];
        const pendingSteps = status.pending_steps || [];
        const errors = status.errors || [];
        
        return `
            <div class="mb-4">
                <div class="d-flex align-items-center mb-3">
                    <div class="me-3">
                        <span class="badge ${statusClass} fs-6 p-2">
                            <i class="fas ${statusIcon}"></i>
                            ${statusText}
                        </span>
                    </div>
                    <div class="flex-grow-1">
                        <div class="progress" style="height: 20px;">
                            <div class="progress-bar ${statusClass} progress-bar-striped ${status.status === 'running' ? 'progress-bar-animated' : ''}" 
                                role="progressbar" style="width: ${progress}%" 
                                aria-valuenow="${progress}" aria-valuemin="0" aria-valuemax="100">
                                ${progress}%
                            </div>
                        </div>
                    </div>
                </div>
                
                ${status.status === 'running' ? `
                    <div class="alert alert-info">
                        <div class="d-flex align-items-center">
                            <div class="spinner-border spinner-border-sm me-2" role="status">
                                <span class="visually-hidden">Loading...</span>
                            </div>
                            <div>
                                <strong>Current Step:</strong> ${currentStep.title || 'N/A'}
                                <div>${currentStep.description || ''}</div>
                            </div>
                        </div>
                    </div>
                ` : ''}
                
                ${status.status === 'paused' ? `
                    <div class="alert alert-warning">
                        <i class="fas fa-pause-circle"></i>
                        Migration is paused. Click "Resume Migration" to continue.
                    </div>
                ` : ''}
                
                ${status.status === 'failed' ? `
                    <div class="alert alert-danger">
                        <i class="fas fa-times-circle"></i>
                        Migration failed. See errors below for details.
                    </div>
                ` : ''}
                
                ${status.status === 'cancelled' ? `
                    <div class="alert alert-warning">
                        <i class="fas fa-times-circle"></i>
                        Migration was cancelled.
                    </div>
                ` : ''}
                
                ${errors.length > 0 ? `
                    <div class="card mb-3">
                        <div class="card-header bg-danger text-white">
                            <h6 class="card-title mb-0">
                                <i class="fas fa-exclamation-triangle"></i>
                                Errors
                            </h6>
                        </div>
                        <div class="card-body">
                            <ul class="list-group">
                                ${errors.map(error => `
                                    <li class="list-group-item list-group-item-danger">
                                        ${error.message}
                                        ${error.details ? `<div class="small">${error.details}</div>` : ''}
                                    </li>
                                `).join('')}
                            </ul>
                        </div>
                    </div>
                ` : ''}
                
                <div class="row">
                    <div class="col-md-6">
                        <div class="card mb-3">
                            <div class="card-header bg-success text-white">
                                <h6 class="card-title mb-0">
                                    <i class="fas fa-check-circle"></i>
                                    Completed Steps (${completedSteps.length})
                                </h6>
                            </div>
                            <div class="card-body">
                                <ul class="list-group">
                                    ${completedSteps.length > 0 ? completedSteps.map(step => `
                                        <li class="list-group-item list-group-item-success">
                                            <i class="fas fa-check-circle me-2"></i>
                                            ${step.title}
                                        </li>
                                    `).join('') : `
                                        <li class="list-group-item">
                                            No steps completed yet.
                                        </li>
                                    `}
                                </ul>
                            </div>
                        </div>
                    </div>
                    
                    <div class="col-md-6">
                        <div class="card mb-3">
                            <div class="card-header bg-secondary text-white">
                                <h6 class="card-title mb-0">
                                    <i class="fas fa-hourglass-half"></i>
                                    Pending Steps (${pendingSteps.length})
                                </h6>
                            </div>
                            <div class="card-body">
                                <ul class="list-group">
                                    ${pendingSteps.length > 0 ? pendingSteps.map(step => `
                                        <li class="list-group-item">
                                            <i class="fas fa-hourglass-half me-2"></i>
                                            ${step.title}
                                        </li>
                                    `).join('') : `
                                        <li class="list-group-item">
                                            No pending steps.
                                        </li>
                                    `}
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>
                
                ${status.start_time ? `
                    <div class="row">
                        <div class="col-md-6">
                            <p><strong>Started:</strong> ${new Date(status.start_time).toLocaleString()}</p>
                        </div>
                        ${status.end_time ? `
                            <div class="col-md-6">
                                <p><strong>Ended:</strong> ${new Date(status.end_time).toLocaleString()}</p>
                            </div>
                        ` : ''}
                    </div>
                ` : ''}
                
                ${status.status === 'completed' ? `
                    <div class="alert alert-success">
                        <i class="fas fa-check-circle"></i>
                        Migration completed successfully! You can view the detailed report.
                    </div>
                ` : ''}
            </div>
        `;
    },

    /**
     * Get status class
     * @param {string} status - Status
     * @returns {string} Status class
     * @private
     */
    _getStatusClass: function(status) {
        switch (status) {
            case 'running':
                return 'bg-primary';
            case 'completed':
                return 'bg-success';
            case 'failed':
                return 'bg-danger';
            case 'paused':
                return 'bg-warning';
            case 'cancelled':
                return 'bg-secondary';
            default:
                return 'bg-secondary';
        }
    },

    /**
     * Get status icon
     * @param {string} status - Status
     * @returns {string} Status icon
     * @private
     */
    _getStatusIcon: function(status) {
        switch (status) {
            case 'running':
                return 'fa-sync fa-spin';
            case 'completed':
                return 'fa-check-circle';
            case 'failed':
                return 'fa-times-circle';
            case 'paused':
                return 'fa-pause-circle';
            case 'cancelled':
                return 'fa-ban';
            default:
                return 'fa-question-circle';
        }
    },

    /**
     * Get status text
     * @param {string} status - Status
     * @returns {string} Status text
     * @private
     */
    _getStatusText: function(status) {
        switch (status) {
            case 'running':
                return 'Running';
            case 'completed':
                return 'Completed';
            case 'failed':
                return 'Failed';
            case 'paused':
                return 'Paused';
            case 'cancelled':
                return 'Cancelled';
            default:
                return 'Unknown';
        }
    }
};

export default ExecutionStep;
