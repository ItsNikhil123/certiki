document.addEventListener('DOMContentLoaded', function() {
    const urlParams = new URLSearchParams(window.location.search);
    const previewFile = urlParams.get('file');
    const loadingSpinner = document.getElementById('loading-spinner');
    const previewContainer = document.getElementById('preview-container');
    const previewError = document.getElementById('preview-error');
    const errorMessage = document.getElementById('error-message');
    const previewFrame = document.getElementById('preview-frame');
    const downloadPreview = document.getElementById('download-preview');
    
    if (previewFile) {
        // Set download link
        downloadPreview.href = `/get_preview/${previewFile}`;
        
        // Attempt to display preview (though browsers might not display .docx directly)
        previewFrame.src = `/get_preview/${previewFile}`;
        
        // Show preview container
        loadingSpinner.classList.add('d-none');
        previewContainer.classList.remove('d-none');
    } else {
        // Show error
        loadingSpinner.classList.add('d-none');
        previewError.classList.remove('d-none');
        errorMessage.textContent = 'No preview file specified';
    }
    
    // Handle iframe load error
    previewFrame.addEventListener('error', function() {
        const warningDiv = document.createElement('div');
        warningDiv.className = 'alert alert-warning mt-3';
        warningDiv.innerHTML = `
            <i class="fas fa-exclamation-triangle me-2"></i>
            Your browser cannot display Word documents directly. Please use the download button to view the preview.
        `;
        previewContainer.insertBefore(warningDiv, previewContainer.firstChild);
    });
});
