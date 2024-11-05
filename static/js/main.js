document.addEventListener('DOMContentLoaded', function() {
    // File input validation
    const fileInput = document.getElementById('file');
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            validateFileInput(this);
        });
    }
});

function validateForm() {
    const fileInput = document.getElementById('file');
    if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
        showError('Please select a file to upload');
        return false;
    }

    if (!validateFileInput(fileInput)) {
        return false;
    }

    return true;
}

function validateFileInput(input) {
    const file = input.files[0];
    if (!file) return false;

    // Check file extension
    const extension = file.name.split('.').pop().toLowerCase();
    if (!['musicxml', 'xml'].includes(extension)) {
        showError('Please select a valid MusicXML file (.musicxml or .xml)');
        input.value = '';
        return false;
    }

    // Check file size (10MB = 10 * 1024 * 1024 bytes)
    if (file.size > 10 * 1024 * 1024) {
        showError('File size exceeds 10MB limit. Please select a smaller file.');
        input.value = '';
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
