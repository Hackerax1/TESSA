/**
 * Migration Wizard Base Component
 * Provides the foundation for multi-step wizard navigation
 */

export class WizardBase {
    constructor(containerId, steps = []) {
        this.containerId = containerId;
        this.container = document.getElementById(containerId);
        this.steps = steps;
        this.currentStepIndex = 0;
        this.data = {};
        this.eventListeners = {};
    }

    /**
     * Initialize the wizard
     */
    init() {
        if (!this.container) {
            console.error(`Container element with ID "${this.containerId}" not found`);
            return;
        }

        this.renderWizard();
        this.goToStep(0);
    }

    /**
     * Render the wizard structure
     */
    renderWizard() {
        const wizardHtml = `
            <div class="wizard">
                <div class="wizard-header">
                    <ul class="nav nav-tabs wizard-steps">
                        ${this.steps.map((step, index) => `
                            <li class="nav-item">
                                <a class="nav-link ${index === 0 ? 'active' : ''}" data-step="${index}">
                                    <span class="step-number">${index + 1}</span>
                                    <span class="step-title">${step.title}</span>
                                </a>
                            </li>
                        `).join('')}
                    </ul>
                </div>
                <div class="wizard-content">
                    ${this.steps.map((step, index) => `
                        <div class="wizard-step" data-step="${index}" style="display: ${index === 0 ? 'block' : 'none'}">
                            <div class="step-content" id="step-content-${index}">
                                <!-- Step content will be rendered here -->
                            </div>
                        </div>
                    `).join('')}
                </div>
                <div class="wizard-footer">
                    <div class="row">
                        <div class="col-6">
                            <button class="btn btn-secondary" id="wizard-prev-btn" style="display: none;">Previous</button>
                        </div>
                        <div class="col-6 text-end">
                            <button class="btn btn-primary" id="wizard-next-btn">Next</button>
                            <button class="btn btn-success" id="wizard-finish-btn" style="display: none;">Finish</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        this.container.innerHTML = wizardHtml;

        // Set up event listeners
        const prevBtn = document.getElementById('wizard-prev-btn');
        const nextBtn = document.getElementById('wizard-next-btn');
        const finishBtn = document.getElementById('wizard-finish-btn');
        const stepLinks = this.container.querySelectorAll('.wizard-steps .nav-link');

        if (prevBtn) {
            prevBtn.addEventListener('click', () => this.previousStep());
        }

        if (nextBtn) {
            nextBtn.addEventListener('click', () => this.nextStep());
        }

        if (finishBtn) {
            finishBtn.addEventListener('click', () => this.finish());
        }

        stepLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                const stepIndex = parseInt(e.currentTarget.dataset.step);
                if (stepIndex < this.currentStepIndex) {
                    this.goToStep(stepIndex);
                }
            });
        });
    }

    /**
     * Render content for the current step
     */
    renderStepContent() {
        const step = this.steps[this.currentStepIndex];
        const contentContainer = document.getElementById(`step-content-${this.currentStepIndex}`);

        if (contentContainer && step.render) {
            contentContainer.innerHTML = step.render(this.data);
            
            if (step.init) {
                step.init(contentContainer, this.data);
            }
        }
    }

    /**
     * Go to a specific step
     * @param {number} stepIndex - Index of the step to go to
     */
    goToStep(stepIndex) {
        if (stepIndex < 0 || stepIndex >= this.steps.length) {
            return;
        }

        // Hide all steps
        const stepElements = this.container.querySelectorAll('.wizard-step');
        stepElements.forEach(el => {
            el.style.display = 'none';
        });

        // Show the target step
        const targetStep = this.container.querySelector(`.wizard-step[data-step="${stepIndex}"]`);
        if (targetStep) {
            targetStep.style.display = 'block';
        }

        // Update step tabs
        const stepLinks = this.container.querySelectorAll('.wizard-steps .nav-link');
        stepLinks.forEach((link, index) => {
            if (index <= stepIndex) {
                link.classList.add('active');
            } else {
                link.classList.remove('active');
            }
        });

        // Update buttons
        const prevBtn = document.getElementById('wizard-prev-btn');
        const nextBtn = document.getElementById('wizard-next-btn');
        const finishBtn = document.getElementById('wizard-finish-btn');

        if (prevBtn) {
            prevBtn.style.display = stepIndex > 0 ? 'inline-block' : 'none';
        }

        if (nextBtn && finishBtn) {
            if (stepIndex === this.steps.length - 1) {
                nextBtn.style.display = 'none';
                finishBtn.style.display = 'inline-block';
            } else {
                nextBtn.style.display = 'inline-block';
                finishBtn.style.display = 'none';
            }
        }

        // Update current step index
        this.currentStepIndex = stepIndex;

        // Render step content
        this.renderStepContent();

        // Trigger step change event
        this.triggerEvent('stepChange', { stepIndex, step: this.steps[stepIndex] });
    }

    /**
     * Go to the next step
     */
    nextStep() {
        const currentStep = this.steps[this.currentStepIndex];
        
        // Validate current step if validation function exists
        if (currentStep.validate) {
            const isValid = currentStep.validate(this.data);
            if (!isValid) {
                return;
            }
        }

        // Process data if process function exists
        if (currentStep.process) {
            currentStep.process(this.data);
        }

        // Go to next step
        this.goToStep(this.currentStepIndex + 1);
    }

    /**
     * Go to the previous step
     */
    previousStep() {
        this.goToStep(this.currentStepIndex - 1);
    }

    /**
     * Finish the wizard
     */
    finish() {
        const currentStep = this.steps[this.currentStepIndex];
        
        // Validate final step if validation function exists
        if (currentStep.validate) {
            const isValid = currentStep.validate(this.data);
            if (!isValid) {
                return;
            }
        }

        // Process data if process function exists
        if (currentStep.process) {
            currentStep.process(this.data);
        }

        // Trigger finish event
        this.triggerEvent('finish', { data: this.data });
    }

    /**
     * Set wizard data
     * @param {Object} data - Data to set
     */
    setData(data) {
        this.data = { ...this.data, ...data };
        this.renderStepContent();
    }

    /**
     * Get wizard data
     * @returns {Object} Wizard data
     */
    getData() {
        return this.data;
    }

    /**
     * Add event listener
     * @param {string} event - Event name
     * @param {Function} callback - Event callback
     */
    on(event, callback) {
        if (!this.eventListeners[event]) {
            this.eventListeners[event] = [];
        }
        this.eventListeners[event].push(callback);
    }

    /**
     * Trigger event
     * @param {string} event - Event name
     * @param {Object} data - Event data
     */
    triggerEvent(event, data) {
        if (this.eventListeners[event]) {
            this.eventListeners[event].forEach(callback => {
                callback(data);
            });
        }
    }
}
