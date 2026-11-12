/**
 * CLARIO AI Workspace Controller
 */

let activeDocumentId = null;
let csvChartInstance = null;

document.addEventListener('DOMContentLoaded', () => {
    initDropzone();
    initSampleButtons();
    initDocumentSelection();
    initDocQA();

    // Auto-select first document if present
    const firstDoc = document.querySelector('.doc-item-card');
    if (firstDoc) {
        const docId = firstDoc.getAttribute('data-doc-id');
        loadDocumentDetails(docId);
    }
});

function initDropzone() {
    const dropzone = document.getElementById('docDropzone');
    const fileInput = document.getElementById('fileInput');
    const browseBtn = document.getElementById('browseFileBtn');
    const progressBar = document.getElementById('uploadProgressBar');

    if (!dropzone || !fileInput) return;

    browseBtn.addEventListener('click', () => fileInput.click());
    dropzone.addEventListener('click', (e) => {
        if (e.target !== browseBtn) fileInput.click();
    });

    ['dragenter', 'dragover'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropzone.classList.add('dragover');
        });
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropzone.classList.remove('dragover');
        });
    });

    dropzone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length) uploadFile(files[0]);
    });

    fileInput.addEventListener('change', () => {
        if (fileInput.files.length) uploadFile(fileInput.files[0]);
    });

    function uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);

        progressBar.classList.remove('d-none');
        if (window.showToast) showToast(`Uploading & analyzing ${file.name}...`, 'info');

        fetch('/api/documents/upload', {
            method: 'POST',
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            progressBar.classList.add('d-none');
            fileInput.value = '';

            if (data.success) {
                if (window.showToast) showToast('Document analyzed successfully!', 'success');
                setTimeout(() => window.location.reload(), 800);
            } else {
                if (window.showToast) showToast(data.error || 'Upload failed', 'danger');
            }
        })
        .catch(err => {
            progressBar.classList.add('d-none');
            fileInput.value = '';
            if (window.showToast) showToast('Upload network error', 'danger');
        });
    }
}

function initSampleButtons() {
    const btn1 = document.getElementById('loadSampleDocBtn');
    const btn2 = document.getElementById('placeholderSampleBtn');

    function loadSample() {
        if (window.showToast) showToast('Loading demonstration financial report...', 'info');
        fetch('/api/documents/load-sample', { method: 'POST' })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    if (window.showToast) showToast('Sample loaded successfully!', 'success');
                    setTimeout(() => window.location.reload(), 600);
                } else {
                    if (window.showToast) showToast(data.error || 'Failed to load sample', 'danger');
                }
            })
            .catch(() => {
                if (window.showToast) showToast('Sample loader network error', 'danger');
            });
    }

    if (btn1) btn1.addEventListener('click', loadSample);
    if (btn2) btn2.addEventListener('click', loadSample);
}

function initDocumentSelection() {
    document.addEventListener('click', (e) => {
        const card = e.target.closest('.doc-item-card');
        const delBtn = e.target.closest('.delete-doc-btn');

        if (delBtn) {
            e.stopPropagation();
            const docId = delBtn.getAttribute('data-doc-id');
            if (confirm('Are you sure you want to delete this document from your workspace?')) {
                deleteDocument(docId);
            }
            return;
        }

        if (card) {
            const docId = card.getAttribute('data-doc-id');
            loadDocumentDetails(docId);
        }
    });
}

function loadDocumentDetails(docId) {
    activeDocumentId = docId;
    const activeView = document.getElementById('activeDocView');
    const placeholder = document.getElementById('emptyWorkspacePlaceholder');

    // Visual card selection
    document.querySelectorAll('.doc-item-card').forEach(c => c.classList.remove('border-primary', 'bg-light'));
    const selected = document.querySelector(`.doc-item-card[data-doc-id="${docId}"]`);
    if (selected) selected.classList.add('border-primary', 'bg-light');

    fetch(`/api/documents/${docId}`)
        .then(res => res.json())
        .then(res => {
            if (!res.success) return;
            const doc = res.document;

            placeholder.classList.add('d-none');
            activeView.classList.remove('d-none');

            document.getElementById('activeDocTitle').textContent = doc.original_filename;
            document.getElementById('activeDocBadge').textContent = `${doc.file_type.toUpperCase()} • ${(doc.file_size / 1024).toFixed(1)} KB`;
            document.getElementById('activeDocTimestamp').textContent = `Uploaded ${new Date(doc.uploaded_at).toLocaleString()}`;
            document.getElementById('docSummaryText').innerHTML = renderSafeMarkdown(doc.summary || 'No summary available.');
            document.getElementById('docContentPreview').textContent = doc.content_preview || '';
            document.getElementById('downloadReportBtn').href = `/api/documents/${doc.id}/download-report`;

            // Render Dates
            const datesList = document.getElementById('keyDatesList');
            if (doc.key_dates && doc.key_dates.length) {
                datesList.innerHTML = doc.key_dates.map(d => `<li class="d-flex align-items-center gap-2"><i data-lucide="check" class="text-primary" style="width:14px;"></i> ${d}</li>`).join('');
            } else {
                datesList.innerHTML = `<li class="text-muted">No explicit temporal markers found.</li>`;
            }

            // Render Entities
            const entitiesBox = document.getElementById('keyEntitiesContainer');
            if (doc.key_entities && Object.keys(doc.key_entities).length) {
                entitiesBox.innerHTML = Object.entries(doc.key_entities).map(([k, vals]) => `
                    <div class="mb-2">
                        <strong class="text-dark">${k.replace('_', ' ').toUpperCase()}:</strong>
                        <div class="mt-1">${Array.isArray(vals) ? vals.map(v => `<span class="badge bg-light text-dark border me-1">${v}</span>`).join('') : vals}</div>
                    </div>
                `).join('');
            } else {
                entitiesBox.innerHTML = `<span class="text-muted">No named entities extracted.</span>`;
            }

            // CSV handling
            const csvTabItem = document.getElementById('csv-tab-item');
            if (doc.file_type === 'csv' && doc.csv_metadata) {
                csvTabItem.classList.remove('d-none');
                renderCsvAnalytics(doc.csv_metadata);
            } else {
                csvTabItem.classList.add('d-none');
            }

            // Load persistent conversation messages history
            loadDocumentChatHistory(docId);

            if (window.lucide) lucide.createIcons();
        })
        .catch(() => {});
}

function loadDocumentChatHistory(docId) {
    const list = document.getElementById('qaMessagesList');
    if (!list) return;

    fetch(`/api/documents/${docId}/messages`)
        .then(res => res.json())
        .then(data => {
            if (data.success && data.messages && data.messages.length) {
                list.innerHTML = data.messages.map(m => {
                    if (m.sender === 'user') {
                        return `<div class="p-3 bg-white rounded-3 border mb-2 text-dark small"><strong>You:</strong> <div class="mt-1">${escapeHtml(m.content)}</div></div>`;
                    } else {
                        return `
                            <div class="p-3 rounded-3 border mb-2 small" style="background-color: #EFF6FF;">
                                <div class="d-flex justify-content-between align-items-center mb-1">
                                    <strong class="text-primary">Document Agent:</strong>
                                    <span class="badge bg-light text-muted border font-mono" style="font-size:0.65rem;">Grounded Fact</span>
                                </div>
                                <div class="clario-markdown-body mt-1">${renderSafeMarkdown(m.content)}</div>
                            </div>
                        `;
                    }
                }).join('');
                list.scrollTop = list.scrollHeight;
            } else {
                list.innerHTML = `<div class="text-center py-4 text-muted small">Ask any question about this document below.</div>`;
            }
        })
        .catch(() => {});
}

function renderCsvAnalytics(csvMeta) {
    document.getElementById('csvRowCount').textContent = csvMeta.row_count || 0;
    document.getElementById('csvColCount').textContent = csvMeta.col_count || 0;

    // Render Preview Table
    const tableHead = document.querySelector('#csvPreviewTable thead tr');
    const tableBody = document.querySelector('#csvPreviewTable tbody');
    if (csvMeta.columns && csvMeta.preview_rows) {
        tableHead.innerHTML = csvMeta.columns.map(c => `<th>${c.name}</th>`).join('');
        tableBody.innerHTML = csvMeta.preview_rows.map(row => `
            <tr>${csvMeta.columns.map(c => `<td>${row[c.name] !== undefined ? row[c.name] : ''}</td>`).join('')}</tr>
        `).join('');
    }

    // Render Dynamic Chart
    const ctx = document.getElementById('csvDynamicChart');
    if (ctx && csvMeta.chart_config) {
        if (csvChartInstance) csvChartInstance.destroy();
        const conf = csvMeta.chart_config;

        csvChartInstance = new Chart(ctx, {
            type: conf.type || 'bar',
            data: {
                labels: conf.labels || [],
                datasets: [{
                    label: conf.label || 'Value',
                    data: conf.data || [],
                    backgroundColor: conf.type === 'pie' ? ['#2563EB', '#7C3AED', '#06B6D4', '#10B981', '#F59E0B'] : '#2563EB',
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: { display: true, text: conf.title || 'CSV Analysis Chart', font: { size: 14 } }
                }
            }
        });
    }
}

function deleteDocument(docId) {
    fetch(`/api/documents/${docId}`, { method: 'DELETE' })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                if (window.showToast) showToast('Document deleted', 'success');
                setTimeout(() => window.location.reload(), 500);
            }
        });
}

function initDocQA() {
    const form = document.getElementById('docQuestionForm');
    const input = document.getElementById('docQuestionInput');
    const btn = document.getElementById('askQuestionBtn');
    const list = document.getElementById('qaMessagesList');

    if (!form) return;

    form.addEventListener('submit', (e) => {
        e.preventDefault();
        const q = input.value.trim();
        if (!q || !activeDocumentId) return;

        // Append user message
        const userMsg = document.createElement('div');
        userMsg.className = 'p-3 bg-white rounded-3 border mb-2 text-dark small';
        userMsg.innerHTML = `<strong>You:</strong> <div class="mt-1">${escapeHtml(q)}</div>`;
        list.appendChild(userMsg);
        input.value = '';

        // Append loading placeholder
        const agentMsg = document.createElement('div');
        agentMsg.className = 'p-3 rounded-3 border mb-2 small';
        agentMsg.style.backgroundColor = '#EFF6FF';
        agentMsg.innerHTML = `<strong>Document Agent:</strong> <div class="skeleton py-3 mt-1"></div>`;
        list.appendChild(agentMsg);
        list.scrollTop = list.scrollHeight;

        btn.disabled = true;

        fetch('/api/documents/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ document_id: activeDocumentId, question: q })
        })
        .then(res => res.json())
        .then(data => {
            btn.disabled = false;
            if (data.success) {
                agentMsg.innerHTML = `
                    <div class="d-flex justify-content-between align-items-center mb-1">
                        <strong class="text-primary">Document Agent:</strong>
                        <span class="badge bg-light text-muted border font-mono" style="font-size:0.65rem;">Grounded Fact</span>
                    </div>
                    <div class="clario-markdown-body mt-1">${renderSafeMarkdown(data.answer)}</div>
                `;
            } else {
                agentMsg.innerHTML = `<span class="text-danger">Error: ${data.error || 'Failed to answer'}</span>`;
            }
            list.scrollTop = list.scrollHeight;
        })
        .catch(err => {
            btn.disabled = false;
            agentMsg.innerHTML = `<span class="text-danger">Network error: ${err.message}</span>`;
        });
    });
}
