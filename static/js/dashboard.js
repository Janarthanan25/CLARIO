/**
 * CLARIO Dashboard Controller
 */

let riskChartInstance = null;
let moduleChartInstance = null;

document.addEventListener('DOMContentLoaded', () => {
    loadDashboardMetrics();
    loadDashboardActivity();
    setupCommandCenter();
});

function loadDashboardMetrics() {
    fetch('/api/dashboard/stats')
        .then(res => res.json())
        .then(res => {
            if (!res.success) return;
            const stats = res.stats;
            const chartData = res.chart_data;

            document.getElementById('statDocsAnalyzed').textContent = stats.documents_analyzed;
            document.getElementById('statEmailsProcessed').textContent = stats.emails_processed;
            document.getElementById('statTxsMonitored').textContent = stats.transactions_monitored;
            document.getElementById('statSuspiciousTxs').textContent = stats.suspicious_transactions;
            document.getElementById('statAgentActivity').textContent = stats.ai_agent_activity;
            document.getElementById('statPlan').textContent = stats.plan;

            renderRiskChart(chartData.risk_distribution);
            renderModuleChart(chartData.module_usage);
        })
        .catch(err => {
            console.error('Error fetching dashboard stats:', err);
        });
}

function renderRiskChart(dist) {
    const ctx = document.getElementById('riskDistributionChart');
    if (!ctx) return;

    if (riskChartInstance) riskChartInstance.destroy();

    const hasData = dist.data.some(v => v > 0);
    const dataVals = hasData ? dist.data : [1, 0, 0];
    const labels = hasData ? dist.labels : ['No Audits Yet', 'Medium', 'High'];

    riskChartInstance = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: dataVals,
                backgroundColor: hasData ? ['#10B981', '#F59E0B', '#EF4444'] : ['#E2E8F0', '#CBD5E1', '#94A3B8'],
                borderWidth: 2,
                borderColor: '#ffffff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { font: { family: 'Plus Jakarta Sans', size: 12 } }
                }
            },
            cutout: '72%'
        }
    });
}

function renderModuleChart(usage) {
    const ctx = document.getElementById('moduleUsageChart');
    if (!ctx) return;

    if (moduleChartInstance) moduleChartInstance.destroy();

    moduleChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: usage.labels,
            datasets: [{
                label: 'Interactions',
                data: usage.data,
                backgroundColor: ['#2563EB', '#7C3AED', '#06B6D4', '#10B981'],
                borderRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { precision: 0 }
                }
            }
        }
    });
}

function loadDashboardActivity() {
    const container = document.getElementById('recentActivityList');
    if (!container) return;

    fetch('/api/dashboard/activity')
        .then(res => res.json())
        .then(res => {
            if (!res.success || !res.activities.length) {
                container.innerHTML = `
                    <div class="text-center py-4 text-muted small">
                        No recent actions recorded. Start by uploading a document or auditing transactions.
                    </div>`;
                return;
            }

            container.innerHTML = `
                <div class="table-responsive">
                    <table class="table table-hover align-middle mb-0">
                        <thead class="table-light small text-secondary">
                            <tr>
                                <th>Action</th>
                                <th>Resource</th>
                                <th>IP Address</th>
                                <th>Timestamp</th>
                            </tr>
                        </thead>
                        <tbody class="small">
                            ${res.activities.map(a => `
                                <tr>
                                    <td><span class="badge bg-light text-dark border font-mono">${a.action}</span></td>
                                    <td class="text-secondary">${a.resource || 'system'}</td>
                                    <td class="text-muted font-mono" style="font-size:0.75rem;">${a.ip_address}</td>
                                    <td class="text-muted">${new Date(a.created_at).toLocaleString()}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            `;
        })
        .catch(() => {});
}

function setupCommandCenter() {
    const form = document.getElementById('globalCommandForm');
    const input = document.getElementById('globalCommandInput');
    const btn = document.getElementById('globalCommandSubmitBtn');
    const outputBox = document.getElementById('commandExecutionOutput');
    const agentNameEl = document.getElementById('commandAgentName');
    const execTimeEl = document.getElementById('commandExecTime');
    const reasoningEl = document.getElementById('commandRoutingReasoning');
    const resultBodyEl = document.getElementById('commandResultBody');

    if (!form) return;

    form.addEventListener('submit', (e) => {
        e.preventDefault();
        const prompt = input.value.trim();
        if (!prompt) return;

        btn.disabled = true;
        btn.innerHTML = `<span class="spinner-border spinner-border-sm"></span> Orchestrating...`;
        outputBox.classList.remove('d-none');
        agentNameEl.textContent = 'Master Orchestrator Reasoning...';
        execTimeEl.textContent = 'Processing';
        reasoningEl.textContent = 'Decomposing request and evaluating specialist requirements...';
        resultBodyEl.innerHTML = `<div class="skeleton py-4"></div>`;

        fetch('/api/agents/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt: prompt, context: { load_demo: true } })
        })
        .then(res => res.json())
        .then(data => {
            btn.disabled = false;
            btn.innerHTML = `<span>Dispatch</span> <i data-lucide="send" style="width:16px;height:16px;"></i>`;
            if (window.lucide) lucide.createIcons();

            if (data.success && data.result) {
                const r = data.result;
                const orch = r.master_orchestration;
                agentNameEl.textContent = `Master Agent → ${orch.primary_agent.replace('_', ' ').toUpperCase()}`;
                execTimeEl.textContent = `${r.execution_time_ms} ms`;
                reasoningEl.innerHTML = `<strong>Routing Decision:</strong> ${orch.reasoning}`;
                resultBodyEl.innerHTML = `<div class="clario-markdown-body">${renderSafeMarkdown(r.final_summary || 'Task completed successfully.')}</div>`;
                if (window.showToast) showToast('Master Agent executed task successfully!', 'success');
                // Refresh metrics
                loadDashboardMetrics();
                loadDashboardActivity();
            } else {
                resultBodyEl.innerHTML = `<div class="text-danger small">Orchestration error: ${escapeHtml(data.error || 'Failed to execute command.')}</div>`;
                if (window.showToast) showToast('Command processing failed', 'danger');
            }
        })
        .catch(err => {
            btn.disabled = false;
            btn.innerHTML = `<span>Dispatch</span>`;
            resultBodyEl.textContent = `Connection error: ${err.message}`;
            if (window.showToast) showToast('Network error', 'danger');
        });
    });
}
