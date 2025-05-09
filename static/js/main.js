document.addEventListener('DOMContentLoaded', function() {
    // State variables
    let state = {
        excelFile: null,
        templateFile: null,
        excelFileName: '',
        templateFileName: '',
        excelHeaders: [],
        rowCount: 0,
        currentStep: 1,
        mappings: {},
        previewFile: null
    };

    // Elements
    const excelFileInput = document.getElementById('excel-file');
    const templateFileInput = document.getElementById('template-file');
    const excelFeedback = excelFileInput.parentElement.querySelector('.file-upload-feedback');
    const templateFeedback = templateFileInput.parentElement.querySelector('.file-upload-feedback');
    const step1Next = document.getElementById('step1-next');
    const nextStepButtons = document.querySelectorAll('.next-step');
    const prevStepButtons = document.querySelectorAll('.prev-step');
    const fieldMappingsContainer = document.getElementById('field-mappings');
    const generatePreviewBtn = document.getElementById('generate-preview-btn');
    const downloadPreviewBtn = document.getElementById('download-preview-btn');
    const previewRowSelect = document.getElementById('preview-row');
    const previewLoading = document.getElementById('preview-loading');
    const previewContainer = document.getElementById('preview-container');
    const generateCertificatesBtn = document.getElementById('generate-certificates-btn');
    const generatingSpinner = document.getElementById('generating-spinner');
    const generationComplete = document.getElementById('generation-complete');
    const generationError = document.getElementById('generation-error');
    const errorMessage = document.getElementById('error-message');
    const downloadCertificatesBtn = document.getElementById('download-certificates-btn');
    const retryGenerationBtn = document.getElementById('retry-generation-btn');
    const startOverBtn = document.getElementById('start-over-btn');
    
    // Default template fields
    const defaultTemplateFields = [
        'name', 'course', 'completion date','instructor'
    ];

    // File upload event listeners
    excelFileInput.addEventListener('change', handleExcelUpload);
    templateFileInput.addEventListener('change', handleTemplateUpload);
    
    // Button click event listeners
    step1Next.addEventListener('click', () => goToStep(2));
    nextStepButtons.forEach(button => {
        button.addEventListener('click', () => {
            const currentStepId = button.closest('.step-content').id;
            const nextStep = parseInt(currentStepId.split('-')[0].substring(4)) + 1;
            goToStep(nextStep);
        });
    });
    
    prevStepButtons.forEach(button => {
        button.addEventListener('click', () => {
            const currentStepId = button.closest('.step-content').id;
            const prevStep = parseInt(currentStepId.split('-')[0].substring(4)) - 1;
            goToStep(prevStep);
        });
    });
    
    generatePreviewBtn.addEventListener('click', generatePreview);
    generateCertificatesBtn.addEventListener('click', generateCertificates);
    retryGenerationBtn.addEventListener('click', generateCertificates);
    startOverBtn.addEventListener('click', resetApp);
    previewRowSelect.addEventListener('change', generatePreview);
    
    // Function to handle Excel file upload
    function handleExcelUpload(event) {
        const file = event.target.files[0];
        if (file) {
            state.excelFile = file;
            excelFeedback.textContent = file.name;
            excelFileInput.parentElement.querySelector('.file-upload-label').classList.add('border-primary');
            
            const formData = new FormData();
            formData.append('excel_file', file);
            
            fetch('/upload_excel', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    state.excelFileName = data.filename;
                    state.excelHeaders = data.headers;
                    
                    // Populate preview row dropdown
                    populatePreviewRowSelect(10); // Assume at least 10 rows for now
                    
                    checkStep1Complete();
                } else {
                    showError(data.error || 'Error uploading Excel file');
                    resetExcelUpload();
                }
            })
            .catch(error => {
                showError('Error uploading Excel file: ' + error.message);
                resetExcelUpload();
            });
        }
    }
    
    // Function to handle template file upload
    function handleTemplateUpload(event) {
        const file = event.target.files[0];
        if (file) {
            state.templateFile = file;
            templateFeedback.textContent = file.name;
            templateFileInput.parentElement.querySelector('.file-upload-label').classList.add('border-primary');
            
            const formData = new FormData();
            formData.append('template_file', file);
            
            fetch('/upload_template', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    state.templateFileName = data.filename;
                    checkStep1Complete();
                } else {
                    showError(data.error || 'Error uploading template file');
                    resetTemplateUpload();
                }
            })
            .catch(error => {
                showError('Error uploading template file: ' + error.message);
                resetTemplateUpload();
            });
        }
    }
    
    // Check if step 1 is complete to enable next button
    function checkStep1Complete() {
        if (state.excelFileName && state.templateFileName) {
            step1Next.disabled = false;
        } else {
            step1Next.disabled = true;
        }
    }
    
    // Navigate to a specific step
    function goToStep(stepNumber) {
        // Update current step
        state.currentStep = stepNumber;
        
        // Handle specific step transitions
        if (stepNumber === 2) {
            populateFieldMappings();
        }
        
        // Update UI for current step
        document.querySelectorAll('.step-content').forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById(`step${stepNumber}-content`).classList.add('active');
        
        // Update stepper UI
        updateStepperUI(stepNumber);
    }
    
    // Update the stepper UI to show current step
    function updateStepperUI(currentStep) {
        document.querySelectorAll('.step-circle').forEach((circle, index) => {
            const step = index + 1;
            circle.classList.remove('active', 'completed');
            
            if (step < currentStep) {
                circle.classList.add('completed');
                circle.innerHTML = '<i class="fas fa-check"></i>';
            } else if (step === currentStep) {
                circle.classList.add('active');
                circle.textContent = step;
            } else {
                circle.textContent = step;
            }
        });
        
        document.querySelectorAll('.step').forEach((step, index) => {
            const stepNum = index + 1;
            step.classList.remove('active', 'completed');
            
            if (stepNum < currentStep) {
                step.classList.add('completed');
            } else if (stepNum === currentStep) {
                step.classList.add('active');
            }
        });
        
        document.querySelectorAll('.step-line').forEach((line, index) => {
            line.classList.remove('completed');
            if (index < (currentStep - 1)) {
                line.classList.add('completed');
            }
        });
    }
    
    // Populate field mappings in step 2
    function populateFieldMappings() {
        fieldMappingsContainer.innerHTML = '';
        
        // Create field mappings UI
        defaultTemplateFields.forEach(field => {
            const fieldName = field.replace(/_/g, ' ');
            const fieldNameCapitalized = fieldName.charAt(0).toUpperCase() + fieldName.slice(1);
            
            const rowDiv = document.createElement('div');
            rowDiv.className = 'row mapping-row align-items-center';
            
            const fieldLabelDiv = document.createElement('div');
            fieldLabelDiv.className = 'col-md-5';
            fieldLabelDiv.textContent = fieldNameCapitalized;
            
            const selectDiv = document.createElement('div');
            selectDiv.className = 'col-md-7';
            
            const select = document.createElement('select');
            select.className = 'form-select field-mapping';
            select.dataset.field = field;
            
            // Add empty option
            const emptyOption = document.createElement('option');
            emptyOption.value = '';
            emptyOption.textContent = '-- Select Excel Column --';
            select.appendChild(emptyOption);
            
            // Add options for each Excel header
            state.excelHeaders.forEach(header => {
                const option = document.createElement('option');
                option.value = header;
                option.textContent = header;
                
                // Auto-select matching fields
                if (header.toLowerCase().includes(field.toLowerCase()) || 
                    field.toLowerCase().includes(header.toLowerCase())) {
                    option.selected = true;
                    state.mappings[field] = header;
                }
                
                select.appendChild(option);
            });
            
            // Add change listener
            select.addEventListener('change', function() {
                state.mappings[field] = this.value;
            });
            
            selectDiv.appendChild(select);
            rowDiv.appendChild(fieldLabelDiv);
            rowDiv.appendChild(selectDiv);
            fieldMappingsContainer.appendChild(rowDiv);
        });
    }
    
    // Populate preview row select dropdown
    function populatePreviewRowSelect(count) {
        previewRowSelect.innerHTML = '';
        
        for (let i = 0; i < count; i++) {
            const option = document.createElement('option');
            option.value = i;
            option.textContent = `Row ${i + 1}`;
            previewRowSelect.appendChild(option);
        }
        
        state.rowCount = count;
    }
    
    // Generate certificate preview
    function generatePreview() {
        // Show loading state
        previewLoading.classList.remove('d-none');
        previewContainer.querySelector('p.text-muted').classList.add('d-none');
        downloadPreviewBtn.classList.add('d-none');
        
        const rowIndex = parseInt(previewRowSelect.value);
        
        fetch('/preview', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                excel_filename: state.excelFileName,
                template_filename: state.templateFileName,
                mappings: state.mappings,
                row_index: rowIndex
            })
        })
        .then(response => response.json())
        .then(data => {
            previewLoading.classList.add('d-none');
            
            if (data.success) {
                state.previewFile = data.preview_file;
                
                // Update UI
                downloadPreviewBtn.href = `/get_preview/${data.preview_file}`;
                downloadPreviewBtn.classList.remove('d-none');
                
                previewContainer.querySelector('p.text-muted').textContent = 'Preview generated! Click the download button to view.';
                previewContainer.querySelector('p.text-muted').classList.remove('d-none');
            } else {
                showError(data.error || 'Error generating preview');
            }
        })
        .catch(error => {
            previewLoading.classList.add('d-none');
            showError('Error generating preview: ' + error.message);
        });
    }
    
    // Generate all certificates
    function generateCertificates() {
        // Show loading state
        generateCertificatesBtn.classList.add('d-none');
        generatingSpinner.classList.remove('d-none');
        generationComplete.classList.add('d-none');
        generationError.classList.add('d-none');
        
        fetch('/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                excel_filename: state.excelFileName,
                template_filename: state.templateFileName,
                mappings: state.mappings
            })
        })
        .then(response => response.json())
        .then(data => {
            generatingSpinner.classList.add('d-none');
            
            if (data.success) {
                generationComplete.classList.remove('d-none');
                downloadCertificatesBtn.href = `/download/${data.zip_file}`;
            } else {
                generationError.classList.remove('d-none');
                errorMessage.textContent = data.error || 'Error generating certificates';
            }
        })
        .catch(error => {
            generatingSpinner.classList.add('d-none');
            generationError.classList.remove('d-none');
            errorMessage.textContent = 'Error generating certificates: ' + error.message;
        });
    }
    
    // Reset the application state
    function resetApp() {
        // Reset state
        state = {
            excelFile: null,
            templateFile: null,
            excelFileName: '',
            templateFileName: '',
            excelHeaders: [],
            rowCount: 0,
            currentStep: 1,
            mappings: {},
            previewFile: null
        };
        
        // Reset file inputs
        excelFileInput.value = '';
        templateFileInput.value = '';
        excelFeedback.textContent = 'No file chosen';
        templateFeedback.textContent = 'No file chosen';
        excelFileInput.parentElement.querySelector('.file-upload-label').classList.remove('border-primary');
        templateFileInput.parentElement.querySelector('.file-upload-label').classList.remove('border-primary');
        
        // Reset UI
        step1Next.disabled = true;
        previewRowSelect.innerHTML = '<option value="0">First row</option>';
        downloadPreviewBtn.classList.add('d-none');
        previewContainer.querySelector('p.text-muted').textContent = 'Click "Generate Preview" to see how your certificate will look.';
        previewContainer.querySelector('p.text-muted').classList.remove('d-none');
        
        // Reset generation UI
        generateCertificatesBtn.classList.remove('d-none');
        generatingSpinner.classList.add('d-none');
        generationComplete.classList.add('d-none');
        generationError.classList.add('d-none');
        
        // Go to step 1
        goToStep(1);
    }
    
    // Reset Excel upload
    function resetExcelUpload() {
        excelFileInput.value = '';
        excelFeedback.textContent = 'No file chosen';
        excelFileInput.parentElement.querySelector('.file-upload-label').classList.remove('border-primary');
        state.excelFile = null;
        state.excelFileName = '';
        checkStep1Complete();
    }
    
    // Reset template upload
    function resetTemplateUpload() {
        templateFileInput.value = '';
        templateFeedback.textContent = 'No file chosen';
        templateFileInput.parentElement.querySelector('.file-upload-label').classList.remove('border-primary');
        state.templateFile = null;
        state.templateFileName = '';
        checkStep1Complete();
    }
    
    // Show error message
    function showError(message) {
        const errorAlert = document.createElement('div');
        errorAlert.className = 'alert alert-danger alert-dismissible fade show mt-3';
        errorAlert.role = 'alert';
        errorAlert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        const stepContent = document.querySelector('.step-content.active');
        stepContent.prepend(errorAlert);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            errorAlert.classList.remove('show');
            setTimeout(() => errorAlert.remove(), 150);
        }, 5000);
    }
});
