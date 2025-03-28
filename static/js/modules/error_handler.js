/**
 * Error handling module for comprehensive application-wide error management
 */
export default class ErrorHandler {
    static errorListeners = [];
    static errorHistory = [];
    static maxErrorHistory = 50;
    
    /**
     * Initialize global error handlers
     */
    static initialize() {
        // Capture unhandled promise rejections
        window.addEventListener('unhandledrejection', (event) => {
            this.handleError(event.reason || 'Unhandled Promise Rejection');
        });
        
        // Capture global errors
        window.addEventListener('error', (event) => {
            this.handleError(event.error || event.message);
        });
        
        // Override console.error to capture errors
        const originalConsoleError = console.error;
        console.error = (...args) => {
            // Call original console.error
            originalConsoleError.apply(console, args);
            
            // Handle the error
            const errorMessage = args.map(arg => {
                if (arg instanceof Error) {
                    return arg.stack || arg.message;
                }
                return String(arg);
            }).join(' ');
            
            this.handleError(errorMessage, false);
        };
        
        console.log('Error handler initialized');
    }
    
    /**
     * Handle an error
     * @param {Error|string} error - The error to handle
     * @param {boolean} notify - Whether to notify listeners
     */
    static handleError(error, notify = true) {
        const errorObj = this.normalizeError(error);
        
        // Add to error history
        this.addToErrorHistory(errorObj);
        
        // Log to server if it's a significant error
        if (errorObj.level === 'error' || errorObj.level === 'fatal') {
            this.logToServer(errorObj);
        }
        
        // Notify listeners if requested
        if (notify) {
            this.notifyListeners(errorObj);
        }
        
        return errorObj;
    }
    
    /**
     * Normalize an error into a standard format
     * @param {Error|string} error - The error to normalize
     * @returns {Object} - Normalized error object
     */
    static normalizeError(error) {
        let errorObj = {
            message: '',
            stack: '',
            timestamp: new Date().toISOString(),
            level: 'error',
            code: 'UNKNOWN_ERROR',
            context: {},
            userMessage: 'An unexpected error occurred. Please try again.'
        };
        
        if (error instanceof Error) {
            errorObj.message = error.message;
            errorObj.stack = error.stack;
            errorObj.code = error.code || errorObj.code;
            errorObj.context = error.context || {};
            errorObj.userMessage = error.userMessage || errorObj.userMessage;
        } else if (typeof error === 'string') {
            errorObj.message = error;
            
            // Try to extract a more user-friendly message
            if (error.includes('NetworkError') || error.includes('Failed to fetch')) {
                errorObj.code = 'NETWORK_ERROR';
                errorObj.userMessage = 'Unable to connect to the server. Please check your internet connection.';
            } else if (error.includes('timeout')) {
                errorObj.code = 'TIMEOUT_ERROR';
                errorObj.userMessage = 'The request timed out. Please try again.';
            } else if (error.includes('401') || error.includes('Unauthorized')) {
                errorObj.code = 'AUTH_ERROR';
                errorObj.userMessage = 'Your session has expired. Please log in again.';
            } else if (error.includes('403') || error.includes('Forbidden')) {
                errorObj.code = 'PERMISSION_ERROR';
                errorObj.userMessage = 'You do not have permission to perform this action.';
            } else if (error.includes('404') || error.includes('Not Found')) {
                errorObj.code = 'NOT_FOUND_ERROR';
                errorObj.userMessage = 'The requested resource was not found.';
            } else if (error.includes('500') || error.includes('Internal Server Error')) {
                errorObj.code = 'SERVER_ERROR';
                errorObj.userMessage = 'The server encountered an error. Please try again later.';
            }
        } else if (typeof error === 'object') {
            errorObj = { ...errorObj, ...error };
        }
        
        return errorObj;
    }
    
    /**
     * Add an error to the error history
     * @param {Object} errorObj - The error object to add
     */
    static addToErrorHistory(errorObj) {
        this.errorHistory.unshift(errorObj);
        
        // Limit the size of the error history
        if (this.errorHistory.length > this.maxErrorHistory) {
            this.errorHistory.pop();
        }
    }
    
    /**
     * Log an error to the server
     * @param {Object} errorObj - The error object to log
     */
    static async logToServer(errorObj) {
        try {
            // Add browser and user information
            const errorData = {
                ...errorObj,
                userAgent: navigator.userAgent,
                url: window.location.href,
                userId: localStorage.getItem('user_id') || 'anonymous'
            };
            
            // Send to server
            await fetch('/api/log/error', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify(errorData)
            });
        } catch (e) {
            // Don't do anything if logging fails
            console.warn('Failed to log error to server:', e);
        }
    }
    
    /**
     * Add an error listener
     * @param {Function} listener - The listener function
     */
    static addListener(listener) {
        if (typeof listener === 'function' && !this.errorListeners.includes(listener)) {
            this.errorListeners.push(listener);
        }
    }
    
    /**
     * Remove an error listener
     * @param {Function} listener - The listener function to remove
     */
    static removeListener(listener) {
        const index = this.errorListeners.indexOf(listener);
        if (index !== -1) {
            this.errorListeners.splice(index, 1);
        }
    }
    
    /**
     * Notify all listeners of an error
     * @param {Object} errorObj - The error object
     */
    static notifyListeners(errorObj) {
        this.errorListeners.forEach(listener => {
            try {
                listener(errorObj);
            } catch (e) {
                console.warn('Error in error listener:', e);
            }
        });
    }
    
    /**
     * Show an error to the user
     * @param {Error|string} error - The error to show
     * @param {string} title - Optional title for the error
     */
    static showUserError(error, title = 'Error') {
        const errorObj = this.handleError(error, false);
        
        // Check if UI module is available
        if (window.UI && typeof window.UI.showError === 'function') {
            window.UI.showError(errorObj.userMessage, title);
        } else {
            // Fallback to alert if UI module is not available
            alert(`${title}: ${errorObj.userMessage}`);
        }
    }
    
    /**
     * Create a custom error with additional context
     * @param {string} message - The error message
     * @param {string} code - The error code
     * @param {string} userMessage - User-friendly message
     * @param {Object} context - Additional context
     * @returns {Error} - The custom error
     */
    static createError(message, code = 'CUSTOM_ERROR', userMessage = null, context = {}) {
        const error = new Error(message);
        error.code = code;
        error.userMessage = userMessage || message;
        error.context = context;
        return error;
    }
    
    /**
     * Get the error history
     * @returns {Array} - The error history
     */
    static getErrorHistory() {
        return [...this.errorHistory];
    }
    
    /**
     * Clear the error history
     */
    static clearErrorHistory() {
        this.errorHistory = [];
    }
}
