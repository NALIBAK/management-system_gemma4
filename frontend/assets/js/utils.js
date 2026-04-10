/* ============================================================
   Utils — Shared helper functions
   ============================================================ */

const utils = {
    // Toast notifications
    toast(message, type = 'info', duration = 3500) {
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'toast-container';
            document.body.appendChild(container);
        }
        const icons = { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' };
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `<span>${icons[type] || 'ℹ️'}</span><span>${message}</span>`;
        container.appendChild(toast);
        setTimeout(() => {
            toast.style.animation = 'slideIn 0.3s ease reverse';
            setTimeout(() => toast.remove(), 300);
        }, duration);
    },

    // Format date
    formatDate(dateStr, format = 'short') {
        if (!dateStr) return '—';
        const d = new Date(dateStr);
        if (format === 'short') return d.toLocaleDateString('en-IN');
        if (format === 'long') return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' });
        return d.toLocaleDateString('en-IN');
    },

    // Format currency
    formatCurrency(amount) {
        if (amount == null) return '—';
        return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(amount);
    },

    // Confirm dialog
    confirm(message, onConfirm, title = 'Confirm Action') {
        const overlay = document.createElement('div');
        overlay.className = 'modal-overlay open';
        overlay.innerHTML = `
      <div class="modal" style="max-width:420px">
        <div class="modal-header">
          <h3 class="modal-title">⚠️ ${title}</h3>
        </div>
        <div class="modal-body">
          <p style="color:var(--text-secondary)">${message}</p>
        </div>
        <div class="modal-footer">
          <button class="btn btn-ghost" id="confirm-cancel">Cancel</button>
          <button class="btn btn-danger" id="confirm-ok">Confirm</button>
        </div>
      </div>`;
        document.body.appendChild(overlay);
        overlay.querySelector('#confirm-cancel').onclick = () => overlay.remove();
        overlay.querySelector('#confirm-ok').onclick = () => { overlay.remove(); onConfirm(); };
        overlay.onclick = (e) => { if (e.target === overlay) overlay.remove(); };
    },

    // Open/close modal
    openModal(id) { document.getElementById(id)?.classList.add('open'); },
    closeModal(id) { document.getElementById(id)?.classList.remove('open'); },

    // Render table rows
    renderTable(tbodyId, rows, renderFn, emptyMsg = 'No records found') {
        const tbody = document.getElementById(tbodyId);
        if (!tbody) return;
        if (!rows || rows.length === 0) {
            tbody.innerHTML = `<tr><td colspan="100" style="text-align:center;padding:40px;color:var(--text-muted)">${emptyMsg}</td></tr>`;
            return;
        }
        tbody.innerHTML = rows.map(renderFn).join('');
    },

    // Populate select
    populateSelect(selectId, items, valueKey, labelKey, placeholder = 'Select...') {
        const sel = document.getElementById(selectId);
        if (!sel) return;
        sel.innerHTML = `<option value="">${placeholder}</option>` +
            items.map(i => `<option value="${i[valueKey]}">${typeof labelKey === 'function' ? labelKey(i) : i[labelKey]}</option>`).join('');
    },

    // Get form data as object
    getFormData(formId) {
        const form = document.getElementById(formId);
        if (!form) return {};
        const data = {};
        new FormData(form).forEach((val, key) => { data[key] = val; });
        return data;
    },

    // Debounce
    debounce(fn, delay = 300) {
        let timer;
        return (...args) => { clearTimeout(timer); timer = setTimeout(() => fn(...args), delay); };
    },

    // Status badge
    statusBadge(status) {
        const map = {
            active: 'badge-success', inactive: 'badge-danger',
            pass: 'badge-success', fail: 'badge-danger', pending: 'badge-warning',
            sent: 'badge-success', failed: 'badge-danger',
            approved: 'badge-success', rejected: 'badge-danger',
            P: 'badge-success', A: 'badge-danger', OD: 'badge-info'
        };
        return `<span class="badge ${map[status] || 'badge-muted'}">${status}</span>`;
    },

    // Attendance color
    attendanceColor(pct) {
        if (pct >= 75) return 'var(--success)';
        if (pct >= 60) return 'var(--warning)';
        return 'var(--danger)';
    }
};

window.utils = utils;
