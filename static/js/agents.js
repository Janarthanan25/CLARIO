/**
 * CLARIO AI Agents Controller
 */

document.addEventListener('DOMContentLoaded', () => {
    initAgentConsole();
});

function initAgentConsole() {
    const form = document.getElementById('agentConsoleForm');
    const input = document.getElementById('agentConsoleInput');
    const btn = document.getElementById('agentConsoleBtn');
    const outputBox = document.getElementById('agentConsoleOutput');
    const targetLabel = document.getElementById('consoleAgentTarget');
    const execTimeLabel = document.getElementById('consoleExecTime');
    const toolsList = document.getElementById('consoleToolsList');
    const resultText = document.getElementById('consoleResultText');

    if (!form) return;

    form.addEventListener('submit', (e) => {
        e.preventDefault();
        const prompt = input.value.trim();
        if (!prompt) return;

        btn.disabled = true;
        btn.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span> Orchestrating...`;
        outputBox.classList.remove('d-none');
        targetLabel.textContent = 'Master Agent Orchestrating...';
        execTimeLabel.textContent = 'Processing...';
        toolsList.innerHTML = '';
        resultText.innerHTML = `<div class="skeleton py-4"></div>`;

        fetch('/api/agents/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt: prompt, context: { load_demo: true } })
        })
        .then(res => res.json())
        .then(data => {
            btn.disabled = false;
            btn.innerHTML = `<span>Execute Workflow</span>`;

            if (data.success && data.result) {
                const r = data.result;
                const orch = r.master_orchestration;
                targetLabel.textContent = `Master Agent → ${orch.primary_agent.replace('_', ' ').toUpperCase()}`;
                execTimeLabel.textContent = `${r.execution_time_ms} ms`;

                if (r.tools_called && r.tools_called.length) {
                    toolsList.innerHTML = `<strong>Tools Executed:</strong> ${r.tools_called.map(t => `<span class="badge bg-light text-dark border font-mono me-1">${t}</span>`).join('')}`;
                }

                resultText.innerHTML = `<div class="clario-markdown-body">${renderSafeMarkdown(r.final_summary || 'Task completed successfully.')}</div>`;
                if (window.showToast) showToast('Agent workflow completed!', 'success');
            } else {
                resultText.innerHTML = `<div class="text-danger small">Error: ${escapeHtml(data.error || 'Execution failed')}</div>`;
                if (window.showToast) showToast('Agent execution failed', 'danger');
            }
        })
        .catch(err => {
            btn.disabled = false;
            btn.innerHTML = `<span>Execute Workflow</span>`;
            resultText.innerHTML = `<div class="text-danger small">Network error: ${escapeHtml(err.message)}</div>`;
            if (window.showToast) showToast('Network error', 'danger');
        });
    });
}
