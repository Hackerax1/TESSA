/**
 * Mobile module - Handles mobile device detection and UI optimization
 */
export default class Mobile {
    /**
     * Initialize mobile detection and optimization
     */
    constructor() {
        this.isMobile = this.detectMobile();
        this.applyMobileOptimizations();
        
        // Make mobile detection available globally
        window.isMobile = this.isMobile;
        
        // Handle orientation changes
        window.addEventListener('orientationchange', () => {
            this.handleOrientationChange();
        });
        
        // Handle resize events for responsive adjustments
        window.addEventListener('resize', () => {
            this.handleResize();
        });
    }
    
    /**
     * Detect if the current device is mobile
     * @returns {boolean} True if the device is mobile
     */
    detectMobile() {
        // Check if the user agent contains mobile keywords
        const userAgent = navigator.userAgent || navigator.vendor || window.opera;
        const mobileRegex = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i;
        
        // Also check screen width as a fallback
        const isMobileWidth = window.innerWidth <= 768;
        
        return mobileRegex.test(userAgent) || isMobileWidth;
    }
    
    /**
     * Apply mobile-specific optimizations to the UI
     */
    applyMobileOptimizations() {
        if (!this.isMobile) return;
        
        // Add mobile class to body for CSS targeting
        document.body.classList.add('mobile-device');
        
        // Load mobile-specific stylesheet
        this.loadMobileStylesheet();
        
        // Adjust UI elements for touch
        this.optimizeForTouch();
        
        // Set viewport meta tag for proper scaling
        this.setMobileViewport();
        
        console.log('Mobile optimizations applied');
    }
    
    /**
     * Load the mobile-specific stylesheet
     */
    loadMobileStylesheet() {
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = '/static/css/mobile.css';
        link.id = 'mobile-stylesheet';
        document.head.appendChild(link);
    }
    
    /**
     * Optimize UI elements for touch interaction
     */
    optimizeForTouch() {
        // Increase button sizes for touch targets
        document.querySelectorAll('.btn-sm').forEach(button => {
            button.classList.remove('btn-sm');
        });
        
        // Add extra padding to clickable elements
        document.querySelectorAll('.nav-link, .list-group-item, .card-header').forEach(element => {
            element.classList.add('touch-target');
        });
        
        // Simplify complex UI components
        this.simplifyUIForMobile();
    }
    
    /**
     * Simplify complex UI components for mobile
     */
    simplifyUIForMobile() {
        // Convert multi-column layouts to single column
        document.querySelectorAll('.row').forEach(row => {
            row.classList.add('mobile-stack');
        });
        
        // Simplify navigation
        const navbar = document.querySelector('.navbar');
        if (navbar) {
            navbar.classList.add('mobile-nav');
        }
        
        // Simplify dashboards
        const dashboard = document.querySelector('.dashboard-container');
        if (dashboard) {
            dashboard.classList.add('mobile-dashboard');
        }
    }
    
    /**
     * Set the viewport meta tag for mobile devices
     */
    setMobileViewport() {
        let viewport = document.querySelector('meta[name="viewport"]');
        if (!viewport) {
            viewport = document.createElement('meta');
            viewport.name = 'viewport';
            document.head.appendChild(viewport);
        }
        viewport.content = 'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no';
    }
    
    /**
     * Handle device orientation changes
     */
    handleOrientationChange() {
        console.log('Orientation changed');
        
        // Adjust UI based on new orientation
        const isLandscape = window.orientation === 90 || window.orientation === -90;
        document.body.classList.toggle('landscape', isLandscape);
        document.body.classList.toggle('portrait', !isLandscape);
        
        // Trigger resize event to adjust layouts
        window.dispatchEvent(new Event('resize'));
    }
    
    /**
     * Handle window resize events
     */
    handleResize() {
        // Update mobile detection on resize
        const wasMobile = this.isMobile;
        this.isMobile = this.detectMobile();
        
        // If mobile status changed, apply or remove optimizations
        if (wasMobile !== this.isMobile) {
            if (this.isMobile) {
                this.applyMobileOptimizations();
            } else {
                this.removeMobileOptimizations();
            }
        }
    }
    
    /**
     * Remove mobile optimizations when switching to desktop
     */
    removeMobileOptimizations() {
        document.body.classList.remove('mobile-device', 'landscape', 'portrait');
        
        // Remove mobile stylesheet
        const mobileStylesheet = document.getElementById('mobile-stylesheet');
        if (mobileStylesheet) {
            mobileStylesheet.remove();
        }
        
        // Remove touch optimizations
        document.querySelectorAll('.touch-target').forEach(element => {
            element.classList.remove('touch-target');
        });
        
        // Restore multi-column layouts
        document.querySelectorAll('.mobile-stack').forEach(element => {
            element.classList.remove('mobile-stack');
        });
        
        // Restore navigation
        const navbar = document.querySelector('.mobile-nav');
        if (navbar) {
            navbar.classList.remove('mobile-nav');
        }
        
        // Restore dashboards
        const dashboard = document.querySelector('.mobile-dashboard');
        if (dashboard) {
            dashboard.classList.remove('mobile-dashboard');
        }
        
        console.log('Mobile optimizations removed');
    }
}
