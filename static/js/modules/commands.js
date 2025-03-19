/**
 * Commands module - Handles command history and favorite commands
 */
import API from './api.js';

export default class Commands {
    constructor() {
        this.commandHistory = [];
        this.favoriteCommands = [];
        this.loadCommandHistory();
        this.loadFavoriteCommands();
    }

    /**
     * Load command history from the server
     * @returns {Promise<Array>} - Command history
     */
    async loadCommandHistory() {
        try {
            const userId = localStorage.getItem('user_id') || 'default_user';
            const response = await API.fetchWithAuth(`/command-history/${userId}`);
            const data = await response.json();
            
            if (data.success) {
                this.commandHistory = data.history || [];
                return this.commandHistory;
            } else {
                throw new Error(data.message || 'Failed to load command history');
            }
        } catch (error) {
            console.error('Error loading command history:', error);
            return [];
        }
    }

    /**
     * Load favorite commands from the server
     * @returns {Promise<Array>} - Favorite commands
     */
    async loadFavoriteCommands() {
        try {
            const userId = localStorage.getItem('user_id') || 'default_user';
            const response = await API.fetchWithAuth(`/favorite-commands/${userId}`);
            const data = await response.json();
            
            if (data.success) {
                this.favoriteCommands = data.favorites || [];
                return this.favoriteCommands;
            } else {
                throw new Error(data.message || 'Failed to load favorite commands');
            }
        } catch (error) {
            console.error('Error loading favorite commands:', error);
            return [];
        }
    }

    /**
     * Add a command to the history
     * @param {string} command - Command text
     * @returns {Promise<boolean>} - Success status
     */
    async addCommandToHistory(command) {
        try {
            // Get current user ID (in a real app, this would come from authentication)
            const userId = localStorage.getItem('user_id') || 'default_user';
            
            const response = await API.fetchWithAuth(`/command-history/${userId}`, {
                method: 'POST',
                body: JSON.stringify({ command_text: command })
            });
            
            const data = await response.json();
            
            if (data.success) {
                await this.loadCommandHistory(); // Reload history
                return true;
            } else {
                console.error('Failed to add command to history:', data.message);
                return false;
            }
        } catch (error) {
            console.error('Error adding command to history:', error);
            return false;
        }
    }

    /**
     * Add a command to favorites
     * @param {string} command - Command text
     * @param {string} description - Command description
     * @returns {Promise<boolean>} - Success status
     */
    async addToFavorites(command, description) {
        try {
            // Get current user ID (in a real app, this would come from authentication)
            const userId = localStorage.getItem('user_id') || 'default_user';
            
            const response = await API.fetchWithAuth(`/favorite-commands/${userId}`, {
                method: 'POST',
                body: JSON.stringify({ 
                    command_text: command,
                    description: description
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                await this.loadFavoriteCommands(); // Reload favorites
                return true;
            } else {
                console.error('Failed to add command to favorites:', data.message);
                return false;
            }
        } catch (error) {
            console.error('Error adding to favorites:', error);
            return false;
        }
    }
    
    /**
     * Remove a command from favorites
     * @param {string} commandId - Command ID
     * @returns {Promise<boolean>} - Success status
     */
    async removeFavoriteCommand(commandId) {
        try {
            // Get current user ID (in a real app, this would come from authentication)
            const userId = localStorage.getItem('user_id') || 'default_user';
            
            const response = await API.fetchWithAuth(`/favorite-commands/${userId}/${commandId}`, {
                method: 'DELETE'
            });
            
            const data = await response.json();
            
            if (data.success) {
                await this.loadFavoriteCommands(); // Reload favorites
                return true;
            } else {
                console.error('Failed to remove command from favorites:', data.message);
                return false;
            }
        } catch (error) {
            console.error('Error removing favorite:', error);
            return false;
        }
    }
    
    /**
     * Clear command history
     * @returns {Promise<boolean>} - Success status
     */
    async clearCommandHistory() {
        if (!confirm('Are you sure you want to clear your command history?')) {
            return false;
        }
        
        try {
            // Get current user ID (in a real app, this would come from authentication)
            const userId = localStorage.getItem('user_id') || 'default_user';
            
            const response = await API.fetchWithAuth(`/command-history/${userId}/clear`, {
                method: 'POST'
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.commandHistory = [];
                return true;
            } else {
                console.error('Failed to clear command history:', data.message);
                return false;
            }
        } catch (error) {
            console.error('Error clearing history:', error);
            return false;
        }
    }
    
    /**
     * Render command history in UI
     * @param {HTMLElement} container - Container element
     * @param {boolean} successfulOnly - Show only successful commands
     */
    renderCommandHistory(container, successfulOnly = false) {
        if (!container) return;
        
        container.innerHTML = '';
        
        if (this.commandHistory.length === 0) {
            document.getElementById('noHistoryMessage').style.display = 'block';
            return;
        }
        
        document.getElementById('noHistoryMessage').style.display = 'none';
        
        // Filter history if needed
        const filteredHistory = successfulOnly 
            ? this.commandHistory.filter(cmd => cmd.success) 
            : this.commandHistory;
        
        const tableBody = document.createElement('tbody');
        tableBody.id = 'commandHistoryTable';
        
        filteredHistory.forEach(item => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${item.command}</td>
                <td>${item.intent || 'N/A'}</td>
                <td>${new Date(item.timestamp).toLocaleString()}</td>
                <td><span class="badge ${item.success ? 'bg-success' : 'bg-danger'}">${item.success ? 'Success' : 'Failed'}</span></td>
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
        
        // Replace the existing tbody
        const existingTable = container.querySelector('table');
        if (existingTable) {
            const existingBody = existingTable.querySelector('tbody');
            existingTable.replaceChild(tableBody, existingBody);
        } else {
            // Create new table if it doesn't exist
            const table = document.createElement('table');
            table.className = 'table table-hover';
            table.innerHTML = `
                <thead>
                    <tr>
                        <th>Command</th>
                        <th>Intent</th>
                        <th>Time</th>
                        <th>Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
            `;
            table.appendChild(tableBody);
            container.appendChild(table);
        }
    }
    
    /**
     * Render favorite commands in UI
     * @param {HTMLElement} container - Container element
     */
    renderFavoriteCommands(container) {
        if (!container) return;
        
        container.innerHTML = '';
        
        if (this.favoriteCommands.length === 0) {
            document.getElementById('noFavoritesMessage').style.display = 'block';
            return;
        }
        
        document.getElementById('noFavoritesMessage').style.display = 'none';
        
        const listGroup = document.createElement('div');
        listGroup.className = 'list-group';
        
        this.favoriteCommands.forEach(item => {
            const listItem = document.createElement('div');
            listItem.className = 'list-group-item list-group-item-action d-flex justify-content-between align-items-center';
            
            const contentDiv = document.createElement('div');
            contentDiv.className = 'flex-grow-1';
            contentDiv.innerHTML = `
                <h6 class="mb-1">${item.command}</h6>
                <p class="mb-1 text-muted small">${item.description || ''}</p>
            `;
            
            const actionsDiv = document.createElement('div');
            actionsDiv.className = 'btn-group';
            actionsDiv.innerHTML = `
                <button class="btn btn-sm btn-outline-primary run-command" data-command="${item.command}">
                    <i class="bi bi-play-fill"></i>
                </button>
                <button class="btn btn-sm btn-outline-danger remove-favorite" data-id="${item.id}">
                    <i class="bi bi-trash"></i>
                </button>
            `;
            
            listItem.appendChild(contentDiv);
            listItem.appendChild(actionsDiv);
            listGroup.appendChild(listItem);
        });
        
        container.appendChild(listGroup);
    }
}
