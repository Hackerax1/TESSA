/**
 * Network Planning Module
 * Handles the network planning wizard functionality
 */

import { apiRequest } from './api.js';
import { showToast } from './notifications.js';

/**
 * Network Planning Module
 */
const NetworkPlanning = {
    /**
     * Initialize the network planning module
     */
    init: function() {
        console.log('Initializing Network Planning module');
        this.bindEvents();
        this.loadPlans();
    },

    /**
     * Bind event listeners
     */
    bindEvents: function() {
        // Create plan button
        const createPlanBtn = document.getElementById('create-plan-btn');
        if (createPlanBtn) {
            createPlanBtn.addEventListener('click', () => {
                const createPlanModal = new bootstrap.Modal(document.getElementById('create-plan-modal'));
                createPlanModal.show();
            });
        }

        // Create plan submit
        const createPlanSubmit = document.getElementById('create-plan-submit');
        if (createPlanSubmit) {
            createPlanSubmit.addEventListener('click', () => {
                this.createPlan();
            });
        }

        // Template buttons
        const templateBtns = document.querySelectorAll('.template-btn');
        if (templateBtns) {
            templateBtns.forEach(btn => {
                btn.addEventListener('click', (e) => {
                    const template = e.target.dataset.template;
                    const createPlanModal = new bootstrap.Modal(document.getElementById('create-plan-modal'));
                    document.getElementById('plan-template').value = template;
                    createPlanModal.show();
                });
            });
        }

        // Delete plan confirm
        const deletePlanConfirm = document.getElementById('delete-plan-confirm');
        if (deletePlanConfirm) {
            deletePlanConfirm.addEventListener('click', () => {
                const planId = deletePlanConfirm.dataset.planId;
                this.deletePlan(planId);
            });
        }
    },

    /**
     * Load network plans
     */
    loadPlans: async function() {
        const plansLoading = document.getElementById('plans-loading');
        const plansList = document.getElementById('plans-list');
        const noPlansMessage = document.getElementById('no-plans-message');
        const plansTableBody = document.getElementById('plans-table-body');

        if (!plansLoading || !plansList || !noPlansMessage || !plansTableBody) {
            console.error('Required elements not found');
            return;
        }

        try {
            plansLoading.classList.remove('d-none');
            plansList.classList.add('d-none');

            const response = await apiRequest('GET', '/api/network-planning/plans');
            
            plansLoading.classList.add('d-none');
            plansList.classList.remove('d-none');

            if (response && response.success) {
                const plans = response.plans || [];
                
                if (plans.length === 0) {
                    noPlansMessage.classList.remove('d-none');
                    plansTableBody.innerHTML = '';
                } else {
                    noPlansMessage.classList.add('d-none');
                    this.renderPlansTable(plans);
                }
            } else {
                throw new Error(response.message || 'Failed to load network plans');
            }
        } catch (error) {
            console.error('Error loading network plans:', error);
            plansLoading.classList.add('d-none');
            plansList.classList.remove('d-none');
            showToast(`Error loading network plans: ${error.message}`, 'error');
            
            // Show error message in table
            plansTableBody.innerHTML = `
                <tr>
                    <td colspan="4" class="text-center text-danger">
                        <i class="fas fa-exclamation-circle"></i>
                        Error loading network plans. Please try again.
                    </td>
                </tr>
            `;
        }
    },

    /**
     * Render plans table
     * @param {Array} plans - Network plans
     */
    renderPlansTable: function(plans) {
        const plansTableBody = document.getElementById('plans-table-body');
        if (!plansTableBody) return;

        plansTableBody.innerHTML = '';

        plans.forEach(plan => {
            const row = document.createElement('tr');
            
            const nameCell = document.createElement('td');
            nameCell.textContent = plan.name;
            
            const descriptionCell = document.createElement('td');
            descriptionCell.textContent = plan.description || '-';
            
            const updatedCell = document.createElement('td');
            updatedCell.textContent = plan.updated_at ? new Date(plan.updated_at).toLocaleString() : '-';
            
            const actionsCell = document.createElement('td');
            actionsCell.innerHTML = `
                <div class="btn-group btn-group-sm" role="group">
                    <a href="/network-planning/designer/${plan.id}" class="btn btn-primary" title="Edit Plan">
                        <i class="fas fa-edit"></i>
                    </a>
                    <button type="button" class="btn btn-danger delete-plan-btn" data-plan-id="${plan.id}" data-plan-name="${plan.name}" title="Delete Plan">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            `;
            
            row.appendChild(nameCell);
            row.appendChild(descriptionCell);
            row.appendChild(updatedCell);
            row.appendChild(actionsCell);
            
            plansTableBody.appendChild(row);
        });

        // Bind delete buttons
        const deleteButtons = plansTableBody.querySelectorAll('.delete-plan-btn');
        deleteButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const planId = e.currentTarget.dataset.planId;
                const planName = e.currentTarget.dataset.planName;
                
                const deletePlanModal = new bootstrap.Modal(document.getElementById('delete-plan-modal'));
                document.getElementById('delete-plan-name').textContent = planName;
                document.getElementById('delete-plan-confirm').dataset.planId = planId;
                deletePlanModal.show();
            });
        });
    },

    /**
     * Create a new network plan
     */
    createPlan: async function() {
        const nameInput = document.getElementById('plan-name');
        const descriptionInput = document.getElementById('plan-description');
        const templateSelect = document.getElementById('plan-template');
        
        if (!nameInput || !descriptionInput || !templateSelect) {
            console.error('Required form elements not found');
            return;
        }
        
        const name = nameInput.value.trim();
        if (!name) {
            showToast('Please enter a plan name', 'warning');
            nameInput.focus();
            return;
        }
        
        const description = descriptionInput.value.trim();
        const template = templateSelect.value;
        
        try {
            const createPlanSubmit = document.getElementById('create-plan-submit');
            if (createPlanSubmit) {
                createPlanSubmit.disabled = true;
                createPlanSubmit.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Creating...';
            }
            
            const response = await apiRequest('POST', '/api/network-planning/plans', {
                name,
                description,
                template
            });
            
            if (createPlanSubmit) {
                createPlanSubmit.disabled = false;
                createPlanSubmit.innerHTML = 'Create Plan';
            }
            
            if (response && response.success) {
                // Close modal
                const createPlanModal = bootstrap.Modal.getInstance(document.getElementById('create-plan-modal'));
                if (createPlanModal) {
                    createPlanModal.hide();
                }
                
                // Reset form
                nameInput.value = '';
                descriptionInput.value = '';
                templateSelect.value = 'empty';
                
                // Show success message
                showToast('Network plan created successfully', 'success');
                
                // Redirect to designer
                window.location.href = `/network-planning/designer/${response.plan.id}`;
            } else {
                throw new Error(response.message || 'Failed to create network plan');
            }
        } catch (error) {
            console.error('Error creating network plan:', error);
            
            const createPlanSubmit = document.getElementById('create-plan-submit');
            if (createPlanSubmit) {
                createPlanSubmit.disabled = false;
                createPlanSubmit.innerHTML = 'Create Plan';
            }
            
            showToast(`Error creating network plan: ${error.message}`, 'error');
        }
    },

    /**
     * Delete a network plan
     * @param {string} planId - Plan ID
     */
    deletePlan: async function(planId) {
        if (!planId) {
            console.error('No plan ID provided');
            return;
        }
        
        try {
            const deletePlanConfirm = document.getElementById('delete-plan-confirm');
            if (deletePlanConfirm) {
                deletePlanConfirm.disabled = true;
                deletePlanConfirm.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Deleting...';
            }
            
            const response = await apiRequest('DELETE', `/api/network-planning/plans/${planId}`);
            
            if (deletePlanConfirm) {
                deletePlanConfirm.disabled = false;
                deletePlanConfirm.innerHTML = 'Delete';
            }
            
            if (response && response.success) {
                // Close modal
                const deletePlanModal = bootstrap.Modal.getInstance(document.getElementById('delete-plan-modal'));
                if (deletePlanModal) {
                    deletePlanModal.hide();
                }
                
                // Show success message
                showToast('Network plan deleted successfully', 'success');
                
                // Reload plans
                this.loadPlans();
            } else {
                throw new Error(response.message || 'Failed to delete network plan');
            }
        } catch (error) {
            console.error('Error deleting network plan:', error);
            
            const deletePlanConfirm = document.getElementById('delete-plan-confirm');
            if (deletePlanConfirm) {
                deletePlanConfirm.disabled = false;
                deletePlanConfirm.innerHTML = 'Delete';
            }
            
            showToast(`Error deleting network plan: ${error.message}`, 'error');
        }
    }
};

// Initialize the module when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    NetworkPlanning.init();
});

export default NetworkPlanning;
