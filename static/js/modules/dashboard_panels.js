/**
 * Dashboard panel components with customization support
 */
export default class DashboardPanels {
    constructor() {
        this.panelTypes = {
            'vm_status': {
                render: this._renderVMStatus.bind(this),
                defaultConfig: {
                    showResourceUsage: true,
                    limit: 5,
                    sortBy: 'name'
                }
            },
            'system_metrics': {
                render: this._renderSystemMetrics.bind(this),
                defaultConfig: {
                    metrics: ['cpu', 'memory', 'storage'],
                    refreshInterval: 30
                }
            },
            'resource_forecast': {
                render: this._renderResourceForecast.bind(this),
                defaultConfig: {
                    forecastHours: 24,
                    showPredictions: true,
                    resources: ['cpu', 'memory']
                }
            },
            'power_efficiency': {
                render: this._renderPowerEfficiency.bind(this),
                defaultConfig: {
                    showRecommendations: true,
                    thresholds: {
                        warning: 70,
                        critical: 90
                    }
                }
            },
            'quick_actions': {
                render: this._renderQuickActions.bind(this),
                defaultConfig: {
                    actions: ['start', 'stop', 'restart'],
                    showLabels: true
                }
            }
        };
    }
    
    /**
     * Create a new panel instance
     */
    createPanel(type, config = {}) {
        if (!this.panelTypes[type]) {
            throw new Error(`Unknown panel type: ${type}`);
        }
        
        // Merge default config with provided config
        const panelConfig = {
            ...this.panelTypes[type].defaultConfig,
            ...config
        };
        
        return {
            type,
            config: panelConfig,
            render: (container) => this.panelTypes[type].render(container, panelConfig)
        };
    }
    
    /**
     * Render VM status panel
     */
    async _renderVMStatus(container, config) {
        try {
            // Get VM data
            const response = await fetch('/api/vms/status');
            const data = await response.json();
            
            if (!data.success) {
                throw new Error(data.error || 'Failed to get VM status');
            }
            
            // Sort VMs
            let vms = data.vms;
            if (config.sortBy === 'name') {
                vms.sort((a, b) => a.name.localeCompare(b.name));
            } else if (config.sortBy === 'status') {
                vms.sort((a, b) => a.status.localeCompare(b.status));
            }
            
            // Limit number of VMs shown
            if (config.limit) {
                vms = vms.slice(0, config.limit);
            }
            
            // Generate HTML
            const vmList = vms.map(vm => `
                <div class="vm-item ${vm.status.toLowerCase()}">
                    <div class="vm-name">${vm.name}</div>
                    <div class="vm-status">
                        <span class="status-indicator"></span>
                        ${vm.status}
                    </div>
                    ${config.showResourceUsage ? `
                        <div class="vm-resources">
                            <div class="resource">
                                <i class="bi bi-cpu"></i>
                                ${vm.cpu_usage}%
                            </div>
                            <div class="resource">
                                <i class="bi bi-memory"></i>
                                ${vm.memory_usage}%
                            </div>
                        </div>
                    ` : ''}
                </div>
            `).join('');
            
            container.innerHTML = `
                <div class="vm-status-panel">
                    ${vmList}
                </div>
            `;
            
        } catch (error) {
            container.innerHTML = `
                <div class="alert alert-danger">
                    Error loading VM status: ${error.message}
                </div>
            `;
        }
    }
    
    /**
     * Render system metrics panel
     */
    async _renderSystemMetrics(container, config) {
        try {
            // Get metrics data
            const response = await fetch('/api/cluster-resources');
            const data = await response.json();
            
            if (!data.success) {
                throw new Error(data.error || 'Failed to get system metrics');
            }
            
            const metrics = data.resources;
            
            // Generate metrics HTML
            const metricsHtml = config.metrics.map(metric => {
                const value = metrics[metric];
                const percentage = (value.used / value.total * 100).toFixed(1);
                
                return `
                    <div class="metric-item">
                        <div class="metric-header">
                            <span class="metric-name">${metric.toUpperCase()}</span>
                            <span class="metric-value">${percentage}%</span>
                        </div>
                        <div class="progress">
                            <div class="progress-bar ${percentage > 90 ? 'bg-danger' : percentage > 70 ? 'bg-warning' : 'bg-success'}"
                                role="progressbar"
                                style="width: ${percentage}%"
                                aria-valuenow="${percentage}"
                                aria-valuemin="0"
                                aria-valuemax="100">
                            </div>
                        </div>
                        <div class="metric-details">
                            ${this._formatBytes(value.used)} / ${this._formatBytes(value.total)}
                        </div>
                    </div>
                `;
            }).join('');
            
            container.innerHTML = `
                <div class="system-metrics-panel">
                    ${metricsHtml}
                </div>
            `;
            
            // Set up auto-refresh if configured
            if (config.refreshInterval) {
                setTimeout(() => this._renderSystemMetrics(container, config), 
                    config.refreshInterval * 1000);
            }
            
        } catch (error) {
            container.innerHTML = `
                <div class="alert alert-danger">
                    Error loading system metrics: ${error.message}
                </div>
            `;
        }
    }
    
    /**
     * Render resource forecast panel
     */
    async _renderResourceForecast(container, config) {
        try {
            // Get forecast data
            const response = await fetch('/api/resource-forecast');
            const data = await response.json();
            
            if (!data.success) {
                throw new Error(data.error || 'Failed to get resource forecast');
            }
            
            const forecasts = data.forecasts;
            
            // Generate forecast charts
            const chartHtml = config.resources.map(resource => {
                const forecast = forecasts[resource];
                return `
                    <div class="forecast-chart">
                        <h6>${resource.toUpperCase()} Usage Forecast</h6>
                        <canvas id="forecast-${resource}"></canvas>
                        ${config.showPredictions ? `
                            <div class="forecast-predictions">
                                <div class="prediction">
                                    <span class="label">Peak Time:</span>
                                    <span class="value">Hour ${forecast.peak_time}</span>
                                </div>
                                <div class="prediction">
                                    <span class="label">Trend:</span>
                                    <span class="value ${forecast.trend}">${forecast.trend}</span>
                                </div>
                            </div>
                        ` : ''}
                    </div>
                `;
            }).join('');
            
            container.innerHTML = `
                <div class="resource-forecast-panel">
                    ${chartHtml}
                </div>
            `;
            
            // Initialize charts
            config.resources.forEach(resource => {
                const forecast = forecasts[resource];
                const ctx = document.getElementById(`forecast-${resource}`).getContext('2d');
                new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: Array.from({length: config.forecastHours}, (_, i) => `+${i}h`),
                        datasets: [{
                            label: `${resource.toUpperCase()} Usage`,
                            data: forecast.next_24h,
                            borderColor: resource === 'cpu' ? '#007bff' : '#28a745',
                            tension: 0.4
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            y: {
                                beginAtZero: true,
                                max: 100,
                                ticks: {
                                    callback: value => value + '%'
                                }
                            }
                        }
                    }
                });
            });
            
        } catch (error) {
            container.innerHTML = `
                <div class="alert alert-danger">
                    Error loading resource forecast: ${error.message}
                </div>
            `;
        }
    }
    
    /**
     * Render power efficiency panel
     */
    async _renderPowerEfficiency(container, config) {
        try {
            // Get power efficiency data
            const response = await fetch('/api/power-efficiency');
            const data = await response.json();
            
            if (!data.success) {
                throw new Error(data.error || 'Failed to get power efficiency data');
            }
            
            const metrics = data.metrics;
            const recommendations = data.recommendations;
            
            // Calculate efficiency score (0-100)
            const score = Math.round((1 - metrics.power_saving_potential / 100) * 100);
            
            // Determine status based on thresholds
            const status = score < config.thresholds.critical ? 'danger' :
                          score < config.thresholds.warning ? 'warning' : 'success';
            
            container.innerHTML = `
                <div class="power-efficiency-panel">
                    <div class="efficiency-score ${status}">
                        <div class="score-value">${score}</div>
                        <div class="score-label">Efficiency Score</div>
                    </div>
                    
                    <div class="efficiency-metrics">
                        <div class="metric">
                            <span class="label">CPU Efficiency:</span>
                            <span class="value">${(metrics.cpu_efficiency * 100).toFixed(1)}%</span>
                        </div>
                        <div class="metric">
                            <span class="label">Memory Efficiency:</span>
                            <span class="value">${(metrics.memory_efficiency * 100).toFixed(1)}%</span>
                        </div>
                    </div>
                    
                    ${config.showRecommendations && recommendations.length ? `
                        <div class="efficiency-recommendations">
                            <h6>Recommendations</h6>
                            <ul class="recommendations-list">
                                ${recommendations.map(rec => `
                                    <li class="recommendation ${rec.severity}">
                                        <i class="bi bi-lightbulb"></i>
                                        ${rec.message}
                                    </li>
                                `).join('')}
                            </ul>
                        </div>
                    ` : ''}
                </div>
            `;
            
        } catch (error) {
            container.innerHTML = `
                <div class="alert alert-danger">
                    Error loading power efficiency data: ${error.message}
                </div>
            `;
        }
    }
    
    /**
     * Render quick actions panel
     */
    _renderQuickActions(container, config) {
        const actionButtons = config.actions.map(action => `
            <button class="btn btn-outline-primary action-btn ${config.showLabels ? 'with-label' : ''}"
                    data-action="${action}">
                <i class="bi bi-${this._getActionIcon(action)}"></i>
                ${config.showLabels ? `<span>${action.charAt(0).toUpperCase() + action.slice(1)}</span>` : ''}
            </button>
        `).join('');
        
        container.innerHTML = `
            <div class="quick-actions-panel">
                ${actionButtons}
            </div>
        `;
        
        // Add event listeners
        container.querySelectorAll('.action-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const action = btn.dataset.action;
                this._handleQuickAction(action);
            });
        });
    }
    
    /**
     * Handle quick action button click
     */
    async _handleQuickAction(action) {
        try {
            const response = await fetch('/api/vm/action', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    action: action,
                    vm_id: window.selectedVMId
                })
            });
            
            const data = await response.json();
            if (!data.success) {
                throw new Error(data.error || `Failed to ${action} VM`);
            }
            
            // Show success message
            window.showToast('success', `Successfully ${action}ed VM`);
            
        } catch (error) {
            window.showToast('error', error.message);
        }
    }
    
    /**
     * Get icon for quick action button
     */
    _getActionIcon(action) {
        switch (action) {
            case 'start': return 'play-circle';
            case 'stop': return 'stop-circle';
            case 'restart': return 'arrow-repeat';
            default: return 'gear';
        }
    }
    
    /**
     * Format bytes to human readable string
     */
    _formatBytes(bytes) {
        const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
        if (bytes === 0) return '0 B';
        const i = parseInt(Math.floor(Math.log(bytes) / Math.log(1024)));
        return Math.round(bytes / Math.pow(1024, i), 2) + ' ' + sizes[i];
    }
}