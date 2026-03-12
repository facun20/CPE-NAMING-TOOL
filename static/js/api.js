/**
 * Shared API client for the CPE Naming Tool.
 * Handles auth token storage and request helpers.
 */

const API = {
    getToken() {
        return sessionStorage.getItem('cpe_token');
    },

    setToken(token) {
        sessionStorage.setItem('cpe_token', token);
    },

    clearToken() {
        sessionStorage.removeItem('cpe_token');
    },

    _headers() {
        const headers = { 'Content-Type': 'application/json' };
        const token = this.getToken();
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        return headers;
    },

    async get(path) {
        const res = await fetch(path, { headers: this._headers() });
        if (res.status === 401) {
            this.clearToken();
            window.location.reload();
            throw new Error('Unauthorized');
        }
        return res.json();
    },

    async post(path, body) {
        const res = await fetch(path, {
            method: 'POST',
            headers: this._headers(),
            body: JSON.stringify(body),
        });
        if (res.status === 401) {
            this.clearToken();
            window.location.reload();
            throw new Error('Unauthorized');
        }
        return res;
    },

    async upload(path, formData) {
        const headers = {};
        const token = this.getToken();
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        const res = await fetch(path, {
            method: 'POST',
            headers,
            body: formData,
        });
        if (res.status === 401) {
            this.clearToken();
            window.location.reload();
            throw new Error('Unauthorized');
        }
        return res;
    },

    async downloadPost(path, body) {
        const res = await fetch(path, {
            method: 'POST',
            headers: this._headers(),
            body: JSON.stringify(body),
        });
        if (res.status === 401) {
            this.clearToken();
            window.location.reload();
            throw new Error('Unauthorized');
        }
        return res;
    },
};

// ─── Toast notification ─────────────────────────────────────────

function showToast(message, duration = 2000) {
    const toast = document.getElementById('toast');
    if (!toast) return;
    toast.textContent = message;
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), duration);
}

// ─── Copy to clipboard ──────────────────────────────────────────

async function copyText(text, btn) {
    try {
        await navigator.clipboard.writeText(text);
        if (btn) {
            const orig = btn.textContent;
            btn.textContent = 'Copied!';
            btn.classList.add('copied');
            setTimeout(() => {
                btn.textContent = orig;
                btn.classList.remove('copied');
            }, 1500);
        }
        showToast('Copied to clipboard');
    } catch {
        showToast('Failed to copy');
    }
}

// ─── Format file size ───────────────────────────────────────────

function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

export { API, showToast, copyText, formatFileSize };
