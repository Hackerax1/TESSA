/**
 * API module - Handles all API requests and authentication
 */
export default class API {
    static cache = new Map();
    static pendingRequests = new Map();
    static defaultCacheTTL = 60000; // 1 minute default cache TTL
    static requestTimeouts = new Map();
    
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
        
        try {
            const response = await fetch(url, {
                ...options,
                headers
            });
            
            // Check for unauthorized response (token expired)
            if (response.status === 401) {
                // Clear token and redirect to login
                localStorage.removeItem('token');
                window.location.href = '/login';
                throw new Error('Authentication token expired. Please log in again.');
            }
            
            return response;
        } catch (error) {
            console.error(`API request failed: ${url}`, error);
            throw error;
        }
    }
    
    /**
     * GET request with caching
     * @param {string} url - The URL to fetch
     * @param {Object} options - Options including cache settings
     * @returns {Promise} - The fetch promise with JSON data
     */
    static async get(url, options = {}) {
        const cacheKey = url;
        const useCache = options.cache !== false;
        const cacheTTL = options.cacheTTL || this.defaultCacheTTL;
        
        // Return cached data if available and not expired
        if (useCache && this.cache.has(cacheKey)) {
            const cachedData = this.cache.get(cacheKey);
            if (cachedData.expiry > Date.now()) {
                return cachedData.data;
            }
            // Clear expired cache
            this.cache.delete(cacheKey);
        }
        
        // Check if there's already a pending request for this URL
        if (this.pendingRequests.has(cacheKey)) {
            return this.pendingRequests.get(cacheKey);
        }
        
        // Create the request promise
        const requestPromise = (async () => {
            try {
                const response = await this.fetchWithAuth(url, {
                    method: 'GET',
                    ...options
                });
                
                if (!response.ok) {
                    throw new Error(`API error: ${response.status} ${response.statusText}`);
                }
                
                const data = await response.json();
                
                // Cache the response if caching is enabled
                if (useCache) {
                    this.cache.set(cacheKey, {
                        data,
                        expiry: Date.now() + cacheTTL
                    });
                }
                
                return data;
            } catch (error) {
                // Remove from cache if request failed
                this.cache.delete(cacheKey);
                throw error;
            } finally {
                // Remove from pending requests
                this.pendingRequests.delete(cacheKey);
            }
        })();
        
        // Store the pending request
        this.pendingRequests.set(cacheKey, requestPromise);
        
        return requestPromise;
    }
    
    /**
     * POST request
     * @param {string} url - The URL to fetch
     * @param {Object} data - The data to send
     * @param {Object} options - Fetch options
     * @returns {Promise} - The fetch promise with JSON data
     */
    static async post(url, data, options = {}) {
        try {
            const response = await this.fetchWithAuth(url, {
                method: 'POST',
                body: JSON.stringify(data),
                ...options
            });
            
            if (!response.ok) {
                throw new Error(`API error: ${response.status} ${response.statusText}`);
            }
            
            // Invalidate cache for this URL pattern
            this.invalidateRelatedCache(url);
            
            return await response.json();
        } catch (error) {
            console.error(`POST request failed: ${url}`, error);
            throw error;
        }
    }
    
    /**
     * PUT request
     * @param {string} url - The URL to fetch
     * @param {Object} data - The data to send
     * @param {Object} options - Fetch options
     * @returns {Promise} - The fetch promise with JSON data
     */
    static async put(url, data, options = {}) {
        try {
            const response = await this.fetchWithAuth(url, {
                method: 'PUT',
                body: JSON.stringify(data),
                ...options
            });
            
            if (!response.ok) {
                throw new Error(`API error: ${response.status} ${response.statusText}`);
            }
            
            // Invalidate cache for this URL pattern
            this.invalidateRelatedCache(url);
            
            return await response.json();
        } catch (error) {
            console.error(`PUT request failed: ${url}`, error);
            throw error;
        }
    }
    
    /**
     * DELETE request
     * @param {string} url - The URL to fetch
     * @param {Object} options - Fetch options
     * @returns {Promise} - The fetch promise with JSON data
     */
    static async delete(url, options = {}) {
        try {
            const response = await this.fetchWithAuth(url, {
                method: 'DELETE',
                ...options
            });
            
            if (!response.ok) {
                throw new Error(`API error: ${response.status} ${response.statusText}`);
            }
            
            // Invalidate cache for this URL pattern
            this.invalidateRelatedCache(url);
            
            return await response.json();
        } catch (error) {
            console.error(`DELETE request failed: ${url}`, error);
            throw error;
        }
    }
    
    /**
     * Clear all cached data
     */
    static clearCache() {
        this.cache.clear();
    }
    
    /**
     * Invalidate cache entries related to a URL
     * @param {string} url - The URL pattern to match
     */
    static invalidateRelatedCache(url) {
        // Extract the base path from the URL
        const urlParts = url.split('/');
        const basePath = urlParts.slice(0, -1).join('/');
        
        // Remove any cache entries that start with the base path
        for (const key of this.cache.keys()) {
            if (key.startsWith(basePath)) {
                this.cache.delete(key);
            }
        }
    }
    
    /**
     * Set a timeout for a request
     * @param {string} url - The URL to set timeout for
     * @param {number} timeout - Timeout in milliseconds
     * @returns {Promise} - A promise that rejects after timeout
     */
    static setRequestTimeout(url, timeout = 10000) {
        return new Promise((_, reject) => {
            const timeoutId = setTimeout(() => {
                reject(new Error(`Request timeout for ${url}`));
                this.requestTimeouts.delete(url);
            }, timeout);
            
            this.requestTimeouts.set(url, timeoutId);
        });
    }
    
    /**
     * Clear a request timeout
     * @param {string} url - The URL to clear timeout for
     */
    static clearRequestTimeout(url) {
        if (this.requestTimeouts.has(url)) {
            clearTimeout(this.requestTimeouts.get(url));
            this.requestTimeouts.delete(url);
        }
    }
    
    /**
     * Fetch with timeout
     * @param {string} url - The URL to fetch
     * @param {Object} options - Fetch options
     * @param {number} timeout - Timeout in milliseconds
     * @returns {Promise} - The fetch promise with timeout
     */
    static async fetchWithTimeout(url, options = {}, timeout = 10000) {
        try {
            return await Promise.race([
                this.fetchWithAuth(url, options),
                this.setRequestTimeout(url, timeout)
            ]);
        } finally {
            this.clearRequestTimeout(url);
        }
    }
}
