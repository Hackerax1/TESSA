/**
 * UI module - Handles UI-related functionality
 */
export default class UI {
    /**
     * Add a message to the chat interface
     * @param {string} text - Message text
     * @param {string} type - Message type ('user' or 'system')
     * @param {HTMLElement} chatBody - Chat body element
     */
    static addMessage(text, type, chatBody) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        messageDiv.textContent = text;
        chatBody.appendChild(messageDiv);
        chatBody.scrollTop = chatBody.scrollHeight;
    }

    /**
     * Show an error message in the specified containers
     * @param {string} message - Error message
     * @param {Array<string>} containerIds - Array of container IDs
     */
    static showError(message, containerIds = ['cluster-status', 'vm-list']) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'alert alert-danger';
        errorDiv.textContent = message;
        
        containerIds.forEach(containerId => {
            const container = document.getElementById(containerId);
            if (container) {
                container.innerHTML = '';
                container.appendChild(errorDiv.cloneNode(true));
            }
        });
    }

    /**
     * Adjust UI based on user experience level
     * @param {string} level - Experience level ('beginner', 'intermediate', 'advanced')
     */
    static adjustUIForExperienceLevel(level) {
        // Hide/show elements based on experience level
        const advancedElements = document.querySelectorAll('.advanced-feature');
        const intermediateElements = document.querySelectorAll('.intermediate-feature');
        const beginnerHelp = document.querySelectorAll('.beginner-help');
        
        switch (level) {
            case 'beginner':
                advancedElements.forEach(el => el.classList.add('d-none'));
                intermediateElements.forEach(el => el.classList.add('d-none'));
                beginnerHelp.forEach(el => el.classList.remove('d-none'));
                break;
            case 'intermediate':
                advancedElements.forEach(el => el.classList.add('d-none'));
                intermediateElements.forEach(el => el.classList.remove('d-none'));
                beginnerHelp.forEach(el => el.classList.add('d-none'));
                break;
            case 'advanced':
                advancedElements.forEach(el => el.classList.remove('d-none'));
                intermediateElements.forEach(el => el.classList.remove('d-none'));
                beginnerHelp.forEach(el => el.classList.add('d-none'));
                break;
        }
    }

    /**
     * Update VM list in the UI
     * @param {Object} data - VM data
     * @param {HTMLElement} vmList - VM list container
     */
    static updateVMList(data, vmList) {
        vmList.innerHTML = '';
        if (data.error) {
            vmList.innerHTML = `
                <div class="alert alert-danger" role="alert">
                    ${data.error}
                </div>`;
            return;
        }
        
        if (!data.vms || data.vms.length === 0) {
            vmList.innerHTML = `
                <div class="alert alert-info" role="alert">
                    No virtual machines found
                </div>`;
            return;
        }

        data.vms.forEach(vm => {
            const card = document.createElement('div');
            card.className = `card vm-card ${vm.status === 'running' ? 'border-success' : 'border-danger'}`;
            card.innerHTML = `
                <div class="card-body">
                    <h5 class="card-title">VM ${vm.id} - ${vm.name}</h5>
                    <p class="card-text">
                        Status: <span class="badge bg-${vm.status === 'running' ? 'success' : 'danger'}">${vm.status}</span><br>
                        CPU: ${vm.cpu} cores | Memory: ${vm.memory.toFixed(1)} MB | Disk: ${vm.disk.toFixed(1)} GB
                    </p>
                </div>
            `;
            vmList.appendChild(card);
        });
    }

    /**
     * Update cluster status in the UI
     * @param {Object} data - Cluster status data
     * @param {HTMLElement} clusterStatus - Cluster status container
     */
    static updateClusterStatus(data, clusterStatus) {
        clusterStatus.innerHTML = '';
        if (data.error) {
            clusterStatus.innerHTML = `
                <div class="alert alert-danger" role="alert">
                    ${data.error}
                </div>`;
            return;
        }

        if (!data.status || data.status.length === 0) {
            clusterStatus.innerHTML = `
                <div class="alert alert-info" role="alert">
                    No cluster nodes found
                </div>`;
            return;
        }

        data.status.forEach(node => {
            const nodeElement = document.createElement('div');
            nodeElement.className = 'mb-2';
            nodeElement.innerHTML = `
                <strong>${node.name}</strong>
                <span class="badge bg-${node.status === 'online' ? 'success' : 'danger'} ms-2">${node.status}</span>
            `;
            clusterStatus.appendChild(nodeElement);
        });
    }
}
