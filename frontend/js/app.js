/**
 * App.js — Upload page logic
 * Handles file upload, form submission, Alpine.js integration,
 * processing animation, error modal, auto-populate, and
 * navigation to dashboard.
 */

document.addEventListener('alpine:init', () => {
    Alpine.data('uploadApp', () => ({
        files: [],
        gstin: '',
        location: '',
        insights: '',
        isProcessing: false,

        init() {
            // No auth required
        },

        processingStep: 0,
        processingSteps: [
            'Extracting data from documents...',
            'Cleaning & validating data...',
            'Verifying company authenticity...',
            'Fetching intelligence signals...',
            'Running federated scoring model...',
            'Generating results...',
        ],
        dragOver: false,

        // Error modal state
        showErrorModal: false,
        errorModalTitle: '',
        errorModalIcon: '⚠️',
        errorModalMessages: [],

        // Auto-populate tracking
        autoPopulated: { gstin: false, location: false },

        // Field-level errors
        fieldErrors: { gstin: '', location: '', insights: '' },

        // Extraction state
        isExtracting: false,

        // ── File Handling ──
        onDrop(event) {
            this.dragOver = false;
            const droppedFiles = Array.from(event.dataTransfer.files);
            this.addFiles(droppedFiles);
        },

        onFileSelect(event) {
            const selectedFiles = Array.from(event.target.files);
            this.addFiles(selectedFiles);
            event.target.value = '';
        },

        addFiles(newFiles) {
            const allowed = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.csv', '.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp'];
            let added = false;
            for (const f of newFiles) {
                const ext = '.' + f.name.split('.').pop().toLowerCase();
                if (allowed.includes(ext)) {
                    if (!this.files.find(ef => ef.name === f.name)) {
                        this.files.push(f);
                        added = true;
                    }
                }
            }
            // Auto-extract fields from newly uploaded files
            if (added && this.files.length > 0) {
                this.extractFieldsFromFiles();
            }
        },

        // ── Auto-extract GSTIN/location from uploaded files ──
        async extractFieldsFromFiles() {
            this.isExtracting = true;
            try {
                const formData = new FormData();
                for (const f of this.files) {
                    formData.append('files', f);
                }
                const response = await fetch('/api/extract-fields', {
                    method: 'POST',
                    body: formData,
                });
                if (response.ok) {
                    const data = await response.json();
                    const fields = data.extracted_fields || {};
                    if (fields.gstin && !this.gstin) {
                        this.gstin = fields.gstin;
                        this.autoPopulated.gstin = true;
                    }
                    if (fields.location && !this.location) {
                        this.location = fields.location;
                        this.autoPopulated.location = true;
                    }
                }
            } catch (err) {
                // Silently fail — user can still type manually
                console.warn('Auto-extraction failed:', err);
            } finally {
                this.isExtracting = false;
            }
        },

        removeFile(index) {
            this.files.splice(index, 1);
        },

        formatSize(bytes) {
            if (bytes < 1024) return bytes + ' B';
            if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
            return (bytes / 1048576).toFixed(1) + ' MB';
        },

        // ── Error Display ──
        showError(title, messages, icon = '⚠️') {
            this.errorModalTitle = title;
            this.errorModalMessages = messages;
            this.errorModalIcon = icon;
            this.showErrorModal = true;
        },

        // ── Clear field errors ──
        clearFieldErrors() {
            this.fieldErrors = { gstin: '', location: '', insights: '' };
        },

        // ── Handle structured error response ──
        handleErrorResponse(data) {
            // Auto-populate extracted fields
            if (data.extracted_fields) {
                if (data.extracted_fields.gstin && !this.gstin) {
                    this.gstin = data.extracted_fields.gstin;
                    this.autoPopulated.gstin = true;
                }
                if (data.extracted_fields.location && !this.location) {
                    this.location = data.extracted_fields.location;
                    this.autoPopulated.location = true;
                }
            }

            // Map error types to titles and icons
            const errorConfig = {
                validation_error: { title: 'Missing Required Fields', icon: '📋' },
                gstin_format_error: { title: 'Invalid GSTIN Format', icon: '🔢' },
                verification_error: { title: 'Company Verification Failed', icon: '🏢' },
                processing_error: { title: 'Document Processing Error', icon: '📄' },
            };

            const config = errorConfig[data.error_type] || { title: 'Analysis Error', icon: '⚠️' };

            // Set field-level errors
            this.clearFieldErrors();
            if (data.error_type === 'validation_error') {
                for (const err of data.errors) {
                    if (err.toLowerCase().includes('gstin')) this.fieldErrors.gstin = err;
                    if (err.toLowerCase().includes('location')) this.fieldErrors.location = err;
                    if (err.toLowerCase().includes('insight')) this.fieldErrors.insights = err;
                }
            } else if (data.error_type === 'gstin_format_error') {
                this.fieldErrors.gstin = data.errors[0] || 'Invalid GSTIN format';
            }

            // Show modal
            this.showError(config.title, data.errors, config.icon);
        },

        // ── Analysis ──
        async analyze() {
            if (this.files.length === 0) {
                this.showError('No Documents', ['Please upload at least one financial document.'], '📄');
                return;
            }

            if (!this.insights || this.insights.trim().length < 10) {
                this.fieldErrors.insights = 'Officer insights are required. Please provide a detailed assessment (at least 10 characters).';
                this.showError('Officer Insights Required', ['Please provide your assessment of the company. Officer insights are mandatory and directly influence the federated credit score.'], '📝');
                return;
            }

            this.isProcessing = true;
            this.processingStep = 0;
            this.clearFieldErrors();
            this.showErrorModal = false;

            const stepInterval = setInterval(() => {
                if (this.processingStep < this.processingSteps.length - 1) {
                    this.processingStep++;
                }
            }, 1200);

            try {
                const formData = new FormData();
                for (const f of this.files) {
                    formData.append('files', f);
                }
                formData.append('gstin', this.gstin);
                formData.append('location', this.location);
                formData.append('insights', this.insights);

                const response = await fetch('/api/upload', {
                    method: 'POST',
                    body: formData,
                });

                clearInterval(stepInterval);

                if (!response.ok) {
                    const data = await response.json().catch(() => null);
                    this.isProcessing = false;

                    if (data && data.error_type) {
                        this.handleErrorResponse(data);
                    } else {
                        this.showError(
                            'Server Error',
                            [data?.detail || `Server returned status ${response.status}`],
                            '🔥'
                        );
                    }
                    return;
                }

                const result = await response.json();
                sessionStorage.setItem('analysisResult', JSON.stringify(result));
                // Set flag to load latest on dashboard
                sessionStorage.setItem('loadLatest', 'true');

                this.processingStep = this.processingSteps.length - 1;

                await new Promise(r => setTimeout(r, 800));
                window.location.href = '/dashboard';
            } catch (err) {
                clearInterval(stepInterval);
                this.isProcessing = false;
                this.showError('Connection Error', ['Could not reach the server: ' + err.message], '🔌');
            }
        },
    }));
});
