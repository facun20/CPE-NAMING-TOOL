/**
 * Main application controller for the CPE Naming Tool.
 * Handles auth, tab routing, and config loading.
 */

import { API } from './api.js';
import { initGenerator } from './generator.js';
import { initAnalyzer } from './analyzer.js';
import { initLocation } from './location.js';

// Global config store
window.APP_CONFIG = null;

document.addEventListener('DOMContentLoaded', async () => {
    // Check auth
    const token = API.getToken();
    if (token) {
        try {
            await API.get('/api/config');
            showApp();
        } catch {
            showLogin();
        }
    } else {
        // Try without auth (password might not be set)
        try {
            const config = await API.get('/api/config');
            if (!config.auth_required) {
                // No auth needed, get a token anyway
                const res = await API.post('/api/auth/login', { password: '' });
                const data = await res.json();
                API.setToken(data.token);
                showApp();
            } else {
                showLogin();
            }
        } catch {
            showLogin();
        }
    }

    // Login form handler
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const passwordInput = document.getElementById('login-password');
            const errorEl = document.getElementById('login-error');

            try {
                const res = await API.post('/api/auth/login', {
                    password: passwordInput.value,
                });
                if (res.ok) {
                    const data = await res.json();
                    API.setToken(data.token);
                    errorEl.style.display = 'none';
                    showApp();
                } else {
                    errorEl.textContent = 'Invalid password. Please try again.';
                    errorEl.style.display = 'block';
                    passwordInput.value = '';
                    passwordInput.focus();
                }
            } catch {
                errorEl.textContent = 'Connection error. Please try again.';
                errorEl.style.display = 'block';
            }
        });
    }

    // Tab navigation
    document.querySelectorAll('.tab-btn').forEach((btn) => {
        btn.addEventListener('click', () => {
            const tabId = btn.dataset.tab;
            switchTab(tabId);
        });
    });

    // Logout
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => {
            API.clearToken();
            window.location.reload();
        });
    }

    // Handle hash-based routing
    const hash = window.location.hash.slice(1);
    if (['generator', 'analyzer', 'location'].includes(hash)) {
        switchTab(hash);
    }
});

function switchTab(tabId) {
    document.querySelectorAll('.tab-btn').forEach((b) => b.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach((p) => p.classList.remove('active'));

    const btn = document.querySelector(`.tab-btn[data-tab="${tabId}"]`);
    const panel = document.getElementById(`tab-${tabId}`);
    if (btn) btn.classList.add('active');
    if (panel) panel.classList.add('active');

    window.location.hash = tabId;
}

async function showApp() {
    document.getElementById('login-overlay').classList.add('hidden');
    document.getElementById('app-shell').classList.remove('hidden');

    // Load config
    try {
        window.APP_CONFIG = await API.get('/api/config');
    } catch {
        console.error('Failed to load config');
    }

    // Initialize tab modules
    initGenerator();
    initAnalyzer();
    initLocation();
}

function showLogin() {
    document.getElementById('login-overlay').classList.remove('hidden');
    document.getElementById('app-shell').classList.add('hidden');
}
