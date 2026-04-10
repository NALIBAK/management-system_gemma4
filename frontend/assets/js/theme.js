/* ============================================================
   Theme — Dark / Light toggle
   ============================================================ */

const theme = {
    STORAGE_KEY: 'cms_theme',

    get() { return localStorage.getItem(this.STORAGE_KEY) || 'light'; },

    set(t) {
        localStorage.setItem(this.STORAGE_KEY, t);
        document.documentElement.setAttribute('data-theme', t);
        this._updateIcons(t);
    },

    toggle() { this.set(this.get() === 'dark' ? 'light' : 'dark'); },

    init() {
        const saved = this.get();
        document.documentElement.setAttribute('data-theme', saved);
        this._updateIcons(saved);
    },

    _updateIcons(t) {
        document.querySelectorAll('.theme-toggle').forEach(btn => {
            btn.textContent = t === 'dark' ? '☀️' : '🌙';
            btn.title = t === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode';
        });
    }
};

// Auto-init on load
document.addEventListener('DOMContentLoaded', () => theme.init());

window.theme = theme;
