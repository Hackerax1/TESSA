/**
 * Data module - Handles data loading and management
 */
import API from './api.js';
import Commands from './commands.js';

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
     * @param {boolean} successfulOnly - Show only successful commands
     * @returns {Promise<Array>} - Command history
     */
    static async loadCommandHistory(historyContainer, successfulOnly = false) {
        try {
            const commands = new Commands();
            await commands.loadCommandHistory();
            
            if (historyContainer) {
                commands.renderCommandHistory(historyContainer, successfulOnly);
            }
            
            return commands.commandHistory;
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
            const commands = new Commands();
            await commands.loadFavoriteCommands();
            
            if (favoritesContainer) {
                commands.renderFavoriteCommands(favoritesContainer);
            }
            
            return commands.favoriteCommands;
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
                // Update VM list with the new updateVMList function
                if (typeof window.updateVMList === 'function') {
                    window.updateVMList(data.vm_status.vms);
                }
                
                // Also call the original callback for backward compatibility
                if (onVMUpdate) {
                    onVMUpdate(data.vm_status);
                }
                
                // Update cluster status
                if (onClusterUpdate) {
                    onClusterUpdate(data.cluster_status.nodes);
                }
            } else {
                if (onError) {
                    onError(data.message || 'Failed to load initial data');
                }
            }
        } catch (error) {
            console.error('Error loading initial data:', error);
            if (onError) {
                onError(error.message || 'Network error');
            }
        }
    }
}
