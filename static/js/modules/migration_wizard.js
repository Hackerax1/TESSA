/**
 * Migration Wizard Module
 * Provides UI for cross-platform migration tools
 */

import { WizardBase } from './migration_wizard/wizard_base.js';
import { PlatformSelectionStep } from './migration_wizard/steps/platform_selection.js';
import { CredentialsStep } from './migration_wizard/steps/credentials.js';
import { AnalysisStep } from './migration_wizard/steps/analysis.js';
import { ResourceSelectionStep } from './migration_wizard/steps/resource_selection.js';
import { TargetSelectionStep } from './migration_wizard/steps/target_selection.js';
import { MigrationPlanStep } from './migration_wizard/steps/migration_plan.js';
import { ExecutionStep } from './migration_wizard/steps/execution.js';
import { SummaryStep } from './migration_wizard/steps/summary.js';
import { apiRequest } from './api.js';
import { showToast } from './notifications.js';

export class MigrationWizard {
    constructor() {
        this.wizard = null;
        this.activeMigrationId = null;
        this.migrationStatus = null;
        this.statusInterval = null;
    }

    /**
     * Initialize the migration wizard
     */
    init() {
        const steps = [
            {
                title: 'Select Platform',
                render: PlatformSelectionStep.render,
                init: PlatformSelectionStep.init,
                validate: PlatformSelectionStep.validate,
                process: PlatformSelectionStep.process
            },
            {
                title: 'Credentials',
                render: CredentialsStep.render,
                init: CredentialsStep.init,
                validate: CredentialsStep.validate,
                process: CredentialsStep.process
            },
            {
                title: 'Analysis',
                render: AnalysisStep.render,
                init: AnalysisStep.init,
                validate: AnalysisStep.validate,
                process: AnalysisStep.process
            },
            {
                title: 'Select Resources',
                render: ResourceSelectionStep.render,
                init: ResourceSelectionStep.init,
                validate: ResourceSelectionStep.validate,
                process: ResourceSelectionStep.process
            },
            {
                title: 'Target Selection',
                render: TargetSelectionStep.render,
                init: TargetSelectionStep.init,
                validate: TargetSelectionStep.validate,
                process: TargetSelectionStep.process
            },
            {
                title: 'Migration Plan',
                render: MigrationPlanStep.render,
                init: MigrationPlanStep.init,
                validate: MigrationPlanStep.validate,
                process: MigrationPlanStep.process
            },
            {
                title: 'Execution',
                render: ExecutionStep.render,
                init: ExecutionStep.init,
                validate: ExecutionStep.validate,
                process: ExecutionStep.process
            },
            {
                title: 'Summary',
                render: SummaryStep.render,
                init: SummaryStep.init
            }
        ];

        this.wizard = new WizardBase('migration-wizard-container', steps);
        this.wizard.init();

        // Set up event listeners
        this.wizard.on('finish', this.onFinish.bind(this));
        this.wizard.on('stepChange', this.onStepChange.bind(this));

        // Check for existing migrations
        this.loadExistingMigrations();

        // Add wizard instance to window for debugging
        window.migrationWizard = this;
    }

    /**
     * Load existing migrations
     */
    async loadExistingMigrations() {
        try {
            const response = await apiRequest('GET', '/api/migration/list');
            
            if (response && response.success && response.migrations && response.migrations.length > 0) {
                // Add existing migrations to wizard data
                this.wizard.setData({ existingMigrations: response.migrations });
            }
        } catch (error) {
            console.error('Error loading existing migrations:', error);
        }
    }

    /**
     * Handle step change event
     * @param {Object} data - Step change event data
     */
    onStepChange(data) {
        const { stepIndex, step } = data;
        
        // Clear status interval when changing steps
        if (this.statusInterval) {
            clearInterval(this.statusInterval);
            this.statusInterval = null;
        }

        // Start status polling for execution step
        if (step.title === 'Execution' && this.activeMigrationId) {
            this.startStatusPolling();
        }
    }

    /**
     * Start polling for migration status
     */
    startStatusPolling() {
        if (!this.activeMigrationId) return;

        // Poll every 5 seconds
        this.statusInterval = setInterval(async () => {
            try {
                const response = await apiRequest('GET', `/api/migration/status/${this.activeMigrationId}`);
                
                if (response && response.success) {
                    this.migrationStatus = response;
                    
                    // Update wizard data with status
                    this.wizard.setData({ migrationStatus: response });
                    
                    // Check if migration is complete
                    if (response.status === 'completed' || response.status === 'failed' || response.status === 'cancelled') {
                        clearInterval(this.statusInterval);
                        this.statusInterval = null;
                        
                        // Move to summary step if completed
                        if (response.status === 'completed') {
                            this.wizard.goToStep(7); // Summary step
                        }
                    }
                }
            } catch (error) {
                console.error('Error polling migration status:', error);
            }
        }, 5000);
    }

    /**
     * Handle wizard finish event
     * @param {Object} data - Finish event data
     */
    onFinish(data) {
        // Show completion message
        showToast('Migration process completed', 'success');
        
        // Redirect to dashboard or reload page
        setTimeout(() => {
            window.location.href = '/dashboard';
        }, 2000);
    }

    /**
     * Execute migration
     * @param {Object} migrationPlan - Migration plan
     * @returns {Promise<Object>} Migration result
     */
    async executeMigration(migrationPlan) {
        try {
            if (!this.activeMigrationId) {
                throw new Error('No active migration ID');
            }

            const response = await apiRequest('POST', '/api/migration/execute', {
                migration_id: this.activeMigrationId,
                migration_plan: migrationPlan
            });

            if (response && response.success) {
                this.startStatusPolling();
                return response;
            } else {
                throw new Error(response.message || 'Failed to execute migration');
            }
        } catch (error) {
            console.error('Error executing migration:', error);
            showToast(`Error executing migration: ${error.message}`, 'error');
            return { success: false, message: error.message };
        }
    }

    /**
     * Cancel migration
     * @returns {Promise<Object>} Cancellation result
     */
    async cancelMigration() {
        try {
            if (!this.activeMigrationId) {
                throw new Error('No active migration ID');
            }

            const response = await apiRequest('POST', `/api/migration/cancel/${this.activeMigrationId}`);

            if (response && response.success) {
                if (this.statusInterval) {
                    clearInterval(this.statusInterval);
                    this.statusInterval = null;
                }
                
                showToast('Migration cancelled', 'warning');
                return response;
            } else {
                throw new Error(response.message || 'Failed to cancel migration');
            }
        } catch (error) {
            console.error('Error cancelling migration:', error);
            showToast(`Error cancelling migration: ${error.message}`, 'error');
            return { success: false, message: error.message };
        }
    }

    /**
     * Set active migration ID
     * @param {string} migrationId - Migration ID
     */
    setActiveMigrationId(migrationId) {
        this.activeMigrationId = migrationId;
        this.wizard.setData({ activeMigrationId: migrationId });
    }
}

// Export singleton instance
export default MigrationWizard;
