/**
 * CLARIO Financial Transaction Security AI Controller
 */

let activeModalTxId = null;

document.addEventListener('DOMContentLoaded', () => {
    initDemoLoaders();
    initCsvUpload();
    initDetailsModal();
});

function initDemoLoaders() {
    const btn1 = document.getElementById('loadDemoTransactionsBtn');
    const btn2 = document.getElementById('tableLoadDemoBtn');

    function loadDemo() {
        if (window.showToast) showToast('Loading demonstration transaction dataset...', 'info');

        fetch('/api/security/load-demo', { method: 'POST' })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    if (window.showToast) showToast('Demo transactions loaded & audited!', 'success');
                    setTimeout(() => window.location.reload(), 600);
                } else {
                    if (window.showToast) showToast(data.error || 'Failed to load demo', 'danger');
                }
            })
            .catch(() => {
                if (window.showToast) showToast('Network error loading demo', 'danger');
            });
    }

    if (btn1) btn1.addEventListener('click', loadDemo);
    if (btn2) btn2.addEventListener('click', loadDemo);
}

function initCsvUpload() {
    const fileInput = document.getElementById('txCsvFileInput');
    if (!fileInput) return;

    fileInput.addEventListener('change', () => {
        if (!fileInput.files.length) return;
        const file = fileInput.files[0];
        const formData = new FormData();
        formData.append('file', file);

        if (window.showToast) showToast(`Uploading & scanning ${file.name}...`, 'info');

        fetch('/api/security/analyze', {
            method: 'POST',
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            fileInput.value = '';
            if (data.success) {
                if (window.showToast) showToast(`Audited ${data.transactions.length} transactions successfully!`, 'success');
                setTimeout(() => window.location.reload(), 800);
            } else {
                if (window.showToast) showToast(data.error || 'Audit failed', 'danger');
            }
        })
        .catch(() => {
            fileInput.value = '';
            if (window.showToast) showToast('CSV upload error', 'danger');
        });
    });
}

function initDetailsModal() {
    const modalEl = document.getElementById('txReviewModal');
    if (!modalEl) return;
    const modal = new bootstrap.Modal(modalEl);

    document.addEventListener('click', (e) => {
        const btn = e.target.closest('.view-details-btn');
        if (!btn) return;

        const tx = JSON.parse(btn.getAttribute('data-tx'));
        activeModalTxId = tx.id;
        const risk = tx.risk_result || {};

        document.getElementById('modalTxId').textContent = tx.external_tx_id;
        document.getElementById('modalAmount').textContent = `$${parseFloat(tx.amount).toFixed(2)} ${tx.currency}`;
        document.getElementById('modalRiskScore').textContent = `${(risk.risk_score || 15).toFixed(1)} / 100`;
        document.getElementById('modalRiskLevel').textContent = risk.risk_level || 'LOW';

        const indList = document.getElementById('modalIndicatorsList');
        if (risk.detected_indicators && risk.detected_indicators.length) {
            indList.innerHTML = risk.detected_indicators.map(i => `<li>${i}</li>`).join('');
        } else {
            indList.innerHTML = `<li>Conforms to baseline.</li>`;
        }

        document.getElementById('modalExplanation').innerHTML = renderSafeMarkdown(risk.explanation || 'Normal transaction profile.');
        document.getElementById('modalRecommendedAction').textContent = risk.recommended_action || 'Approve transaction';

        modal.show();
    });

    const approveBtn = document.getElementById('modalApproveBtn');
    const flagBtn = document.getElementById('modalFlagFraudBtn');

    function sendDecision(decision) {
        if (!activeModalTxId) return;

        fetch('/api/security/review', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ transaction_id: activeModalTxId, decision: decision })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                if (window.showToast) showToast(`Transaction marked as ${decision}`, 'success');
                const badge = document.getElementById(`statusBadge-${activeModalTxId}`);
                if (badge) {
                    badge.textContent = decision.toUpperCase();
                    badge.className = `badge ${decision === 'approved' ? 'bg-success-subtle text-success' : 'bg-danger-subtle text-danger'}`;
                }
                modal.hide();
            } else {
                if (window.showToast) showToast(data.error || 'Review failed', 'danger');
            }
        });
    }

    if (approveBtn) approveBtn.addEventListener('click', () => sendDecision('approved'));
    if (flagBtn) flagBtn.addEventListener('click', () => sendDecision('flagged_fraud'));
}
