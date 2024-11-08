document.addEventListener('DOMContentLoaded', function() {
    // ... [previous code remains the same] ...

    // Music Generation Form Handling
    const generateMusicForm = document.getElementById('generateMusicForm');
    const generationResult = document.getElementById('generationResult');

    if (generateMusicForm) {
        generateMusicForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const prompt = document.getElementById('musicPrompt').value.trim();
            const style = document.getElementById('musicStyle').value;
            
            if (!prompt) {
                const alertContainer = document.createElement('div');
                alertContainer.className = 'alert alert-danger alert-dismissible fade show mt-3';
                alertContainer.innerHTML = `
                    <strong>Error:</strong> Please provide a description for the music you want to generate.
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                `;
                generateMusicForm.appendChild(alertContainer);
                return;
            }
            
            // Show loading overlay
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
                
                if (response.ok) {
                    // Show success message and download button
                    generationResult.classList.remove('d-none');
                    // Scroll to result
                    generationResult.scrollIntoView({ behavior: 'smooth' });
                } else {
                    throw new Error(result.error || 'Failed to generate music');
                }
            } catch (error) {
                console.error('Music generation error:', error);
                const alertContainer = document.createElement('div');
                alertContainer.className = 'alert alert-danger alert-dismissible fade show mt-3';
                alertContainer.innerHTML = `
                    <strong>Error:</strong> ${error.message}
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                `;
                generateMusicForm.appendChild(alertContainer);
            } finally {
                loadingOverlay.classList.remove('active');
            }
        });
    }

    // ... [rest of the previous code remains the same] ...
});
