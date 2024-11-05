function validateForm() {
    const fileInput = document.getElementById('file');
    if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
        showError('Please select a file to upload');
        return false;
    }

    const file = fileInput.files[0];
    const maxSize = 10 * 1024 * 1024; // 10MB
    
    // Check file extension
    const extension = file.name.split('.').pop().toLowerCase();
    if (!['musicxml', 'xml'].includes(extension)) {
        showError('Invalid file type. Please select a MusicXML file (.musicxml or .xml)');
        return false;
    }

    // Check file size
    if (file.size > maxSize) {
        showError('File size exceeds 10MB limit');
        return false;
    }

    return true;
}

function showError(message) {
    const alertHtml = `
        <div class="alert alert-danger alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;

    // Find existing alerts container or create one
    let alertsContainer = document.querySelector('.alerts-container');
    if (!alertsContainer) {
        alertsContainer = document.createElement('div');
        alertsContainer.className = 'alerts-container';
        const form = document.querySelector('form');
        form.insertBefore(alertsContainer, form.firstChild);
    }

    alertsContainer.innerHTML = alertHtml;
}
