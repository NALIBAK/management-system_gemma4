/* ============================================================
   API Client — Fetch wrapper with JWT auth
   ============================================================ */

// Dynamically resolve backend URL based on current page hostname.
// This makes the app work from any device: localhost, LAN IP, or public tunnel URL.
// Backend always runs on port 5000; only the hostname changes.
const _apiHost = window.location.hostname;
const _apiProtocol = window.location.protocol;
const API_BASE = `${_apiProtocol}//${_apiHost}:5000/api`;

const api = {
  _getToken() {
    return localStorage.getItem('cms_token');
  },

  _headers(extra = {}) {
    const headers = { 'Content-Type': 'application/json', ...extra };
    const token = this._getToken();
    if (token) headers['Authorization'] = `Bearer ${token}`;
    return headers;
  },

  async _request(method, endpoint, body = null, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    const config = {
      method,
      headers: this._headers(options.headers || {}),
    };
    if (body) config.body = JSON.stringify(body);

    try {
      const res = await fetch(url, config);
      const data = await res.json();

      if (res.status === 401 && !endpoint.includes('/auth/login')) {
        // Token expired — redirect to login
        localStorage.removeItem('cms_token');
        localStorage.removeItem('cms_user');
        window.location.href = '/login.html';
        return;
      }

      return { ok: res.ok, status: res.status, data };
    } catch (err) {
      console.error('API Error Details:', err);
      return { ok: false, status: 0, data: { message: 'Network error. Is the backend running?' } };
    }
  },

  get(endpoint, params = {}) {
    const qs = new URLSearchParams(params).toString();
    return this._request('GET', qs ? `${endpoint}?${qs}` : endpoint);
  },

  post(endpoint, body) {
    return this._request('POST', endpoint, body);
  },

  put(endpoint, body) {
    return this._request('PUT', endpoint, body);
  },

  delete(endpoint) {
    return this._request('DELETE', endpoint);
  },

  patch(endpoint, body) {
    return this._request('PATCH', endpoint, body);
  }
};

window.api = api;
