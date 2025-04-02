/**
 * Personalized Setup Journey Module
 * Provides UI components for personalized setup journeys
 */

import { showToast } from './notifications.js';
import { apiRequest } from './api.js';

export class PersonalizedSetup {
    constructor() {
        this.currentJourney = null;
        this.currentStep = null;
        this.journeyContainer = document.getElementById('personalized-journey-container');
        this.setupWizardContainer = document.getElementById('setup-wizard-container');
    }

    /**
     * Initialize the personalized setup module
     */
    async init() {
        // Check for active journey
        try {
            const response = await apiRequest('GET', '/api/user-experience/journey/progress');
            if (response && !response.error) {
                this.currentJourney = response;
                this.loadCurrentStep();
            }
        } catch (error) {
            console.error('Error checking for active journey:', error);
        }

        // Set up event listeners
        document.addEventListener('click', (event) => {
            if (event.target.matches('.start-journey-btn')) {
                const expertiseLevel = event.target.dataset.level || null;
                this.startJourney(expertiseLevel);
            } else if (event.target.matches('.next-step-btn')) {
                this.advanceJourney();
            } else if (event.target.matches('.customize-journey-btn')) {
                this.showCustomizeJourneyModal();
            }
        });
    }

    /**
     * Start a personalized setup journey
     * @param {string} expertiseLevel - Optional expertise level override
     */
    async startJourney(expertiseLevel = null) {
        try {
            const response = await apiRequest('POST', '/api/user-experience/journey/start', {
                expertise_level: expertiseLevel
            });

            if (response && !response.error) {
                this.currentJourney = response;
                this.loadCurrentStep();
                showToast('Journey started: ' + response.template_name, 'success');
            } else {
                showToast('Failed to start journey', 'error');
            }
        } catch (error) {
            console.error('Error starting journey:', error);
            showToast('Error starting journey', 'error');
        }
    }

    /**
     * Load the current step in the journey
     */
    async loadCurrentStep() {
        try {
            const response = await apiRequest('GET', '/api/user-experience/journey/current-step');
            
            if (response && !response.error) {
                this.currentStep = response;
                this.renderCurrentStep();
            } else if (this.currentJourney && this.currentJourney.status === 'completed') {
                this.renderJourneyComplete();
            } else {
                this.renderNoActiveJourney();
            }
        } catch (error) {
            console.error('Error loading current step:', error);
            showToast('Error loading journey step', 'error');
        }
    }

    /**
     * Advance to the next step in the journey
     */
    async advanceJourney() {
        try {
            const response = await apiRequest('POST', '/api/user-experience/journey/advance');
            
            if (response && !response.error) {
                this.currentJourney = response;
                this.loadCurrentStep();
                showToast('Advanced to next step', 'success');
            } else {
                showToast('Failed to advance journey', 'error');
            }
        } catch (error) {
            console.error('Error advancing journey:', error);
            showToast('Error advancing journey', 'error');
        }
    }

    /**
     * Customize the journey
     * @param {Object} customizations - Journey customizations
     */
    async customizeJourney(customizations) {
        try {
            const response = await apiRequest('POST', '/api/user-experience/journey/customize', customizations);
            
            if (response && !response.error) {
                this.currentJourney = response;
                this.loadCurrentStep();
                showToast('Journey customized', 'success');
            } else {
                showToast('Failed to customize journey', 'error');
            }
        } catch (error) {
            console.error('Error customizing journey:', error);
            showToast('Error customizing journey', 'error');
        }
    }

    /**
     * Render the current step in the journey
     */
    renderCurrentStep() {
        if (!this.journeyContainer) return;

        // Get journey progress
        this.getJourneyProgress().then(progress => {
            const step = this.currentStep;
            
            // Create step content
            let content = `
                <div class="journey-step card">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h5>${step.name}</h5>
                        <span class="badge bg-primary">${progress.percent_complete.toFixed(0)}% Complete</span>
                    </div>
                    <div class="card-body">
                        <p class="step-description">${step.description}</p>
                        <div class="step-content mb-4">
                            ${step.content}
                        </div>`;
            
            // Add step-specific UI based on type
            if (step.type === 'interactive' && step.action) {
                content += this.renderInteractiveStep(step);
            }
            
            // Add next button
            content += `
                        <div class="d-flex justify-content-between mt-4">
                            <div>
                                <span class="text-muted">Estimated time: ${step.duration_minutes} minutes</span>
                            </div>
                            <button class="btn btn-primary next-step-btn">Continue</button>
                        </div>
                    </div>
                    <div class="card-footer">
                        <div class="progress">
                            <div class="progress-bar" role="progressbar" style="width: ${progress.percent_complete}%" 
                                aria-valuenow="${progress.percent_complete}" aria-valuemin="0" aria-valuemax="100"></div>
                        </div>
                    </div>
                </div>
            `;
            
            this.journeyContainer.innerHTML = content;
            this.setupActionHandlers(step);
        });
    }

    /**
     * Render interactive step content
     * @param {Object} step - Step object
     * @returns {string} HTML content
     */
    renderInteractiveStep(step) {
        let content = '';
        
        switch (step.action) {
            case 'goal_selection':
                content = `
                    <div class="goal-selection">
                        <h6>Select your goals:</h6>
                        <div class="goal-options">
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" value="media_server" id="goal-media">
                                <label class="form-check-label" for="goal-media">
                                    Media Server (Plex, Jellyfin, etc.)
                                </label>
                            </div>
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" value="file_storage" id="goal-storage">
                                <label class="form-check-label" for="goal-storage">
                                    File Storage & Backup
                                </label>
                            </div>
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" value="home_automation" id="goal-automation">
                                <label class="form-check-label" for="goal-automation">
                                    Home Automation
                                </label>
                            </div>
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" value="web_hosting" id="goal-web">
                                <label class="form-check-label" for="goal-web">
                                    Web Hosting
                                </label>
                            </div>
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" value="development" id="goal-dev">
                                <label class="form-check-label" for="goal-dev">
                                    Development Environment
                                </label>
                            </div>
                        </div>
                    </div>
                `;
                break;
                
            case 'hardware_check':
                content = `
                    <div class="hardware-check">
                        <button class="btn btn-outline-primary mb-3" id="detect-resources-btn">
                            <i class="fas fa-search"></i> Detect System Resources
                        </button>
                        <div id="hardware-results" class="d-none">
                            <div class="card mb-3">
                                <div class="card-body">
                                    <h6>System Resources</h6>
                                    <div class="row">
                                        <div class="col-md-4">
                                            <p><strong>CPU:</strong> <span id="cpu-info">Detecting...</span></p>
                                        </div>
                                        <div class="col-md-4">
                                            <p><strong>Memory:</strong> <span id="memory-info">Detecting...</span></p>
                                        </div>
                                        <div class="col-md-4">
                                            <p><strong>Storage:</strong> <span id="storage-info">Detecting...</span></p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
                break;
                
            case 'service_selection':
                content = `
                    <div class="service-selection">
                        <h6>Recommended Services:</h6>
                        <div id="recommended-services" class="row">
                            <p>Loading recommendations based on your goals...</p>
                        </div>
                    </div>
                `;
                break;
                
            default:
                content = `
                    <div class="generic-interactive">
                        <p>This step requires your input.</p>
                    </div>
                `;
        }
        
        return content;
    }

    /**
     * Set up action handlers for interactive steps
     * @param {Object} step - Step object
     */
    setupActionHandlers(step) {
        if (!step.action) return;
        
        switch (step.action) {
            case 'goal_selection':
                // Handle goal selection
                document.querySelector('.next-step-btn').addEventListener('click', () => {
                    const selectedGoals = Array.from(document.querySelectorAll('.goal-options input:checked'))
                        .map(input => input.value);
                    
                    apiRequest('POST', '/api/user-experience/setup/goals', {
                        goals: selectedGoals
                    }).then(response => {
                        if (response && !response.error) {
                            this.advanceJourney();
                        } else {
                            showToast('Failed to process goals', 'error');
                        }
                    }).catch(error => {
                        console.error('Error processing goals:', error);
                        showToast('Error processing goals', 'error');
                    });
                });
                break;
                
            case 'hardware_check':
                // Handle hardware detection
                document.getElementById('detect-resources-btn').addEventListener('click', () => {
                    document.getElementById('hardware-results').classList.remove('d-none');
                    
                    apiRequest('GET', '/api/system/resources').then(response => {
                        if (response && !response.error) {
                            document.getElementById('cpu-info').textContent = 
                                `${response.cpu.cores} cores (${response.cpu.model})`;
                            document.getElementById('memory-info').textContent = 
                                `${(response.memory.total / 1024 / 1024 / 1024).toFixed(1)} GB`;
                            document.getElementById('storage-info').textContent = 
                                `${(response.storage.total / 1024 / 1024 / 1024).toFixed(1)} GB`;
                        } else {
                            showToast('Failed to detect resources', 'error');
                        }
                    }).catch(error => {
                        console.error('Error detecting resources:', error);
                        showToast('Error detecting resources', 'error');
                    });
                });
                break;
                
            case 'service_selection':
                // Load recommended services
                apiRequest('GET', '/api/user-experience/setup/recommendations').then(response => {
                    if (response && !response.error && response.services) {
                        const servicesContainer = document.getElementById('recommended-services');
                        servicesContainer.innerHTML = '';
                        
                        response.services.forEach(service => {
                            const serviceCard = document.createElement('div');
                            serviceCard.className = 'col-md-4 mb-3';
                            serviceCard.innerHTML = `
                                <div class="card h-100">
                                    <div class="card-body">
                                        <h6>${service.name}</h6>
                                        <p class="small">${service.description}</p>
                                        <div class="form-check">
                                            <input class="form-check-input service-checkbox" 
                                                type="checkbox" value="${service.id}" id="service-${service.id}"
                                                ${service.recommended ? 'checked' : ''}>
                                            <label class="form-check-label" for="service-${service.id}">
                                                Select this service
                                            </label>
                                        </div>
                                    </div>
                                    <div class="card-footer bg-transparent">
                                        <small class="text-muted">
                                            <i class="fas fa-microchip"></i> ${service.resources.cpu} CPU
                                            <i class="fas fa-memory ml-2"></i> ${service.resources.memory} MB
                                        </small>
                                    </div>
                                </div>
                            `;
                            servicesContainer.appendChild(serviceCard);
                        });
                    } else {
                        showToast('Failed to load recommendations', 'error');
                    }
                }).catch(error => {
                    console.error('Error loading recommendations:', error);
                    showToast('Error loading recommendations', 'error');
                });
                break;
        }
    }

    /**
     * Render journey completion screen
     */
    renderJourneyComplete() {
        if (!this.journeyContainer) return;
        
        this.journeyContainer.innerHTML = `
            <div class="journey-complete card">
                <div class="card-body text-center">
                    <div class="mb-4">
                        <i class="fas fa-check-circle text-success fa-5x"></i>
                    </div>
                    <h4>Journey Complete!</h4>
                    <p>You've completed the ${this.currentJourney.template_name}.</p>
                    <p>Your personalized setup is now ready to use.</p>
                    <div class="mt-4">
                        <a href="/dashboard" class="btn btn-primary">Go to Dashboard</a>
                        <button class="btn btn-outline-secondary ms-2 start-journey-btn">Start New Journey</button>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Render no active journey screen
     */
    renderNoActiveJourney() {
        if (!this.journeyContainer) return;
        
        this.journeyContainer.innerHTML = `
            <div class="no-journey card">
                <div class="card-body">
                    <h5>No Active Journey</h5>
                    <p>You don't have an active setup journey. Would you like to start one?</p>
                    <div class="journey-options mt-4">
                        <div class="row">
                            <div class="col-md-3 mb-3">
                                <div class="card h-100">
                                    <div class="card-body text-center">
                                        <h6>Beginner</h6>
                                        <p class="small">A guided journey for those new to self-hosting</p>
                                        <button class="btn btn-primary start-journey-btn" data-level="beginner">Start</button>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-3 mb-3">
                                <div class="card h-100">
                                    <div class="card-body text-center">
                                        <h6>Intermediate</h6>
                                        <p class="small">A balanced journey for those with some experience</p>
                                        <button class="btn btn-primary start-journey-btn" data-level="intermediate">Start</button>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-3 mb-3">
                                <div class="card h-100">
                                    <div class="card-body text-center">
                                        <h6>Advanced</h6>
                                        <p class="small">An in-depth journey for experienced users</p>
                                        <button class="btn btn-primary start-journey-btn" data-level="advanced">Start</button>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-3 mb-3">
                                <div class="card h-100">
                                    <div class="card-body text-center">
                                        <h6>Expert</h6>
                                        <p class="small">A customizable journey with full control</p>
                                        <button class="btn btn-primary start-journey-btn" data-level="expert">Start</button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Show customize journey modal
     */
    showCustomizeJourneyModal() {
        // Create modal if it doesn't exist
        if (!document.getElementById('customize-journey-modal')) {
            const modalHtml = `
                <div class="modal fade" id="customize-journey-modal" tabindex="-1" aria-hidden="true">
                    <div class="modal-dialog modal-lg">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title">Customize Journey</h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                            </div>
                            <div class="modal-body">
                                <div class="mb-3">
                                    <label class="form-label">UI Simplification</label>
                                    <div class="form-check form-switch">
                                        <input class="form-check-input" type="checkbox" id="ui-simplification">
                                        <label class="form-check-label" for="ui-simplification">
                                            Simplify the user interface
                                        </label>
                                    </div>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Explanation Detail</label>
                                    <select class="form-select" id="explanation-detail">
                                        <option value="basic">Basic</option>
                                        <option value="detailed">Detailed</option>
                                        <option value="technical">Technical</option>
                                        <option value="comprehensive">Comprehensive</option>
                                    </select>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Automation Level</label>
                                    <select class="form-select" id="automation-level">
                                        <option value="high">High (Automate most tasks)</option>
                                        <option value="medium">Medium (Balance automation and control)</option>
                                        <option value="low">Low (More manual control)</option>
                                        <option value="minimal">Minimal (Maximum control)</option>
                                    </select>
                                </div>
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                                <button type="button" class="btn btn-primary" id="save-customizations-btn">Save Changes</button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            const modalContainer = document.createElement('div');
            modalContainer.innerHTML = modalHtml;
            document.body.appendChild(modalContainer.firstChild);
            
            // Add event listener for save button
            document.getElementById('save-customizations-btn').addEventListener('click', () => {
                const customizations = {
                    ui_settings: {
                        simplification: document.getElementById('ui-simplification').checked,
                        explanation_detail: document.getElementById('explanation-detail').value,
                        automation_level: document.getElementById('automation-level').value
                    }
                };
                
                this.customizeJourney(customizations);
                
                // Close modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('customize-journey-modal'));
                modal.hide();
            });
        }
        
        // Set current values
        if (this.currentJourney && this.currentJourney.ui_settings) {
            document.getElementById('ui-simplification').checked = 
                this.currentJourney.ui_settings.simplification;
            document.getElementById('explanation-detail').value = 
                this.currentJourney.ui_settings.explanation_detail;
            document.getElementById('automation-level').value = 
                this.currentJourney.ui_settings.automation_level;
        }
        
        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('customize-journey-modal'));
        modal.show();
    }

    /**
     * Get journey progress
     * @returns {Promise<Object>} Journey progress object
     */
    async getJourneyProgress() {
        try {
            const response = await apiRequest('GET', '/api/user-experience/journey/progress');
            return response && !response.error ? response : { percent_complete: 0 };
        } catch (error) {
            console.error('Error getting journey progress:', error);
            return { percent_complete: 0 };
        }
    }
}

// Initialize module
document.addEventListener('DOMContentLoaded', () => {
    const personalizedSetup = new PersonalizedSetup();
    personalizedSetup.init();
    
    // Export to global scope for debugging
    window.personalizedSetup = personalizedSetup;
});

export default PersonalizedSetup;
