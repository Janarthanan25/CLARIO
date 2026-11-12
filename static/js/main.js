/**
 * CLARIO Global Application Framework
 */

function getCsrfToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute('content') : '';
}

// Global fetch wrapper to auto-inject CSRF token on state-changing requests
const originalFetch = window.fetch;
window.fetch = function(url, options = {}) {
    if (options.method && !['GET', 'HEAD', 'OPTIONS'].includes(options.method.toUpperCase())) {
        options.headers = options.headers || {};
        const token = getCsrfToken();
        if (token) {
            if (options.headers instanceof Headers) {
                if (!options.headers.has('X-CSRFToken')) {
                    options.headers.append('X-CSRFToken', token);
                }
            } else if (Array.isArray(options.headers)) {
                options.headers.push(['X-CSRFToken', token]);
            } else {
                if (!options.headers['X-CSRFToken']) {
                    options.headers['X-CSRFToken'] = token;
                }
            }
        }
    }
    return originalFetch(url, options);
};

/**
 * Safe HTML text escaper
 */
function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = String(str);
    return div.innerHTML;
}

let _markedConfigured = false;
function initMarked() {
    if (_markedConfigured || typeof marked === 'undefined') return;
    try {
        const renderer = new marked.Renderer();
        renderer.code = function(code, lang) {
            let codeStr = code;
            let langStr = lang;
            if (typeof code === 'object' && code !== null) {
                codeStr = code.text || '';
                langStr = code.lang || '';
            }
            const validLang = (langStr || '').match(/\S*/)[0];
            let highlighted = codeStr;
            if (typeof hljs !== 'undefined') {
                if (validLang && hljs.getLanguage(validLang)) {
                    try {
                        highlighted = hljs.highlight(codeStr, { language: validLang, ignoreIllegals: true }).value;
                    } catch (e) {}
                } else {
                    try {
                        highlighted = hljs.highlightAuto(codeStr).value;
                    } catch (e) {}
                }
            }
            const langClass = validLang ? ` language-${validLang}` : '';
            return `<pre class="code-block my-2"><code class="hljs${langClass}">${highlighted}</code></pre>`;
        };

        marked.use({
            renderer: renderer,
            gfm: true,
            breaks: true
        });
        _markedConfigured = true;
    } catch (e) {
        console.warn('Failed to configure marked:', e);
    }
}

/**
 * Safe, sanitized Markdown renderer with syntax highlighting
 * @param {string} markdownText
 * @returns {string} Sanitized HTML
 */
function renderSafeMarkdown(markdownText) {
    if (!markdownText) return '';
    const text = String(markdownText);

    if (typeof marked !== 'undefined') {
        try {
            initMarked();
            const parsedHtml = marked.parse(text);

            if (typeof DOMPurify !== 'undefined') {
                return DOMPurify.sanitize(parsedHtml, {
                    ADD_ATTR: ['target', 'class']
                });
            }
            return parsedHtml;
        } catch (err) {
            console.warn('Markdown parsing error:', err);
        }
    }

    // Fallback simple escape
    return escapeHtml(text).replace(/\n/g, '<br>');
}

document.addEventListener('DOMContentLoaded', () => {
    // 1. Initialize Lucide Icons
    if (window.lucide) {
        lucide.createIcons();
    }

    // 2. Setup Mobile Sidebar Toggle
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('clarioSidebar');
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', () => {
            sidebar.classList.toggle('show');
        });
    }

    // 3. Setup In-App Notification Center
    initNotificationCenter();
});

/**
 * Toast Notification System
 * @param {string} message 
 * @param {'success'|'danger'|'warning'|'info'} type 
 */
function showToast(message, type = 'info') {
    let container = document.getElementById('toastContainer');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
    }

    const toastEl = document.createElement('div');
    toastEl.className = `toast align-items-center text-bg-${type} border-0 show shadow-lg mb-2`;
    toastEl.setAttribute('role', 'alert');
    toastEl.setAttribute('aria-live', 'assertive');
    toastEl.setAttribute('aria-atomic', 'true');

    toastEl.innerHTML = `
        <div class="d-flex">
            <div class="toast-body d-flex align-items-center gap-2">
                <span>${message}</span>
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;

    container.appendChild(toastEl);

    setTimeout(() => {
        toastEl.classList.remove('show');
        setTimeout(() => toastEl.remove(), 300);
    }, 4500);
}

/**
 * Copy to Clipboard with Visual Feedback
 */
function copyToClipboard(text, btnElement = null) {
    if (!navigator.clipboard) {
        // Fallback
        const textarea = document.createElement('textarea');
        textarea.value = text;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
        showToast('Copied to clipboard!', 'success');
        return;
    }

    navigator.clipboard.writeText(text).then(() => {
        showToast('Copied to clipboard!', 'success');
        if (btnElement) {
            const originalHTML = btnElement.innerHTML;
            btnElement.innerHTML = `<i data-lucide="check" style="width:16px;height:16px;"></i> Copied!`;
            if (window.lucide) lucide.createIcons();
            setTimeout(() => {
                btnElement.innerHTML = originalHTML;
                if (window.lucide) lucide.createIcons();
            }, 2000);
        }
    }).catch(err => {
        showToast('Failed to copy text', 'danger');
    });
}

/**
 * In-App Notification Center
 */
function initNotificationCenter() {
    const notifBtn = document.getElementById('notificationDropdownBtn');
    const notifList = document.getElementById('notificationList');
    const notifBadge = document.getElementById('notificationBadge');

    if (!notifBtn || !notifList) return;

    function fetchNotifications() {
        fetch('/api/notifications')
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    if (data.unread_count > 0) {
                        notifBadge.textContent = data.unread_count;
                        notifBadge.classList.remove('d-none');
                    } else {
                        notifBadge.classList.add('d-none');
                    }

                    if (data.notifications.length === 0) {
                        notifList.innerHTML = `<li class="p-3 text-center text-muted small">No notifications yet</li>`;
                    } else {
                        notifList.innerHTML = data.notifications.map(n => `
                            <li class="dropdown-item p-2 border-bottom ${n.is_read ? 'opacity-75' : 'bg-light'}">
                                <div class="d-flex justify-content-between align-items-start">
                                    <strong class="small text-dark">${n.title}</strong>
                                    <small class="text-muted" style="font-size:0.75rem;">${new Date(n.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</small>
                                </div>
                                <div class="text-secondary small mt-1">${n.message}</div>
                            </li>
                        `).join('');
                    }
                }
            })
            .catch(() => {});
    }

    fetchNotifications();

    const markAllReadBtn = document.getElementById('markAllNotificationsReadBtn');
    if (markAllReadBtn) {
        markAllReadBtn.addEventListener('click', (e) => {
            e.preventDefault();
            fetch('/api/notifications/read-all', { method: 'POST' })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        notifBadge.classList.add('d-none');
                        fetchNotifications();
                    }
                });
        });
    }
}
