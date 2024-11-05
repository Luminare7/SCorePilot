document.addEventListener('DOMContentLoaded', function() {
    // File input validation
    const fileInput = document.getElementById('files');
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            updateSelectedFilesList(this);
            validateFileInput(this);
        });
    }
});

function validateForm() {
    const fileInput = document.getElementById('files');
    if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
        showError('Please select at least one file to upload');
        return false;
    }

    if (!validateFileInput(fileInput)) {
        return false;
    }

    return true;
}

function updateSelectedFilesList(input) {
    const selectedFilesDiv = document.getElementById('selectedFiles');
    if (!selectedFilesDiv) return;

    let html = '<div class="list-group mt-3">';
    for (let i = 0; i < input.files.length; i++) {
        const file = input.files[i];
        html += `<div class="list-group-item d-flex justify-content-between align-items-center">
            <span>${file.name}</span>
            <span class="badge bg-primary rounded-pill">${formatFileSize(file.size)}</span>
        </div>`;
    }
    html += '</div>';
    selectedFilesDiv.innerHTML = html;
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function validateFileInput(input) {
    const files = input.files;
    const maxSize = 10 * 1024 * 1024; // 10MB
    let hasErrors = false;

    for (let i = 0; i < files.length; i++) {
        const file = files[i];
        
        // Check file extension
        const extension = file.name.split('.').pop().toLowerCase();
        if (!['musicxml', 'xml'].includes(extension)) {
            showError(`Invalid file type: ${file.name}. Please select only MusicXML files (.musicxml or .xml)`);
            hasErrors = true;
        }

        // Check file size
        if (file.size > maxSize) {
            showError(`File size exceeds 10MB limit: ${file.name}`);
            hasErrors = true;
        }
    }

    if (hasErrors) {
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
