/**
 * API module - Handles all API requests and authentication
 */
export default class API {
    /**
     * Helper method for fetch with authentication
     * @param {string} url - The URL to fetch
     * @param {Object} options - Fetch options
     * @returns {Promise} - The fetch promise
     */
    static async fetchWithAuth(url, options = {}) {
        // Get token from localStorage if available
        const token = localStorage.getItem('token');
        
        const headers = {
            'Content-Type': 'application/json',
            ...(token && { 'Authorization': `Bearer ${token}` }),
            ...(options.headers || {})
        };
        
        return fetch(url, {
            ...options,
            headers
        });
    }
}
