document.addEventListener('DOMContentLoaded', function() {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('file');
    const fileInfo = document.getElementById('fileInfo');
    const fileName = document.getElementById('fileName');
    const uploadForm = document.getElementById('uploadForm');
    const loadingOverlay = document.getElementById('loadingOverlay');

    // File size limit in bytes (10MB)
    const MAX_FILE_SIZE = 10 * 1024 * 1024;

    function handleFiles(files) {
        const file = files[0];
        
        if (!file) return;

        // Check file size
        if (file.size > MAX_FILE_SIZE) {
            alert('File is too large. Maximum size is 10MB.');
            fileInput.value = '';
            return;
        }

        // Check file type
        const extension = file.name.split('.').pop().toLowerCase();
        if (!['musicxml', 'xml'].includes(extension)) {
            alert('Please select a valid MusicXML file (.musicxml or .xml)');
            fileInput.value = '';
            return;
        }

        // Update UI with file info
        fileName.textContent = file.name;
        fileInfo.classList.remove('d-none');
        
        // If file was dragged, update the input
        fileInput.files = files;
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
            alert('Please select a file to upload.');
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
