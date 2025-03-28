/**
 * QR Code module - Handles QR code generation and display
 */
export default class QRCode {
    /**
     * Initialize QR code functionality
     */
    constructor() {
        // Create QR code modal if it doesn't exist
        this.ensureQRCodeModalExists();
        
        // Make the showQRCode function globally available
        window.showQRCode = this.showQRCode.bind(this);
    }
    
    /**
     * Ensure the QR code modal exists in the DOM
     */
    ensureQRCodeModalExists() {
        // Check if the modal already exists
        if (document.getElementById('qrCodeModal')) {
            return;
        }
        
        // Create the modal
        const modalHTML = `
            <div class="modal fade" id="qrCodeModal" tabindex="-1" aria-labelledby="qrCodeModalLabel" aria-hidden="true">
                <div class="modal-dialog modal-dialog-centered">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="qrCodeModalLabel">Mobile Access QR Code</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body text-center">
                            <p>Scan this QR code with your mobile device to access this resource:</p>
                            <div id="qrcode-container" class="d-flex justify-content-center">
                                <img id="qrcode-image" src="" alt="QR Code" class="img-fluid border p-2" style="max-width: 250px;">
                            </div>
                            <p class="mt-3 small text-muted">
                                The QR code provides direct access to this resource from your mobile device.
                                <br>You may need to authenticate if you're not already logged in.
                            </p>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Append the modal to the body
        const modalContainer = document.createElement('div');
        modalContainer.innerHTML = modalHTML;
        document.body.appendChild(modalContainer.firstElementChild);
    }
    
    /**
     * Show the QR code modal for a resource
     * @param {string} resourceType - Type of resource (vm or service)
     * @param {string} resourceId - ID of the resource
     */
    showQRCode(resourceType, resourceId) {
        // Ensure the modal exists
        this.ensureQRCodeModalExists();
        
        // Get modal elements
        const modal = new bootstrap.Modal(document.getElementById('qrCodeModal'));
        const qrCodeImage = document.getElementById('qrcode-image');
        const modalTitle = document.getElementById('qrCodeModalLabel');
        
        // Set the modal title based on resource type
        modalTitle.textContent = resourceType === 'vm' ? 'VM Access QR Code' : 'Service Access QR Code';
        
        // Set the QR code image source
        qrCodeImage.src = `/qr-code/${resourceType}/${resourceId}`;
        
        // Show the modal
        modal.show();
    }
}
