/**
 * GPU Passthrough Optimization Assistant Module
 * Provides UI components for GPU passthrough detection, configuration, and optimization
 */

import { showToast } from './notifications.js';
import { apiRequest } from './api.js';

export class GPUPassthroughAssistant {
    constructor() {
        this.gpuContainer = document.getElementById('gpu-passthrough-container');
        this.detectedGPUs = [];
        this.compatibilityInfo = null;
        this.selectedNode = null;
        this.selectedVM = null;
    }

    /**
     * Initialize the GPU passthrough assistant
     */
    async init() {
        // Set up event listeners
        document.addEventListener('click', (event) => {
            if (event.target.matches('.detect-gpus-btn')) {
                const node = event.target.dataset.node || this.selectedNode;
                this.detectGPUs(node);
            } else if (event.target.matches('.check-compatibility-btn')) {
                const node = event.target.dataset.node || this.selectedNode;
                this.checkCompatibility(node);
            } else if (event.target.matches('.get-recommendations-btn')) {
                const node = event.target.dataset.node || this.selectedNode;
                const vmid = event.target.dataset.vmid || this.selectedVM;
                this.getRecommendations(node, vmid);
            } else if (event.target.matches('.apply-optimization-btn')) {
                const node = event.target.dataset.node || this.selectedNode;
                const vmid = event.target.dataset.vmid || this.selectedVM;
                const optimization = event.target.dataset.optimization;
                this.applyOptimization(node, vmid, [optimization]);
            } else if (event.target.matches('.configure-gpu-btn')) {
                const node = event.target.dataset.node || this.selectedNode;
                const vmid = event.target.dataset.vmid || this.selectedVM;
                const gpuId = event.target.dataset.gpuId;
                this.configureGPUPassthrough(node, vmid, gpuId);
            }
        });

        // Initialize GPU container if it exists
        if (this.gpuContainer) {
            this.renderInitialView();
        }
    }

    /**
     * Render initial view
     */
    renderInitialView() {
        if (!this.gpuContainer) return;

        this.gpuContainer.innerHTML = `
            <div class="card">
                <div class="card-header">
                    <h5>GPU Passthrough Optimization Assistant</h5>
                </div>
                <div class="card-body">
                    <div class="row mb-4">
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="node-select" class="form-label">Node</label>
                                <select class="form-select" id="node-select">
                                    <option value="">Loading nodes...</option>
                                </select>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="mb-3">
                                <label for="vm-select" class="form-label">Virtual Machine</label>
                                <select class="form-select" id="vm-select" disabled>
                                    <option value="">Select a node first</option>
                                </select>
                            </div>
                        </div>
                    </div>
                    <div class="d-grid gap-2 d-md-flex justify-content-md-start mb-4">
                        <button class="btn btn-primary detect-gpus-btn">
                            <i class="fas fa-search"></i> Detect GPUs
                        </button>
                        <button class="btn btn-info check-compatibility-btn">
                            <i class="fas fa-check-circle"></i> Check Compatibility
                        </button>
                        <button class="btn btn-success get-recommendations-btn" disabled>
                            <i class="fas fa-lightbulb"></i> Get Recommendations
                        </button>
                    </div>
                    <div id="gpu-results" class="mt-4"></div>
                </div>
            </div>
        `;

        // Load nodes
        this.loadNodes();

        // Set up node and VM selection
        const nodeSelect = document.getElementById('node-select');
        const vmSelect = document.getElementById('vm-select');

        if (nodeSelect) {
            nodeSelect.addEventListener('change', () => {
                this.selectedNode = nodeSelect.value;
                if (this.selectedNode) {
                    this.loadVMs(this.selectedNode);
                    vmSelect.disabled = false;
                } else {
                    vmSelect.disabled = true;
                    vmSelect.innerHTML = '<option value="">Select a node first</option>';
                }
            });
        }

        if (vmSelect) {
            vmSelect.addEventListener('change', () => {
                this.selectedVM = vmSelect.value;
                const recommendBtn = document.querySelector('.get-recommendations-btn');
                if (recommendBtn) {
                    recommendBtn.disabled = !this.selectedVM;
                }
            });
        }
    }

    /**
     * Load available nodes
     */
    async loadNodes() {
        try {
            const response = await apiRequest('GET', '/api/nodes');
            const nodeSelect = document.getElementById('node-select');
            
            if (nodeSelect && response && response.success) {
                nodeSelect.innerHTML = '<option value="">Select a node</option>';
                
                response.data.forEach(node => {
                    const option = document.createElement('option');
                    option.value = node.node;
                    option.textContent = node.node;
                    nodeSelect.appendChild(option);
                });
            }
        } catch (error) {
            console.error('Error loading nodes:', error);
            showToast('Error loading nodes', 'error');
        }
    }

    /**
     * Load VMs for a node
     * @param {string} node - Node name
     */
    async loadVMs(node) {
        try {
            const response = await apiRequest('GET', `/api/nodes/${node}/qemu`);
            const vmSelect = document.getElementById('vm-select');
            
            if (vmSelect && response && response.success) {
                vmSelect.innerHTML = '<option value="">Select a VM</option>';
                
                response.data.forEach(vm => {
                    const option = document.createElement('option');
                    option.value = vm.vmid;
                    option.textContent = `${vm.name || 'VM ' + vm.vmid} (${vm.vmid})`;
                    vmSelect.appendChild(option);
                });
            }
        } catch (error) {
            console.error('Error loading VMs:', error);
            showToast('Error loading VMs', 'error');
        }
    }

    /**
     * Detect GPUs on a node
     * @param {string} node - Node name
     */
    async detectGPUs(node) {
        if (!node) {
            showToast('Please select a node first', 'warning');
            return;
        }

        try {
            showToast('Detecting GPUs...', 'info');
            
            const response = await apiRequest('GET', `/api/gpu/detect?node=${node}`);
            
            if (response && response.success) {
                this.detectedGPUs = response.gpus;
                this.renderGPUResults(response);
                showToast(`Detected ${response.gpus.length} GPUs`, 'success');
            } else {
                showToast(response.message || 'Failed to detect GPUs', 'error');
            }
        } catch (error) {
            console.error('Error detecting GPUs:', error);
            showToast('Error detecting GPUs', 'error');
        }
    }

    /**
     * Check GPU passthrough compatibility
     * @param {string} node - Node name
     */
    async checkCompatibility(node) {
        if (!node) {
            showToast('Please select a node first', 'warning');
            return;
        }

        try {
            showToast('Checking compatibility...', 'info');
            
            const response = await apiRequest('GET', `/api/gpu/compatibility?node=${node}`);
            
            if (response && response.success) {
                this.compatibilityInfo = response.compatibility;
                this.renderCompatibilityResults(response);
                
                if (response.compatibility.compatible) {
                    showToast('System is compatible with GPU passthrough', 'success');
                } else {
                    showToast('System needs configuration for GPU passthrough', 'warning');
                }
            } else {
                showToast(response.message || 'Failed to check compatibility', 'error');
            }
        } catch (error) {
            console.error('Error checking compatibility:', error);
            showToast('Error checking compatibility', 'error');
        }
    }

    /**
     * Get optimization recommendations
     * @param {string} node - Node name
     * @param {string} vmid - VM ID
     */
    async getRecommendations(node, vmid) {
        if (!node || !vmid) {
            showToast('Please select a node and VM first', 'warning');
            return;
        }

        try {
            showToast('Getting recommendations...', 'info');
            
            const response = await apiRequest('GET', `/api/gpu/recommendations?node=${node}&vmid=${vmid}`);
            
            if (response && response.success) {
                this.renderRecommendations(response);
                showToast(`Found ${response.recommendations.length} recommendations`, 'success');
            } else {
                showToast(response.message || 'Failed to get recommendations', 'error');
            }
        } catch (error) {
            console.error('Error getting recommendations:', error);
            showToast('Error getting recommendations', 'error');
        }
    }

    /**
     * Apply optimization
     * @param {string} node - Node name
     * @param {string} vmid - VM ID
     * @param {Array} optimizations - List of optimizations to apply
     */
    async applyOptimization(node, vmid, optimizations) {
        if (!node || !vmid || !optimizations.length) {
            showToast('Missing required parameters', 'warning');
            return;
        }

        try {
            showToast('Applying optimizations...', 'info');
            
            const response = await apiRequest('POST', '/api/gpu/optimize', {
                node: node,
                vmid: vmid,
                optimizations: optimizations
            });
            
            if (response && response.success) {
                showToast('Optimizations applied successfully', 'success');
                
                // Refresh recommendations
                this.getRecommendations(node, vmid);
            } else {
                showToast(response.message || 'Failed to apply optimizations', 'error');
            }
        } catch (error) {
            console.error('Error applying optimizations:', error);
            showToast('Error applying optimizations', 'error');
        }
    }

    /**
     * Configure GPU passthrough
     * @param {string} node - Node name
     * @param {string} vmid - VM ID
     * @param {string} gpuId - GPU PCI ID
     */
    async configureGPUPassthrough(node, vmid, gpuId) {
        if (!node || !vmid || !gpuId) {
            showToast('Missing required parameters', 'warning');
            return;
        }

        try {
            showToast('Configuring GPU passthrough...', 'info');
            
            const response = await apiRequest('POST', '/api/gpu/configure', {
                node: node,
                vmid: vmid,
                gpu_pci_id: gpuId
            });
            
            if (response && response.success) {
                showToast('GPU passthrough configured successfully', 'success');
                
                // Get current status
                this.getPassthroughStatus(node);
            } else {
                showToast(response.message || 'Failed to configure GPU passthrough', 'error');
            }
        } catch (error) {
            console.error('Error configuring GPU passthrough:', error);
            showToast('Error configuring GPU passthrough', 'error');
        }
    }

    /**
     * Get passthrough status
     * @param {string} node - Node name
     */
    async getPassthroughStatus(node) {
        if (!node) {
            showToast('Please select a node first', 'warning');
            return;
        }

        try {
            const response = await apiRequest('GET', `/api/gpu/status?node=${node}`);
            
            if (response && response.success) {
                this.renderStatusResults(response);
            } else {
                showToast(response.message || 'Failed to get passthrough status', 'error');
            }
        } catch (error) {
            console.error('Error getting passthrough status:', error);
            showToast('Error getting passthrough status', 'error');
        }
    }

    /**
     * Render GPU detection results
     * @param {Object} data - GPU detection results
     */
    renderGPUResults(data) {
        const resultsContainer = document.getElementById('gpu-results');
        if (!resultsContainer) return;

        let content = `
            <div class="card mb-4">
                <div class="card-header">
                    <h6>Detected GPUs on ${data.node}</h6>
                </div>
                <div class="card-body">
        `;

        if (data.gpus && data.gpus.length > 0) {
            content += `
                <div class="table-responsive">
                    <table class="table table-hover">
                        <thead>
                            <tr>
                                <th>Name</th>
                                <th>PCI ID</th>
                                <th>Driver</th>
                                <th>IOMMU Group</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
            `;

            data.gpus.forEach(gpu => {
                const isVfio = gpu.driver === 'vfio-pci';
                
                content += `
                    <tr>
                        <td>${gpu.name}</td>
                        <td><code>${gpu.pci_id}</code></td>
                        <td>
                            <span class="badge ${isVfio ? 'bg-success' : 'bg-warning'}">
                                ${gpu.driver}
                            </span>
                        </td>
                        <td>${gpu.iommu_group || 'N/A'}</td>
                        <td>
                            <button class="btn btn-sm btn-primary configure-gpu-btn" 
                                data-node="${data.node}" 
                                data-gpu-id="${gpu.pci_id}"
                                ${!this.selectedVM ? 'disabled' : ''}>
                                Configure Passthrough
                            </button>
                        </td>
                    </tr>
                `;
            });

            content += `
                        </tbody>
                    </table>
                </div>
            `;
        } else {
            content += `
                <div class="alert alert-warning">
                    No GPUs detected on this node.
                </div>
            `;
        }

        content += `
                </div>
                <div class="card-footer">
                    <small class="text-muted">
                        VFIO Loaded: <span class="${data.vfio_loaded ? 'text-success' : 'text-danger'}">
                            ${data.vfio_loaded ? 'Yes' : 'No'}
                        </span> | 
                        IOMMU Enabled: <span class="${data.iommu_enabled ? 'text-success' : 'text-danger'}">
                            ${data.iommu_enabled ? 'Yes' : 'No'}
                        </span>
                    </small>
                </div>
            </div>
        `;

        resultsContainer.innerHTML = content;
    }

    /**
     * Render compatibility results
     * @param {Object} data - Compatibility check results
     */
    renderCompatibilityResults(data) {
        const resultsContainer = document.getElementById('gpu-results');
        if (!resultsContainer) return;

        const compat = data.compatibility;
        
        let content = `
            <div class="card mb-4">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <h6>GPU Passthrough Compatibility</h6>
                    <span class="badge ${compat.compatible ? 'bg-success' : 'bg-warning'}">
                        ${compat.compatible ? 'Compatible' : 'Needs Configuration'}
                    </span>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-6">
                            <ul class="list-group">
                                <li class="list-group-item d-flex justify-content-between align-items-center">
                                    CPU Virtualization
                                    <span class="badge ${compat.virt_supported ? 'bg-success' : 'bg-danger'}">
                                        ${compat.virt_supported ? 'Enabled' : 'Disabled'}
                                    </span>
                                </li>
                                <li class="list-group-item d-flex justify-content-between align-items-center">
                                    IOMMU Enabled
                                    <span class="badge ${compat.iommu_enabled ? 'bg-success' : 'bg-danger'}">
                                        ${compat.iommu_enabled ? 'Yes' : 'No'}
                                    </span>
                                </li>
                                <li class="list-group-item d-flex justify-content-between align-items-center">
                                    VFIO Modules Available
                                    <span class="badge ${compat.vfio_available ? 'bg-success' : 'bg-danger'}">
                                        ${compat.vfio_available ? 'Yes' : 'No'}
                                    </span>
                                </li>
                                <li class="list-group-item d-flex justify-content-between align-items-center">
                                    GPUs Using VFIO
                                    <span class="badge ${compat.gpus_using_vfio ? 'bg-success' : 'bg-warning'}">
                                        ${compat.gpus_using_vfio ? 'Yes' : 'No'}
                                    </span>
                                </li>
                            </ul>
                        </div>
                        <div class="col-md-6">
                            <div class="card h-100">
                                <div class="card-body">
                                    <h6 class="card-title">Compatibility Notes</h6>
                                    <ul class="list-unstyled">
        `;

        if (!compat.virt_supported) {
            content += `
                <li class="text-danger mb-2">
                    <i class="fas fa-times-circle"></i> CPU virtualization is not enabled. Enable VT-x/AMD-V in BIOS.
                </li>
            `;
        }

        if (!compat.iommu_enabled) {
            content += `
                <li class="text-danger mb-2">
                    <i class="fas fa-times-circle"></i> IOMMU is not enabled. Add 'intel_iommu=on' or 'amd_iommu=on' to kernel parameters.
                </li>
            `;
        }

        if (!compat.vfio_available) {
            content += `
                <li class="text-danger mb-2">
                    <i class="fas fa-times-circle"></i> VFIO modules are not available. Install VFIO modules.
                </li>
            `;
        }

        if (!compat.gpus_using_vfio) {
            content += `
                <li class="text-warning mb-2">
                    <i class="fas fa-exclamation-triangle"></i> No GPUs are using the VFIO driver. Configure GPU for passthrough.
                </li>
            `;
        }

        if (compat.compatible) {
            content += `
                <li class="text-success mb-2">
                    <i class="fas fa-check-circle"></i> System is compatible with GPU passthrough!
                </li>
            `;
        }

        content += `
                                    </ul>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        resultsContainer.innerHTML = content + resultsContainer.innerHTML;
    }

    /**
     * Render optimization recommendations
     * @param {Object} data - Recommendations data
     */
    renderRecommendations(data) {
        const resultsContainer = document.getElementById('gpu-results');
        if (!resultsContainer) return;

        let content = `
            <div class="card mb-4">
                <div class="card-header">
                    <h6>Optimization Recommendations for VM ${data.vm_id}</h6>
                </div>
                <div class="card-body">
        `;

        if (data.recommendations && data.recommendations.length > 0) {
            content += `
                <div class="list-group">
            `;

            data.recommendations.forEach(rec => {
                const typeClass = rec.type === 'error' ? 'list-group-item-danger' : 
                                 rec.type === 'warning' ? 'list-group-item-warning' : 
                                 'list-group-item-info';
                
                const icon = rec.type === 'error' ? 'fas fa-times-circle' : 
                           rec.type === 'warning' ? 'fas fa-exclamation-triangle' : 
                           'fas fa-info-circle';
                
                // Determine optimization key based on message
                let optimizationKey = '';
                if (rec.message.includes('machine type')) {
                    optimizationKey = 'machine_type';
                } else if (rec.message.includes('CPU type')) {
                    optimizationKey = 'cpu_type';
                } else if (rec.message.includes('CPU flags')) {
                    optimizationKey = 'cpu_flags';
                } else if (rec.message.includes('IOMMU')) {
                    optimizationKey = 'iommu_fix';
                } else if (rec.message.includes('hugepages')) {
                    optimizationKey = 'hugepages';
                }
                
                content += `
                    <div class="list-group-item ${typeClass}">
                        <div class="d-flex w-100 justify-content-between">
                            <h6 class="mb-1">
                                <i class="${icon}"></i> 
                                ${rec.component.toUpperCase()}: ${rec.message}
                            </h6>
                            ${optimizationKey ? `
                                <button class="btn btn-sm btn-outline-primary apply-optimization-btn"
                                    data-node="${data.node}"
                                    data-vmid="${data.vm_id}"
                                    data-optimization="${optimizationKey}">
                                    Apply Fix
                                </button>
                            ` : ''}
                        </div>
                        <p class="mb-1">${rec.solution}</p>
                        ${rec.gpu_name ? `<small>GPU: ${rec.gpu_name}</small>` : ''}
                    </div>
                `;
            });

            content += `
                </div>
            `;
        } else {
            content += `
                <div class="alert alert-success">
                    No optimization recommendations needed. Your configuration looks good!
                </div>
            `;
        }

        content += `
                </div>
            </div>
        `;

        resultsContainer.innerHTML = content + resultsContainer.innerHTML;
    }

    /**
     * Render passthrough status
     * @param {Object} data - Passthrough status data
     */
    renderStatusResults(data) {
        const resultsContainer = document.getElementById('gpu-results');
        if (!resultsContainer) return;

        let content = `
            <div class="card mb-4">
                <div class="card-header">
                    <h6>GPU Passthrough Status</h6>
                </div>
                <div class="card-body">
        `;

        if (data.vms_with_gpu && data.vms_with_gpu.length > 0) {
            content += `
                <h6>VMs with GPU Passthrough</h6>
                <div class="table-responsive">
                    <table class="table table-hover">
                        <thead>
                            <tr>
                                <th>VM</th>
                                <th>Status</th>
                                <th>GPU</th>
                                <th>PCI ID</th>
                            </tr>
                        </thead>
                        <tbody>
            `;

            data.vms_with_gpu.forEach(vm => {
                content += `
                    <tr>
                        <td>${vm.name} (${vm.vm_id})</td>
                        <td>
                            <span class="badge ${vm.status === 'running' ? 'bg-success' : 'bg-secondary'}">
                                ${vm.status}
                            </span>
                        </td>
                        <td>${vm.gpu}</td>
                        <td><code>${vm.pci_id}</code></td>
                    </tr>
                `;
            });

            content += `
                        </tbody>
                    </table>
                </div>
            `;
        } else {
            content += `
                <div class="alert alert-info">
                    No VMs are currently using GPU passthrough.
                </div>
            `;
        }

        content += `
                </div>
            </div>
        `;

        resultsContainer.innerHTML = content + resultsContainer.innerHTML;
    }
}

// Initialize module
document.addEventListener('DOMContentLoaded', () => {
    const gpuAssistant = new GPUPassthroughAssistant();
    gpuAssistant.init();
    
    // Export to global scope for debugging
    window.gpuAssistant = gpuAssistant;
});

export default GPUPassthroughAssistant;
