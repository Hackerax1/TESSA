/**
 * Shortcuts module for managing user-specific command shortcuts
 */
class Shortcuts {
    constructor() {
        this.shortcuts = [];
        this.categories = [];
        this.draggedItem = null;
    }

    /**
     * Initialize the shortcuts module
     */
    async initialize() {
        try {
            await this.loadShortcuts();
            this.setupEventListeners();
            this.setupCategoryTabs();
            this.setupIconPreview();
            this.setupKeyboardShortcutRecording();
            return true;
        } catch (error) {
            console.error('Error initializing shortcuts:', error);
            return false;
        }
    }

    /**
     * Load shortcuts from the server
     * @param {HTMLElement} container - Optional container to render shortcuts into
     */
    async loadShortcuts(container = null) {
        try {
            const userId = localStorage.getItem('user_id');
            if (!userId) {
                console.error('No user ID found');
                return false;
            }

            const response = await fetch(`/shortcuts/${userId}`);
            if (!response.ok) {
                throw new Error(`Failed to load shortcuts: ${response.statusText}`);
            }

            const data = await response.json();
            this.shortcuts = data;

            // Load categories
            await this.loadCategories();

            // Render shortcuts if container provided
            if (container) {
                this.renderShortcuts(container);
            }

            return true;
        } catch (error) {
            console.error('Error loading shortcuts:', error);
            return false;
        }
    }

    /**
     * Load shortcut categories from the server
     */
    async loadCategories() {
        try {
            const userId = localStorage.getItem('user_id');
            if (!userId) {
                console.error('No user ID found');
                return false;
            }

            const response = await fetch(`/shortcuts/${userId}/categories`);
            if (!response.ok) {
                throw new Error(`Failed to load shortcut categories: ${response.statusText}`);
            }

            const data = await response.json();
            this.categories = data.categories || [];
            return true;
        } catch (error) {
            console.error('Error loading shortcut categories:', error);
            return false;
        }
    }

    /**
     * Render shortcuts into a container
     * @param {HTMLElement} container - Container to render shortcuts into
     * @param {string} category - Optional category to filter shortcuts by
     */
    renderShortcuts(container, category = null) {
        if (!container) return;

        // Clear container
        container.innerHTML = '';

        // Filter shortcuts by category if provided
        const filteredShortcuts = category && category !== 'all'
            ? this.shortcuts.filter(s => s.category === category)
            : this.shortcuts;

        if (filteredShortcuts.length === 0) {
            container.innerHTML = `
                <div class="shortcuts-empty-state">
                    <i class="bi bi-bookmark-plus"></i>
                    <p>No shortcuts found in this category.</p>
                    <button class="btn btn-sm btn-primary" data-bs-toggle="modal" data-bs-target="#addShortcutModal">
                        Add Your First Shortcut
                    </button>
                </div>
            `;
            return;
        }

        // Create shortcut list
        const shortcutList = document.createElement('div');
        shortcutList.className = 'list-group shortcut-list';
        shortcutList.setAttribute('data-shortcut-list', '');

        // Add shortcuts to list
        filteredShortcuts.forEach(shortcut => {
            const shortcutItem = document.createElement('div');
            shortcutItem.className = 'list-group-item list-group-item-action d-flex justify-content-between align-items-center shortcut-item';
            shortcutItem.setAttribute('data-shortcut-id', shortcut.id);
            shortcutItem.setAttribute('draggable', 'true');

            // Icon and name
            const nameSection = document.createElement('div');
            nameSection.className = 'd-flex align-items-center';
            
            // Drag handle
            const dragHandle = document.createElement('div');
            dragHandle.className = 'drag-handle me-2';
            dragHandle.innerHTML = '<i class="bi bi-grip-vertical text-muted"></i>';
            nameSection.appendChild(dragHandle);

            // Icon
            if (shortcut.icon) {
                const icon = document.createElement('i');
                icon.className = `bi ${shortcut.icon} me-2`;
                if (shortcut.color) {
                    icon.style.color = shortcut.color;
                }
                nameSection.appendChild(icon);
            }

            // Name and description
            const textContent = document.createElement('div');
            textContent.className = 'shortcut-text';
            
            const nameWrapper = document.createElement('div');
            nameWrapper.className = 'd-flex align-items-center';
            
            const name = document.createElement('div');
            name.className = 'shortcut-name';
            name.textContent = shortcut.name;
            nameWrapper.appendChild(name);
            
            // Keyboard shortcut if available
            if (shortcut.shortcut_key) {
                const keyBadge = document.createElement('span');
                keyBadge.className = 'shortcut-key ms-2';
                keyBadge.textContent = shortcut.shortcut_key;
                nameWrapper.appendChild(keyBadge);
            }
            
            textContent.appendChild(nameWrapper);

            if (shortcut.description) {
                const description = document.createElement('small');
                description.className = 'text-muted shortcut-description';
                description.textContent = shortcut.description;
                textContent.appendChild(description);
            }
            
            nameSection.appendChild(textContent);
            shortcutItem.appendChild(nameSection);

            // Action buttons
            const actions = document.createElement('div');
            actions.className = 'shortcut-actions';

            // Execute button
            const executeBtn = document.createElement('button');
            executeBtn.className = 'btn btn-sm btn-outline-primary me-1 execute-shortcut';
            executeBtn.innerHTML = '<i class="bi bi-play-fill"></i>';
            executeBtn.setAttribute('title', 'Execute shortcut');
            executeBtn.setAttribute('data-command', shortcut.command);
            actions.appendChild(executeBtn);

            // Edit button
            const editBtn = document.createElement('button');
            editBtn.className = 'btn btn-sm btn-outline-secondary me-1 edit-shortcut';
            editBtn.innerHTML = '<i class="bi bi-pencil"></i>';
            editBtn.setAttribute('title', 'Edit shortcut');
            editBtn.setAttribute('data-shortcut-id', shortcut.id);
            actions.appendChild(editBtn);

            // Delete button
            const deleteBtn = document.createElement('button');
            deleteBtn.className = 'btn btn-sm btn-outline-danger delete-shortcut';
            deleteBtn.innerHTML = '<i class="bi bi-trash"></i>';
            deleteBtn.setAttribute('title', 'Delete shortcut');
            deleteBtn.setAttribute('data-shortcut-id', shortcut.id);
            actions.appendChild(deleteBtn);

            shortcutItem.appendChild(actions);
            shortcutList.appendChild(shortcutItem);
        });

        container.appendChild(shortcutList);
        this.setupDragAndDrop();
    }

    /**
     * Set up event listeners for shortcuts
     */
    setupEventListeners() {
        // Save shortcut button
        document.addEventListener('click', async (e) => {
            // Save shortcut
            if (e.target.id === 'save-shortcut' || e.target.closest('#save-shortcut')) {
                const nameInput = document.getElementById('shortcut-name');
                const commandInput = document.getElementById('shortcut-command');
                const descriptionInput = document.getElementById('shortcut-description');
                const categorySelect = document.getElementById('shortcut-category');
                const iconSelect = document.getElementById('shortcut-icon');
                const colorInput = document.getElementById('shortcut-color');
                const keyInput = document.getElementById('shortcut-key');
                const favoriteCheckbox = document.getElementById('shortcut-favorite');
                
                if (!nameInput.value || !commandInput.value) {
                    alert('Please enter both a name and command for the shortcut');
                    return;
                }
                
                await this.addShortcut(
                    nameInput.value, 
                    commandInput.value, 
                    descriptionInput.value, 
                    categorySelect.value,
                    iconSelect.value,
                    colorInput.value,
                    keyInput.value
                );
                
                // Close modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('addShortcutModal'));
                modal.hide();
                
                // Reload shortcuts
                await this.loadShortcuts(document.getElementById('shortcuts-list'));
                
                // Clear form
                nameInput.value = '';
                commandInput.value = '';
                descriptionInput.value = '';
                categorySelect.value = 'general';
                iconSelect.value = 'bi-command';
                colorInput.value = '#0d6efd';
                keyInput.value = '';
                favoriteCheckbox.checked = false;
            }
            
            // Initialize default shortcuts
            if (e.target.id === 'initialize-shortcuts' || e.target.closest('#initialize-shortcuts')) {
                if (confirm('This will reset your shortcuts to the default set. Are you sure?')) {
                    await this.initializeDefaultShortcuts();
                    await this.loadShortcuts(document.getElementById('shortcuts-list'));
                }
            }
            
            // Execute shortcut
            if (e.target.classList.contains('execute-shortcut') || e.target.closest('.execute-shortcut')) {
                const button = e.target.classList.contains('execute-shortcut') ? e.target : e.target.closest('.execute-shortcut');
                const command = button.getAttribute('data-command');
                
                if (command) {
                    // Get the chat input and submit the command
                    const chatInput = document.getElementById('user-input');
                    const chatForm = document.getElementById('chat-form');
                    
                    if (chatInput && chatForm) {
                        chatInput.value = command;
                        chatForm.dispatchEvent(new Event('submit'));
                        
                        // Close the shortcuts modal
                        const modal = bootstrap.Modal.getInstance(document.getElementById('shortcutsModal'));
                        if (modal) {
                            modal.hide();
                        }
                    }
                }
            }
            
            // Edit shortcut
            if (e.target.classList.contains('edit-shortcut') || e.target.closest('.edit-shortcut')) {
                const button = e.target.classList.contains('edit-shortcut') ? e.target : e.target.closest('.edit-shortcut');
                const shortcutId = parseInt(button.getAttribute('data-shortcut-id'));
                
                const shortcut = this.shortcuts.find(s => s.id === shortcutId);
                if (shortcut) {
                    // Open the add shortcut modal with pre-filled values
                    const nameInput = document.getElementById('shortcut-name');
                    const commandInput = document.getElementById('shortcut-command');
                    const descriptionInput = document.getElementById('shortcut-description');
                    const categorySelect = document.getElementById('shortcut-category');
                    const iconSelect = document.getElementById('shortcut-icon');
                    const colorInput = document.getElementById('shortcut-color');
                    const keyInput = document.getElementById('shortcut-key');
                    
                    nameInput.value = shortcut.name;
                    commandInput.value = shortcut.command;
                    descriptionInput.value = shortcut.description || '';
                    
                    if (shortcut.category && categorySelect.querySelector(`option[value="${shortcut.category}"]`)) {
                        categorySelect.value = shortcut.category;
                    }
                    
                    if (shortcut.icon && iconSelect.querySelector(`option[value="${shortcut.icon}"]`)) {
                        iconSelect.value = shortcut.icon;
                        document.getElementById('icon-preview').className = `bi ${shortcut.icon}`;
                    }
                    
                    if (shortcut.color) {
                        colorInput.value = shortcut.color;
                    }
                    
                    if (shortcut.shortcut_key) {
                        keyInput.value = shortcut.shortcut_key;
                    }
                    
                    // Show the modal
                    const modal = new bootstrap.Modal(document.getElementById('addShortcutModal'));
                    modal.show();
                }
            }
            
            // Delete shortcut
            if (e.target.classList.contains('delete-shortcut') || e.target.closest('.delete-shortcut')) {
                const button = e.target.classList.contains('delete-shortcut') ? e.target : e.target.closest('.delete-shortcut');
                const shortcutId = parseInt(button.getAttribute('data-shortcut-id'));
                
                if (confirm('Are you sure you want to delete this shortcut?')) {
                    await this.deleteShortcut(shortcutId);
                    await this.loadShortcuts(document.getElementById('shortcuts-list'));
                }
            }
        });
    }
    
    /**
     * Set up category tabs
     */
    setupCategoryTabs() {
        const categoryTabs = document.getElementById('shortcut-categories');
        if (!categoryTabs) return;
        
        categoryTabs.addEventListener('click', (e) => {
            const categoryTab = e.target.closest('.shortcut-category');
            if (!categoryTab) return;
            
            // Set active tab
            const allTabs = categoryTabs.querySelectorAll('.shortcut-category');
            allTabs.forEach(tab => tab.classList.remove('active'));
            categoryTab.classList.add('active');
            
            // Filter shortcuts by category
            const category = categoryTab.getAttribute('data-category');
            this.renderShortcuts(document.getElementById('shortcuts-list'), category);
        });
        
        // Add dynamic categories
        this.loadCategories().then(() => {
            const existingCategories = Array.from(categoryTabs.querySelectorAll('.shortcut-category'))
                .map(tab => tab.getAttribute('data-category'));
            
            // Add any new categories from the server
            this.categories.forEach(category => {
                if (!existingCategories.includes(category) && category !== 'general' && category !== 'monitoring' && category !== 'networking') {
                    const newTab = document.createElement('div');
                    newTab.className = 'shortcut-category';
                    newTab.setAttribute('data-category', category);
                    newTab.textContent = category.charAt(0).toUpperCase() + category.slice(1);
                    categoryTabs.appendChild(newTab);
                }
            });
        });
    }
    
    /**
     * Set up icon preview in the add shortcut modal
     */
    setupIconPreview() {
        const iconSelect = document.getElementById('shortcut-icon');
        const iconPreview = document.getElementById('icon-preview');
        
        if (!iconSelect || !iconPreview) return;
        
        iconSelect.addEventListener('change', () => {
            iconPreview.className = `bi ${iconSelect.value}`;
        });
    }
    
    /**
     * Set up keyboard shortcut recording
     */
    setupKeyboardShortcutRecording() {
        const recordButton = document.getElementById('record-shortcut');
        const keyInput = document.getElementById('shortcut-key');
        
        if (!recordButton || !keyInput) return;
        
        let isRecording = false;
        
        recordButton.addEventListener('click', () => {
            isRecording = !isRecording;
            
            if (isRecording) {
                recordButton.textContent = 'Stop';
                recordButton.classList.add('btn-danger');
                recordButton.classList.remove('btn-outline-secondary');
                keyInput.value = 'Press keys...';
                keyInput.focus();
            } else {
                recordButton.textContent = 'Record';
                recordButton.classList.remove('btn-danger');
                recordButton.classList.add('btn-outline-secondary');
            }
        });
        
        document.addEventListener('keydown', (e) => {
            if (!isRecording) return;
            
            e.preventDefault();
            
            const keys = [];
            if (e.ctrlKey) keys.push('Ctrl');
            if (e.altKey) keys.push('Alt');
            if (e.shiftKey) keys.push('Shift');
            if (e.metaKey) keys.push('Meta');
            
            // Add the key if it's not a modifier
            if (!['Control', 'Alt', 'Shift', 'Meta'].includes(e.key)) {
                keys.push(e.key.length === 1 ? e.key.toUpperCase() : e.key);
            }
            
            keyInput.value = keys.join('+');
            
            // Stop recording after a key is pressed
            isRecording = false;
            recordButton.textContent = 'Record';
            recordButton.classList.remove('btn-danger');
            recordButton.classList.add('btn-outline-secondary');
        });
    }

    /**
     * Set up drag and drop for shortcuts
     */
    setupDragAndDrop() {
        const shortcutItems = document.querySelectorAll('.shortcut-item');
        const shortcutList = document.querySelector('[data-shortcut-list]');
        
        if (!shortcutItems.length || !shortcutList) return;
        
        shortcutItems.forEach(item => {
            item.addEventListener('dragstart', (e) => {
                this.draggedItem = item;
                setTimeout(() => {
                    item.classList.add('dragging');
                }, 0);
            });
            
            item.addEventListener('dragend', () => {
                item.classList.remove('dragging');
                this.draggedItem = null;
            });
        });
        
        shortcutList.addEventListener('dragover', (e) => {
            e.preventDefault();
            if (!this.draggedItem) return;
            
            const afterElement = this.getDragAfterElement(shortcutList, e.clientY);
            if (afterElement == null) {
                shortcutList.appendChild(this.draggedItem);
            } else {
                shortcutList.insertBefore(this.draggedItem, afterElement);
            }
            
            // Update positions on server
            this.updateShortcutPositions();
        });
    }

    /**
     * Get the element to insert after when dragging
     * @param {HTMLElement} container - Container element
     * @param {number} y - Y position of the mouse
     * @returns {HTMLElement|null} - Element to insert after
     */
    getDragAfterElement(container, y) {
        const draggableElements = [...container.querySelectorAll('.shortcut-item:not(.dragging)')];
        
        return draggableElements.reduce((closest, child) => {
            const box = child.getBoundingClientRect();
            const offset = y - box.top - box.height / 2;
            
            if (offset < 0 && offset > closest.offset) {
                return { offset, element: child };
            } else {
                return closest;
            }
        }, { offset: Number.NEGATIVE_INFINITY }).element;
    }

    /**
     * Update shortcut positions on the server
     */
    async updateShortcutPositions() {
        const shortcutItems = document.querySelectorAll('.shortcut-item');
        const userId = localStorage.getItem('user_id');
        
        if (!shortcutItems.length || !userId) return;
        
        // Get the new order of shortcuts
        const newOrder = Array.from(shortcutItems).map((item, index) => ({
            id: parseInt(item.getAttribute('data-shortcut-id')),
            position: index
        }));
        
        // Update positions on server
        for (const item of newOrder) {
            try {
                const response = await fetch(`/shortcuts/${userId}/position`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        shortcut_id: item.id,
                        position: item.position
                    })
                });
                
                if (!response.ok) {
                    console.error(`Failed to update shortcut position: ${response.statusText}`);
                }
            } catch (error) {
                console.error('Error updating shortcut position:', error);
            }
        }
    }

    /**
     * Add a new shortcut
     * @param {string} name - Shortcut name
     * @param {string} command - Command to execute
     * @param {string} description - Optional description
     * @param {string} category - Optional category
     * @param {string} icon - Optional icon class
     * @param {string} color - Optional color
     * @param {string} shortcutKey - Optional keyboard shortcut
     * @returns {Promise<boolean>} - Success status
     */
    async addShortcut(name, command, description = null, category = 'general', icon = null, color = null, shortcutKey = null) {
        try {
            const userId = localStorage.getItem('user_id');
            if (!userId) {
                console.error('No user ID found');
                return false;
            }

            const response = await fetch(`/shortcuts/${userId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    name,
                    command,
                    description,
                    category,
                    icon,
                    color,
                    shortcut_key: shortcutKey
                })
            });

            if (!response.ok) {
                throw new Error(`Failed to add shortcut: ${response.statusText}`);
            }

            const data = await response.json();
            return data.success;
        } catch (error) {
            console.error('Error adding shortcut:', error);
            return false;
        }
    }

    /**
     * Delete a shortcut
     * @param {number} shortcutId - ID of the shortcut to delete
     * @returns {Promise<boolean>} - Success status
     */
    async deleteShortcut(shortcutId) {
        try {
            const userId = localStorage.getItem('user_id');
            if (!userId) {
                console.error('No user ID found');
                return false;
            }

            const response = await fetch(`/shortcuts/${userId}/${shortcutId}`, {
                method: 'DELETE'
            });

            if (!response.ok) {
                throw new Error(`Failed to delete shortcut: ${response.statusText}`);
            }

            const data = await response.json();
            return data.success;
        } catch (error) {
            console.error('Error deleting shortcut:', error);
            return false;
        }
    }

    /**
     * Initialize default shortcuts for a user
     * @returns {Promise<boolean>} - Success status
     */
    async initializeDefaultShortcuts() {
        try {
            const userId = localStorage.getItem('user_id');
            if (!userId) {
                console.error('No user ID found');
                return false;
            }

            const response = await fetch(`/shortcuts/${userId}/initialize`, {
                method: 'POST'
            });

            if (!response.ok) {
                throw new Error(`Failed to initialize default shortcuts: ${response.statusText}`);
            }

            const data = await response.json();
            return data.success;
        } catch (error) {
            console.error('Error initializing default shortcuts:', error);
            return false;
        }
    }
}

// Export the Shortcuts class
export default Shortcuts;
