/**
 * Dashboards module - Handles dashboard management and customization
 */
import API from './api.js';

export default class Dashboards {
    constructor() {
        this.dashboards = [];
        this.currentDashboard = null;
        this.currentPanel = null;
        this.panelTypes = {
            'vm_status': {
                name: 'VM Status',
                description: 'Shows status of virtual machines',
                icon: 'bi-hdd',
                configOptions: {
                    showResourceUsage: { type: 'checkbox', label: 'Show Resource Usage', default: true },
                    limit: { type: 'number', label: 'Number of VMs to Show', default: 5, min: 1, max: 20 }
                }
            },
            'system_metrics': {
                name: 'System Metrics',
                description: 'Shows system resource usage metrics',
                icon: 'bi-graph-up',
                configOptions: {
                    metrics: { 
                        type: 'multiselect', 
                        label: 'Metrics to Display',
                        options: ['cpu', 'memory', 'storage', 'network'],
                        default: ['cpu', 'memory', 'storage']
                    }
                }
            },
            'storage_usage': {
                name: 'Storage Usage',
                description: 'Shows storage usage across nodes',
                icon: 'bi-device-hdd',
                configOptions: {
                    showChart: { type: 'checkbox', label: 'Show Chart', default: true },
                    showTable: { type: 'checkbox', label: 'Show Table', default: false }
                }
            },
            'network_traffic': {
                name: 'Network Traffic',
                description: 'Displays network traffic statistics',
                icon: 'bi-diagram-3',
                configOptions: {
                    trafficType: { 
                        type: 'select', 
                        label: 'Traffic Type', 
                        options: [
                            { value: 'all', label: 'All Traffic' },
                            { value: 'internal', label: 'Internal Traffic' },
                            { value: 'external', label: 'External Traffic' }
                        ],
                        default: 'all'
                    },
                    timeframe: {
                        type: 'select',
                        label: 'Timeframe',
                        options: [
                            { value: 'hour', label: 'Last Hour' },
                            { value: 'day', label: 'Last Day' },
                            { value: 'week', label: 'Last Week' },
                            { value: 'month', label: 'Last Month' }
                        ],
                        default: 'day'
                    }
                }
            },
            'recent_commands': {
                name: 'Recent Commands',
                description: 'Shows recently executed commands',
                icon: 'bi-terminal',
                configOptions: {
                    limit: { type: 'number', label: 'Number of Commands', default: 5, min: 1, max: 20 },
                    showTimestamp: { type: 'checkbox', label: 'Show Timestamp', default: true },
                    showStatus: { type: 'checkbox', label: 'Show Status', default: true }
                }
            },
            'favorite_commands': {
                name: 'Favorite Commands',
                description: 'Displays favorite commands for quick access',
                icon: 'bi-star',
                configOptions: {
                    showDescription: { type: 'checkbox', label: 'Show Command Description', default: true }
                }
            },
            'recent_events': {
                name: 'Recent Events',
                description: 'Shows recent system events and alerts',
                icon: 'bi-bell',
                configOptions: {
                    eventTypes: {
                        type: 'multiselect',
                        label: 'Event Types',
                        options: ['vm', 'system', 'security', 'backup', 'service'],
                        default: ['vm', 'system', 'security']
                    },
                    limit: { type: 'number', label: 'Number of Events', default: 5, min: 1, max: 20 }
                }
            },
            'backup_status': {
                name: 'Backup Status',
                description: 'Shows status of recent backups',
                icon: 'bi-cloud-arrow-up',
                configOptions: {
                    showChart: { type: 'checkbox', label: 'Show Success Rate Chart', default: true },
                    limit: { type: 'number', label: 'Number of Backups', default: 5, min: 1, max: 20 }
                }
            },
            'performance_chart': {
                name: 'Performance Chart',
                description: 'Displays performance metrics over time',
                icon: 'bi-bar-chart-line',
                configOptions: {
                    metric: {
                        type: 'select',
                        label: 'Metric',
                        options: [
                            { value: 'cpu', label: 'CPU Usage' },
                            { value: 'memory', label: 'Memory Usage' },
                            { value: 'disk_io', label: 'Disk I/O' },
                            { value: 'network_io', label: 'Network I/O' }
                        ],
                        default: 'cpu'
                    },
                    chartType: {
                        type: 'select',
                        label: 'Chart Type',
                        options: [
                            { value: 'line', label: 'Line Chart' },
                            { value: 'bar', label: 'Bar Chart' },
                            { value: 'area', label: 'Area Chart' }
                        ],
                        default: 'line'
                    },
                    timeframe: {
                        type: 'select',
                        label: 'Timeframe',
                        options: [
                            { value: 'hour', label: 'Last Hour' },
                            { value: 'day', label: 'Last Day' },
                            { value: 'week', label: 'Last Week' },
                            { value: 'month', label: 'Last Month' }
                        ],
                        default: 'day'
                    }
                }
            },
            'resource_usage_table': {
                name: 'Resource Usage Table',
                description: 'Shows detailed resource usage in a table',
                icon: 'bi-table',
                configOptions: {
                    resourceType: {
                        type: 'select',
                        label: 'Resource Type',
                        options: [
                            { value: 'vm', label: 'Virtual Machines' },
                            { value: 'node', label: 'Nodes' },
                            { value: 'service', label: 'Services' }
                        ],
                        default: 'vm'
                    },
                    metrics: {
                        type: 'multiselect',
                        label: 'Metrics',
                        options: ['cpu', 'memory', 'disk', 'network'],
                        default: ['cpu', 'memory', 'disk']
                    },
                    limit: { type: 'number', label: 'Number of Items', default: 10, min: 1, max: 50 }
                }
            }
        };
        this.selectedPanelType = null;
    }

    /**
     * Initialize the dashboards module
     */
    async initialize() {
        this.setupEventListeners();
    }

    /**
     * Load dashboards for a user
     * @param {string} userId - User ID
     */
    async loadDashboards(userId) {
        try {
            const response = await API.fetchWithAuth(`/dashboards/${userId}`);
            const data = await response.json();
            
            if (data.success) {
                this.dashboards = data.dashboards || [];
                return this.dashboards;
            } else {
                console.error('Error loading dashboards:', data.message);
                return [];
            }
        } catch (error) {
            console.error('Error loading dashboards:', error);
            return [];
        }
    }

    /**
     * Render dashboard list in UI
     * @param {HTMLElement} container - Container element
     */
    renderDashboardList(container) {
        if (!container) return;
        
        // Clear container
        container.innerHTML = '';
        
        // Show message if no dashboards
        if (!this.dashboards || this.dashboards.length === 0) {
            document.getElementById('noDashboardsMessage').classList.remove('d-none');
            return;
        }
        
        // Hide no dashboards message
        document.getElementById('noDashboardsMessage').classList.add('d-none');
        
        // Create a row for the dashboard cards
        const row = document.createElement('div');
        row.className = 'row';
        
        // Add dashboard cards
        this.dashboards.forEach(dashboard => {
            const col = document.createElement('div');
            col.className = 'col-md-6 mb-3';
            
            const card = document.createElement('div');
            card.className = 'card h-100' + (dashboard.is_default ? ' border-primary' : '');
            
            card.innerHTML = `
                <div class="card-body">
                    <h6 class="card-title">
                        ${dashboard.name}
                        ${dashboard.is_default ? '<span class="badge bg-primary ms-2">Default</span>' : ''}
                    </h6>
                    <p class="card-text text-muted small">
                        ${dashboard.panels?.length || 0} panels
                        <br>Last updated: ${new Date(dashboard.updated_at).toLocaleString()}
                    </p>
                </div>
                <div class="card-footer d-flex justify-content-between">
                    <button class="btn btn-sm btn-outline-primary view-dashboard-btn" data-dashboard-id="${dashboard.id}">
                        <i class="bi bi-eye"></i> View
                    </button>
                    <button class="btn btn-sm btn-outline-secondary edit-dashboard-btn" data-dashboard-id="${dashboard.id}">
                        <i class="bi bi-pencil"></i> Edit
                    </button>
                </div>
            `;
            
            col.appendChild(card);
            row.appendChild(col);
        });
        
        container.appendChild(row);
        
        // Also populate the default dashboard dropdown
        this.populateDefaultDashboardDropdown();
    }

    /**
     * Populate the default dashboard dropdown
     */
    populateDefaultDashboardDropdown() {
        const select = document.getElementById('default-dashboard-select');
        if (!select) return;
        
        // Clear current options except the first one
        while (select.options.length > 1) {
            select.remove(1);
        }
        
        // Add dashboard options
        this.dashboards.forEach(dashboard => {
            const option = document.createElement('option');
            option.value = dashboard.id;
            option.textContent = dashboard.name;
            option.selected = dashboard.is_default;
            select.appendChild(option);
        });
    }

    /**
     * Create a new dashboard
     * @param {string} userId - User ID
     * @param {string} name - Dashboard name
     * @param {boolean} isDefault - Whether this is the default dashboard
     * @param {string} layout - Dashboard layout type
     */
    async createDashboard(userId, name, isDefault = false, layout = 'grid') {
        try {
            const response = await API.fetchWithAuth(`/dashboards/${userId}`, {
                method: 'POST',
                body: JSON.stringify({
                    name,
                    is_default: isDefault,
                    layout
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Reload dashboards to get the new one
                await this.loadDashboards(userId);
                return data.dashboard_id;
            } else {
                console.error('Error creating dashboard:', data.message);
                return null;
            }
        } catch (error) {
            console.error('Error creating dashboard:', error);
            return null;
        }
    }

    /**
     * Get a specific dashboard by ID
     * @param {number} dashboardId - Dashboard ID
     */
    async getDashboard(dashboardId) {
        try {
            const response = await API.fetchWithAuth(`/dashboards/${dashboardId}`);
            const data = await response.json();
            
            if (data.success) {
                this.currentDashboard = data.dashboard;
                return this.currentDashboard;
            } else {
                console.error('Error getting dashboard:', data.message);
                return null;
            }
        } catch (error) {
            console.error('Error getting dashboard:', error);
            return null;
        }
    }

    /**
     * Update a dashboard
     * @param {number} dashboardId - Dashboard ID
     * @param {string} name - Dashboard name
     * @param {boolean} isDefault - Whether this is the default dashboard
     * @param {string} layout - Dashboard layout type
     */
    async updateDashboard(dashboardId, name, isDefault, layout) {
        try {
            const response = await API.fetchWithAuth(`/dashboards/${dashboardId}`, {
                method: 'PUT',
                body: JSON.stringify({
                    name,
                    is_default: isDefault,
                    layout
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Re-fetch the dashboard to get updated info
                await this.getDashboard(dashboardId);
                return true;
            } else {
                console.error('Error updating dashboard:', data.message);
                return false;
            }
        } catch (error) {
            console.error('Error updating dashboard:', error);
            return false;
        }
    }

    /**
     * Delete a dashboard
     * @param {number} dashboardId - Dashboard ID
     */
    async deleteDashboard(dashboardId) {
        try {
            const response = await API.fetchWithAuth(`/dashboards/${dashboardId}`, {
                method: 'DELETE'
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Remove from local array
                this.dashboards = this.dashboards.filter(d => d.id !== dashboardId);
                return true;
            } else {
                console.error('Error deleting dashboard:', data.message);
                return false;
            }
        } catch (error) {
            console.error('Error deleting dashboard:', error);
            return false;
        }
    }

    /**
     * Add a panel to a dashboard
     * @param {number} dashboardId - Dashboard ID
     * @param {string} panelType - Panel type
     * @param {string} title - Panel title
     * @param {object} config - Panel configuration
     * @param {number} positionX - X position
     * @param {number} positionY - Y position
     * @param {number} width - Panel width
     * @param {number} height - Panel height
     */
    async addPanel(dashboardId, panelType, title, config = {}, positionX = 0, positionY = 0, width = 6, height = 4) {
        try {
            const response = await API.fetchWithAuth(`/dashboards/${dashboardId}/panels`, {
                method: 'POST',
                body: JSON.stringify({
                    panel_type: panelType,
                    title,
                    config,
                    position_x: positionX,
                    position_y: positionY,
                    width,
                    height
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Re-fetch the dashboard to get the new panel
                await this.getDashboard(dashboardId);
                return data.panel_id;
            } else {
                console.error('Error adding panel:', data.message);
                return null;
            }
        } catch (error) {
            console.error('Error adding panel:', error);
            return null;
        }
    }

    /**
     * Update a panel
     * @param {number} panelId - Panel ID
     * @param {string} title - Panel title
     * @param {object} config - Panel configuration
     * @param {number} positionX - X position
     * @param {number} positionY - Y position
     * @param {number} width - Panel width
     * @param {number} height - Panel height
     */
    async updatePanel(panelId, title, config = null, positionX = null, positionY = null, width = null, height = null) {
        try {
            const response = await API.fetchWithAuth(`/dashboards/panels/${panelId}`, {
                method: 'PUT',
                body: JSON.stringify({
                    title,
                    config,
                    position_x: positionX,
                    position_y: positionY,
                    width,
                    height
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Re-fetch the current dashboard to update panels
                if (this.currentDashboard) {
                    await this.getDashboard(this.currentDashboard.id);
                }
                return true;
            } else {
                console.error('Error updating panel:', data.message);
                return false;
            }
        } catch (error) {
            console.error('Error updating panel:', error);
            return false;
        }
    }

    /**
     * Delete a panel
     * @param {number} panelId - Panel ID
     */
    async deletePanel(panelId) {
        try {
            const response = await API.fetchWithAuth(`/dashboards/panels/${panelId}`, {
                method: 'DELETE'
            });
            
            const data = await response.json();
            
            if (data.success) {
                if (this.currentDashboard) {
                    // Remove from current dashboard panels
                    this.currentDashboard.panels = this.currentDashboard.panels.filter(p => p.id !== panelId);
                }
                return true;
            } else {
                console.error('Error deleting panel:', data.message);
                return false;
            }
        } catch (error) {
            console.error('Error deleting panel:', error);
            return false;
        }
    }

    /**
     * Render panels in the dashboard editor
     */
    renderPanelsList() {
        const container = document.getElementById('dashboard-panels');
        const noMessage = document.getElementById('no-panels-message');
        
        if (!container) return;
        
        // Clear container except the no-panels message
        Array.from(container.children).forEach(child => {
            if (child.id !== 'no-panels-message') {
                container.removeChild(child);
            }
        });
        
        if (!this.currentDashboard || !this.currentDashboard.panels || this.currentDashboard.panels.length === 0) {
            noMessage.classList.remove('d-none');
            return;
        }
        
        // Hide no panels message
        noMessage.classList.add('d-none');
        
        // Add panels
        this.currentDashboard.panels.forEach(panel => {
            const panelEl = this.createPanelElement(panel);
            container.appendChild(panelEl);
        });
    }

    /**
     * Create a panel element for the dashboard editor
     * @param {object} panel - Panel data
     * @returns {HTMLElement} - Panel element
     */
    createPanelElement(panel) {
        const template = document.getElementById('panel-template');
        const panelEl = template.cloneNode(true).children[0];
        panelEl.classList.remove('d-none');
        panelEl.dataset.panelId = panel.id;
        
        // Set panel title
        panelEl.querySelector('.panel-title').textContent = panel.title;
        
        // Set panel type
        const panelTypeInfo = this.panelTypes[panel.panel_type] || { 
            name: panel.panel_type, 
            description: 'Custom panel type' 
        };
        
        panelEl.querySelector('.panel-type-label .badge').textContent = panelTypeInfo.name;
        
        // Set panel description (size and additional info)
        let description = `${panel.width}x${panel.height}`;
        if (panel.panel_type === 'vm_status' && panel.config?.limit) {
            description += ` • Shows ${panel.config.limit} VMs`;
        }
        panelEl.querySelector('.panel-description').textContent = description;
        
        // Set up edit button
        panelEl.querySelector('.panel-edit-btn').addEventListener('click', () => {
            this.editPanel(panel);
        });
        
        // Set up delete button
        panelEl.querySelector('.panel-delete-btn').addEventListener('click', () => {
            if (confirm(`Are you sure you want to delete the panel "${panel.title}"?`)) {
                this.deletePanel(panel.id).then(success => {
                    if (success) {
                        this.renderPanelsList();
                    }
                });
            }
        });
        
        return panelEl;
    }

    /**
     * Open the panel editor for a panel
     * @param {object} panel - Panel data
     */
    editPanel(panel) {
        this.currentPanel = panel;
        
        const titleInput = document.getElementById('panel-title');
        const typeSelect = document.getElementById('panel-type');
        const widthInput = document.getElementById('panel-width');
        const heightInput = document.getElementById('panel-height');
        const xInput = document.getElementById('panel-x');
        const yInput = document.getElementById('panel-y');
        const configContainer = document.getElementById('panel-config-container');
        
        // Set panel values
        titleInput.value = panel.title;
        typeSelect.value = panel.panel_type;
        widthInput.value = panel.width;
        heightInput.value = panel.height;
        xInput.value = panel.position_x;
        yInput.value = panel.position_y;
        
        // Show position or size options based on dashboard layout
        if (this.currentDashboard.layout === 'free') {
            document.getElementById('panel-size-options').classList.add('d-none');
            document.getElementById('panel-position-options').classList.remove('d-none');
        } else {
            document.getElementById('panel-size-options').classList.remove('d-none');
            document.getElementById('panel-position-options').classList.add('d-none');
        }
        
        // Generate config options
        this.generatePanelConfigOptions(panel.panel_type, panel.config || {});
        
        // Show the modal
        const modal = new bootstrap.Modal(document.getElementById('panelEditorModal'));
        modal.show();
    }

    /**
     * Generate panel configuration options based on panel type
     * @param {string} panelType - Panel type
     * @param {object} currentConfig - Current panel configuration
     */
    generatePanelConfigOptions(panelType, currentConfig = {}) {
        const container = document.getElementById('panel-config-container');
        container.innerHTML = '';
        
        const panelTypeInfo = this.panelTypes[panelType];
        if (!panelTypeInfo || !panelTypeInfo.configOptions) {
            container.innerHTML = '<p>No configuration options for this panel type</p>';
            return;
        }
        
        // Add each config option
        Object.entries(panelTypeInfo.configOptions).forEach(([key, option]) => {
            const value = currentConfig[key] !== undefined ? currentConfig[key] : option.default;
            let configElement;
            
            switch (option.type) {
                case 'checkbox':
                    configElement = this.createCheckboxOption(key, option.label, value);
                    break;
                case 'number':
                    configElement = this.createNumberOption(key, option.label, value, option.min, option.max);
                    break;
                case 'select':
                    configElement = this.createSelectOption(key, option.label, option.options, value);
                    break;
                case 'multiselect':
                    configElement = this.createMultiselectOption(key, option.label, option.options, value);
                    break;
                default:
                    configElement = document.createElement('div');
                    configElement.innerHTML = `<p>Unknown option type: ${option.type}</p>`;
            }
            
            container.appendChild(configElement);
        });
    }

    /**
     * Create a checkbox config option
     * @param {string} key - Option key
     * @param {string} label - Option label
     * @param {boolean} checked - Whether checkbox is checked
     * @returns {HTMLElement} - Checkbox element
     */
    createCheckboxOption(key, label, checked) {
        const div = document.createElement('div');
        div.className = 'form-check mb-2';
        div.innerHTML = `
            <input class="form-check-input panel-config-input" type="checkbox" id="config-${key}" 
                   data-key="${key}" ${checked ? 'checked' : ''}>
            <label class="form-check-label" for="config-${key}">${label}</label>
        `;
        return div;
    }

    /**
     * Create a number config option
     * @param {string} key - Option key
     * @param {string} label - Option label
     * @param {number} value - Current value
     * @param {number} min - Minimum value
     * @param {number} max - Maximum value
     * @returns {HTMLElement} - Number input element
     */
    createNumberOption(key, label, value, min, max) {
        const div = document.createElement('div');
        div.className = 'mb-2';
        div.innerHTML = `
            <label for="config-${key}" class="form-label">${label}</label>
            <input type="number" class="form-control panel-config-input" 
                   id="config-${key}" data-key="${key}" value="${value}"
                   min="${min || 1}" max="${max || 100}">
        `;
        return div;
    }

    /**
     * Create a select config option
     * @param {string} key - Option key
     * @param {string} label - Option label
     * @param {Array} options - Select options
     * @param {string} value - Current value
     * @returns {HTMLElement} - Select element
     */
    createSelectOption(key, label, options, value) {
        const div = document.createElement('div');
        div.className = 'mb-2';
        
        const selectId = `config-${key}`;
        div.innerHTML = `<label for="${selectId}" class="form-label">${label}</label>`;
        
        const select = document.createElement('select');
        select.id = selectId;
        select.className = 'form-select panel-config-input';
        select.dataset.key = key;
        
        options.forEach(opt => {
            const option = document.createElement('option');
            
            // Handle options as objects or strings
            if (typeof opt === 'object') {
                option.value = opt.value;
                option.textContent = opt.label;
                option.selected = opt.value === value;
            } else {
                option.value = opt;
                option.textContent = opt;
                option.selected = opt === value;
            }
            
            select.appendChild(option);
        });
        
        div.appendChild(select);
        return div;
    }

    /**
     * Create a multiselect config option
     * @param {string} key - Option key
     * @param {string} label - Option label
     * @param {Array} options - Select options
     * @param {Array} values - Current selected values
     * @returns {HTMLElement} - Multiselect element
     */
    createMultiselectOption(key, label, options, values) {
        const div = document.createElement('div');
        div.className = 'mb-2';
        
        div.innerHTML = `<label class="form-label">${label}</label>`;
        
        options.forEach(opt => {
            const isChecked = Array.isArray(values) ? values.includes(opt) : false;
            
            const checkDiv = document.createElement('div');
            checkDiv.className = 'form-check';
            checkDiv.innerHTML = `
                <input class="form-check-input panel-config-multiselect" type="checkbox"
                       id="config-${key}-${opt}" data-key="${key}" data-value="${opt}" 
                       ${isChecked ? 'checked' : ''}>
                <label class="form-check-label" for="config-${key}-${opt}">${opt}</label>
            `;
            
            div.appendChild(checkDiv);
        });
        
        return div;
    }

    /**
     * Get panel config from form inputs
     * @returns {object} - Panel configuration
     */
    getPanelConfigFromForm() {
        const config = {};
        
        // Regular inputs
        document.querySelectorAll('.panel-config-input').forEach(input => {
            const key = input.dataset.key;
            let value;
            
            if (input.type === 'checkbox') {
                value = input.checked;
            } else if (input.type === 'number') {
                value = parseInt(input.value, 10);
            } else {
                value = input.value;
            }
            
            config[key] = value;
        });
        
        // Multiselect inputs
        const multiselects = {};
        document.querySelectorAll('.panel-config-multiselect').forEach(checkbox => {
            const key = checkbox.dataset.key;
            const value = checkbox.dataset.value;
            
            if (!multiselects[key]) {
                multiselects[key] = [];
            }
            
            if (checkbox.checked) {
                multiselects[key].push(value);
            }
        });
        
        // Add multiselects to config
        Object.assign(config, multiselects);
        
        return config;
    }

    /**
     * Setup event listeners for dashboard functionality
     */
    setupEventListeners() {
        // Dashboard tabs are shown
        document.getElementById('dashboards-tab')?.addEventListener('shown.bs.tab', async () => {
            const userId = localStorage.getItem('user_id') || 'default_user';
            await this.loadDashboards(userId);
            this.renderDashboardList(document.getElementById('dashboard-list'));
        });
        
        // Create dashboard button
        document.getElementById('create-dashboard-btn')?.addEventListener('click', () => {
            this.currentDashboard = null;
            
            // Reset form
            document.getElementById('dashboard-name').value = 'New Dashboard';
            document.getElementById('is-default-dashboard').checked = false;
            document.getElementById('dashboard-layout').value = 'grid';
            
            // Clear panels
            document.getElementById('dashboard-panels').innerHTML = `
                <div class="text-center py-4" id="no-panels-message">
                    <p class="text-muted">No panels added yet. Add your first panel to get started.</p>
                </div>
            `;
            
            // Update modal title
            document.getElementById('dashboardEditorModalLabel').textContent = 'Create Dashboard';
            
            // Hide delete button for new dashboards
            document.getElementById('delete-dashboard-btn').classList.add('d-none');
            
            // Show the modal
            const modal = new bootstrap.Modal(document.getElementById('dashboardEditorModal'));
            modal.show();
        });
        
        // Edit dashboard button in dashboard list
        document.addEventListener('click', async (e) => {
            const editButton = e.target.closest('.edit-dashboard-btn');
            if (!editButton) return;
            
            const dashboardId = parseInt(editButton.dataset.dashboardId);
            const dashboard = await this.getDashboard(dashboardId);
            
            if (dashboard) {
                // Set form values
                document.getElementById('dashboard-name').value = dashboard.name;
                document.getElementById('is-default-dashboard').checked = dashboard.is_default;
                document.getElementById('dashboard-layout').value = dashboard.layout || 'grid';
                
                // Update modal title
                document.getElementById('dashboardEditorModalLabel').textContent = 'Edit Dashboard';
                
                // Show delete button for existing dashboards
                document.getElementById('delete-dashboard-btn').classList.remove('d-none');
                
                // Render panels
                this.renderPanelsList();
                
                // Show the modal
                const modal = new bootstrap.Modal(document.getElementById('dashboardEditorModal'));
                modal.show();
            }
        });
        
        // View dashboard button in dashboard list
        document.addEventListener('click', async (e) => {
            const viewButton = e.target.closest('.view-dashboard-btn');
            if (!viewButton) return;
            
            const dashboardId = parseInt(viewButton.dataset.dashboardId);
            const dashboard = await this.getDashboard(dashboardId);
            
            if (dashboard) {
                // Close the user preferences modal
                const userPrefsModal = bootstrap.Modal.getInstance(document.getElementById('userPreferencesModal'));
                if (userPrefsModal) {
                    userPrefsModal.hide();
                }
                
                // TODO: Open the dashboard viewer
                console.log('Open dashboard viewer for', dashboard);
                alert('Dashboard viewer not yet implemented.');
            }
        });
        
        // Save dashboard button
        document.getElementById('save-dashboard-btn')?.addEventListener('click', async () => {
            const userId = localStorage.getItem('user_id') || 'default_user';
            const name = document.getElementById('dashboard-name').value;
            const isDefault = document.getElementById('is-default-dashboard').checked;
            const layout = document.getElementById('dashboard-layout').value;
            
            if (!name) {
                alert('Please enter a dashboard name');
                return;
            }
            
            if (this.currentDashboard) {
                // Update existing dashboard
                const success = await this.updateDashboard(
                    this.currentDashboard.id, 
                    name, 
                    isDefault, 
                    layout
                );
                
                if (success) {
                    // Refresh dashboards
                    await this.loadDashboards(userId);
                    this.renderDashboardList(document.getElementById('dashboard-list'));
                    
                    // Close the modal
                    const modal = bootstrap.Modal.getInstance(document.getElementById('dashboardEditorModal'));
                    modal.hide();
                }
            } else {
                // Create new dashboard
                const dashboardId = await this.createDashboard(userId, name, isDefault, layout);
                
                if (dashboardId) {
                    // Refresh dashboards
                    await this.loadDashboards(userId);
                    this.renderDashboardList(document.getElementById('dashboard-list'));
                    
                    // Close the modal
                    const modal = bootstrap.Modal.getInstance(document.getElementById('dashboardEditorModal'));
                    modal.hide();
                }
            }
        });
        
        // Delete dashboard button
        document.getElementById('delete-dashboard-btn')?.addEventListener('click', async () => {
            if (!this.currentDashboard) return;
            
            if (confirm(`Are you sure you want to delete the dashboard "${this.currentDashboard.name}"?`)) {
                const success = await this.deleteDashboard(this.currentDashboard.id);
                
                if (success) {
                    const userId = localStorage.getItem('user_id') || 'default_user';
                    
                    // Refresh dashboards
                    await this.loadDashboards(userId);
                    this.renderDashboardList(document.getElementById('dashboard-list'));
                    
                    // Close the modal
                    const modal = bootstrap.Modal.getInstance(document.getElementById('dashboardEditorModal'));
                    modal.hide();
                }
            }
        });
        
        // Add panel button
        document.getElementById('add-panel-btn')?.addEventListener('click', () => {
            if (!this.currentDashboard) return;
            
            // Reset form
            this.currentPanel = null;
            document.getElementById('panel-title').value = '';
            document.getElementById('panel-type').value = 'vm_status';
            document.getElementById('panel-width').value = '6';
            document.getElementById('panel-height').value = '4';
            document.getElementById('panel-x').value = '0';
            document.getElementById('panel-y').value = '0';
            
            // Generate config options
            this.generatePanelConfigOptions('vm_status', {});
            
            // Show position or size options based on dashboard layout
            if (this.currentDashboard.layout === 'free') {
                document.getElementById('panel-size-options').classList.add('d-none');
                document.getElementById('panel-position-options').classList.remove('d-none');
            } else {
                document.getElementById('panel-size-options').classList.remove('d-none');
                document.getElementById('panel-position-options').classList.add('d-none');
            }
            
            // Update modal title
            document.getElementById('panelEditorModalLabel').textContent = 'Add Panel';
            
            // Show the modal
            const modal = new bootstrap.Modal(document.getElementById('panelEditorModal'));
            modal.show();
        });
        
        // Panel type change
        document.getElementById('panel-type')?.addEventListener('change', (e) => {
            const panelType = e.target.value;
            this.generatePanelConfigOptions(panelType, {});
        });
        
        // Save panel button
        document.getElementById('save-panel-btn')?.addEventListener('click', async () => {
            if (!this.currentDashboard) return;
            
            const title = document.getElementById('panel-title').value;
            const panelType = document.getElementById('panel-type').value;
            const config = this.getPanelConfigFromForm();
            
            let positionX, positionY, width, height;
            
            if (this.currentDashboard.layout === 'free') {
                positionX = parseInt(document.getElementById('panel-x').value || 0);
                positionY = parseInt(document.getElementById('panel-y').value || 0);
                width = 4; // Default width for free layout
                height = 3; // Default height for free layout
            } else {
                positionX = 0; // Grid layout handles positioning
                positionY = 0; // Grid layout handles positioning
                width = parseInt(document.getElementById('panel-width').value || 6);
                height = parseInt(document.getElementById('panel-height').value || 4);
            }
            
            if (!title) {
                alert('Please enter a panel title');
                return;
            }
            
            if (this.currentPanel) {
                // Update existing panel
                const success = await this.updatePanel(
                    this.currentPanel.id,
                    title,
                    config,
                    positionX,
                    positionY,
                    width,
                    height
                );
                
                if (success) {
                    // Update panels list
                    this.renderPanelsList();
                    
                    // Close the modal
                    const modal = bootstrap.Modal.getInstance(document.getElementById('panelEditorModal'));
                    modal.hide();
                }
            } else {
                // Add new panel
                const panelId = await this.addPanel(
                    this.currentDashboard.id,
                    panelType,
                    title,
                    config,
                    positionX,
                    positionY,
                    width,
                    height
                );
                
                if (panelId) {
                    // Update panels list
                    this.renderPanelsList();
                    
                    // Close the modal
                    const modal = bootstrap.Modal.getInstance(document.getElementById('panelEditorModal'));
                    modal.hide();
                }
            }
        });
    }
}