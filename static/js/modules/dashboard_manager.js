/**
 * Dashboard management module for customizable user dashboards
 */
import DashboardPanels from './dashboard_panels.js';

export default class DashboardManager {
    constructor() {
        this.panels = new DashboardPanels();
        this.currentLayout = 'grid';
        this.dashboards = new Map();
        this.activeDashboard = null;
        this.gridStack = null;
        this.setupEventListeners();
    }
    
    /**
     * Initialize dashboard system
     */
    async initialize() {
        try {
            // Load user dashboards
            const response = await fetch('/api/dashboards/' + window.userId);
            const data = await response.json();
            
            if (!data.success) {
                throw new Error(data.error || 'Failed to load dashboards');
            }
            
            // Store dashboards
            data.dashboards.forEach(dashboard => {
                this.dashboards.set(dashboard.id, dashboard);
                if (dashboard.is_default) {
                    this.activeDashboard = dashboard.id;
                }
            });
            
            // If no default dashboard, use first one or create new
            if (!this.activeDashboard) {
                if (this.dashboards.size > 0) {
                    this.activeDashboard = this.dashboards.values().next().value.id;
                } else {
                    await this.createDefaultDashboard();
                }
            }
            
            // Initialize grid layout system
            this.initializeGridStack();
            
            // Load active dashboard
            await this.loadDashboard(this.activeDashboard);
            
        } catch (error) {
            console.error('Error initializing dashboards:', error);
            this.showError('Failed to initialize dashboards: ' + error.message);
        }
    }
    
    /**
     * Initialize GridStack layout system
     */
    initializeGridStack() {
        this.gridStack = GridStack.init({
            column: 12,
            cellHeight: 60,
            animate: true,
            float: true,
            resizable: {
                handles: 'e,se,s,sw,w'
            }
        });
        
        // Handle layout changes
        this.gridStack.on('change', () => {
            this.saveLayout();
        });
    }
    
    /**
     * Load a dashboard
     */
    async loadDashboard(dashboardId) {
        try {
            const dashboard = this.dashboards.get(dashboardId);
            if (!dashboard) {
                throw new Error('Dashboard not found');
            }
            
            // Clear current layout
            this.gridStack.removeAll();
            
            // Load panels
            for (const panel of dashboard.panels) {
                await this.addPanel(panel.type, panel.config, panel.position);
            }
            
            this.activeDashboard = dashboardId;
            this.updateDashboardList();
            
        } catch (error) {
            console.error('Error loading dashboard:', error);
            this.showError('Failed to load dashboard: ' + error.message);
        }
    }
    
    /**
     * Add a new panel to the dashboard
     */
    async addPanel(type, config = {}, position = {}) {
        try {
            // Create panel instance
            const panel = this.panels.createPanel(type, config);
            
            // Create grid item
            const itemEl = document.createElement('div');
            itemEl.className = 'grid-stack-item';
            itemEl.innerHTML = `
                <div class="grid-stack-item-content panel ${type}-panel">
                    <div class="panel-header">
                        <h5 class="panel-title">${config.title || type}</h5>
                        <div class="panel-actions">
                            <button class="btn btn-sm btn-link configure-panel">
                                <i class="bi bi-gear"></i>
                            </button>
                            <button class="btn btn-sm btn-link remove-panel">
                                <i class="bi bi-x-lg"></i>
                            </button>
                        </div>
                    </div>
                    <div class="panel-body"></div>
                </div>
            `;
            
            // Add to grid
            const gridItem = this.gridStack.addWidget(itemEl, {
                x: position.x || 0,
                y: position.y || 0,
                w: position.w || 6,
                h: position.h || 4,
                minW: 3,
                minH: 2
            });
            
            // Render panel content
            const panelBody = gridItem.querySelector('.panel-body');
            await panel.render(panelBody);
            
            // Add event listeners
            const configureBtn = gridItem.querySelector('.configure-panel');
            configureBtn.addEventListener('click', () => {
                this.showPanelConfig(panel, gridItem);
            });
            
            const removeBtn = gridItem.querySelector('.remove-panel');
            removeBtn.addEventListener('click', () => {
                if (confirm('Remove this panel?')) {
                    this.gridStack.removeWidget(gridItem);
                    this.saveLayout();
                }
            });
            
        } catch (error) {
            console.error('Error adding panel:', error);
            this.showError('Failed to add panel: ' + error.message);
        }
    }
    
    /**
     * Show panel configuration modal
     */
    showPanelConfig(panel, gridItem) {
        const modal = document.getElementById('panelConfigModal');
        const form = modal.querySelector('form');
        
        // Clear previous form
        form.innerHTML = '';
        
        // Add config fields based on panel type
        const config = panel.config;
        for (const [key, value] of Object.entries(config)) {
            if (typeof value === 'boolean') {
                form.innerHTML += `
                    <div class="mb-3 form-check">
                        <input type="checkbox" class="form-check-input" id="${key}" 
                               name="${key}" ${value ? 'checked' : ''}>
                        <label class="form-check-label" for="${key}">
                            ${key.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())}
                        </label>
                    </div>
                `;
            } else if (typeof value === 'number') {
                form.innerHTML += `
                    <div class="mb-3">
                        <label class="form-label" for="${key}">
                            ${key.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())}
                        </label>
                        <input type="number" class="form-control" id="${key}" 
                               name="${key}" value="${value}">
                    </div>
                `;
            } else if (typeof value === 'string') {
                form.innerHTML += `
                    <div class="mb-3">
                        <label class="form-label" for="${key}">
                            ${key.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())}
                        </label>
                        <input type="text" class="form-control" id="${key}" 
                               name="${key}" value="${value}">
                    </div>
                `;
            }
        }
        
        // Show modal
        const modalInstance = new bootstrap.Modal(modal);
        modalInstance.show();
        
        // Handle form submission
        form.onsubmit = async (e) => {
            e.preventDefault();
            const formData = new FormData(form);
            const newConfig = {};
            
            for (const [key, value] of formData.entries()) {
                if (typeof config[key] === 'boolean') {
                    newConfig[key] = value === 'on';
                } else if (typeof config[key] === 'number') {
                    newConfig[key] = Number(value);
                } else {
                    newConfig[key] = value;
                }
            }
            
            // Update panel
            const updatedPanel = this.panels.createPanel(panel.type, newConfig);
            const panelBody = gridItem.querySelector('.panel-body');
            await updatedPanel.render(panelBody);
            
            // Save layout
            this.saveLayout();
            
            modalInstance.hide();
        };
    }
    
    /**
     * Save current layout
     */
    async saveLayout() {
        if (!this.activeDashboard) return;
        
        try {
            const layout = this.gridStack.save();
            const panels = [];
            
            // Get panel configurations
            layout.forEach(item => {
                const panelEl = item.el;
                const type = panelEl.querySelector('.grid-stack-item-content').classList[2].replace('-panel', '');
                const config = this.panels.panelTypes[type].defaultConfig;
                
                panels.push({
                    type,
                    config,
                    position: {
                        x: item.x,
                        y: item.y,
                        w: item.w,
                        h: item.h
                    }
                });
            });
            
            // Save to server
            const response = await fetch(`/api/dashboards/${this.activeDashboard}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    layout: panels
                })
            });
            
            const data = await response.json();
            if (!data.success) {
                throw new Error(data.error || 'Failed to save layout');
            }
            
        } catch (error) {
            console.error('Error saving layout:', error);
            this.showError('Failed to save layout: ' + error.message);
        }
    }
    
    /**
     * Create a new dashboard
     */
    async createDashboard(name, isDefault = false) {
        try {
            const response = await fetch('/api/dashboards/' + window.userId, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    name,
                    is_default: isDefault
                })
            });
            
            const data = await response.json();
            if (!data.success) {
                throw new Error(data.error || 'Failed to create dashboard');
            }
            
            // Add to local collection
            this.dashboards.set(data.dashboard.id, data.dashboard);
            
            // Switch to new dashboard if it's default
            if (isDefault) {
                await this.loadDashboard(data.dashboard.id);
            }
            
            this.updateDashboardList();
            
        } catch (error) {
            console.error('Error creating dashboard:', error);
            this.showError('Failed to create dashboard: ' + error.message);
        }
    }
    
    /**
     * Create default dashboard for new users
     */
    async createDefaultDashboard() {
        await this.createDashboard('Default Dashboard', true);
        
        // Add default panels
        await this.addPanel('vm_status', {
            title: 'VM Status',
            showResourceUsage: true,
            limit: 5
        }, { x: 0, y: 0, w: 6, h: 4 });
        
        await this.addPanel('system_metrics', {
            title: 'System Resources',
            metrics: ['cpu', 'memory', 'storage'],
            refreshInterval: 30
        }, { x: 6, y: 0, w: 6, h: 4 });
        
        await this.addPanel('power_efficiency', {
            title: 'Power Efficiency',
            showRecommendations: true
        }, { x: 0, y: 4, w: 6, h: 4 });
        
        await this.addPanel('quick_actions', {
            title: 'Quick Actions',
            showLabels: true
        }, { x: 6, y: 4, w: 6, h: 2 });
    }
    
    /**
     * Update dashboard list in UI
     */
    updateDashboardList() {
        const list = document.getElementById('dashboard-list');
        if (!list) return;
        
        list.innerHTML = '';
        
        this.dashboards.forEach((dashboard, id) => {
            const item = document.createElement('li');
            item.className = 'nav-item';
            item.innerHTML = `
                <a class="nav-link ${id === this.activeDashboard ? 'active' : ''}" href="#">
                    ${dashboard.name}
                    ${dashboard.is_default ? '<span class="badge bg-primary">Default</span>' : ''}
                </a>
            `;
            
            item.querySelector('a').addEventListener('click', (e) => {
                e.preventDefault();
                this.loadDashboard(id);
            });
            
            list.appendChild(item);
        });
    }
    
    /**
     * Set up event listeners
     */
    setupEventListeners() {
        // New dashboard button
        const newDashboardBtn = document.getElementById('new-dashboard');
        if (newDashboardBtn) {
            newDashboardBtn.addEventListener('click', () => {
                const name = prompt('Enter dashboard name:');
                if (name) {
                    this.createDashboard(name);
                }
            });
        }
        
        // Add panel button
        const addPanelBtn = document.getElementById('add-panel');
        if (addPanelBtn) {
            addPanelBtn.addEventListener('click', () => {
                this.showAddPanelModal();
            });
        }
    }
    
    /**
     * Show add panel modal
     */
    showAddPanelModal() {
        const modal = document.getElementById('addPanelModal');
        const list = modal.querySelector('.panel-type-list');
        
        // Clear previous list
        list.innerHTML = '';
        
        // Add panel types
        for (const [type, info] of Object.entries(this.panels.panelTypes)) {
            const item = document.createElement('div');
            item.className = 'panel-type-item';
            item.innerHTML = `
                <div class="panel-type-info">
                    <h6>${type.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())}</h6>
                    <small class="text-muted">Add ${type} monitoring panel</small>
                </div>
                <button class="btn btn-primary btn-sm">Add</button>
            `;
            
            item.querySelector('button').addEventListener('click', () => {
                this.addPanel(type);
                bootstrap.Modal.getInstance(modal).hide();
            });
            
            list.appendChild(item);
        }
        
        // Show modal
        const modalInstance = new bootstrap.Modal(modal);
        modalInstance.show();
    }
    
    /**
     * Show error message
     */
    showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'alert alert-danger alert-dismissible fade show';
        errorDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.querySelector('.dashboard-container').prepend(errorDiv);
    }
    
    /**
     * Handle dashboard sync update
     */
    syncDashboards(dashboardData) {
        // Update local dashboard collection
        dashboardData.forEach(dashboard => {
            this.dashboards.set(dashboard.id, dashboard);
        });
        
        // Reload active dashboard if it was updated
        if (dashboardData.some(d => d.id === this.activeDashboard)) {
            this.loadDashboard(this.activeDashboard);
        }
        
        this.updateDashboardList();
    }
}