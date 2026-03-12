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

document.addEventListener('DOMContentLoaded', () => {
    // Setup login form handler immediately (no async, no network calls)
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const passwordInput = document.getElementById('login-password');
            const errorEl = document.getElementById('login-error');

            try {
                const res = await fetch('/api/auth/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ password: passwordInput.value }),
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
            showLogin();
        });
    }

    // Startup auth check
    checkAuth();
});

async function checkAuth() {
    // Check if auth is required via the public health endpoint
    let authRequired = true;
    try {
        const res = await fetch('/api/health');
        const health = await res.json();
        authRequired = health.auth_required;
    } catch {
        // Assume auth required if health check fails
    }

    const token = API.getToken();

    if (!authRequired) {
        // No password set - get a token and go straight to app
        if (!token) {
            try {
                const res = await fetch('/api/auth/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ password: '' }),
                });
                if (res.ok) {
                    const data = await res.json();
                    API.setToken(data.token);
                }
            } catch {
                // Continue anyway
            }
        }
        showApp();
    } else if (token) {
        // Has token - verify it still works
        try {
            const res = await fetch('/api/config', {
                headers: { 'Authorization': `Bearer ${token}` },
            });
            if (res.ok) {
                showApp();
            } else {
                API.clearToken();
                showLogin();
            }
        } catch {
            showLogin();
        }
    } else {
        showLogin();
    }
}

function switchTab(tabId) {
    document.querySelectorAll('.tab-btn').forEach((b) => b.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach((p) => p.classList.remove('active'));

    const btn = document.querySelector(`.tab-btn[data-tab="${tabId}"]`);
    const panel = document.getElementById(`tab-${tabId}`);
    if (btn) btn.classList.add('active');
    if (panel) panel.classList.add('active');

    window.location.hash = tabId;
}

let appInitialized = false;

async function showApp() {
    document.getElementById('login-overlay').classList.add('hidden');
    document.getElementById('app-shell').classList.remove('hidden');

    if (appInitialized) return;
    appInitialized = true;

    // Load config using raw fetch to avoid any 401 handling side effects
    try {
        const token = API.getToken();
        const res = await fetch('/api/config', {
            headers: token ? { 'Authorization': `Bearer ${token}` } : {},
        });
        if (res.ok) {
            window.APP_CONFIG = await res.json();
        }
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
