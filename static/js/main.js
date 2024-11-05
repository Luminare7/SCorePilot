document.addEventListener('DOMContentLoaded', function() {
    // File input validation
    const fileInput = document.getElementById('file');
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                const extension = file.name.split('.').pop().toLowerCase();
                if (!['musicxml', 'xml'].includes(extension)) {
                    alert('Please select a valid MusicXML file');
                    this.value = '';
                }
            }
        });
    }
});
