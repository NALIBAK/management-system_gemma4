/* ============================================================
   AIRA — Persistent Side Panel (Phase 2)
   College Management System
   ============================================================ */

(function () {
    'use strict';

    // ── Constants ──────────────────────────────────────────────
    const DEFAULT_WIDTH = 480;
    const MIN_WIDTH = 300;
    const MAX_WIDTH = 720;
    const LS_WIDTH = 'aira_panel_width';
    const LS_OPEN = 'aira_panel_open';
    const SS_PAGE = 'aira_last_page';
    const SS_CONV = 'aira_conversation_id';

    // ── Quick Action Chips ─────────────────────────────────────
    const QUICK_CHIPS = [
        { label: '📊 Dept Summary', q: 'Show department summary' },
        { label: '🏆 Top CGPA', q: 'Show top 10 students by CGPA' },
        { label: '⚠️ Low Attendance', q: 'Show students below 75% attendance' },
        { label: '💰 Fee Defaulters', q: 'Show fee defaulters' },
        { label: '📝 Marks Report', q: 'Show marks report' },
        { label: '✅ Eligibility', q: 'Show eligibility report' },
        { label: '🎓 Scholarship', q: 'Show scholarship report' },
        { label: '🏆 Activities', q: 'Show extracurricular activities' },
        { label: '🏫 Overview', q: 'Show college overview' },
        { label: '📋 My Reports', q: 'Show my saved reports' },
        { label: '📈 CGPA Report', q: 'Show CGPA report' },
        { label: '🔍 Help', q: 'help' },
    ];

    // ── State ─────────────────────────────────────────────────
    let conversationId = sessionStorage.getItem(SS_CONV) || null;
    let isTyping = false;
    let csvDetected = null;
    let panelEl = null;
    let messagesEl = null;
    let mainContentEl = null;
    let currentWidth = parseInt(localStorage.getItem(LS_WIDTH)) || DEFAULT_WIDTH;

    // ── marked.js loader ──────────────────────────────────────
    function loadMarked() {
        return new Promise(resolve => {
            if (window.marked) { resolve(); return; }
            const s = document.createElement('script');
            s.src = 'https://cdn.jsdelivr.net/npm/marked/marked.min.js';
            s.onload = resolve;
            s.onerror = resolve; // fallback gracefully
            document.head.appendChild(s);
        });
    }

    function renderMd(text) {
        if (!text) return '';
        try {
            if (window.marked) return marked.parse(String(text));
        } catch (e) { }
        return String(text).replace(/\n/g, '<br>');
    }

    function escHtml(str) {
        return String(str)
            .replace(/&/g, '&amp;').replace(/</g, '&lt;')
            .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }

    // ── Page navigation map ───────────────────────────────────
    const PAGE_MAP = {
        'dashboard': '../dashboard.html',
        'students': '../students/index.html',
        'staff': '../staff/index.html',
        'departments': '../departments/index.html',
        'courses': '../courses/index.html',
        'timetable': '../timetable/index.html',
        'attendance': '../attendance/index.html',
        'marks': '../marks/index.html',
        'fees': '../fees/index.html',
        'reports': '../reports/index.html',
        'notifications': '../notifications/index.html',
        'settings': '../settings/index.html',
    };

    // ── Build panel HTML ──────────────────────────────────────
    function buildPanel() {
        const chips = QUICK_CHIPS.map(c =>
            `<button class="aira-quick-chip" data-q="${escHtml(c.q)}">${c.label}</button>`
        ).join('');

        return `
    <div class="aira-resize-handle" id="aira-handle"></div>
    <aside class="aira-side-panel" id="aira-panel">
      <div class="aira-panel-header">
        <div class="aira-panel-header-left">
          <div class="aira-panel-avatar">🤖</div>
          <div>
            <div class="aira-panel-title">
              AIRA <span class="aira-panel-badge">Autonomous Agent</span>
            </div>
            <div class="aira-panel-subtitle" id="aira-status-indicator">⏳ Checking AI Status...</div>
          </div>
        </div>
        <div class="aira-panel-header-right">
          <button class="aira-collapse-btn" id="aira-collapse" title="Collapse AIRA">◀</button>
        </div>
      </div>

      <div class="aira-messages" id="aira-messages"></div>

      <div class="aira-quick-actions" id="aira-quick-actions">${chips}</div>

      <div class="aira-input-area">
        <div class="aira-csv-banner" id="aira-csv-banner" style="display:none">
          📋 CSV detected — <strong>use this to upload marks?</strong>
          <span id="aira-csv-dismiss" style="cursor:pointer;font-size:14px">✕</span>
        </div>
        <div class="aira-input-row">
          <textarea
            id="aira-input"
            placeholder="Ask AIRA anything about students, staff, fees, marks..."
            rows="1"
          ></textarea>
          <button id="aira-send" title="Send">➤</button>
        </div>
        <div class="aira-powered-by">Powered by Gemma 4 (Local Offline AI) • Role-Based Access</div>
      </div>
    </aside>`;
    }

    // ── Width & margin helpers ────────────────────────────────
    function applyWidth(w, save) {
        currentWidth = Math.min(MAX_WIDTH, Math.max(MIN_WIDTH, w));
        if (panelEl) panelEl.style.width = currentWidth + 'px';
        const handleEl = document.getElementById('aira-handle');
        if (handleEl) handleEl.style.right = currentWidth + 'px';
        if (mainContentEl && !panelEl.classList.contains('aira-panel-collapsed')) {
            mainContentEl.style.marginRight = currentWidth + 'px';
        }
        if (save) localStorage.setItem(LS_WIDTH, currentWidth);
    }

    function openPanel() {
        panelEl.classList.remove('aira-panel-collapsed');
        const handle = document.getElementById('aira-handle');
        if (handle) handle.style.display = '';
        if (mainContentEl) mainContentEl.style.marginRight = currentWidth + 'px';
        const toggleBtn = document.getElementById('aira-toggle');
        if (toggleBtn) toggleBtn.classList.remove('panel-closed');
        localStorage.setItem(LS_OPEN, 'true');
        scrollBottom();
    }

    function closePanel() {
        panelEl.classList.add('aira-panel-collapsed');
        const handle = document.getElementById('aira-handle');
        if (handle) handle.style.display = 'none';
        if (mainContentEl) mainContentEl.style.marginRight = '0';
        const toggleBtn = document.getElementById('aira-toggle');
        if (toggleBtn) toggleBtn.classList.add('panel-closed');
        localStorage.setItem(LS_OPEN, 'false');
    }

    function scrollBottom() {
        if (messagesEl) setTimeout(() => { messagesEl.scrollTop = messagesEl.scrollHeight; }, 60);
    }

    // ── History Persistence ───────────────────────────────────
    const SS_HISTORY = 'aira_html_history';
    function saveHistory() {
        if (messagesEl) sessionStorage.setItem(SS_HISTORY, messagesEl.innerHTML);
    }

    // ── Message renderers ─────────────────────────────────────
    function appendUserMsg(text) {
        const user = (typeof auth !== 'undefined') ? auth.getUser() : null;
        const initials = user?.username?.slice(0, 2).toUpperCase() || 'U';
        const div = document.createElement('div');
        div.className = 'aira-msg user';
        div.innerHTML = `
      <div class="aira-msg-avatar">${escHtml(initials)}</div>
      <div class="aira-msg-content">
        <div class="aira-bubble">${escHtml(text)}</div>
      </div>`;
        messagesEl.appendChild(div);
        scrollBottom();
        saveHistory();
        // hide chips after first send
        const qa = document.getElementById('aira-quick-actions');
        if (qa) qa.style.display = 'none';
    }

    function appendAiraMsg(text, extraHtml) {
        const div = document.createElement('div');
        div.className = 'aira-msg aira';
        const rendered = renderMd(text);
        const showCopy = text.length > 200;
        div.innerHTML = `
      <div class="aira-msg-avatar">🤖</div>
      <div class="aira-msg-content">
        <div class="aira-bubble" data-raw="${escHtml(text)}">${rendered}</div>
        ${extraHtml || ''}
        ${showCopy ? '<button class="aira-copy-btn">📋 Copy</button>' : ''}
      </div>`;
        messagesEl.appendChild(div);
        scrollBottom();
        saveHistory();
        return div;
    }

    function appendPageSep(pageName) {
        const sep = document.createElement('div');
        sep.className = 'aira-page-sep';
        sep.textContent = `Now on: ${pageName}`;
        messagesEl.appendChild(sep);
        scrollBottom();
        saveHistory();
    }

    function showTypingIndicator() {
        const div = document.createElement('div');
        div.className = 'aira-msg aira';
        div.id = 'aira-typing';
        div.innerHTML = `
      <div class="aira-msg-avatar">🤖</div>
      <div class="aira-msg-content">
        <div class="aira-typing"><span></span><span></span><span></span></div>
      </div>`;
        messagesEl.appendChild(div);
        scrollBottom();
    }

    function hideTypingIndicator() {
        document.getElementById('aira-typing')?.remove();
    }

    // ── Global event delegation for messages ──────────────────
    function setupMessageDelegation() {
        messagesEl.addEventListener('click', e => {
            if (e.target.classList.contains('aira-copy-btn')) {
                const btn = e.target;
                const bubble = btn.parentElement.querySelector('.aira-bubble');
                const text = bubble ? (bubble.getAttribute('data-raw') || bubble.innerText) : '';
                navigator.clipboard?.writeText(text).then(() => {
                    btn.textContent = '✅ Copied!';
                    setTimeout(() => { btn.textContent = '📋 Copy'; }, 2000);
                });
            }
        });
    }

    // ── Card builders ─────────────────────────────────────────
    function reportCard(data) {
        const icon = (data.format || '').toLowerCase() === 'excel' ? '📊' : '📄';
        const baseUrl = 'http://localhost:6000';
        return `
      <div class="aira-card">
        <div class="aira-card-title">${icon} ${escHtml(data.filename || 'report')}</div>
        <div class="aira-card-meta">Generated ${new Date().toLocaleDateString()}</div>
        <div class="aira-card-actions">
          <a href="${baseUrl}${escHtml(data.preview_url)}" target="_blank" class="aira-card-btn">👁 Preview</a>
          <a href="${baseUrl}${escHtml(data.download_url)}" download="${escHtml(data.filename)}" class="aira-card-btn primary">⬇ Download</a>
        </div>
      </div>`;
    }

    function navCard(data) {
        return `
      <div class="aira-card">
        <div class="aira-card-title">📍 ${escHtml(data.label || data.page)}</div>
        <div class="aira-card-actions">
          <a href="${escHtml(data.url)}" target="_blank" class="aira-card-btn">🔗 Open Page</a>
          <a href="${escHtml(data.url)}" class="aira-card-btn primary">Take me there →</a>
        </div>
      </div>`;
    }

    function bulkCard(data, uid) {
        const studentRows = (data.students || [])
            .map(s => `<div style="padding:3px 0;border-bottom:1px solid var(--border);font-size:11px">
        ${escHtml(s.name)} <span style="color:var(--text-muted)">(${escHtml(s.reg_no || '')})</span>
      </div>`).join('');
        return `
      <div class="aira-card" id="bulk-${uid}">
        <div class="aira-card-title">⚠️ ${escHtml(data.action_description || 'Bulk operation')}</div>
        <div class="aira-card-meta">Affects <strong>${data.count || 0}</strong> students</div>
        ${studentRows ? `<details style="margin-bottom:8px">
          <summary style="cursor:pointer;font-size:12px;color:var(--accent);font-weight:600;list-style:none">
            ▶ Show student list
          </summary>
          <div style="margin-top:6px;max-height:140px;overflow-y:auto">${studentRows}</div>
        </details>` : ''}
        <div class="aira-card-actions">
          <button class="aira-card-btn" onclick="document.getElementById('bulk-${uid}').remove()">✕ Cancel</button>
          <button class="aira-card-btn primary" id="bulk-confirm-${uid}" onclick="window._airaBulkConfirm('${uid}', '${escHtml(data.action_id || '')}')">✅ Confirm</button>
        </div>
      </div>`;
    }

    window._airaBulkConfirm = async function (uid, actionId) {
        const btn = document.getElementById('bulk-confirm-' + uid);
        if (btn) { btn.disabled = true; btn.textContent = '⏳ Processing...'; }
        try {
            const res = await window.api.post('/aira/execute-tool', { tool: 'bulk_execute', params: { action_id: actionId } });
            if (!res.ok) throw new Error(res.data?.message || 'Error executing tool');
            document.getElementById('bulk-' + uid)?.remove();
            appendAiraMsg(res.data?.data?.message || '✅ Bulk operation completed.');
        } catch (e) {
            if (btn) { btn.disabled = false; btn.textContent = '✅ Confirm'; }
            appendAiraMsg('❌ Bulk operation failed. Please try again.');
        }
    };

    // ── Send message ──────────────────────────────────────────
    async function sendMessage() {
        const inputEl = document.getElementById('aira-input');
        const sendBtn = document.getElementById('aira-send');
        const text = inputEl.value.trim();
        if (!text || isTyping) return;

        inputEl.value = '';
        inputEl.style.height = 'auto';
        csvDetected = null;
        document.getElementById('aira-csv-banner').style.display = 'none';

        appendUserMsg(text);
        isTyping = true;
        sendBtn.disabled = true;
        showTypingIndicator();

        try {
            const pageName = document.title.replace(/—.*/, '').trim();
            const payload = {
                message: text,
                conversation_id: conversationId,
                page_context: pageName,
            };
            if (csvDetected) payload.csv_data = csvDetected;

            const res = await window.api.post('/aira/chat', payload);
            hideTypingIndicator();

            if (!res.ok) throw new Error(res.data?.message || 'Error from server');

            const data = res.data.data || {};
            if (data.conversation_id) {
                conversationId = data.conversation_id;
                sessionStorage.setItem(SS_CONV, conversationId);
            }

            // Determine extra card HTML
            let cardHtml = '';
            const rt = data.response_type || data.type;
            if (rt === 'report' && data.filename) cardHtml = reportCard(data);
            else if (rt === 'navigate' && data.url) cardHtml = navCard(data);
            else if (rt === 'bulk_confirm') cardHtml = bulkCard(data, Date.now());

            appendAiraMsg(data.response || data.message || 'Done.', cardHtml);

        } catch (err) {
            hideTypingIndicator();
            appendAiraMsg('❌ Something went wrong. Check your connection and try again.\n\n`' + (err.message || 'Unknown error') + '`');
        } finally {
            isTyping = false;
            sendBtn.disabled = false;
        }
    }

    // ── Main init ─────────────────────────────────────────────
    async function init() {
        // Only inject on pages that have .app-layout (i.e. not login.html)
        const layout = document.querySelector('.app-layout');
        if (!layout) return;

        await loadMarked();

        async function checkAIStatus() {
            try {
                const res = await window.api.get('/aira/test');
                const statusEl = document.getElementById('aira-status-indicator');
                if (statusEl) {
                    if (res?.ok && res?.data?.success) {
                        statusEl.innerHTML = '🟢 <b>AI Online (Local Gemma 4)</b>';
                    } else {
                        statusEl.innerHTML = '🔴 <b>AI Offline — Basic Mode</b>';
                    }
                }
            } catch (e) {
                const statusEl = document.getElementById('aira-status-indicator');
                if (statusEl) statusEl.innerHTML = '🔴 <b>AI Offline — Basic Mode</b>';
            }
        }

        // Inject panel HTML
        layout.insertAdjacentHTML('beforeend', buildPanel());
        panelEl = document.getElementById('aira-panel');
        messagesEl = document.getElementById('aira-messages');
        mainContentEl = document.querySelector('.main-content');

        // Inject AIRA toggle button into nav header-actions
        const headerActions = document.querySelector('.header-actions');
        if (headerActions) {
            const btn = document.createElement('button');
            btn.className = 'btn-aira-toggle';
            btn.id = 'aira-toggle';
            btn.title = 'Toggle AIRA Panel';
            btn.innerHTML = '🤖 AIRA';
            headerActions.insertBefore(btn, headerActions.firstChild);
        }

        // Apply saved width
        applyWidth(currentWidth, false);

        // Apply saved open state (default open)
        const savedOpen = localStorage.getItem(LS_OPEN);
        if (savedOpen === 'false') {
            closePanel();
        } else {
            openPanel();
        }

        // ── Resize drag ────────────────────────────────────────
        const handleEl = document.getElementById('aira-handle');
        let dragging = false, startX, startW;

        handleEl.addEventListener('mousedown', e => {
            dragging = true;
            startX = e.clientX;
            startW = currentWidth;
            handleEl.classList.add('dragging');
            document.body.style.userSelect = 'none';
            document.body.style.cursor = 'col-resize';
            e.preventDefault();
        });

        document.addEventListener('mousemove', e => {
            if (!dragging) return;
            const delta = startX - e.clientX;
            applyWidth(startW + delta, false);
        });

        document.addEventListener('mouseup', () => {
            if (!dragging) return;
            dragging = false;
            handleEl.classList.remove('dragging');
            document.body.style.userSelect = '';
            document.body.style.cursor = '';
            applyWidth(currentWidth, true); // save
        });

        // ── Collapse / Expand ──────────────────────────────────
        document.getElementById('aira-collapse').addEventListener('click', () => {
            if (panelEl.classList.contains('aira-panel-collapsed')) openPanel();
            else closePanel();
        });

        document.getElementById('aira-toggle')?.addEventListener('click', () => {
            if (panelEl.classList.contains('aira-panel-collapsed')) openPanel();
            else closePanel();
        });

        // ── Restore History ────────────────────────────────────
        const savedHistory = sessionStorage.getItem(SS_HISTORY);
        if (savedHistory) {
            messagesEl.innerHTML = savedHistory;
            setupMessageDelegation();
        }

        // ── Page separator ─────────────────────────────────────
        const lastPage = sessionStorage.getItem(SS_PAGE);
        const currentPage = document.title.replace(/—.*/, '').trim();
        if (lastPage && lastPage !== currentPage && messagesEl.children.length > 0) {
            appendPageSep(currentPage);
        }
        sessionStorage.setItem(SS_PAGE, currentPage);

        // ── Welcome message ────────────────────────────────────
        if (messagesEl.children.length === 0) {
            appendAiraMsg(
                `👋 **Welcome to AIRA** — your autonomous AI assistant!

I have **full access** to the college database and can:
- 📊 **Reports**: attendance, marks, fees, CGPA, eligibility, scholarships
- 🏆 **Rankings**: top students by CGPA, low attendance alerts
- 📄 **Export**: generate PDF or Excel reports directly from chat
- 🧭 **Navigate**: take you to any page in the system
- 📋 **Bulk ops**: mark entire sections present/absent with confirmation
- 🔍 **Search**: find any student, staff, or department instantly

Type **help** to see all commands or click a quick action above.`
            );
        }

        // ── Input handlers ─────────────────────────────────────
        const inputEl = document.getElementById('aira-input');
        const sendBtn = document.getElementById('aira-send');

        sendBtn.addEventListener('click', sendMessage);
        inputEl.addEventListener('keydown', e => {
            if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
        });

        // Auto-resize + CSV detection
        inputEl.addEventListener('input', () => {
            inputEl.style.height = 'auto';
            inputEl.style.height = Math.min(inputEl.scrollHeight, 120) + 'px';

            const val = inputEl.value;
            const lines = val.trim().split('\n');
            const looksLikeCsv = lines.length > 1 &&
                lines[0].includes(',') && lines[0].split(',').length >= 2;
            if (looksLikeCsv) {
                csvDetected = val;
                document.getElementById('aira-csv-banner').style.display = 'flex';
            } else {
                csvDetected = null;
                document.getElementById('aira-csv-banner').style.display = 'none';
            }
        });

        document.getElementById('aira-csv-dismiss').addEventListener('click', () => {
            csvDetected = null;
            document.getElementById('aira-csv-banner').style.display = 'none';
        });

        // ── Quick chips ────────────────────────────────────────
        document.querySelectorAll('.aira-quick-chip').forEach(chip => {
            chip.addEventListener('click', () => {
                inputEl.value = chip.dataset.q;
                sendMessage();
            });
        });

        // ── Mobile: auto-hide below 768px ─────────────────────
        function checkMobile() {
            if (window.innerWidth < 768) {
                panelEl.classList.remove('mobile-visible');
                if (mainContentEl) mainContentEl.style.marginRight = '0';
                handleEl.style.display = 'none';
            } else {
                handleEl.style.display = '';
                // restore desktop state
                if (!panelEl.classList.contains('aira-panel-collapsed') && mainContentEl) {
                    mainContentEl.style.marginRight = currentWidth + 'px';
                }
            }
        }
        window.addEventListener('resize', checkMobile);
        checkMobile();

        checkMobile();
        checkAIStatus();
        document.getElementById('aira-toggle')?.addEventListener('click', () => {
            if (window.innerWidth < 768) {
                panelEl.classList.toggle('mobile-visible');
            }
        }, true); // true = capture phase so this runs first
    }

    // Run after DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
