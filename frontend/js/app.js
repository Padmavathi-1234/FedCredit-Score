/**
 * App.js — Upload page logic
 * Handles file upload, form submission, Alpine.js integration,
 * processing animation, and navigation to dashboard.
 */

document.addEventListener('alpine:init', () => {
    Alpine.data('uploadApp', () => ({
        files: [],
        gstin: '',
        location: '',
        insights: '',
        isProcessing: false,
        processingStep: 0,
        processingSteps: [
            'Analyzing documents...',
            'Extracting financial data...',
            'Fetching intelligence signals...',
            'Running federated scoring model...',
            'Generating results...',
        ],
        dragOver: false,

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
            const allowed = ['.pdf', '.doc', '.docx', '.xls', '.xlsx'];
            for (const f of newFiles) {
                const ext = '.' + f.name.split('.').pop().toLowerCase();
                if (allowed.includes(ext)) {
                    if (!this.files.find(ef => ef.name === f.name)) {
                        this.files.push(f);
                    }
                }
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

        // ── Analysis ──
        async analyze() {
            if (this.files.length === 0) {
                alert('Please upload at least one financial document.');
                return;
            }

            this.isProcessing = true;
            this.processingStep = 0;

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

                if (!response.ok) {
                    throw new Error(`Server error: ${response.status}`);
                }

                const result = await response.json();
                sessionStorage.setItem('analysisResult', JSON.stringify(result));

                clearInterval(stepInterval);
                this.processingStep = this.processingSteps.length - 1;

                await new Promise(r => setTimeout(r, 800));
                window.location.href = '/dashboard';
            } catch (err) {
                clearInterval(stepInterval);
                this.isProcessing = false;
                alert('Analysis failed: ' + err.message);
            }
        },
    }));
});
