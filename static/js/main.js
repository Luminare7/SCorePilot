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
        if (!files.length) {
            fileInfo.classList.add('d-none');
            fileList.innerHTML = 'No files selected';
            return;
        }

        let validFiles = true;
        let fileListHTML = '';

        Array.from(files).forEach(file => {
            // Check file size
            if (file.size > MAX_FILE_SIZE) {
                alert(`File "${file.name}" is too large. Maximum size is 10MB.`);
                validFiles = false;
                return;
            }

            // Check file type
            const extension = file.name.split('.').pop().toLowerCase();
            if (!['musicxml', 'xml'].includes(extension)) {
                alert(`File "${file.name}" is not a valid MusicXML file (.musicxml or .xml)`);
                validFiles = false;
                return;
            }

            fileListHTML += `
                <div class="mb-2">
                    <i class="fas fa-file-code me-2"></i>
                    ${file.name}
                </div>`;
        });

        if (!validFiles) {
            fileInput.value = '';
            return;
        }

        fileList.innerHTML = fileListHTML;
        fileInfo.classList.remove('d-none');
        
        // If files were dragged, update the input
        if (files instanceof FileList) {
            fileInput.files = files;
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
