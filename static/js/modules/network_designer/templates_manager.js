/**
 * Templates Manager Module
 * Handles VLAN and subnet templates in the network topology designer
 */

import { apiRequest } from '../api.js';
import { showToast } from '../notifications.js';

/**
 * Templates Manager
 */
const TemplatesManager = {
    /**
     * Initialize the templates manager
     * @param {Object} designer - Network designer instance
     */
    init: function(designer) {
        this.designer = designer;
        this.vlanTemplates = null;
        this.subnetTemplates = null;
        this._initModals();
    },

    /**
     * Initialize modals
     * @private
     */
    _initModals: function() {
        // VLAN Templates modal
        const vlanTemplatesModal = document.getElementById('vlan-templates-modal');
        if (vlanTemplatesModal) {
            this.vlanTemplatesModal = new bootstrap.Modal(vlanTemplatesModal);
            
            // Apply button
            const applyVlanTemplateBtn = document.getElementById('apply-vlan-template-btn');
            if (applyVlanTemplateBtn) {
                applyVlanTemplateBtn.addEventListener('click', () => {
                    this._applyVlanTemplate();
                });
            }
        }
        
        // Subnet Templates modal
        const subnetTemplatesModal = document.getElementById('subnet-templates-modal');
        if (subnetTemplatesModal) {
            this.subnetTemplatesModal = new bootstrap.Modal(subnetTemplatesModal);
            
            // Apply button
            const applySubnetTemplateBtn = document.getElementById('apply-subnet-template-btn');
            if (applySubnetTemplateBtn) {
                applySubnetTemplateBtn.addEventListener('click', () => {
                    this._applySubnetTemplate();
                });
            }
        }
    },

    /**
     * Load VLAN templates
     */
    loadVlanTemplates: async function() {
        try {
            const response = await apiRequest('GET', '/api/network-planning/vlan-templates');
            
            if (response && response.success) {
                this.vlanTemplates = response.templates;
                return this.vlanTemplates;
            } else {
                throw new Error(response.message || 'Failed to load VLAN templates');
            }
        } catch (error) {
            console.error('Error loading VLAN templates:', error);
            showToast(`Error loading VLAN templates: ${error.message}`, 'error');
            return null;
        }
    },

    /**
     * Load subnet templates
     */
    loadSubnetTemplates: async function() {
        try {
            const response = await apiRequest('GET', '/api/network-planning/subnet-templates');
            
            if (response && response.success) {
                this.subnetTemplates = response.templates;
                return this.subnetTemplates;
            } else {
                throw new Error(response.message || 'Failed to load subnet templates');
            }
        } catch (error) {
            console.error('Error loading subnet templates:', error);
            showToast(`Error loading subnet templates: ${error.message}`, 'error');
            return null;
        }
    },

    /**
     * Show VLAN templates modal
     */
    showVlanTemplatesModal: async function() {
        // Load templates if not already loaded
        if (!this.vlanTemplates) {
            await this.loadVlanTemplates();
        }
        
        if (!this.vlanTemplates) {
            showToast('Failed to load VLAN templates', 'error');
            return;
        }
        
        // Render templates
        this._renderVlanTemplates();
        
        // Show modal
        this.vlanTemplatesModal.show();
    },

    /**
     * Show subnet templates modal
     */
    showSubnetTemplatesModal: async function() {
        // Load templates if not already loaded
        if (!this.subnetTemplates) {
            await this.loadSubnetTemplates();
        }
        
        if (!this.subnetTemplates) {
            showToast('Failed to load subnet templates', 'error');
            return;
        }
        
        // Render templates
        this._renderSubnetTemplates();
        
        // Show modal
        this.subnetTemplatesModal.show();
    },

    /**
     * Render VLAN templates
     * @private
     */
    _renderVlanTemplates: function() {
        const templatesContainer = document.getElementById('vlan-templates-container');
        if (!templatesContainer) return;
        
        let html = '';
        
        Object.entries(this.vlanTemplates).forEach(([id, template]) => {
            html += `
                <div class="col-md-6 mb-3">
                    <div class="card h-100">
                        <div class="card-header">
                            <div class="form-check">
                                <input class="form-check-input vlan-template-radio" type="radio" name="vlan-template" id="vlan-template-${id}" value="${id}">
                                <label class="form-check-label" for="vlan-template-${id}">
                                    ${template.name}
                                </label>
                            </div>
                        </div>
                        <div class="card-body">
                            <p class="card-text">${template.description}</p>
                            <h6>VLANs:</h6>
                            <ul class="list-group">
                                ${template.vlans.map(vlan => `
                                    <li class="list-group-item">
                                        <strong>VLAN ${vlan.id}:</strong> ${vlan.name}
                                        <div class="small text-muted">${vlan.subnet} - ${vlan.purpose}</div>
                                    </li>
                                `).join('')}
                            </ul>
                        </div>
                    </div>
                </div>
            `;
        });
        
        templatesContainer.innerHTML = html;
    },

    /**
     * Render subnet templates
     * @private
     */
    _renderSubnetTemplates: function() {
        const templatesContainer = document.getElementById('subnet-templates-container');
        if (!templatesContainer) return;
        
        let html = '';
        
        Object.entries(this.subnetTemplates).forEach(([id, template]) => {
            html += `
                <div class="col-md-6 mb-3">
                    <div class="card h-100">
                        <div class="card-header">
                            <div class="form-check">
                                <input class="form-check-input subnet-template-radio" type="radio" name="subnet-template" id="subnet-template-${id}" value="${id}">
                                <label class="form-check-label" for="subnet-template-${id}">
                                    ${template.name}
                                </label>
                            </div>
                        </div>
                        <div class="card-body">
                            <p class="card-text">${template.description}</p>
                            ${template.base_network ? `
                                <p><strong>Base Network:</strong> ${template.base_network}</p>
                                <p><strong>Subnet Size:</strong> ${template.subnet_size}</p>
                                <p><strong>Allocation Strategy:</strong> ${this._formatAllocationStrategy(template.allocation_strategy)}</p>
                            ` : ''}
                            ${template.base_networks ? `
                                <h6>Base Networks:</h6>
                                <ul class="list-group">
                                    ${template.base_networks.map(network => `
                                        <li class="list-group-item">
                                            <strong>${network.network}:</strong> ${network.purpose}
                                        </li>
                                    `).join('')}
                                </ul>
                            ` : ''}
                        </div>
                    </div>
                </div>
            `;
        });
        
        templatesContainer.innerHTML = html;
    },

    /**
     * Apply VLAN template
     * @private
     */
    _applyVlanTemplate: async function() {
        // Get selected template
        const selectedTemplate = document.querySelector('input[name="vlan-template"]:checked');
        if (!selectedTemplate) {
            showToast('Please select a VLAN template', 'warning');
            return;
        }
        
        const templateId = selectedTemplate.value;
        
        try {
            // Disable apply button
            const applyBtn = document.getElementById('apply-vlan-template-btn');
            if (applyBtn) {
                applyBtn.disabled = true;
                applyBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Applying...';
            }
            
            const response = await apiRequest('POST', `/api/network-planning/plans/${this.designer.planId}/apply-vlan-template`, {
                template_id: templateId
            });
            
            // Re-enable apply button
            if (applyBtn) {
                applyBtn.disabled = false;
                applyBtn.innerHTML = 'Apply Template';
            }
            
            if (response && response.success) {
                // Update plan data
                this.designer.plan = response.plan;
                
                // Reload the designer
                this.designer._renderTopology();
                
                // Hide modal
                this.vlanTemplatesModal.hide();
                
                showToast('VLAN template applied successfully', 'success');
            } else {
                throw new Error(response.message || 'Failed to apply VLAN template');
            }
        } catch (error) {
            console.error('Error applying VLAN template:', error);
            
            // Re-enable apply button
            const applyBtn = document.getElementById('apply-vlan-template-btn');
            if (applyBtn) {
                applyBtn.disabled = false;
                applyBtn.innerHTML = 'Apply Template';
            }
            
            showToast(`Error applying VLAN template: ${error.message}`, 'error');
        }
    },

    /**
     * Apply subnet template
     * @private
     */
    _applySubnetTemplate: async function() {
        // Get selected template
        const selectedTemplate = document.querySelector('input[name="subnet-template"]:checked');
        if (!selectedTemplate) {
            showToast('Please select a subnet template', 'warning');
            return;
        }
        
        const templateId = selectedTemplate.value;
        
        try {
            // Disable apply button
            const applyBtn = document.getElementById('apply-subnet-template-btn');
            if (applyBtn) {
                applyBtn.disabled = true;
                applyBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Applying...';
            }
            
            const response = await apiRequest('POST', `/api/network-planning/plans/${this.designer.planId}/apply-subnet-template`, {
                template_id: templateId
            });
            
            // Re-enable apply button
            if (applyBtn) {
                applyBtn.disabled = false;
                applyBtn.innerHTML = 'Apply Template';
            }
            
            if (response && response.success) {
                // Update plan data
                this.designer.plan = response.plan;
                
                // Reload the designer
                this.designer._renderTopology();
                
                // Hide modal
                this.subnetTemplatesModal.hide();
                
                showToast('Subnet template applied successfully', 'success');
            } else {
                throw new Error(response.message || 'Failed to apply subnet template');
            }
        } catch (error) {
            console.error('Error applying subnet template:', error);
            
            // Re-enable apply button
            const applyBtn = document.getElementById('apply-subnet-template-btn');
            if (applyBtn) {
                applyBtn.disabled = false;
                applyBtn.innerHTML = 'Apply Template';
            }
            
            showToast(`Error applying subnet template: ${error.message}`, 'error');
        }
    },

    /**
     * Format allocation strategy for display
     * @param {string} strategy - Allocation strategy
     * @returns {string} Formatted allocation strategy
     * @private
     */
    _formatAllocationStrategy: function(strategy) {
        switch (strategy) {
            case 'sequential':
                return 'Sequential';
            case 'vlan_mapped':
                return 'VLAN Mapped';
            case 'purpose_based':
                return 'Purpose Based';
            default:
                return strategy.charAt(0).toUpperCase() + strategy.slice(1);
        }
    }
};

export default TemplatesManager;
