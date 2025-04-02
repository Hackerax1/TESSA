/**
 * Mobile Notifications module - Handles mobile-specific notification features
 * Works alongside the main Notifications module
 */
import API from './api.js';

export default class MobileNotifications {
    /**
     * Initialize mobile notifications
     */
    constructor() {
        this.notificationHistory = [];
        this.notificationContainer = document.getElementById('notifications-list');
        this.notificationBadge = null;
        this.unreadCount = 0;
        
        // Create notification badge if it doesn't exist
        this.createNotificationBadge();
        
        // Load notification history from local storage
        this.loadNotificationHistoryFromStorage();
        
        // Listen for new notifications
        this.setupNotificationListeners();
    }
    
    /**
     * Initialize the mobile notifications module
     */
    initialize() {
        // Update notification badge
        this.updateNotificationBadge();
        
        // Set up swipe actions for notifications
        this.setupSwipeActions();
    }
    
    /**
     * Create notification badge for the bottom navigation
     */
    createNotificationBadge() {
        const notificationNavItem = document.querySelector('.bottom-nav-item[href="/mobile/notifications"]');
        if (notificationNavItem) {
            // Check if badge already exists
            let badge = notificationNavItem.querySelector('.notification-badge');
            if (!badge) {
                badge = document.createElement('span');
                badge.className = 'notification-badge';
                badge.style.display = 'none';
                notificationNavItem.appendChild(badge);
            }
            this.notificationBadge = badge;
        }
    }
    
    /**
     * Set up listeners for new notifications
     */
    setupNotificationListeners() {
        // Listen for messages from service worker
        if (navigator.serviceWorker) {
            navigator.serviceWorker.addEventListener('message', (event) => {
                if (event.data && event.data.type === 'PUSH_NOTIFICATION') {
                    this.addNotificationToHistory({
                        id: this.generateNotificationId(),
                        title: event.data.title,
                        message: event.data.message,
                        data: event.data.data || {},
                        timestamp: Date.now(),
                        read: false
                    });
                }
            });
        }
        
        // Listen for custom notification events
        window.addEventListener('notification', (event) => {
            if (event.detail) {
                this.addNotificationToHistory({
                    id: this.generateNotificationId(),
                    title: event.detail.title,
                    message: event.detail.message,
                    data: event.detail.data || {},
                    timestamp: Date.now(),
                    read: false
                });
            }
        });
    }
    
    /**
     * Generate a unique notification ID
     * @returns {string} Unique notification ID
     */
    generateNotificationId() {
        return 'notification_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    /**
     * Load notification history from local storage
     */
    loadNotificationHistoryFromStorage() {
        try {
            const storedHistory = localStorage.getItem('notification_history');
            if (storedHistory) {
                this.notificationHistory = JSON.parse(storedHistory);
                
                // Count unread notifications
                this.unreadCount = this.notificationHistory.filter(notification => !notification.read).length;
            }
        } catch (error) {
            console.error('Error loading notification history from storage:', error);
            this.notificationHistory = [];
            this.unreadCount = 0;
        }
    }
    
    /**
     * Save notification history to local storage
     */
    saveNotificationHistoryToStorage() {
        try {
            localStorage.setItem('notification_history', JSON.stringify(this.notificationHistory));
        } catch (error) {
            console.error('Error saving notification history to storage:', error);
        }
    }
    
    /**
     * Add a notification to history
     * @param {Object} notification - Notification object
     */
    addNotificationToHistory(notification) {
        // Add to beginning of array
        this.notificationHistory.unshift(notification);
        
        // Limit history to 50 notifications
        if (this.notificationHistory.length > 50) {
            this.notificationHistory = this.notificationHistory.slice(0, 50);
        }
        
        // Save to storage
        this.saveNotificationHistoryToStorage();
        
        // Update UI
        this.renderNotificationHistory();
        
        // Update unread count
        if (!notification.read) {
            this.unreadCount++;
            this.updateNotificationBadge();
        }
    }
    
    /**
     * Render notification history in the UI
     */
    renderNotificationHistory() {
        if (!this.notificationContainer) return;
        
        // Clear container
        this.notificationContainer.innerHTML = '';
        
        // If no notifications, show empty state
        if (this.notificationHistory.length === 0) {
            this.notificationContainer.innerHTML = `
                <li class="notification-item text-center py-4">
                    <i class="bi bi-bell-slash fs-3 d-block mb-2 text-muted"></i>
                    <span class="text-muted">No notifications yet</span>
                </li>
            `;
            return;
        }
        
        // Render each notification
        this.notificationHistory.forEach(notification => {
            const notificationItem = document.createElement('li');
            notificationItem.className = 'notification-item swipe-container';
            if (!notification.read) {
                notificationItem.classList.add('unread');
            }
            
            // Create swipe item
            const swipeItem = document.createElement('div');
            swipeItem.className = 'swipe-item';
            
            // Format timestamp
            const timestamp = new Date(notification.timestamp);
            const formattedTime = this.formatNotificationTime(timestamp);
            
            // Create notification content
            swipeItem.innerHTML = `
                <div class="d-flex align-items-start" data-bs-toggle="modal" data-bs-target="#notificationDetailModal" data-notification-id="${notification.id}">
                    <div class="flex-grow-1">
                        <div class="fw-bold">${notification.title}</div>
                        <div class="text-truncate">${notification.message}</div>
                        <div class="notification-time">${formattedTime}</div>
                    </div>
                    ${!notification.read ? '<span class="notification-dot"></span>' : ''}
                </div>
            `;
            
            // Create swipe actions
            const swipeActions = document.createElement('div');
            swipeActions.className = 'swipe-actions';
            
            // Mark as read/unread action
            const readAction = document.createElement('div');
            readAction.className = `swipe-action ${notification.read ? 'edit' : 'primary'}`;
            readAction.innerHTML = `<i class="bi bi-${notification.read ? 'envelope' : 'check2-all'}"></i>`;
            readAction.addEventListener('click', () => {
                if (notification.read) {
                    this.markNotificationAsUnread(notification.id);
                } else {
                    this.markNotificationAsRead(notification.id);
                }
            });
            
            // Delete action
            const deleteAction = document.createElement('div');
            deleteAction.className = 'swipe-action delete';
            deleteAction.innerHTML = '<i class="bi bi-trash"></i>';
            deleteAction.addEventListener('click', () => {
                this.removeNotification(notification.id);
            });
            
            // Add actions to swipe actions
            swipeActions.appendChild(readAction);
            swipeActions.appendChild(deleteAction);
            
            // Add swipe item and actions to container
            notificationItem.appendChild(swipeItem);
            notificationItem.appendChild(swipeActions);
            
            // Add to notification container
            this.notificationContainer.appendChild(notificationItem);
        });
    }
    
    /**
     * Format notification time relative to current time
     * @param {Date} timestamp - Notification timestamp
     * @returns {string} Formatted time string
     */
    formatNotificationTime(timestamp) {
        const now = new Date();
        const diffMs = now - timestamp;
        const diffSec = Math.floor(diffMs / 1000);
        const diffMin = Math.floor(diffSec / 60);
        const diffHour = Math.floor(diffMin / 60);
        const diffDay = Math.floor(diffHour / 24);
        
        if (diffSec < 60) {
            return 'Just now';
        } else if (diffMin < 60) {
            return `${diffMin}m ago`;
        } else if (diffHour < 24) {
            return `${diffHour}h ago`;
        } else if (diffDay < 7) {
            return `${diffDay}d ago`;
        } else {
            // Format as date
            return timestamp.toLocaleDateString();
        }
    }
    
    /**
     * Update notification badge with unread count
     */
    updateNotificationBadge() {
        if (!this.notificationBadge) return;
        
        if (this.unreadCount > 0) {
            this.notificationBadge.textContent = this.unreadCount > 9 ? '9+' : this.unreadCount;
            this.notificationBadge.style.display = 'flex';
        } else {
            this.notificationBadge.style.display = 'none';
        }
    }
    
    /**
     * Mark a notification as read
     * @param {string} notificationId - Notification ID
     */
    markNotificationAsRead(notificationId) {
        const index = this.notificationHistory.findIndex(notification => notification.id === notificationId);
        if (index !== -1 && !this.notificationHistory[index].read) {
            this.notificationHistory[index].read = true;
            this.unreadCount = Math.max(0, this.unreadCount - 1);
            
            // Save to storage
            this.saveNotificationHistoryToStorage();
            
            // Update UI
            this.renderNotificationHistory();
            this.updateNotificationBadge();
        }
    }
    
    /**
     * Mark a notification as unread
     * @param {string} notificationId - Notification ID
     */
    markNotificationAsUnread(notificationId) {
        const index = this.notificationHistory.findIndex(notification => notification.id === notificationId);
        if (index !== -1 && this.notificationHistory[index].read) {
            this.notificationHistory[index].read = false;
            this.unreadCount++;
            
            // Save to storage
            this.saveNotificationHistoryToStorage();
            
            // Update UI
            this.renderNotificationHistory();
            this.updateNotificationBadge();
        }
    }
    
    /**
     * Mark all notifications as read
     */
    markAllNotificationsAsRead() {
        let changed = false;
        
        this.notificationHistory.forEach(notification => {
            if (!notification.read) {
                notification.read = true;
                changed = true;
            }
        });
        
        if (changed) {
            this.unreadCount = 0;
            
            // Save to storage
            this.saveNotificationHistoryToStorage();
            
            // Update UI
            this.renderNotificationHistory();
            this.updateNotificationBadge();
        }
    }
    
    /**
     * Remove a notification from history
     * @param {string} notificationId - Notification ID
     */
    removeNotification(notificationId) {
        const index = this.notificationHistory.findIndex(notification => notification.id === notificationId);
        if (index !== -1) {
            // Update unread count if needed
            if (!this.notificationHistory[index].read) {
                this.unreadCount = Math.max(0, this.unreadCount - 1);
            }
            
            // Remove notification
            this.notificationHistory.splice(index, 1);
            
            // Save to storage
            this.saveNotificationHistoryToStorage();
            
            // Update UI
            this.renderNotificationHistory();
            this.updateNotificationBadge();
        }
    }
    
    /**
     * Clear all notifications
     */
    clearAllNotifications() {
        this.notificationHistory = [];
        this.unreadCount = 0;
        
        // Save to storage
        this.saveNotificationHistoryToStorage();
        
        // Update UI
        this.renderNotificationHistory();
        this.updateNotificationBadge();
    }
    
    /**
     * Get a notification by ID
     * @param {string} notificationId - Notification ID
     * @returns {Object|null} Notification object or null if not found
     */
    getNotificationById(notificationId) {
        return this.notificationHistory.find(notification => notification.id === notificationId) || null;
    }
    
    /**
     * Set up swipe actions for notifications
     */
    setupSwipeActions() {
        // This is handled by the Mobile class in mobile.js
        // We just need to make sure our notifications have the right classes
    }
    
    /**
     * Load notification history from server
     * @returns {Promise<boolean>} True if successful
     */
    async loadNotificationHistory() {
        try {
            const userId = localStorage.getItem('user_id') || 'default_user';
            const response = await API.fetchWithAuth(`/api/notifications/${userId}`);
            
            if (response.ok) {
                const data = await response.json();
                
                if (data.success && data.notifications) {
                    // Merge server notifications with local ones
                    // Server notifications take precedence
                    const serverNotifications = data.notifications.map(notification => ({
                        ...notification,
                        id: notification.id || this.generateNotificationId()
                    }));
                    
                    // Filter out local notifications that exist on server
                    const serverIds = serverNotifications.map(n => n.id);
                    const localOnlyNotifications = this.notificationHistory.filter(
                        n => !serverIds.includes(n.id) && !n.synced
                    );
                    
                    // Combine and sort by timestamp
                    this.notificationHistory = [...serverNotifications, ...localOnlyNotifications]
                        .sort((a, b) => b.timestamp - a.timestamp);
                    
                    // Limit to 50
                    if (this.notificationHistory.length > 50) {
                        this.notificationHistory = this.notificationHistory.slice(0, 50);
                    }
                    
                    // Count unread
                    this.unreadCount = this.notificationHistory.filter(n => !n.read).length;
                    
                    // Save to storage
                    this.saveNotificationHistoryToStorage();
                    
                    // Update UI
                    this.renderNotificationHistory();
                    this.updateNotificationBadge();
                    
                    return true;
                }
            }
            
            return false;
        } catch (error) {
            console.error('Error loading notification history from server:', error);
            return false;
        }
    }
}