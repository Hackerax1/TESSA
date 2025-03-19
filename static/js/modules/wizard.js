/**
 * Wizard module - Handles the setup wizard functionality
 */
export default class Wizard {
    constructor() {
        // Cloud service mappings for goal selections
        this.cloudServiceMappings = {
            'media': ['netflix', 'spotify'],
            'files': ['google_photos', 'google_drive', 'dropbox'],
            'webhosting': ['github'],
            'productivity': ['google_calendar', 'google_docs', 'lastpass']
        };
    }

    /**
     * Set up the cloud services section in the wizard
     * @returns {void}
     */
    setupCloudServicesSection() {
        const step1 = document.getElementById('step1');
        
        // Create cloud services section if it doesn't exist
        if (!document.getElementById('cloud-services-container')) {
            const cloudServicesContainer = document.createElement('div');
            cloudServicesContainer.id = 'cloud-services-container';
            cloudServicesContainer.className = 'mt-4';
            
            const cloudServicesTitle = document.createElement('h5');
            cloudServicesTitle.textContent = 'What cloud services would you like to replace?';
            
            const cloudServicesDescription = document.createElement('p');
            cloudServicesDescription.className = 'text-muted';
            cloudServicesDescription.textContent = 'Select the cloud services you\'d like to replace with self-hosted alternatives';
            
            cloudServicesContainer.appendChild(cloudServicesTitle);
            cloudServicesContainer.appendChild(cloudServicesDescription);
            
            // Create the services grid
            const servicesGrid = document.createElement('div');
            servicesGrid.className = 'row mt-3';
            servicesGrid.id = 'cloud-services-grid';
            
            // Define cloud services to replace
            const cloudServices = [
                { id: 'google_photos', name: 'Google Photos', icon: 'bi-images' },
                { id: 'google_drive', name: 'Google Drive', icon: 'bi-cloud' },
                { id: 'dropbox', name: 'Dropbox', icon: 'bi-folder' },
                { id: 'netflix', name: 'Netflix', icon: 'bi-film' },
                { id: 'spotify', name: 'Spotify', icon: 'bi-music-note-beamed' },
                { id: 'lastpass', name: 'LastPass/1Password', icon: 'bi-key' },
                { id: 'github', name: 'GitHub', icon: 'bi-code-square' },
                { id: 'google_calendar', name: 'Google Calendar', icon: 'bi-calendar' },
                { id: 'google_docs', name: 'Google Docs', icon: 'bi-file-text' }
            ];
            
            // Create two columns for the services
            const col1 = document.createElement('div');
            col1.className = 'col-md-6';
            
            const col2 = document.createElement('div');
            col2.className = 'col-md-6';
            
            // Add services to columns
            cloudServices.forEach((service, index) => {
                const serviceCheck = document.createElement('div');
                serviceCheck.className = 'form-check mb-3';
                serviceCheck.innerHTML = `
                    <input class="form-check-input" type="checkbox" value="${service.id}" id="cloud${service.id}">
                    <label class="form-check-label" for="cloud${service.id}">
                        <i class="bi ${service.icon}"></i> ${service.name}
                    </label>
                `;
                
                // Add to appropriate column
                if (index < cloudServices.length / 2) {
                    col1.appendChild(serviceCheck);
                } else {
                    col2.appendChild(serviceCheck);
                }
            });
            
            servicesGrid.appendChild(col1);
            servicesGrid.appendChild(col2);
            cloudServicesContainer.appendChild(servicesGrid);
            
            // Add to step 1 before the "Other goals" section
            const otherGoalsSection = document.querySelector('#step1 .mt-4:last-child');
            step1.insertBefore(cloudServicesContainer, otherGoalsSection);
        }
    }

    /**
     * Update cloud services options based on selected goals
     * @returns {void}
     */
    updateCloudServicesOptions() {
        const selectedGoals = Array.from(document.querySelectorAll('#step1 input[type="checkbox"]:checked')).map(checkbox => checkbox.value);
        
        // Get all cloud service checkboxes
        const cloudServiceCheckboxes = document.querySelectorAll('#cloud-services-grid input[type="checkbox"]');
        
        // First, hide all cloud services
        cloudServiceCheckboxes.forEach(checkbox => {
            checkbox.closest('.form-check').style.display = 'none';
        });
        
        // Then show only the relevant ones
        if (selectedGoals.length > 0) {
            document.getElementById('cloud-services-container').style.display = 'block';
            
            // For each selected goal, show the relevant cloud services
            selectedGoals.forEach(goal => {
                if (this.cloudServiceMappings[goal]) {
                    this.cloudServiceMappings[goal].forEach(serviceId => {
                        const checkbox = document.getElementById(`cloud${serviceId}`);
                        if (checkbox) {
                            checkbox.closest('.form-check').style.display = 'block';
                        }
                    });
                }
            });
        } else {
            document.getElementById('cloud-services-container').style.display = 'none';
        }
    }

    /**
     * Process goal selections and update recommended services
     * @returns {void}
     */
    processGoalSelections() {
        // Get selected goals
        const selectedGoals = Array.from(document.querySelectorAll('#step1 input[type="checkbox"]:checked')).map(checkbox => checkbox.value);
        const otherGoals = document.getElementById('otherGoals').value;
        
        // Get selected cloud services
        const selectedCloudServices = Array.from(document.querySelectorAll('#cloud-services-grid input[type="checkbox"]:checked')).map(checkbox => checkbox.value);
        
        // Clear previous recommendations
        const recommendedServicesContainer = document.getElementById('recommended-services');
        recommendedServicesContainer.innerHTML = '';
        
        // Map goals to recommended services
        const serviceRecommendations = {
            'media': [
                { id: 'jellyfin', name: 'Jellyfin (Media Server)', description: 'Self-hosted media streaming solution' },
                { id: 'plex', name: 'Plex Media Server', description: 'Organize and stream your personal media' }
            ],
            'files': [
                { id: 'nextcloud', name: 'Nextcloud', description: 'Self-hosted productivity platform and file storage' },
                { id: 'seafile', name: 'Seafile', description: 'File sync and share solution' }
            ],
            'webhosting': [
                { id: 'apache', name: 'Apache HTTP Server', description: 'Web server software' },
                { id: 'nginx', name: 'NGINX', description: 'Web server and reverse proxy' },
                { id: 'gitea', name: 'Gitea', description: 'Self-hosted Git service' }
            ],
            'productivity': [
                { id: 'nextcloud', name: 'Nextcloud', description: 'Self-hosted productivity platform' },
                { id: 'bitwarden', name: 'Bitwarden', description: 'Open source password manager' }
            ],
            'gaming': [
                { id: 'minecraft', name: 'Minecraft Server', description: 'Host your own Minecraft world' },
                { id: 'steam_cache', name: 'Steam Cache', description: 'Cache Steam downloads for faster access' }
            ],
            'homeautomation': [
                { id: 'homeassistant', name: 'Home Assistant', description: 'Open source home automation platform' },
                { id: 'openhab', name: 'OpenHAB', description: 'Vendor and technology agnostic home automation' }
            ]
        };
        
        // Add cloud service specific recommendations
        const cloudServiceRecommendations = {
            'google_photos': { id: 'photoprism', name: 'PhotoPrism', description: 'Personal photo management' },
            'google_drive': { id: 'nextcloud', name: 'Nextcloud', description: 'Self-hosted file storage and sharing' },
            'dropbox': { id: 'seafile', name: 'Seafile', description: 'File sync and share solution' },
            'netflix': { id: 'jellyfin', name: 'Jellyfin', description: 'Free Software Media System' },
            'spotify': { id: 'navidrome', name: 'Navidrome', description: 'Modern Music Server' },
            'lastpass': { id: 'bitwarden', name: 'Bitwarden', description: 'Open source password manager' },
            'github': { id: 'gitea', name: 'Gitea', description: 'Self-hosted Git service' },
            'google_calendar': { id: 'nextcloud', name: 'Nextcloud Calendar', description: 'Self-hosted calendar' },
            'google_docs': { id: 'collabora', name: 'Collabora Online', description: 'Self-hosted office suite' }
        };
        
        // Create a set to avoid duplicate recommendations
        const recommendedServices = new Set();
        
        // Add recommendations based on goals
        selectedGoals.forEach(goal => {
            if (serviceRecommendations[goal]) {
                serviceRecommendations[goal].forEach(service => {
                    recommendedServices.add(JSON.stringify(service));
                });
            }
        });
        
        // Add recommendations based on cloud services
        selectedCloudServices.forEach(service => {
            if (cloudServiceRecommendations[service]) {
                recommendedServices.add(JSON.stringify(cloudServiceRecommendations[service]));
            }
        });
        
        // Create the recommendations UI
        if (recommendedServices.size > 0) {
            const servicesArray = Array.from(recommendedServices).map(service => JSON.parse(service));
            
            servicesArray.forEach(service => {
                const serviceCheck = document.createElement('div');
                serviceCheck.className = 'form-check mb-3';
                serviceCheck.innerHTML = `
                    <input class="form-check-input" type="checkbox" value="${service.id}" id="rec${service.id}" checked>
                    <label class="form-check-label" for="rec${service.id}">
                        ${service.name}
                        <small class="text-muted d-block">${service.description}</small>
                    </label>
                `;
                recommendedServicesContainer.appendChild(serviceCheck);
            });
        } else {
            recommendedServicesContainer.innerHTML = '<div class="alert alert-info">No services recommended based on your selections</div>';
        }
        
        // Move to the next step
        const nextTab = new bootstrap.Tab(document.getElementById('step2-tab'));
        nextTab.show();
    }

    /**
     * Detect system resources for the wizard
     * @returns {void}
     */
    detectSystemResources() {
        // In a real app, this would detect actual system resources
        // For this example, we'll just set some default values
        document.getElementById('cpuCores').value = '4';
        document.getElementById('ramSize').value = '8';
        document.getElementById('diskSize').value = '500';
        document.getElementById('networkSpeed').value = '1000';
    }

    /**
     * Deploy services based on wizard selections
     * @returns {Promise<void>}
     */
    async deployServices() {
        // Collect selected goals
        const selectedGoals = Array.from(document.querySelectorAll('#step1 input[type="checkbox"]:checked')).map(checkbox => checkbox.value);
        const otherGoals = document.getElementById('otherGoals').value;

        // Collect cloud services to replace
        const cloudServices = Array.from(document.querySelectorAll('#cloud-services-container input[type="checkbox"]:checked')).map(checkbox => checkbox.value);

        // Collect resource information
        const resources = {
            cpuCores: document.getElementById('cpuCores').value,
            ramSize: document.getElementById('ramSize').value,
            diskSize: document.getElementById('diskSize').value,
            networkSpeed: document.getElementById('networkSpeed').value
        };

        // Collect recommended services
        const recommendedServices = Array.from(document.querySelectorAll('#recommended-services input[type="checkbox"]:checked')).map(checkbox => checkbox.value);

        // Display summary
        document.getElementById('summary-goals').innerHTML = selectedGoals.join(', ') + (otherGoals ? ', ' + otherGoals : '');
        document.getElementById('summary-resources').innerHTML = `CPU Cores: ${resources.cpuCores}, RAM: ${resources.ramSize} GB, Disk: ${resources.diskSize} GB, Network: ${resources.networkSpeed} Mbps`;
        document.getElementById('summary-services').innerHTML = recommendedServices.join(', ');

        // Send deployment request to the server
        try {
            const response = await fetch('/deploy', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    goals: selectedGoals, 
                    otherGoals, 
                    cloudServices,
                    resources, 
                    services: recommendedServices 
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                alert('Services deployed successfully!');
                // Close the modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('setupWizardModal'));
                modal.hide();
                return true;
            } else {
                alert('Error deploying services: ' + data.error);
                return false;
            }
        } catch (error) {
            console.error('Error deploying services:', error);
            alert('Error deploying services: ' + error.message);
            return false;
        }
    }
}
