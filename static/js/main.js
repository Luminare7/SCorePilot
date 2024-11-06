document.addEventListener('DOMContentLoaded', function() {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('file');
    const fileInfo = document.getElementById('fileInfo');
    const fileList = document.getElementById('fileList');
    const uploadForm = document.getElementById('uploadForm');
    const loadingOverlay = document.getElementById('loadingOverlay');

    // File size limit in bytes (10MB)
    const MAX_FILE_SIZE = 10 * 1024 * 1024;

    function handleFiles(files) {
        if (!files || files.length === 0) {
            fileInfo.classList.add('d-none');
            return;
        }

        let validFiles = [];
        let errorMessages = [];

        // Check each file
        Array.from(files).forEach(file => {
            // Check file size
            if (file.size > MAX_FILE_SIZE) {
                errorMessages.push(`${file.name} is too large. Maximum size is 10MB.`);
                return;
            }

            // Check file type
            const extension = file.name.split('.').pop().toLowerCase();
            if (!['musicxml', 'xml'].includes(extension)) {
                errorMessages.push(`${file.name} is not a valid MusicXML file.`);
                return;
            }

            validFiles.push(file);
        });

        // Show error messages if any
        if (errorMessages.length > 0) {
            alert(errorMessages.join('\n'));
        }

        // Update UI with valid files
        if (validFiles.length > 0) {
            fileList.textContent = Array.from(validFiles)
                .map(file => file.name)
                .join(', ');
            fileInfo.classList.remove('d-none');
            
            // If files were dragged, update the input
            if (validFiles !== fileInput.files) {
                const dt = new DataTransfer();
                validFiles.forEach(file => dt.items.add(file));
                fileInput.files = dt.files;
            }
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
            alert('Please select at least one file to upload.');
            return;
        }
        loadingOverlay.classList.add('active');
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
