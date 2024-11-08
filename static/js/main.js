document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('uploadForm');
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('file');
    const fileInfo = document.getElementById('fileInfo');
    const fileList = document.getElementById('fileList');
    const loadingOverlay = document.getElementById('loadingOverlay');
    const generateMusicForm = document.getElementById('generateMusicForm');
    const generationResult = document.getElementById('generationResult');

    // Initialize file upload handlers
    if (dropZone) {
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
    }

    if (fileInput) {
        fileInput.addEventListener('change', handleFiles, false);
    }

    if (uploadForm) {
        uploadForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            if (!fileInput.files.length) {
                showError('Please select at least one file to upload.');
                return;
            }
            loadingOverlay.classList.add('active');
            uploadForm.submit();
        });
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
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 60000); // Increase timeout to 60 seconds
                
                const response = await fetch('/generate-music', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ prompt, style }),
                    signal: controller.signal,
                    timeout: 60000  // Increase timeout to 60 seconds
                });
                
                clearTimeout(timeoutId);
                
                if (!response.ok) {
                    throw new Error(response.statusText || 'Network error occurred');
                }
                
                const result = await response.json();
                
                if (result.error) {
                    throw new Error(result.error);
                }
                
                generationResult.classList.remove('d-none');
                generationResult.scrollIntoView({ behavior: 'smooth' });
            } catch (error) {
                console.error('Music generation error:', error);
                let errorMessage, errorType;
                
                if (error.name === 'AbortError') {
                    errorMessage = 'Request timed out. Please try again.';
                    errorType = 'timeout';
                } else if (error instanceof TypeError && error.message.includes('network')) {
                    errorMessage = 'Network connection failed. Please check your connection.';
                    errorType = 'network_error';
                } else {
                    errorMessage = error.message || 'An unexpected error occurred';
                    errorType = error.type || 'unexpected_error';
                }
                
                const alertContainer = document.createElement('div');
                alertContainer.className = 'alert alert-warning alert-dismissible fade show mt-3';
                
                let errorText = '';
                if (errorType === 'rate_limit') {
                    errorText = 'The service is currently experiencing high demand. Please wait a moment and try again.';
                } else if (errorType === 'network_error' || errorType === 'timeout') {
                    errorText = 'Unable to connect to the service. Please check your connection and try again.';
                } else {
                    errorText = 'An unexpected error occurred. Please try again in a few moments.';
                }
                
                alertContainer.innerHTML = `
                    <strong>Error:</strong> ${errorMessage}
                    <p class="mb-0 mt-2">${errorText}</p>
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                `;
                generateMusicForm.appendChild(alertContainer);
                
                // Add retry button for rate limit errors and network issues
                if (errorType === 'rate_limit' || errorType === 'network_error' || errorType === 'timeout') {
                    const retryBtn = document.createElement('button');
                    retryBtn.className = 'btn btn-primary mt-3';
                    retryBtn.innerHTML = '<i class="fas fa-redo me-2"></i>Try Again';
                    retryBtn.onclick = () => {
                        generateMusicForm.querySelectorAll('.alert').forEach(alert => alert.remove());
                        generateMusicForm.dispatchEvent(new Event('submit'));
                    };
                    generateMusicForm.appendChild(retryBtn);
                }
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
                    <i class="fas fa-file-music me-2"></i>
                    ${file.name} (${formatFileSize(file.size)})
                </div>
            `).join('');
        } else {
            fileInfo.classList.add('d-none');
            fileList.innerHTML = '';
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
        uploadForm.appendChild(alertContainer);
        setTimeout(() => {
            alertContainer.remove();
        }, 5000);
    }
});
