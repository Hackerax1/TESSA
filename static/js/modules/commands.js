/**
 * Commands module - Handles command history and favorite commands
 */
import API from './api.js';

export default class Commands {
    constructor() {
        this.commandHistory = [];
        this.favoriteCommands = [];
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
                this.commandHistory = data.history || [];
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
}
