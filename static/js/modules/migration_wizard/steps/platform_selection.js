/**
 * Platform Selection Step
 * First step in the migration wizard for selecting the source platform
 */

import { apiRequest } from '../../api.js';
import { showToast } from '../../notifications.js';

export const PlatformSelectionStep = {
    /**
     * Render the platform selection step
     * @param {Object} data - Wizard data
     * @returns {string} HTML content
     */
    render: function(data) {
        return `
            <div class="platform-selection-step">
                <h4 class="mb-4">Select Source Platform</h4>
                <p class="mb-4">
                    Select the platform you want to migrate from. The migration wizard will guide you through
                    the process of migrating your virtual machines, containers, and storage to Proxmox.
                </p>
                
                <div class="row platform-cards" id="platform-cards-container">
                    <div class="col-12 text-center">
                        <div class="spinner-border" role="status">
                            <span class="visually-hidden">Loading...</span>
                        </div>
                        <p>Loading available platforms...</p>
                    </div>
                </div>
                
                ${data.existingMigrations && data.existingMigrations.length > 0 ? `
                    <div class="mt-5">
                        <h5>Existing Migrations</h5>
                        <div class="table-responsive">
                            <table class="table table-hover">
                                <thead>
                                    <tr>
                                        <th>ID</th>
                                        <th>Platform</th>
                                        <th>Status</th>
                                        <th>Date</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${data.existingMigrations.map(migration => `
                                        <tr>
                                            <td><code>${migration.migration_id.substring(0, 8)}</code></td>
                                            <td>${migration.platform}</td>
                                            <td>
                                                <span class="badge ${this._getStatusBadgeClass(migration.status)}">
                                                    ${migration.status}
                                                </span>
                                            </td>
                                            <td>${new Date(migration.timestamp).toLocaleString()}</td>
                                            <td>
                                                <button class="btn btn-sm btn-outline-primary continue-migration-btn"
                                                    data-migration-id="${migration.migration_id}">
                                                    Continue
                                                </button>
                                                <button class="btn btn-sm btn-outline-info view-report-btn"
                                                    data-migration-id="${migration.migration_id}">
                                                    Report
                                                </button>
                                            </td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        </div>
                    </div>
                ` : ''}
            </div>
        `;
    },

    /**
     * Initialize the platform selection step
     * @param {HTMLElement} container - Step container
     * @param {Object} data - Wizard data
     */
    init: function(container, data) {
        // Load available platforms
        this._loadPlatforms(container);

        // Set up event listeners for existing migrations
        const continueBtns = container.querySelectorAll('.continue-migration-btn');
        const reportBtns = container.querySelectorAll('.view-report-btn');

        continueBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const migrationId = e.target.dataset.migrationId;
                this._continueMigration(migrationId, data);
            });
        });

        reportBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const migrationId = e.target.dataset.migrationId;
                this._viewMigrationReport(migrationId);
            });
        });
    },

    /**
     * Validate the platform selection step
     * @param {Object} data - Wizard data
     * @returns {boolean} True if valid, false otherwise
     */
    validate: function(data) {
        if (!data.selectedPlatform) {
            showToast('Please select a platform to continue', 'warning');
            return false;
        }
        return true;
    },

    /**
     * Process the platform selection step
     * @param {Object} data - Wizard data
     */
    process: function(data) {
        // Nothing to process here, just pass the selected platform to the next step
    },

    /**
     * Load available platforms
     * @param {HTMLElement} container - Step container
     * @private
     */
    _loadPlatforms: async function(container) {
        try {
            const response = await apiRequest('GET', '/api/migration/platforms');
            
            if (response && response.success && response.platforms) {
                this._renderPlatformCards(container, response.platforms);
            } else {
                throw new Error(response.message || 'Failed to load platforms');
            }
        } catch (error) {
            console.error('Error loading platforms:', error);
            
            const platformCardsContainer = container.querySelector('#platform-cards-container');
            if (platformCardsContainer) {
                platformCardsContainer.innerHTML = `
                    <div class="col-12 text-center">
                        <div class="alert alert-danger">
                            <i class="fas fa-exclamation-triangle"></i>
                            Error loading platforms: ${error.message}
                        </div>
                        <button class="btn btn-primary retry-load-btn">
                            <i class="fas fa-sync"></i> Retry
                        </button>
                    </div>
                `;
                
                const retryBtn = platformCardsContainer.querySelector('.retry-load-btn');
                if (retryBtn) {
                    retryBtn.addEventListener('click', () => {
                        this._loadPlatforms(container);
                    });
                }
            }
        }
    },

    /**
     * Render platform cards
     * @param {HTMLElement} container - Step container
     * @param {Array} platforms - Available platforms
     * @private
     */
    _renderPlatformCards: function(container, platforms) {
        const platformCardsContainer = container.querySelector('#platform-cards-container');
        if (!platformCardsContainer) return;

        let html = '';

        platforms.forEach(platform => {
            html += `
                <div class="col-md-4 mb-4">
                    <div class="card platform-card ${platform.available ? '' : 'disabled'}" 
                        data-platform-id="${platform.id}">
                        <div class="card-body">
                            <h5 class="card-title">
                                <i class="fas ${platform.icon || 'fa-server'}"></i>
                                ${platform.name}
                            </h5>
                            <p class="card-text">${platform.description}</p>
                            ${!platform.available ? `
                                <div class="alert alert-warning">
                                    <small>${platform.message || 'Not available'}</small>
                                </div>
                            ` : ''}
                        </div>
                        <div class="card-footer">
                            <button class="btn btn-primary select-platform-btn" 
                                ${!platform.available ? 'disabled' : ''}
                                data-platform-id="${platform.id}">
                                Select
                            </button>
                        </div>
                    </div>
                </div>
            `;
        });

        platformCardsContainer.innerHTML = html;

        // Set up event listeners
        const platformCards = platformCardsContainer.querySelectorAll('.platform-card');
        const selectBtns = platformCardsContainer.querySelectorAll('.select-platform-btn');

        platformCards.forEach(card => {
            if (!card.classList.contains('disabled')) {
                card.addEventListener('click', () => {
                    const platformId = card.dataset.platformId;
                    this._selectPlatform(platformId, platformCardsContainer);
                });
            }
        });

        selectBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const platformId = btn.dataset.platformId;
                this._selectPlatform(platformId, platformCardsContainer);
            });
        });
    },

    /**
     * Select a platform
     * @param {string} platformId - Platform ID
     * @param {HTMLElement} container - Container element
     * @private
     */
    _selectPlatform: function(platformId, container) {
        // Remove selected class from all cards
        const platformCards = container.querySelectorAll('.platform-card');
        platformCards.forEach(card => {
            card.classList.remove('selected');
        });

        // Add selected class to the selected card
        const selectedCard = container.querySelector(`.platform-card[data-platform-id="${platformId}"]`);
        if (selectedCard) {
            selectedCard.classList.add('selected');
        }

        // Get platform details
        const platform = this._getPlatformDetails(platformId);

        // Update wizard data
        const wizard = window.migrationWizard.wizard;
        wizard.setData({ 
            selectedPlatform: platformId,
            platformDetails: platform
        });

        showToast(`Selected platform: ${platform.name}`, 'success');
    },

    /**
     * Get platform details
     * @param {string} platformId - Platform ID
     * @returns {Object} Platform details
     * @private
     */
    _getPlatformDetails: function(platformId) {
        // This would normally come from the API, but we'll use a simple lookup for now
        const platforms = {
            'unraid': {
                name: 'Unraid',
                icon: 'fa-server',
                description: 'Migrate from Unraid Server',
                credentialFields: [
                    { name: 'host', label: 'Hostname/IP', type: 'text', required: true },
                    { name: 'port', label: 'SSH Port', type: 'number', default: 22, required: true },
                    { name: 'username', label: 'Username', type: 'text', default: 'root', required: true },
                    { name: 'password', label: 'Password', type: 'password', required: false },
                    { name: 'key_file', label: 'SSH Key File', type: 'file', required: false }
                ]
            },
            'truenas': {
                name: 'TrueNAS',
                icon: 'fa-database',
                description: 'Migrate from TrueNAS Core/Scale',
                credentialFields: [
                    { name: 'host', label: 'Hostname/IP', type: 'text', required: true },
                    { name: 'api_key', label: 'API Key', type: 'password', required: true },
                    { name: 'use_https', label: 'Use HTTPS', type: 'checkbox', default: true, required: false }
                ]
            },
            'esxi': {
                name: 'ESXi/vSphere',
                icon: 'fa-cloud',
                description: 'Migrate from VMware ESXi/vSphere',
                credentialFields: [
                    { name: 'host', label: 'Hostname/IP', type: 'text', required: true },
                    { name: 'username', label: 'Username', type: 'text', required: true },
                    { name: 'password', label: 'Password', type: 'password', required: true },
                    { name: 'use_https', label: 'Use HTTPS', type: 'checkbox', default: true, required: false },
                    { name: 'port', label: 'Port', type: 'number', default: 443, required: true },
                    { name: 'verify_ssl', label: 'Verify SSL', type: 'checkbox', default: false, required: false }
                ]
            }
        };

        return platforms[platformId] || { name: 'Unknown Platform', credentialFields: [] };
    },

    /**
     * Continue an existing migration
     * @param {string} migrationId - Migration ID
     * @param {Object} data - Wizard data
     * @private
     */
    _continueMigration: async function(migrationId, data) {
        try {
            const response = await apiRequest('GET', `/api/migration/status/${migrationId}`);
            
            if (response && response.success) {
                // Set active migration ID
                window.migrationWizard.setActiveMigrationId(migrationId);
                
                // Update wizard data
                const wizard = window.migrationWizard.wizard;
                wizard.setData({ 
                    selectedPlatform: response.platform,
                    platformDetails: this._getPlatformDetails(response.platform),
                    migrationStatus: response
                });
                
                // Determine which step to go to based on migration status
                let targetStep = 0;
                switch (response.status) {
                    case 'analyzed':
                        targetStep = 3; // Resource selection step
                        break;
                    case 'planned':
                        targetStep = 5; // Migration plan step
                        break;
                    case 'executing':
                        targetStep = 6; // Execution step
                        break;
                    case 'completed':
                    case 'failed':
                    case 'cancelled':
                        targetStep = 7; // Summary step
                        break;
                    default:
                        targetStep = 1; // Credentials step
                        break;
                }
                
                // Go to the appropriate step
                wizard.goToStep(targetStep);
                
                showToast(`Continuing migration ${migrationId.substring(0, 8)}`, 'success');
            } else {
                throw new Error(response.message || 'Failed to get migration status');
            }
        } catch (error) {
            console.error('Error continuing migration:', error);
            showToast(`Error continuing migration: ${error.message}`, 'error');
        }
    },

    /**
     * View migration report
     * @param {string} migrationId - Migration ID
     * @private
     */
    _viewMigrationReport: async function(migrationId) {
        try {
            const response = await apiRequest('GET', `/api/migration/report/${migrationId}`);
            
            if (response && response.success) {
                // Show report in a modal
                const modalHtml = `
                    <div class="modal fade" id="migration-report-modal" tabindex="-1" aria-hidden="true">
                        <div class="modal-dialog modal-lg">
                            <div class="modal-content">
                                <div class="modal-header">
                                    <h5 class="modal-title">Migration Report</h5>
                                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                                </div>
                                <div class="modal-body">
                                    <div class="report-header mb-3">
                                        <div class="row">
                                            <div class="col-md-6">
                                                <p><strong>Migration ID:</strong> ${migrationId}</p>
                                                <p><strong>Platform:</strong> ${response.source_platform}</p>
                                                <p><strong>Status:</strong> 
                                                    <span class="badge ${this._getStatusBadgeClass(response.status)}">
                                                        ${response.status}
                                                    </span>
                                                </p>
                                            </div>
                                            <div class="col-md-6">
                                                <p><strong>Start Time:</strong> ${response.start_time ? new Date(response.start_time).toLocaleString() : 'N/A'}</p>
                                                <p><strong>End Time:</strong> ${response.end_time ? new Date(response.end_time).toLocaleString() : 'N/A'}</p>
                                                <p><strong>Duration:</strong> ${response.duration_seconds ? this._formatDuration(response.duration_seconds) : 'N/A'}</p>
                                            </div>
                                        </div>
                                        <div class="progress mb-3">
                                            <div class="progress-bar bg-success" role="progressbar" 
                                                style="width: ${response.success_rate}%;" 
                                                aria-valuenow="${response.success_rate}" aria-valuemin="0" aria-valuemax="100">
                                                ${response.success_rate.toFixed(1)}%
                                            </div>
                                        </div>
                                    </div>
                                    
                                    <h6>Resources Migrated</h6>
                                    <div class="table-responsive mb-3">
                                        <table class="table table-sm">
                                            <thead>
                                                <tr>
                                                    <th>Type</th>
                                                    <th>Name</th>
                                                    <th>Status</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                ${this._renderMigratedResources(response.resources_migrated)}
                                            </tbody>
                                        </table>
                                    </div>
                                    
                                    ${response.errors && response.errors.length > 0 ? `
                                        <h6>Errors</h6>
                                        <div class="alert alert-danger">
                                            <ul class="mb-0">
                                                ${response.errors.map(error => `<li>${error}</li>`).join('')}
                                            </ul>
                                        </div>
                                    ` : ''}
                                    
                                    ${response.warnings && response.warnings.length > 0 ? `
                                        <h6>Warnings</h6>
                                        <div class="alert alert-warning">
                                            <ul class="mb-0">
                                                ${response.warnings.map(warning => `<li>${warning}</li>`).join('')}
                                            </ul>
                                        </div>
                                    ` : ''}
                                </div>
                                <div class="modal-footer">
                                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                                    ${response.status !== 'completed' ? `
                                        <button type="button" class="btn btn-primary continue-migration-modal-btn"
                                            data-migration-id="${migrationId}">
                                            Continue Migration
                                        </button>
                                    ` : ''}
                                </div>
                            </div>
                        </div>
                    </div>
                `;
                
                // Add modal to the page
                const modalContainer = document.createElement('div');
                modalContainer.innerHTML = modalHtml;
                document.body.appendChild(modalContainer);
                
                // Initialize modal
                const modal = new bootstrap.Modal(document.getElementById('migration-report-modal'));
                modal.show();
                
                // Set up continue button
                const continueBtn = document.querySelector('.continue-migration-modal-btn');
                if (continueBtn) {
                    continueBtn.addEventListener('click', () => {
                        modal.hide();
                        this._continueMigration(migrationId, {});
                    });
                }
                
                // Remove modal from DOM when hidden
                document.getElementById('migration-report-modal').addEventListener('hidden.bs.modal', function () {
                    document.body.removeChild(modalContainer);
                });
            } else {
                throw new Error(response.message || 'Failed to get migration report');
            }
        } catch (error) {
            console.error('Error viewing migration report:', error);
            showToast(`Error viewing migration report: ${error.message}`, 'error');
        }
    },

    /**
     * Render migrated resources
     * @param {Object} resources - Migrated resources
     * @returns {string} HTML content
     * @private
     */
    _renderMigratedResources: function(resources) {
        let html = '';
        
        if (resources.vms && resources.vms.length > 0) {
            resources.vms.forEach(vm => {
                html += `
                    <tr>
                        <td>VM</td>
                        <td>${vm.name}</td>
                        <td>
                            <span class="badge ${vm.success ? 'bg-success' : 'bg-danger'}">
                                ${vm.success ? 'Success' : 'Failed'}
                            </span>
                        </td>
                    </tr>
                `;
            });
        }
        
        if (resources.containers && resources.containers.length > 0) {
            resources.containers.forEach(container => {
                html += `
                    <tr>
                        <td>Container</td>
                        <td>${container.name}</td>
                        <td>
                            <span class="badge ${container.success ? 'bg-success' : 'bg-danger'}">
                                ${container.success ? 'Success' : 'Failed'}
                            </span>
                        </td>
                    </tr>
                `;
            });
        }
        
        if (resources.storage && resources.storage.length > 0) {
            resources.storage.forEach(storage => {
                html += `
                    <tr>
                        <td>Storage</td>
                        <td>${storage.name}</td>
                        <td>
                            <span class="badge ${storage.success ? 'bg-success' : 'bg-danger'}">
                                ${storage.success ? 'Success' : 'Failed'}
                            </span>
                        </td>
                    </tr>
                `;
            });
        }
        
        if (html === '') {
            html = `
                <tr>
                    <td colspan="3" class="text-center">No resources migrated</td>
                </tr>
            `;
        }
        
        return html;
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
    },

    /**
     * Get status badge class
     * @param {string} status - Migration status
     * @returns {string} Badge class
     * @private
     */
    _getStatusBadgeClass: function(status) {
        switch (status) {
            case 'completed':
                return 'bg-success';
            case 'failed':
                return 'bg-danger';
            case 'cancelled':
                return 'bg-secondary';
            case 'executing':
                return 'bg-primary';
            case 'planned':
                return 'bg-info';
            case 'analyzed':
                return 'bg-warning';
            default:
                return 'bg-secondary';
        }
    }
};

export default PlatformSelectionStep;
