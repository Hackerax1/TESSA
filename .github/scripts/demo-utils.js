/**
 * Demo utilities for TESSA UI demo on GitHub Pages
 */
document.addEventListener('DOMContentLoaded', function() {
    // Add demo styling
    const demoStylesheet = document.createElement('link');
    demoStylesheet.rel = 'stylesheet';
    demoStylesheet.href = 'demo.css';
    document.head.appendChild(demoStylesheet);

    // Simulate loading states
    simulateLoading();

    // Handle mock form submissions
    handleFormSubmissions();

    // Add event listeners for interactive elements
    addEventListeners();

    // Load mock data
    loadMockData();
});

/**
 * Simulate loading states for UI elements
 */
function simulateLoading() {
    // Simulate loading UI components with spinners
    const loadingContainers = document.querySelectorAll('.loading-container, [data-loading="true"]');
    loadingContainers.forEach(container => {
        setTimeout(() => {
            container.classList.add('loaded');
        }, Math.random() * 1000 + 500);
    });

    // Replace real API endpoints with mock data
    const mockApi = {
        '/api/vms/status': './api/vms-status.json',
        '/api/cluster-resources': './api/cluster-resources.json'
    };

    // Override fetch to use local JSON files
    const originalFetch = window.fetch;
    window.fetch = function(url, options) {
        for (const apiEndpoint in mockApi) {
            if (url.includes(apiEndpoint)) {
                return originalFetch(mockApi[apiEndpoint], options);
            }
        }
        // For other URLs, create a mock response
        return new Promise(resolve => {
            setTimeout(() => {
                resolve({
                    json: () => Promise.resolve({
                        success: true,
                        message: 'This is a demo. No actual data is being processed.'
                    }),
                    text: () => Promise.resolve('This is a demo. No actual data is being processed.')
                });
            }, 500);
        });
    };
}

/**
 * Handle mock form submissions
 */
function handleFormSubmissions() {
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                const originalText = submitBtn.innerHTML;
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processing...';
                
                setTimeout(() => {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalText;
                    
                    // Show success message
                    const alert = document.createElement('div');
                    alert.className = 'alert alert-success mt-3';
                    alert.innerHTML = 'This is a demo. Form submission would be processed in the actual application.';
                    form.appendChild(alert);
                    
                    setTimeout(() => {
                        alert.remove();
                    }, 3000);
                }, 1500);
            }
        });
    });
}

/**
 * Add event listeners for interactive elements
 */
function addEventListeners() {
    // Chat form interaction
    const chatForm = document.getElementById('chat-form');
    const chatBody = document.getElementById('chat-body');
    const userInput = document.getElementById('user-input');
    
    if (chatForm && chatBody && userInput) {
        chatForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const query = userInput.value.trim();
            if (!query) return;
            
            // Add user message
            const userMsg = document.createElement('div');
            userMsg.className = 'message user';
            userMsg.textContent = query;
            chatBody.appendChild(userMsg);
            
            // Clear input
            userInput.value = '';
            
            // Simulate thinking
            setTimeout(() => {
                // Add system response
                const systemMsg = document.createElement('div');
                systemMsg.className = 'message system';
                systemMsg.textContent = "This is a demo. In the actual application, TESSA would respond to your query: '" + query + "'";
                chatBody.appendChild(systemMsg);
                
                // Scroll to bottom
                chatBody.scrollTop = chatBody.scrollHeight;
            }, 1000);
            
            // Scroll to bottom
            chatBody.scrollTop = chatBody.scrollHeight;
        });
    }
    
    // Modal interactions
    document.querySelectorAll('[data-bs-toggle="modal"]').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const target = this.getAttribute('data-bs-target');
            console.log(`Demo: Would open modal ${target} in the actual application`);
        });
    });
    
    // Action buttons
    document.querySelectorAll('.btn:not([type="submit"])').forEach(button => {
        if (!button.getAttribute('data-demo-handled')) {
            button.setAttribute('data-demo-handled', 'true');
            button.addEventListener('click', function(e) {
                if (!this.getAttribute('data-bs-toggle')) {
                    e.preventDefault();
                    const originalText = this.innerHTML;
                    this.disabled = true;
                    
                    if (!this.classList.contains('btn-link')) {
                        this.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>';
                    }
                    
                    setTimeout(() => {
                        this.disabled = false;
                        this.innerHTML = originalText;
                        
                        // Show toast notification
                        showToast('Action Demo', 'This button would perform an action in the actual application.');
                    }, 1000);
                }
            });
        }
    });
}

/**
 * Load mock data for UI components
 */
function loadMockData() {
    // Sample VM data
    const vmData = {
        success: true,
        vms: [
            {id: 101, name: "Web Server", status: "running", memory: 4096, cpu: 2, disk: 50.0},
            {id: 102, name: "Database Server", status: "running", memory: 8192, cpu: 4, disk: 100.0},
            {id: 103, name: "Test Environment", status: "stopped", memory: 2048, cpu: 1, disk: 25.0}
        ]
    };
    
    // Sample cluster status
    const clusterData = {
        success: true,
        status: "healthy",
        nodes: [
            {name: "node1", status: "online"},
            {name: "node2", status: "online"}
        ]
    };
    
    // Populate VM list if it exists
    const vmList = document.getElementById('vm-list');
    if (vmList) {
        let vmHtml = '';
        let runningCount = 0;
        let stoppedCount = 0;
        
        vmData.vms.forEach(vm => {
            const isRunning = vm.status === 'running';
            if (isRunning) runningCount++;
            else stoppedCount++;
            
            vmHtml += `
                <div class="list-group-item d-flex justify-content-between align-items-center">
                    <div>
                        <span class="status-indicator ${isRunning ? 'status-running' : 'status-stopped'}"></span>
                        <strong>${vm.name || 'VM ' + vm.id}</strong>
                        <span class="badge bg-secondary ms-2">${vm.id}</span>
                    </div>
                    <div class="btn-group">
                        <button class="btn btn-sm btn-outline-primary vm-action" data-action="view" data-vmid="${vm.id}">
                            <i class="bi bi-eye"></i>
                        </button>
                        <button class="btn btn-sm ${isRunning ? 'btn-outline-danger' : 'btn-outline-success'} vm-action" 
                                data-action="${isRunning ? 'stop' : 'start'}" data-vmid="${vm.id}">
                            <i class="bi ${isRunning ? 'bi-stop-fill' : 'bi-play-fill'}"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-info vm-action qr-code-btn" data-action="qrcode" data-vmid="${vm.id}" data-type="vm">
                            <i class="bi bi-qr-code"></i>
                        </button>
                    </div>
                </div>
            `;
        });
        
        vmList.innerHTML = vmHtml;
        
        // Update counters
        const runningVms = document.getElementById('running-vms');
        const stoppedVms = document.getElementById('stopped-vms');
        
        if (runningVms) runningVms.textContent = `${runningCount} Running`;
        if (stoppedVms) stoppedVms.textContent = `${stoppedCount} Stopped`;
        
        // Add event listeners to VM actions
        document.querySelectorAll('.vm-action').forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                const action = this.getAttribute('data-action');
                const vmid = this.getAttribute('data-vmid');
                
                showToast('VM Action', `Would ${action} VM ${vmid} in the actual application.`);
            });
        });
    }
    
    // Populate cluster status if it exists
    const clusterStatus = document.getElementById('cluster-status');
    const nodeList = document.getElementById('node-list');
    
    if (clusterStatus) {
        clusterStatus.textContent = clusterData.status.toUpperCase();
        clusterStatus.className = clusterData.status === 'healthy' ? 'badge bg-success' : 'badge bg-danger';
    }
    
    if (nodeList) {
        let nodesHtml = '';
        
        clusterData.nodes.forEach(node => {
            nodesHtml += `
                <div class="list-group-item d-flex justify-content-between align-items-center">
                    <span>${node.name}</span>
                    <span class="badge bg-${node.status === 'online' ? 'success' : 'danger'} ms-2">${node.status}</span>
                </div>
            `;
        });
        
        nodeList.innerHTML = nodesHtml;
    }
}

/**
 * Show a toast notification
 */
function showToast(title, message) {
    // Create toast container if it doesn't exist
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }
    
    // Create toast
    const toastId = 'toast-' + Date.now();
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.id = toastId;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="toast-header">
            <strong class="me-auto">${title}</strong>
            <small>Just now</small>
            <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
        <div class="toast-body">
            ${message}
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    // Show the toast
    // Since this is a demo without Bootstrap JS, we'll simulate it
    toast.style.display = 'block';
    toast.style.opacity = 1;
    
    setTimeout(() => {
        toast.style.opacity = 0;
        setTimeout(() => {
            toast.remove();
        }, 300);
    }, 3000);
}

// Add global functions for the demo
window.showToast = showToast;

// Add placeholder for any code that tries to access window.gridStack
window.gridStack = {
    init: () => { console.log("GridStack initialized (demo mode)"); return { on: () => {}, addWidget: () => {} }; },
    save: () => []
};

// Mock the socket connection
window.io = () => ({
    on: (event, callback) => {
        console.log(`Registered socket event listener for: ${event}`);
    }
});