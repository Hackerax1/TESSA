/**
 * Data module - Handles data loading and management
 */
import API from './api.js';

export default class Data {
    /**
     * Load audit logs from the server
     * @param {HTMLElement} auditLogContainer - Container for audit logs
     * @returns {Promise<void>}
     */
    static async loadAuditLogs(auditLogContainer) {
        try {
            const response = await API.fetchWithAuth('/audit-logs');
            const data = await response.json();
            auditLogContainer.innerHTML = '';
            data.logs.forEach(log => {
                const entry = document.createElement('div');
                entry.className = 'audit-entry';
                entry.innerHTML = `
                    <div class="timestamp">${new Date(log.timestamp).toLocaleString()}</div>
                    <div class="user">${log.user || 'anonymous'}</div>
                    <div class="query">${log.query}</div>
                    <div class="result ${log.success ? 'text-success' : 'text-danger'}">
                        ${log.success ? 'Success' : 'Failed'}
                    </div>
                `;
                auditLogContainer.appendChild(entry);
            });
        } catch (error) {
            console.error('Error loading audit logs:', error);
        }
    }

    /**
     * Load command history from the server
     * @param {HTMLElement} historyContainer - Container for command history
     * @returns {Promise<Array>} - Command history
     */
    static async loadCommandHistory(historyContainer) {
        try {
            const userId = localStorage.getItem('user_id') || 'default_user';
            const response = await API.fetchWithAuth(`/command-history/${userId}`);
            const data = await response.json();
            
            if (data.success) {
                if (historyContainer) {
                    historyContainer.innerHTML = '';
                    
                    if (data.history.length === 0) {
                        historyContainer.innerHTML = '<div class="alert alert-info">No command history found</div>';
                    } else {
                        const table = document.createElement('table');
                        table.className = 'table table-hover';
                        table.innerHTML = `
                            <thead>
                                <tr>
                                    <th>Command</th>
                                    <th>Timestamp</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody id="history-table-body"></tbody>
                        `;
                        
                        const tableBody = table.querySelector('tbody');
                        data.history.forEach(item => {
                            const row = document.createElement('tr');
                            row.innerHTML = `
                                <td>${item.command}</td>
                                <td>${new Date(item.timestamp).toLocaleString()}</td>
                                <td>
                                    <button class="btn btn-sm btn-outline-primary run-command" data-command="${item.command}">
                                        <i class="bi bi-play-fill"></i>
                                    </button>
                                    <button class="btn btn-sm btn-outline-secondary add-favorite" data-command="${item.command}">
                                        <i class="bi bi-star"></i>
                                    </button>
                                </td>
                            `;
                            tableBody.appendChild(row);
                        });
                        
                        historyContainer.appendChild(table);
                        
                        // Add clear history button
                        const clearButton = document.createElement('button');
                        clearButton.className = 'btn btn-outline-danger mt-3';
                        clearButton.innerHTML = '<i class="bi bi-trash"></i> Clear History';
                        clearButton.id = 'clear-history-btn';
                        historyContainer.appendChild(clearButton);
                    }
                }
                return data.history;
            } else {
                throw new Error(data.message || 'Failed to load command history');
            }
        } catch (error) {
            console.error('Error loading command history:', error);
            if (historyContainer) {
                historyContainer.innerHTML = `<div class="alert alert-danger">Error loading command history: ${error.message}</div>`;
            }
            return [];
        }
    }

    /**
     * Load favorite commands from the server
     * @param {HTMLElement} favoritesContainer - Container for favorite commands
     * @returns {Promise<Array>} - Favorite commands
     */
    static async loadFavoriteCommands(favoritesContainer) {
        try {
            const userId = localStorage.getItem('user_id') || 'default_user';
            const response = await API.fetchWithAuth(`/favorite-commands/${userId}`);
            const data = await response.json();
            
            if (data.success) {
                if (favoritesContainer) {
                    favoritesContainer.innerHTML = '';
                    
                    if (data.favorites.length === 0) {
                        favoritesContainer.innerHTML = '<div class="alert alert-info">No favorite commands found</div>';
                    } else {
                        const table = document.createElement('table');
                        table.className = 'table table-hover';
                        table.innerHTML = `
                            <thead>
                                <tr>
                                    <th>Command</th>
                                    <th>Description</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody id="favorites-table-body"></tbody>
                        `;
                        
                        const tableBody = table.querySelector('tbody');
                        data.favorites.forEach(item => {
                            const row = document.createElement('tr');
                            row.innerHTML = `
                                <td>${item.command}</td>
                                <td>${item.description || ''}</td>
                                <td>
                                    <button class="btn btn-sm btn-outline-primary run-command" data-command="${item.command}">
                                        <i class="bi bi-play-fill"></i>
                                    </button>
                                    <button class="btn btn-sm btn-outline-danger remove-favorite" data-id="${item.id}">
                                        <i class="bi bi-trash"></i>
                                    </button>
                                </td>
                            `;
                            tableBody.appendChild(row);
                        });
                        
                        favoritesContainer.appendChild(table);
                    }
                }
                return data.favorites;
            } else {
                throw new Error(data.message || 'Failed to load favorite commands');
            }
        } catch (error) {
            console.error('Error loading favorite commands:', error);
            if (favoritesContainer) {
                favoritesContainer.innerHTML = `<div class="alert alert-danger">Error loading favorite commands: ${error.message}</div>`;
            }
            return [];
        }
    }

    /**
     * Load initial status data from the server
     * @param {Function} onVMUpdate - Callback for VM updates
     * @param {Function} onClusterUpdate - Callback for cluster updates
     * @param {Function} onError - Callback for errors
     * @returns {Promise<void>}
     */
    static async loadInitialData(onVMUpdate, onClusterUpdate, onError) {
        try {
            // Fetch initial status data
            const response = await fetch('/initial-status');
            const data = await response.json();
            
            if (data.success) {
                // Update VM list and cluster status with initial data
                onVMUpdate(data.vm_status);
                onClusterUpdate(data.cluster_status.nodes);
            } else {
                throw new Error(data.error || 'Failed to load initial status');
            }
        } catch (error) {
            console.error('Error loading initial data:', error);
            onError('Failed to load system status. Please refresh the page or contact support.');
        }
    }
}
