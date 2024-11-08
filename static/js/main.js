document.addEventListener('DOMContentLoaded', function() {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('file');
    const fileInfo = document.getElementById('fileInfo');
    const fileList = document.getElementById('fileList');
    const uploadForm = document.getElementById('uploadForm');
    const loadingOverlay = document.getElementById('loadingOverlay');
    const generateMusicForm = document.getElementById('generateMusicForm');
    const generationResult = document.getElementById('generationResult');

    // File Upload Handling
    if (dropZone && fileInput) {
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, preventDefaults, false);
            document.body.addEventListener(eventName, preventDefaults, false);
        });

        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, highlight, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, unhighlight, false);
        });

        dropZone.addEventListener('drop', handleDrop, false);
        dropZone.addEventListener('click', () => fileInput.click());
        fileInput.addEventListener('change', handleFiles);
    }

    // Music Generation Form Handling
    if (generateMusicForm) {
        generateMusicForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const prompt = document.getElementById('musicPrompt').value.trim();
            const style = document.getElementById('musicStyle').value;
            
            if (!prompt) {
                showError('Please provide a description for the music you want to generate.');
                return;
            }
            
            loadingOverlay.classList.add('active');
            
            try {
                const response = await fetch('/generate-music', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ prompt, style })
                });
                
                const result = await response.json();
                
                if (!response.ok) {
                    throw { message: result.error, type: result.error_type };
                }
                
                generationResult.classList.remove('d-none');
                generationResult.scrollIntoView({ behavior: 'smooth' });
            } catch (error) {
                console.error('Music generation error:', error);
                const errorMessage = error.message || 'An unexpected error occurred';
                const alertContainer = document.createElement('div');
                alertContainer.className = 'alert alert-danger alert-dismissible fade show mt-3';
                alertContainer.innerHTML = `
                    <strong>Error:</strong> ${errorMessage}
                    <p class="mb-0 mt-2">
                        ${error.type === 'network_error' ? 
                        'Please check your internet connection and try again.' : 
                        'Please try again in a few moments.'}
                    </p>
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                `;
                generateMusicForm.appendChild(alertContainer);
            } finally {
                loadingOverlay.classList.remove('active');
            }
        });
    }

    // Utility Functions
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    function highlight(e) {
        dropZone.classList.add('dragover');
    }

    function unhighlight(e) {
        dropZone.classList.remove('dragover');
    }

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleFiles({ target: { files: files } });
    }

    function handleFiles(e) {
        const files = Array.from(e.target.files);
        
        if (files.length > 0) {
            fileInfo.classList.remove('d-none');
            fileList.innerHTML = files.map(file => `
                <div class="file-item">
                    <i class="fas fa-file-code"></i>
                    ${file.name} (${formatFileSize(file.size)})
                </div>
            `).join('');
        } else {
            fileInfo.classList.add('d-none');
            fileList.innerHTML = 'No files selected';
        }
    }

    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    function showError(message) {
        const alertContainer = document.createElement('div');
        alertContainer.className = 'alert alert-danger alert-dismissible fade show mt-3';
        alertContainer.innerHTML = `
            <strong>Error:</strong> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        generateMusicForm.appendChild(alertContainer);
    }
});
