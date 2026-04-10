/* ============================================================
   Auth — JWT token management & login/logout
   ============================================================ */

const auth = {
    TOKEN_KEY: 'cms_token',
    USER_KEY: 'cms_user',

    getToken() { return localStorage.getItem(this.TOKEN_KEY); },
    getUser() {
        try { return JSON.parse(localStorage.getItem(this.USER_KEY)); }
        catch { return null; }
    },

    setSession(token, user) {
        localStorage.setItem(this.TOKEN_KEY, token);
        localStorage.setItem(this.USER_KEY, JSON.stringify(user));
    },

    clearSession() {
        localStorage.removeItem(this.TOKEN_KEY);
        localStorage.removeItem(this.USER_KEY);
    },

    isLoggedIn() { return !!this.getToken(); },

    requireAuth() {
        if (!this.isLoggedIn()) {
            window.location.href = '/login.html';
            return false;
        }
        return true;
    },

    requireGuest() {
        if (this.isLoggedIn()) {
            window.location.href = '/dashboard.html';
            return false;
        }
        return true;
    },

    hasRole(...roles) {
        const user = this.getUser();
        return user && roles.includes(user.role);
    },

    async logout() {
        try { await api.post('/auth/logout'); } catch { }
        this.clearSession();
        window.location.href = '/login.html';
    },

    getUserInitials() {
        const user = this.getUser();
        if (!user) return '?';
        return (user.username || 'U').slice(0, 2).toUpperCase();
    }
};

window.auth = auth;
