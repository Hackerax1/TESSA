/**
 * Summary Step
 * Final step in the migration wizard showing the migration summary
 */

import { apiRequest } from '../../api.js';
import { showToast } from '../../notifications.js';

export const SummaryStep = {
    /**
     * Render the summary step
     * @param {Object} data - Wizard data
     * @returns {string} HTML content
     */
    render: function(data) {
        if (!data.migrationStatus || 
            (data.migrationStatus.status !== 'completed' && 
             data.migrationStatus.status !== 'failed' &&
             data.migrationStatus.status !== 'cancelled')) {
            return `
                <div class="alert alert-warning">
                    <i class="fas fa-exclamation-triangle"></i>
                    Please complete the migration execution step first.
                </div>
                <button class="btn btn-primary" id="back-to-execution-btn">
                    <i class="fas fa-arrow-left"></i> Back to Execution
                </button>
            `;
        }

        const platform = data.platformDetails;
        const status = data.migrationStatus;
        const isCompleted = status.status === 'completed';
        const isFailed = status.status === 'failed';
        const isCancelled = status.status === 'cancelled';
        const migrationReport = data.migrationReport || {};

        return `
            <div class="summary-step">
                <h4 class="mb-4">
                    <i class="fas ${platform.icon || 'fa-server'}"></i>
                    Migration Summary
                </h4>
                
                <div class="alert ${isCompleted ? 'alert-success' : isFailed ? 'alert-danger' : 'alert-warning'} mb-4">
                    <i class="fas ${isCompleted ? 'fa-check-circle' : isFailed ? 'fa-times-circle' : 'fa-exclamation-triangle'}"></i>
                    ${isCompleted 
                        ? 'Migration completed successfully!' 
                        : isFailed 
                            ? 'Migration failed. See details below.' 
                            : 'Migration was cancelled.'}
                </div>
                
                <div class="card mb-4">
                    <div class="card-header">
                        <h5 class="card-title mb-0">Migration Overview</h5>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-6">
                                <h6>Source Environment</h6>
                                <p><strong>Platform:</strong> ${platform.name}</p>
                                <p><strong>Host:</strong> ${data.credentials.host}</p>
                            </div>
                            <div class="col-md-6">
                                <h6>Target Environment</h6>
                                <p><strong>Node:</strong> ${data.targetNode}</p>
                                <p><strong>Storage:</strong> ${data.targetStorage}</p>
                                ${data.backupStorage ? `<p><strong>Backup Storage:</strong> ${data.backupStorage}</p>` : ''}
                            </div>
                        </div>
                        
                        <div class="row mt-3">
                            <div class="col-md-6">
                                <h6>Timeline</h6>
                                <p><strong>Started:</strong> ${status.start_time ? new Date(status.start_time).toLocaleString() : 'N/A'}</p>
                                <p><strong>Ended:</strong> ${status.end_time ? new Date(status.end_time).toLocaleString() : 'N/A'}</p>
                                <p><strong>Duration:</strong> ${this._calculateDuration(status.start_time, status.end_time)}</p>
                            </div>
                            <div class="col-md-6">
                                <h6>Statistics</h6>
                                <p><strong>Total Resources:</strong> ${this._getTotalResources(migrationReport)}</p>
                                <p><strong>Successful:</strong> ${migrationReport.successful_count || 0}</p>
                                <p><strong>Failed:</strong> ${migrationReport.failed_count || 0}</p>
                            </div>
                        </div>
                    </div>
                </div>
                
                ${this._renderMigrationResults(migrationReport)}
                
                <div class="card mb-4">
                    <div class="card-header">
                        <h5 class="card-title mb-0">Next Steps</h5>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-12">
                                <div class="mb-3">
                                    <button class="btn btn-primary" id="view-report-btn">
                                        <i class="fas fa-file-alt"></i> View Detailed Report
                                    </button>
                                    <button class="btn btn-secondary" id="download-report-btn">
                                        <i class="fas fa-download"></i> Download Report
                                    </button>
                                </div>
                                
                                <div class="list-group">
                                    <a href="/dashboard" class="list-group-item list-group-item-action">
                                        <i class="fas fa-tachometer-alt"></i> Go to Dashboard
                                    </a>
                                    <a href="/vms" class="list-group-item list-group-item-action">
                                        <i class="fas fa-desktop"></i> Manage Virtual Machines
                                    </a>
                                    <a href="/storage" class="list-group-item list-group-item-action">
                                        <i class="fas fa-hdd"></i> Manage Storage
                                    </a>
                                    <a href="/network" class="list-group-item list-group-item-action">
                                        <i class="fas fa-network-wired"></i> Manage Network
                                    </a>
                                    <a href="/migration" class="list-group-item list-group-item-action">
                                        <i class="fas fa-exchange-alt"></i> Start New Migration
                                    </a>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="mt-4 d-flex justify-content-between">
                    <div>
                        <button class="btn btn-secondary" id="back-to-execution-btn">
                            <i class="fas fa-arrow-left"></i> Back to Execution
                        </button>
                    </div>
                    <div>
                        <button class="btn btn-success" id="finish-wizard-btn">
                            <i class="fas fa-check"></i> Finish
                        </button>
                    </div>
                </div>
            </div>
        `;
    },

    /**
     * Initialize the summary step
     * @param {HTMLElement} container - Step container
     * @param {Object} data - Wizard data
     */
    init: function(container, data) {
        const backBtn = container.querySelector('#back-to-execution-btn');
        if (backBtn) {
            backBtn.addEventListener('click', () => {
                window.migrationWizard.wizard.goToStep(6);
            });
        }

        const finishBtn = container.querySelector('#finish-wizard-btn');
        if (finishBtn) {
            finishBtn.addEventListener('click', () => {
                window.location.href = '/dashboard';
            });
        }

        const viewReportBtn = container.querySelector('#view-report-btn');
        if (viewReportBtn) {
            viewReportBtn.addEventListener('click', () => {
                this._viewMigrationReport(data);
            });
        }

        const downloadReportBtn = container.querySelector('#download-report-btn');
        if (downloadReportBtn) {
            downloadReportBtn.addEventListener('click', () => {
                this._downloadMigrationReport(data);
            });
        }

        // Load migration report if not already loaded
        if (!data.migrationReport && data.migrationStatus && 
            (data.migrationStatus.status === 'completed' || 
             data.migrationStatus.status === 'failed' || 
             data.migrationStatus.status === 'cancelled')) {
            this._loadMigrationReport(container, data);
        }
    },

    /**
     * Validate the summary step
     * @param {Object} data - Wizard data
     * @returns {boolean} True if valid, false otherwise
     */
    validate: function(data) {
        // No validation needed for the summary step
        return true;
    },

    /**
     * Process the summary step
     * @param {Object} data - Wizard data
     */
    process: function(data) {
        // Nothing to process here, this is the final step
    },

    /**
     * Load migration report
     * @param {HTMLElement} container - Step container
     * @param {Object} data - Wizard data
     * @private
     */
    _loadMigrationReport: async function(container, data) {
        try {
            const response = await apiRequest('GET', `/api/migration/${data.activeMigrationId}/report`);
            
            if (response && response.success) {
                // Update wizard data
                window.migrationWizard.wizard.setData({
                    migrationReport: response.report
                });
                
                // Refresh the UI
                container.innerHTML = this.render(window.migrationWizard.wizard.getData());
                this.init(container, window.migrationWizard.wizard.getData());
            } else {
                throw new Error(response.message || 'Failed to load migration report');
            }
        } catch (error) {
            console.error('Error loading migration report:', error);
            showToast(`Error loading migration report: ${error.message}`, 'error');
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
     * Download migration report
     * @param {Object} data - Wizard data
     * @private
     */
    _downloadMigrationReport: function(data) {
        // Download migration report
        window.location.href = `/api/migration/${data.activeMigrationId}/report/download`;
    },

    /**
     * Calculate duration between two timestamps
     * @param {string} startTime - Start time
     * @param {string} endTime - End time
     * @returns {string} Formatted duration
     * @private
     */
    _calculateDuration: function(startTime, endTime) {
        if (!startTime || !endTime) {
            return 'N/A';
        }
        
        const start = new Date(startTime);
        const end = new Date(endTime);
        const durationMs = end - start;
        
        const seconds = Math.floor(durationMs / 1000) % 60;
        const minutes = Math.floor(durationMs / (1000 * 60)) % 60;
        const hours = Math.floor(durationMs / (1000 * 60 * 60));
        
        return `${hours}h ${minutes}m ${seconds}s`;
    },

    /**
     * Get total resources from migration report
     * @param {Object} report - Migration report
     * @returns {number} Total resources
     * @private
     */
    _getTotalResources: function(report) {
        if (!report || !report.resources) {
            return 0;
        }
        
        const resources = report.resources;
        return (resources.vms ? resources.vms.length : 0) +
               (resources.containers ? resources.containers.length : 0) +
               (resources.storage ? resources.storage.length : 0) +
               (resources.networks ? resources.networks.length : 0);
    },

    /**
     * Render migration results
     * @param {Object} report - Migration report
     * @returns {string} HTML content
     * @private
     */
    _renderMigrationResults: function(report) {
        if (!report || !report.resources) {
            return `
                <div class="card mb-4">
                    <div class="card-header">
                        <h5 class="card-title mb-0">Migration Results</h5>
                    </div>
                    <div class="card-body">
                        <div class="alert alert-info">
                            <i class="fas fa-info-circle"></i>
                            No migration results available.
                        </div>
                    </div>
                </div>
            `;
        }
        
        const resources = report.resources;
        const vms = resources.vms || [];
        const containers = resources.containers || [];
        const storage = resources.storage || [];
        const networks = resources.networks || [];
        
        return `
            <div class="card mb-4">
                <div class="card-header">
                    <h5 class="card-title mb-0">Migration Results</h5>
                </div>
                <div class="card-body">
                    <ul class="nav nav-tabs" id="resultsTabs" role="tablist">
                        <li class="nav-item" role="presentation">
                            <button class="nav-link active" id="vms-tab" data-bs-toggle="tab" data-bs-target="#vms" 
                                type="button" role="tab" aria-controls="vms" aria-selected="true">
                                <i class="fas fa-desktop"></i> VMs (${vms.length})
                            </button>
                        </li>
                        <li class="nav-item" role="presentation">
                            <button class="nav-link" id="containers-tab" data-bs-toggle="tab" data-bs-target="#containers" 
                                type="button" role="tab" aria-controls="containers" aria-selected="false">
                                <i class="fas fa-cube"></i> Containers (${containers.length})
                            </button>
                        </li>
                        <li class="nav-item" role="presentation">
                            <button class="nav-link" id="storage-tab" data-bs-toggle="tab" data-bs-target="#storage" 
                                type="button" role="tab" aria-controls="storage" aria-selected="false">
                                <i class="fas fa-hdd"></i> Storage (${storage.length})
                            </button>
                        </li>
                        <li class="nav-item" role="presentation">
                            <button class="nav-link" id="networks-tab" data-bs-toggle="tab" data-bs-target="#networks" 
                                type="button" role="tab" aria-controls="networks" aria-selected="false">
                                <i class="fas fa-network-wired"></i> Networks (${networks.length})
                            </button>
                        </li>
                    </ul>
                    <div class="tab-content p-3 border border-top-0 rounded-bottom" id="resultsTabsContent">
                        <div class="tab-pane fade show active" id="vms" role="tabpanel" aria-labelledby="vms-tab">
                            ${this._renderResourceTable(vms, 'vm')}
                        </div>
                        <div class="tab-pane fade" id="containers" role="tabpanel" aria-labelledby="containers-tab">
                            ${this._renderResourceTable(containers, 'container')}
                        </div>
                        <div class="tab-pane fade" id="storage" role="tabpanel" aria-labelledby="storage-tab">
                            ${this._renderResourceTable(storage, 'storage')}
                        </div>
                        <div class="tab-pane fade" id="networks" role="tabpanel" aria-labelledby="networks-tab">
                            ${this._renderResourceTable(networks, 'network')}
                        </div>
                    </div>
                </div>
            </div>
        `;
    },

    /**
     * Render resource table
     * @param {Array} resources - Resources
     * @param {string} type - Resource type
     * @returns {string} HTML content
     * @private
     */
    _renderResourceTable: function(resources, type) {
        if (!resources || resources.length === 0) {
            return `
                <div class="alert alert-info">
                    <i class="fas fa-info-circle"></i>
                    No ${type}s were migrated.
                </div>
            `;
        }
        
        // Define columns based on resource type
        let columns;
        switch (type) {
            case 'vm':
                columns = ['Name', 'ID', 'Status', 'CPU', 'Memory', 'Disk', 'Actions'];
                break;
            case 'container':
                columns = ['Name', 'ID', 'Status', 'CPU', 'Memory', 'Disk', 'Actions'];
                break;
            case 'storage':
                columns = ['Name', 'Type', 'Size', 'Status', 'Actions'];
                break;
            case 'network':
                columns = ['Name', 'Type', 'Status', 'Actions'];
                break;
            default:
                columns = ['Name', 'Status', 'Actions'];
        }
        
        return `
            <div class="table-responsive">
                <table class="table table-striped table-hover">
                    <thead>
                        <tr>
                            ${columns.map(col => `<th>${col}</th>`).join('')}
                        </tr>
                    </thead>
                    <tbody>
                        ${resources.map(resource => this._renderResourceRow(resource, type, columns)).join('')}
                    </tbody>
                </table>
            </div>
        `;
    },

    /**
     * Render resource row
     * @param {Object} resource - Resource
     * @param {string} type - Resource type
     * @param {Array} columns - Table columns
     * @returns {string} HTML content
     * @private
     */
    _renderResourceRow: function(resource, type, columns) {
        const statusClass = resource.status === 'success' ? 'success' : 'danger';
        const statusIcon = resource.status === 'success' ? 'fa-check-circle' : 'fa-times-circle';
        
        let cells = '';
        
        // Generate cells based on columns
        columns.forEach(col => {
            if (col === 'Actions') {
                cells += `
                    <td>
                        <div class="btn-group btn-group-sm" role="group">
                            ${resource.status === 'success' ? `
                                <a href="${this._getResourceLink(resource, type)}" class="btn btn-primary" target="_blank">
                                    <i class="fas fa-external-link-alt"></i>
                                </a>
                            ` : ''}
                            <button type="button" class="btn btn-info" data-bs-toggle="tooltip" 
                                title="${resource.details || 'No details available'}">
                                <i class="fas fa-info-circle"></i>
                            </button>
                        </div>
                    </td>
                `;
            } else if (col === 'Status') {
                cells += `
                    <td>
                        <span class="badge bg-${statusClass}">
                            <i class="fas ${statusIcon}"></i>
                            ${resource.status === 'success' ? 'Success' : 'Failed'}
                        </span>
                        ${resource.error ? `<div class="small text-danger">${resource.error}</div>` : ''}
                    </td>
                `;
            } else {
                // Handle other columns based on resource type
                switch (col) {
                    case 'Name':
                        cells += `<td>${resource.name || 'N/A'}</td>`;
                        break;
                    case 'ID':
                        cells += `<td>${resource.id || 'N/A'}</td>`;
                        break;
                    case 'CPU':
                        cells += `<td>${resource.cpu || 'N/A'}</td>`;
                        break;
                    case 'Memory':
                        cells += `<td>${this._formatMemory(resource.memory_mb)}</td>`;
                        break;
                    case 'Disk':
                        cells += `<td>${this._formatSize(resource.disk_size_bytes)}</td>`;
                        break;
                    case 'Type':
                        cells += `<td>${resource.type || 'N/A'}</td>`;
                        break;
                    case 'Size':
                        cells += `<td>${this._formatSize(resource.size_bytes)}</td>`;
                        break;
                    default:
                        cells += `<td>N/A</td>`;
                }
            }
        });
        
        return `<tr>${cells}</tr>`;
    },

    /**
     * Get resource link
     * @param {Object} resource - Resource
     * @param {string} type - Resource type
     * @returns {string} Resource link
     * @private
     */
    _getResourceLink: function(resource, type) {
        switch (type) {
            case 'vm':
                return `/vm/${resource.target_id}`;
            case 'container':
                return `/container/${resource.target_id}`;
            case 'storage':
                return `/storage/${resource.target_id}`;
            case 'network':
                return `/network/${resource.target_id}`;
            default:
                return '#';
        }
    },

    /**
     * Format memory size
     * @param {number} size - Memory size in MB
     * @returns {string} Formatted size
     * @private
     */
    _formatMemory: function(size) {
        if (!size) return 'N/A';
        
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
        if (!size) return 'N/A';
        
        const units = ['B', 'KB', 'MB', 'GB', 'TB'];
        let unitIndex = 0;
        let scaledSize = size;

        while (scaledSize >= 1024 && unitIndex < units.length - 1) {
            unitIndex++;
            scaledSize /= 1024;
        }

        return `${scaledSize.toFixed(1)} ${units[unitIndex]}`;
    }
};

export default SummaryStep;
