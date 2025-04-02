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
        
        // Initialize touch gestures if on mobile
        if (this.isMobile) {
            this.initTouchGestures();
        }
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
        
        // Initialize bottom navigation
        this.initBottomNavigation();
        
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
        
        // Add active state for touch feedback
        this.addTouchFeedback();
    }
    
    /**
     * Add touch feedback to interactive elements
     */
    addTouchFeedback() {
        const interactiveElements = document.querySelectorAll(
            'button, .btn, .nav-link, .list-group-item, .card-header, .vm-card, .service-card'
        );
        
        interactiveElements.forEach(element => {
            element.addEventListener('touchstart', () => {
                element.classList.add('touch-active');
            }, { passive: true });
            
            element.addEventListener('touchend', () => {
                element.classList.remove('touch-active');
            }, { passive: true });
            
            element.addEventListener('touchcancel', () => {
                element.classList.remove('touch-active');
            }, { passive: true });
        });
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
        
        // Convert tables to mobile-friendly format
        this.convertTablesToMobile();
    }
    
    /**
     * Convert standard tables to mobile-friendly format
     */
    convertTablesToMobile() {
        document.querySelectorAll('table:not(.no-mobile-convert)').forEach(table => {
            table.classList.add('table-responsive-mobile');
            
            // For very complex tables, create a card-based view
            if (table.querySelectorAll('th').length > 4) {
                this.convertTableToCards(table);
            }
        });
    }
    
    /**
     * Convert a complex table to card-based view for mobile
     * @param {HTMLElement} table - The table to convert
     */
    convertTableToCards(table) {
        // Get table headers
        const headers = Array.from(table.querySelectorAll('thead th')).map(th => th.textContent.trim());
        
        // Create container for cards
        const cardContainer = document.createElement('div');
        cardContainer.className = 'mobile-card-container d-md-none';
        
        // Get table rows
        const rows = table.querySelectorAll('tbody tr');
        
        // Create a card for each row
        rows.forEach(row => {
            const card = document.createElement('div');
            card.className = 'card mobile-card mb-3';
            
            const cardBody = document.createElement('div');
            cardBody.className = 'card-body';
            
            // Get cells from row
            const cells = row.querySelectorAll('td');
            
            // Create content for card
            cells.forEach((cell, index) => {
                if (index < headers.length) {
                    const item = document.createElement('div');
                    item.className = 'mb-2';
                    
                    const label = document.createElement('strong');
                    label.textContent = headers[index] + ': ';
                    
                    item.appendChild(label);
                    item.appendChild(document.createTextNode(cell.textContent.trim()));
                    
                    cardBody.appendChild(item);
                }
            });
            
            card.appendChild(cardBody);
            cardContainer.appendChild(card);
        });
        
        // Insert card container after table
        table.parentNode.insertBefore(cardContainer, table.nextSibling);
        
        // Hide table on mobile
        table.classList.add('d-none', 'd-md-table');
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
     * Initialize bottom navigation
     */
    initBottomNavigation() {
        const bottomNav = document.querySelector('.bottom-nav');
        if (!bottomNav) return;
        
        // Add active class to current page
        const currentPath = window.location.pathname;
        bottomNav.querySelectorAll('.bottom-nav-item').forEach(item => {
            const href = item.getAttribute('href');
            if (href && href !== '#' && currentPath === href) {
                item.classList.add('active');
            }
            
            // Add ripple effect to bottom nav items
            this.addRippleEffect(item);
        });
        
        // Adjust main content padding to account for bottom nav
        const mainContent = document.querySelector('.main-content');
        if (mainContent) {
            mainContent.style.paddingBottom = `${bottomNav.offsetHeight + 8}px`;
        }
    }
    
    /**
     * Add ripple effect to element
     * @param {HTMLElement} element - Element to add ripple effect to
     */
    addRippleEffect(element) {
        element.addEventListener('touchstart', (e) => {
            const rect = element.getBoundingClientRect();
            const x = e.touches[0].clientX - rect.left;
            const y = e.touches[0].clientY - rect.top;
            
            const ripple = document.createElement('span');
            ripple.className = 'ripple-effect';
            ripple.style.left = `${x}px`;
            ripple.style.top = `${y}px`;
            
            element.appendChild(ripple);
            
            setTimeout(() => {
                ripple.remove();
            }, 600);
        }, { passive: true });
    }
    
    /**
     * Initialize touch gestures for mobile
     */
    initTouchGestures() {
        // Initialize swipe containers
        this.initSwipeContainers();
        
        // Initialize pull-to-refresh
        this.initPullToRefresh();
        
        // Add double-tap zoom prevention
        this.preventDoubleTapZoom();
    }
    
    /**
     * Initialize swipe containers for mobile
     */
    initSwipeContainers() {
        document.querySelectorAll('.swipe-container').forEach(container => {
            const swipeItem = container.querySelector('.swipe-item');
            const swipeActions = container.querySelector('.swipe-actions');
            
            if (!swipeItem || !swipeActions) return;
            
            let startX = 0;
            let currentX = 0;
            let isOpen = false;
            
            // Touch start event
            swipeItem.addEventListener('touchstart', (e) => {
                startX = e.touches[0].clientX;
                currentX = startX;
                
                // Reset transition during touch
                swipeItem.style.transition = 'none';
            }, { passive: true });
            
            // Touch move event
            swipeItem.addEventListener('touchmove', (e) => {
                currentX = e.touches[0].clientX;
                const diffX = currentX - startX;
                
                // Only allow swiping left (negative diffX)
                if (diffX < 0 || isOpen) {
                    const translateX = isOpen ? Math.max(-swipeActions.offsetWidth, diffX) : Math.min(0, diffX);
                    swipeItem.style.transform = `translateX(${translateX}px)`;
                }
            }, { passive: true });
            
            // Touch end event
            swipeItem.addEventListener('touchend', () => {
                swipeItem.style.transition = 'transform 0.3s ease';
                
                const diffX = currentX - startX;
                
                // If swiped more than 40% of the actions width or was already open
                if (isOpen && diffX < 0 && Math.abs(diffX) < swipeActions.offsetWidth * 0.4) {
                    // Keep open
                    swipeItem.style.transform = `translateX(-${swipeActions.offsetWidth}px)`;
                } else if (isOpen || (!isOpen && diffX < -swipeActions.offsetWidth * 0.4)) {
                    // Open actions
                    swipeItem.style.transform = `translateX(-${swipeActions.offsetWidth}px)`;
                    isOpen = true;
                } else {
                    // Close actions
                    swipeItem.style.transform = 'translateX(0)';
                    isOpen = false;
                }
            });
            
            // Add click event to close when clicking elsewhere
            document.addEventListener('click', (e) => {
                if (isOpen && !container.contains(e.target)) {
                    swipeItem.style.transition = 'transform 0.3s ease';
                    swipeItem.style.transform = 'translateX(0)';
                    isOpen = false;
                }
            });
            
            // Add click handlers to action buttons
            swipeActions.querySelectorAll('.swipe-action').forEach(action => {
                action.addEventListener('click', () => {
                    // Close the swipe after action
                    setTimeout(() => {
                        swipeItem.style.transition = 'transform 0.3s ease';
                        swipeItem.style.transform = 'translateX(0)';
                        isOpen = false;
                    }, 300);
                });
            });
        });
    }
    
    /**
     * Initialize pull-to-refresh functionality
     */
    initPullToRefresh() {
        const pullContainers = document.querySelectorAll('.pull-to-refresh');
        
        pullContainers.forEach(container => {
            let startY = 0;
            let currentY = 0;
            let isPulling = false;
            let threshold = 80; // Minimum pull distance to trigger refresh
            
            // Create pull indicator if it doesn't exist
            let indicator = container.querySelector('.pull-indicator');
            if (!indicator) {
                indicator = document.createElement('div');
                indicator.className = 'pull-indicator';
                indicator.innerHTML = '<i class="bi bi-arrow-down"></i> Pull to refresh';
                container.prepend(indicator);
            }
            
            // Touch start event
            container.addEventListener('touchstart', (e) => {
                // Only enable pull if at top of container
                if (container.scrollTop <= 0) {
                    startY = e.touches[0].clientY;
                    currentY = startY;
                    isPulling = true;
                }
            }, { passive: true });
            
            // Touch move event
            container.addEventListener('touchmove', (e) => {
                if (!isPulling) return;
                
                currentY = e.touches[0].clientY;
                const diffY = currentY - startY;
                
                // Only allow pulling down
                if (diffY > 0) {
                    // Calculate pull distance with resistance
                    const pullDistance = Math.min(diffY * 0.5, threshold * 1.5);
                    
                    // Update indicator position
                    indicator.style.top = `${pullDistance - 50}px`;
                    
                    // Update indicator text
                    if (pullDistance > threshold) {
                        indicator.innerHTML = '<i class="bi bi-arrow-up"></i> Release to refresh';
                    } else {
                        indicator.innerHTML = '<i class="bi bi-arrow-down"></i> Pull to refresh';
                    }
                    
                    // Prevent default scrolling
                    e.preventDefault();
                }
            }, { passive: false });
            
            // Touch end event
            container.addEventListener('touchend', () => {
                if (!isPulling) return;
                
                const diffY = currentY - startY;
                
                // Reset indicator with transition
                indicator.style.transition = 'top 0.3s ease';
                indicator.style.top = '-50px';
                
                // If pulled enough, trigger refresh
                if (diffY > threshold) {
                    indicator.innerHTML = '<i class="bi bi-arrow-repeat spin"></i> Refreshing...';
                    
                    // Dispatch custom event for refresh
                    const refreshEvent = new CustomEvent('pullrefresh');
                    container.dispatchEvent(refreshEvent);
                    
                    // Reset after animation
                    setTimeout(() => {
                        indicator.style.transition = 'none';
                    }, 300);
                }
                
                isPulling = false;
            });
            
            // Listen for refresh complete event
            container.addEventListener('refreshcomplete', () => {
                indicator.innerHTML = '<i class="bi bi-check-circle"></i> Updated';
                
                // Hide indicator after showing success
                setTimeout(() => {
                    indicator.style.top = '-50px';
                }, 1000);
            });
        });
    }
    
    /**
     * Prevent double-tap zoom on mobile
     */
    preventDoubleTapZoom() {
        let lastTouchEnd = 0;
        document.addEventListener('touchend', (e) => {
            const now = Date.now();
            if (now - lastTouchEnd < 300) {
                e.preventDefault();
            }
            lastTouchEnd = now;
        }, { passive: false });
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
                this.initTouchGestures();
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
        
        // Remove mobile card containers
        document.querySelectorAll('.mobile-card-container').forEach(container => {
            container.remove();
        });
        
        // Show tables that were hidden on mobile
        document.querySelectorAll('table.d-none.d-md-table').forEach(table => {
            table.classList.remove('d-none');
        });
        
        console.log('Mobile optimizations removed');
    }
}
