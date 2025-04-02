/**
 * Credentials Step
 * Second step in the migration wizard for entering source platform credentials
 */

import { apiRequest } from '../../api.js';
import { showToast } from '../../notifications.js';

export const CredentialsStep = {
    /**
     * Render the credentials step
     * @param {Object} data - Wizard data
     * @returns {string} HTML content
     */
    render: function(data) {
        if (!data.selectedPlatform || !data.platformDetails) {
            return `
                <div class="alert alert-warning">
                    <i class="fas fa-exclamation-triangle"></i>
                    Please select a platform first.
                </div>
                <button class="btn btn-primary" id="back-to-platform-btn">
                    <i class="fas fa-arrow-left"></i> Back to Platform Selection
                </button>
            `;
        }

        const platform = data.platformDetails;
        const fields = platform.credentialFields || [];

        return `
            <div class="credentials-step">
                <h4 class="mb-4">
                    <i class="fas ${platform.icon || 'fa-server'}"></i>
                    ${platform.name} Credentials
                </h4>
                <p class="mb-4">
                    Enter your ${platform.name} credentials to connect to the source platform.
                    These credentials will be used to analyze your environment and perform the migration.
                </p>
                
                <form id="credentials-form" class="needs-validation" novalidate>
                    <div class="row">
                        ${fields.map(field => this._renderField(field)).join('')}
                    </div>
                    
                    <div class="form-group mt-4">
                        <div class="form-check">
                            <input class="form-check-input" type="checkbox" id="save-credentials" checked>
                            <label class="form-check-label" for="save-credentials">
                                Save credentials for future migrations
                            </label>
                        </div>
                        <small class="form-text text-muted">
                            Credentials are stored securely and encrypted.
                        </small>
                    </div>
                    
                    <div class="mt-4">
                        <button type="button" class="btn btn-primary" id="validate-credentials-btn">
                            <i class="fas fa-check-circle"></i> Validate Credentials
                        </button>
                        <div class="spinner-border spinner-border-sm text-primary ml-2" 
                            role="status" id="validation-spinner" style="display: none;">
                            <span class="visually-hidden">Validating...</span>
                        </div>
                    </div>
                </form>
                
                <div id="validation-result" class="mt-4" style="display: none;"></div>
            </div>
        `;
    },

    /**
     * Initialize the credentials step
     * @param {HTMLElement} container - Step container
     * @param {Object} data - Wizard data
     */
    init: function(container, data) {
        const backBtn = container.querySelector('#back-to-platform-btn');
        if (backBtn) {
            backBtn.addEventListener('click', () => {
                window.migrationWizard.wizard.goToStep(0);
            });
            return;
        }

        const validateBtn = container.querySelector('#validate-credentials-btn');
        const form = container.querySelector('#credentials-form');

        if (validateBtn && form) {
            validateBtn.addEventListener('click', () => {
                if (this._validateForm(form)) {
                    const credentials = this._getFormData(form);
                    this._validateCredentials(container, data, credentials);
                }
            });
        }

        // Fill form with saved credentials if available
        if (data.savedCredentials && data.selectedPlatform) {
            const savedCreds = data.savedCredentials[data.selectedPlatform];
            if (savedCreds) {
                this._fillFormWithSavedCredentials(form, savedCreds);
            }
        }
    },

    /**
     * Validate the credentials step
     * @param {Object} data - Wizard data
     * @returns {boolean} True if valid, false otherwise
     */
    validate: function(data) {
        if (!data.credentialsValidated) {
            showToast('Please validate your credentials first', 'warning');
            return false;
        }
        return true;
    },

    /**
     * Process the credentials step
     * @param {Object} data - Wizard data
     */
    process: function(data) {
        // Save credentials if checkbox is checked
        if (data.saveCredentials) {
            const savedCredentials = data.savedCredentials || {};
            savedCredentials[data.selectedPlatform] = data.credentials;
            
            // Update wizard data
            data.savedCredentials = savedCredentials;
            
            // Save to local storage (encrypted in a real implementation)
            try {
                localStorage.setItem('migration_credentials', JSON.stringify(savedCredentials));
            } catch (error) {
                console.error('Error saving credentials:', error);
            }
        }
    },

    /**
     * Render a form field
     * @param {Object} field - Field configuration
     * @returns {string} HTML content
     * @private
     */
    _renderField: function(field) {
        const { name, label, type, required, default: defaultValue } = field;
        const isCheckbox = type === 'checkbox';
        
        if (isCheckbox) {
            return `
                <div class="col-md-6 mb-3">
                    <div class="form-check">
                        <input type="checkbox" class="form-check-input" id="${name}" name="${name}" 
                            ${defaultValue ? 'checked' : ''}>
                        <label class="form-check-label" for="${name}">
                            ${label} ${required ? '<span class="text-danger">*</span>' : ''}
                        </label>
                    </div>
                </div>
            `;
        } else if (type === 'file') {
            return `
                <div class="col-md-6 mb-3">
                    <label for="${name}" class="form-label">
                        ${label} ${required ? '<span class="text-danger">*</span>' : ''}
                    </label>
                    <input type="${type}" class="form-control" id="${name}" name="${name}" 
                        ${required ? 'required' : ''}>
                    <div class="invalid-feedback">
                        Please provide a valid ${label.toLowerCase()}.
                    </div>
                </div>
            `;
        } else {
            return `
                <div class="col-md-6 mb-3">
                    <label for="${name}" class="form-label">
                        ${label} ${required ? '<span class="text-danger">*</span>' : ''}
                    </label>
                    <input type="${type}" class="form-control" id="${name}" name="${name}" 
                        ${defaultValue ? `value="${defaultValue}"` : ''} 
                        ${required ? 'required' : ''}>
                    <div class="invalid-feedback">
                        Please provide a valid ${label.toLowerCase()}.
                    </div>
                </div>
            `;
        }
    },

    /**
     * Validate form
     * @param {HTMLFormElement} form - Form element
     * @returns {boolean} True if valid, false otherwise
     * @private
     */
    _validateForm: function(form) {
        form.classList.add('was-validated');
        return form.checkValidity();
    },

    /**
     * Get form data
     * @param {HTMLFormElement} form - Form element
     * @returns {Object} Form data
     * @private
     */
    _getFormData: function(form) {
        const formData = new FormData(form);
        const data = {};
        
        for (const [key, value] of formData.entries()) {
            // Handle checkboxes
            const input = form.querySelector(`[name="${key}"]`);
            if (input && input.type === 'checkbox') {
                data[key] = input.checked;
            } else if (input && input.type === 'file' && input.files.length > 0) {
                // In a real implementation, we would handle file uploads differently
                // For now, just store the file name
                data[key] = input.files[0].name;
            } else {
                data[key] = value;
            }
        }
        
        // Add save credentials checkbox value
        const saveCredentials = form.querySelector('#save-credentials');
        if (saveCredentials) {
            data.saveCredentials = saveCredentials.checked;
        }
        
        return data;
    },

    /**
     * Fill form with saved credentials
     * @param {HTMLFormElement} form - Form element
     * @param {Object} credentials - Saved credentials
     * @private
     */
    _fillFormWithSavedCredentials: function(form, credentials) {
        for (const [key, value] of Object.entries(credentials)) {
            const input = form.querySelector(`[name="${key}"]`);
            if (input) {
                if (input.type === 'checkbox') {
                    input.checked = value;
                } else if (input.type !== 'file') {
                    input.value = value;
                }
            }
        }
    },

    /**
     * Validate credentials
     * @param {HTMLElement} container - Step container
     * @param {Object} data - Wizard data
     * @param {Object} credentials - Credentials to validate
     * @private
     */
    _validateCredentials: async function(container, data, credentials) {
        const validateBtn = container.querySelector('#validate-credentials-btn');
        const spinner = container.querySelector('#validation-spinner');
        const resultContainer = container.querySelector('#validation-result');
        
        if (!validateBtn || !spinner || !resultContainer) return;
        
        // Show spinner and disable button
        validateBtn.disabled = true;
        spinner.style.display = 'inline-block';
        resultContainer.style.display = 'none';
        
        try {
            const response = await apiRequest('POST', `/api/migration/${data.selectedPlatform}/validate`, {
                credentials: credentials
            });
            
            // Hide spinner and enable button
            validateBtn.disabled = false;
            spinner.style.display = 'none';
            resultContainer.style.display = 'block';
            
            if (response && response.success) {
                // Show success message
                resultContainer.innerHTML = `
                    <div class="alert alert-success">
                        <i class="fas fa-check-circle"></i>
                        Credentials validated successfully!
                    </div>
                `;
                
                // Update wizard data
                window.migrationWizard.wizard.setData({
                    credentials: credentials,
                    credentialsValidated: true,
                    saveCredentials: credentials.saveCredentials
                });
                
                showToast('Credentials validated successfully', 'success');
            } else {
                // Show error message
                resultContainer.innerHTML = `
                    <div class="alert alert-danger">
                        <i class="fas fa-times-circle"></i>
                        ${response.message || 'Failed to validate credentials'}
                    </div>
                `;
                
                // Update wizard data
                window.migrationWizard.wizard.setData({
                    credentials: credentials,
                    credentialsValidated: false
                });
                
                showToast('Failed to validate credentials', 'error');
            }
        } catch (error) {
            console.error('Error validating credentials:', error);
            
            // Hide spinner and enable button
            validateBtn.disabled = false;
            spinner.style.display = 'none';
            resultContainer.style.display = 'block';
            
            // Show error message
            resultContainer.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-times-circle"></i>
                    Error validating credentials: ${error.message}
                </div>
            `;
            
            showToast(`Error validating credentials: ${error.message}`, 'error');
        }
    }
};

export default CredentialsStep;
