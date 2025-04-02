/**
 * Version Control System Integration Module
 * Provides UI components for integrating with version control systems
 */

import { showToast } from './notifications.js';
import { apiRequest } from './api.js';

export class VcsIntegration {
    constructor() {
        this.repositoriesContainer = document.getElementById('vcs-repositories-container');
        this.setupFormContainer = document.getElementById('vcs-setup-form-container');
    }

    /**
     * Initialize the VCS integration module
     */
    async init() {
        // Set up event listeners
        document.addEventListener('click', (event) => {
            if (event.target.matches('.setup-vcs-btn')) {
                this.showSetupForm();
            } else if (event.target.matches('.sync-repo-btn')) {
                const repoName = event.target.dataset.repo;
                this.syncRepository(repoName);
            } else if (event.target.matches('.commit-export-btn')) {
                const directory = event.target.dataset.directory;
                const repoName = event.target.dataset.repo;
                this.commitExport(directory, repoName);
            }
        });

        // Initialize repository list if container exists
        if (this.repositoriesContainer) {
            this.listRepositories();
        }

        // Initialize setup form if container exists
        if (this.setupFormContainer) {
            this.renderSetupForm();
        }
    }

    /**
     * List available repositories
     */
    async listRepositories() {
        try {
            const response = await apiRequest('GET', '/api/export/vcs/repositories');
            
            if (response && response.success) {
                this.renderRepositories(response.repositories);
            } else {
                this.renderNoRepositories();
            }
        } catch (error) {
            console.error('Error listing repositories:', error);
            this.renderNoRepositories();
        }
    }

    /**
     * Render repositories list
     * @param {Array} repositories - List of repositories
     */
    renderRepositories(repositories) {
        if (!this.repositoriesContainer) return;

        if (!repositories || repositories.length === 0) {
            this.renderNoRepositories();
            return;
        }

        let content = `
            <div class="card">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <h5>Version Control Repositories</h5>
                    <button class="btn btn-sm btn-primary setup-vcs-btn">
                        <i class="fas fa-plus"></i> Add Repository
                    </button>
                </div>
                <div class="card-body">
                    <div class="table-responsive">
                        <table class="table table-hover">
                            <thead>
                                <tr>
                                    <th>Name</th>
                                    <th>Remote URL</th>
                                    <th>Branch</th>
                                    <th>Last Commit</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
        `;

        repositories.forEach(repo => {
            content += `
                <tr>
                    <td>${repo.name}</td>
                    <td><code>${repo.remote_url || 'N/A'}</code></td>
                    <td>${repo.current_branch || 'N/A'}</td>
                    <td>
                        ${repo.last_commit ? 
                            `<small>${repo.last_commit.message} <br>
                            <span class="text-muted">${repo.last_commit.author} - ${repo.last_commit.date}</span></small>` : 
                            'No commits yet'}
                    </td>
                    <td>
                        <button class="btn btn-sm btn-outline-primary sync-repo-btn" data-repo="${repo.name}">
                            <i class="fas fa-sync"></i> Sync
                        </button>
                    </td>
                </tr>
            `;
        });

        content += `
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        `;

        this.repositoriesContainer.innerHTML = content;
    }

    /**
     * Render no repositories message
     */
    renderNoRepositories() {
        if (!this.repositoriesContainer) return;

        this.repositoriesContainer.innerHTML = `
            <div class="card">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <h5>Version Control Repositories</h5>
                    <button class="btn btn-sm btn-primary setup-vcs-btn">
                        <i class="fas fa-plus"></i> Add Repository
                    </button>
                </div>
                <div class="card-body text-center py-5">
                    <div class="mb-3">
                        <i class="fas fa-code-branch fa-3x text-muted"></i>
                    </div>
                    <h5>No Repositories Found</h5>
                    <p class="text-muted">You haven't set up any version control repositories yet.</p>
                    <button class="btn btn-primary setup-vcs-btn">
                        <i class="fas fa-plus"></i> Set Up Repository
                    </button>
                </div>
            </div>
        `;
    }

    /**
     * Render setup form
     */
    renderSetupForm() {
        if (!this.setupFormContainer) return;

        this.setupFormContainer.innerHTML = `
            <div class="card">
                <div class="card-header">
                    <h5>Set Up Version Control Repository</h5>
                </div>
                <div class="card-body">
                    <form id="vcs-setup-form">
                        <div class="mb-3">
                            <label for="vcs-type" class="form-label">Repository Type</label>
                            <select class="form-select" id="vcs-type" required>
                                <option value="git" selected>Git</option>
                            </select>
                            <div class="form-text">Currently only Git repositories are supported.</div>
                        </div>
                        <div class="mb-3">
                            <label for="repository-url" class="form-label">Repository URL</label>
                            <input type="text" class="form-control" id="repository-url" 
                                placeholder="https://github.com/username/repo.git" required>
                        </div>
                        <div class="mb-3">
                            <label for="branch" class="form-label">Branch</label>
                            <input type="text" class="form-control" id="branch" 
                                placeholder="main" value="main">
                        </div>
                        <div class="mb-3">
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" id="use-auth">
                                <label class="form-check-label" for="use-auth">
                                    Use authentication
                                </label>
                            </div>
                        </div>
                        <div id="auth-fields" class="d-none">
                            <div class="mb-3">
                                <label for="username" class="form-label">Username</label>
                                <input type="text" class="form-control" id="username">
                            </div>
                            <div class="mb-3">
                                <label for="password" class="form-label">Password / Token</label>
                                <input type="password" class="form-control" id="password">
                                <div class="form-text">For GitHub, use a personal access token instead of your password.</div>
                            </div>
                        </div>
                        <div class="d-flex justify-content-end">
                            <button type="button" class="btn btn-secondary me-2" id="cancel-setup-btn">Cancel</button>
                            <button type="submit" class="btn btn-primary">Set Up Repository</button>
                        </div>
                    </form>
                </div>
            </div>
        `;

        // Set up event listeners for the form
        const form = document.getElementById('vcs-setup-form');
        const useAuthCheckbox = document.getElementById('use-auth');
        const authFields = document.getElementById('auth-fields');
        const cancelBtn = document.getElementById('cancel-setup-btn');

        if (useAuthCheckbox && authFields) {
            useAuthCheckbox.addEventListener('change', () => {
                authFields.classList.toggle('d-none', !useAuthCheckbox.checked);
            });
        }

        if (form) {
            form.addEventListener('submit', (event) => {
                event.preventDefault();
                this.setupRepository();
            });
        }

        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => {
                this.hideSetupForm();
            });
        }
    }

    /**
     * Show setup form
     */
    showSetupForm() {
        if (this.setupFormContainer) {
            this.setupFormContainer.classList.remove('d-none');
        }
    }

    /**
     * Hide setup form
     */
    hideSetupForm() {
        if (this.setupFormContainer) {
            this.setupFormContainer.classList.add('d-none');
        }
    }

    /**
     * Set up a repository
     */
    async setupRepository() {
        const vcsType = document.getElementById('vcs-type').value;
        const repositoryUrl = document.getElementById('repository-url').value;
        const branch = document.getElementById('branch').value;
        const useAuth = document.getElementById('use-auth').checked;
        const username = useAuth ? document.getElementById('username').value : null;
        const password = useAuth ? document.getElementById('password').value : null;

        if (!repositoryUrl) {
            showToast('Repository URL is required', 'error');
            return;
        }

        try {
            const response = await apiRequest('POST', '/api/export/vcs/setup', {
                vcs_type: vcsType,
                repository_url: repositoryUrl,
                branch: branch,
                username: username,
                password: password
            });

            if (response && response.success) {
                showToast(response.message, 'success');
                this.hideSetupForm();
                this.listRepositories();
            } else {
                showToast(response.message || 'Failed to set up repository', 'error');
            }
        } catch (error) {
            console.error('Error setting up repository:', error);
            showToast('Error setting up repository', 'error');
        }
    }

    /**
     * Sync a repository
     * @param {string} repoName - Repository name
     */
    async syncRepository(repoName) {
        try {
            const response = await apiRequest('POST', '/api/export/vcs/sync', {
                repo_name: repoName
            });

            if (response && response.success) {
                showToast(response.message, 'success');
                this.listRepositories();
            } else {
                showToast(response.message || 'Failed to sync repository', 'error');
            }
        } catch (error) {
            console.error('Error syncing repository:', error);
            showToast('Error syncing repository', 'error');
        }
    }

    /**
     * Commit exported files to a repository
     * @param {string} directory - Directory containing exported files
     * @param {string} repoName - Repository name
     */
    async commitExport(directory, repoName) {
        try {
            const message = prompt('Enter commit message:', 'Update configuration via TESSA export');
            
            if (message === null) {
                // User cancelled
                return;
            }

            const response = await apiRequest('POST', '/api/export/vcs/commit', {
                directory: directory,
                message: message,
                repo_name: repoName
            });

            if (response && response.success) {
                showToast(response.message, 'success');
            } else {
                showToast(response.message || 'Failed to commit export', 'error');
            }
        } catch (error) {
            console.error('Error committing export:', error);
            showToast('Error committing export', 'error');
        }
    }
}

// Initialize module
document.addEventListener('DOMContentLoaded', () => {
    const vcsIntegration = new VcsIntegration();
    vcsIntegration.init();
    
    // Export to global scope for debugging
    window.vcsIntegration = vcsIntegration;
});

export default VcsIntegration;
