document.addEventListener('DOMContentLoaded', function() {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('file');
    const fileInfo = document.getElementById('fileInfo');
    const fileList = document.getElementById('fileList');
    const uploadForm = document.getElementById('uploadForm');
    const loadingOverlay = document.getElementById('loadingOverlay');

    // File size limit in bytes (10MB)
    const MAX_FILE_SIZE = 10 * 1024 * 1024;

    async function validateFile(file) {
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/validate', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            return {
                valid: result.valid,
                error: result.error || 'File validation failed'
            };
        } catch (error) {
            console.error('Validation error:', error);
            return {
                valid: false,
                error: 'File validation failed'
            };
        }
    }

    async function handleFiles(files) {
        if (!files || files.length === 0) {
            fileInfo.classList.add('d-none');
            return;
        }

        let validFiles = [];
        let errorMessages = [];

        // Show loading state
        loadingOverlay.classList.add('active');
        
        try {
            // Process each file
            for (const file of files) {
                // Basic client-side validation
                if (file.size > MAX_FILE_SIZE) {
                    errorMessages.push(`${file.name} is too large. Maximum size is 10MB.`);
                    continue;
                }

                const extension = file.name.split('.').pop().toLowerCase();
                if (!['musicxml', 'xml'].includes(extension)) {
                    errorMessages.push(`${file.name} is not a valid MusicXML file.`);
                    continue;
                }

                // Server-side validation
                const validation = await validateFile(file);
                if (!validation.valid) {
                    errorMessages.push(`${file.name}: ${validation.error}`);
                    continue;
                }

                validFiles.push(file);
            }
        } catch (error) {
            console.error('Error handling files:', error);
            errorMessages.push('An error occurred while validating files.');
        } finally {
            loadingOverlay.classList.remove('active');
        }

        // Show error messages if any
        if (errorMessages.length > 0) {
            // Create and show alert
            const alertContainer = document.createElement('div');
            alertContainer.className = 'alert alert-warning alert-dismissible fade show';
            alertContainer.innerHTML = `
                <h5>File Validation Issues:</h5>
                <ul class="mb-0">
                    ${errorMessages.map(msg => `<li>${msg}</li>`).join('')}
                </ul>
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;
            
            // Insert alert before the upload form
            uploadForm.parentNode.insertBefore(alertContainer, uploadForm);
        }

        // Update UI with valid files
        if (validFiles.length > 0) {
            fileList.innerHTML = validFiles.map(file => `
                <div class="alert alert-info d-flex align-items-center">
                    <i class="fas fa-file-code me-2"></i>
                    <span>${file.name}</span>
                </div>
            `).join('');
            fileInfo.classList.remove('d-none');
            
            // Update the input with valid files
            const dt = new DataTransfer();
            validFiles.forEach(file => dt.items.add(file));
            fileInput.files = dt.files;
        } else {
            fileInfo.classList.add('d-none');
            fileInput.value = '';
        }
    }

    // Click handling
    dropZone.addEventListener('click', () => fileInput.click());

    // File input change handling
    fileInput.addEventListener('change', (e) => handleFiles(e.target.files));

    // Drag and drop handling
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        handleFiles(e.dataTransfer.files);
    });

    // Form submission handling
    uploadForm.addEventListener('submit', (e) => {
        if (!fileInput.files.length) {
            e.preventDefault();
            const alertContainer = document.createElement('div');
            alertContainer.className = 'alert alert-danger alert-dismissible fade show';
            alertContainer.innerHTML = `
                <strong>Error:</strong> Please select at least one file to upload.
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;
            uploadForm.parentNode.insertBefore(alertContainer, uploadForm);
            return;
        }
        loadingOverlay.classList.add('active');
    });

    // Cleanup on page navigation/refresh
    window.addEventListener('beforeunload', function() {
        // Make synchronous cleanup request
        const xhr = new XMLHttpRequest();
        xhr.open('GET', '/cleanup', false);  // Synchronous
        xhr.send();
    });

    // Initialize tooltips and popovers if they exist
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
});
