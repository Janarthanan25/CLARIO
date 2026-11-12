/**
 * CLARIO Smart Email Assistant Controller
 */

let currentEmailRecordId = null;

document.addEventListener('DOMContentLoaded', () => {
    initSampleSelector();
    initEmailForm();
    initToneSwitchers();
    initCopyButton();
    initApproveButton();
});

function initSampleSelector() {
    document.querySelectorAll('.load-sample-email-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const idx = parseInt(btn.getAttribute('data-index'));
            const sample = window.sampleEmailsData[idx];
            if (!sample) return;

            document.getElementById('emailSubjectInput').value = sample.subject;
            document.getElementById('emailSenderInput').value = sample.sender;
            document.getElementById('emailBodyInput').value = sample.body;

            if (window.showToast) showToast('Sample email loaded into form', 'info');
        });
    });
}

function initEmailForm() {
    const form = document.getElementById('emailAnalysisForm');
    const submitBtn = document.getElementById('analyzeEmailBtn');

    if (!form) return;

    form.addEventListener('submit', (e) => {
        e.preventDefault();
        const subject = document.getElementById('emailSubjectInput').value.trim();
        const sender = document.getElementById('emailSenderInput').value.trim();
        const body = document.getElementById('emailBodyInput').value.trim();
        const tone = document.querySelector('input[name="emailTone"]:checked').value;

        submitBtn.disabled = true;
        submitBtn.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span> Analyzing...`;

        fetch('/api/emails/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ subject, sender, body, tone })
        })
        .then(res => res.json())
        .then(data => {
            submitBtn.disabled = false;
            submitBtn.innerHTML = `<i data-lucide="sparkles" style="width:16px;height:16px;"></i> <span>Analyze & Generate Reply</span>`;
            if (window.lucide) lucide.createIcons();

            if (data.success) {
                renderEmailResults(data.email);
                if (window.showToast) showToast('Email analyzed & reply generated!', 'success');
            } else {
                if (window.showToast) showToast(data.error || 'Analysis failed', 'danger');
            }
        })
        .catch(err => {
            submitBtn.disabled = false;
            submitBtn.innerHTML = `<span>Analyze & Generate Reply</span>`;
            if (window.showToast) showToast('Network error during analysis', 'danger');
        });
    });
}

function renderEmailResults(email) {
    currentEmailRecordId = email.id;
    const approveBtn = document.getElementById('approveEmailDraftBtn');
    if (approveBtn) {
        approveBtn.classList.remove('d-none');
        approveBtn.disabled = false;
        approveBtn.innerHTML = `<i data-lucide="check-circle" style="width:14px;height:14px;"></i> Approve & Authorize`;
    }

    document.getElementById('emailCategoryBadge').textContent = email.category;
    document.getElementById('emailSentimentBadge').textContent = `Sentiment: ${email.sentiment}`;

    const urgencyPercent = Math.round((email.urgency_score || 0.5) * 100);
    document.getElementById('emailUrgencyVal').textContent = `${urgencyPercent}%`;
    const urgencyBar = document.getElementById('emailUrgencyBar');
    urgencyBar.style.width = `${urgencyPercent}%`;

    if (urgencyPercent > 70) {
        urgencyBar.className = 'progress-bar bg-danger';
    } else if (urgencyPercent > 40) {
        urgencyBar.className = 'progress-bar bg-warning';
    } else {
        urgencyBar.className = 'progress-bar bg-success';
    }

    document.getElementById('emailExecutiveSummary').innerHTML = `<div class="clario-markdown-body">${renderSafeMarkdown(email.summary || 'Summary unavailable.')}</div>`;
    document.getElementById('activeReplyToneLabel').textContent = email.reply_tone || 'Professional';
    document.getElementById('emailReplyDraftArea').value = email.generated_reply || '';

    // Render Tasks
    const tasksList = document.getElementById('emailTasksList');
    if (email.extracted_tasks && email.extracted_tasks.length) {
        tasksList.innerHTML = email.extracted_tasks.map(t => `<li class="d-flex align-items-center gap-2"><i data-lucide="check" class="text-success" style="width:14px;"></i> ${t}</li>`).join('');
    } else {
        tasksList.innerHTML = `<li class="text-muted">No explicit action items found.</li>`;
    }

    // Render Deadlines
    const deadlinesList = document.getElementById('emailDeadlinesList');
    if (email.deadlines && email.deadlines.length) {
        deadlinesList.innerHTML = email.deadlines.map(d => `<li class="d-flex align-items-center gap-2"><i data-lucide="calendar" class="text-primary" style="width:14px;"></i> ${d}</li>`).join('');
    } else {
        deadlinesList.innerHTML = `<li class="text-muted">Standard 48-hour response window.</li>`;
    }

    if (window.lucide) lucide.createIcons();
}

function initToneSwitchers() {
    document.querySelectorAll('input[name="emailTone"]').forEach(radio => {
        radio.addEventListener('change', () => {
            const body = document.getElementById('emailBodyInput').value.trim();
            if (!body) return;

            const selectedTone = radio.value;
            document.getElementById('activeReplyToneLabel').textContent = `${selectedTone} (Regenerating...)`;

            fetch('/api/emails/draft', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ body: body, tone: selectedTone })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    document.getElementById('activeReplyToneLabel').textContent = selectedTone;
                    document.getElementById('emailReplyDraftArea').value = data.reply;
                    if (window.showToast) showToast(`Reply regenerated in ${selectedTone} tone!`, 'success');
                }
            });
        });
    });
}

function initCopyButton() {
    const copyBtn = document.getElementById('copyReplyBtn');
    if (!copyBtn) return;

    copyBtn.addEventListener('click', () => {
        const text = document.getElementById('emailReplyDraftArea').value;
        if (!text) {
            if (window.showToast) showToast('No response drafted yet', 'warning');
            return;
        }
        copyToClipboard(text, copyBtn);
    });
}

function initApproveButton() {
    const approveBtn = document.getElementById('approveEmailDraftBtn');
    if (!approveBtn) return;

    approveBtn.addEventListener('click', () => {
        if (!currentEmailRecordId) {
            if (window.showToast) showToast('Please analyze an email first', 'warning');
            return;
        }

        approveBtn.disabled = true;
        approveBtn.innerHTML = `<span class="spinner-border spinner-border-sm me-1"></span> Authorizing...`;

        fetch(`/api/emails/${currentEmailRecordId}/approve`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                approveBtn.className = 'btn btn-sm btn-outline-success';
                approveBtn.innerHTML = `<i data-lucide="check" style="width:14px;height:14px;"></i> Approved & Dispatched`;
                if (window.lucide) lucide.createIcons();
                if (window.showToast) showToast('Draft formally approved by operator!', 'success');
            } else {
                approveBtn.disabled = false;
                approveBtn.innerHTML = `Approve & Authorize`;
                if (window.showToast) showToast(data.error || 'Approval failed', 'danger');
            }
        })
        .catch(() => {
            approveBtn.disabled = false;
            approveBtn.innerHTML = `Approve & Authorize`;
            if (window.showToast) showToast('Network error', 'danger');
        });
    });
}
