/**
 * AI File Analyzer tab logic.
 */

import { API, copyText, formatFileSize, showToast } from './api.js';

let selectedFiles = [];
let piiResults = {};
let analysisResults = [];

export function initAnalyzer() {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');

    if (!dropZone || !fileInput) return;

    // Click to select files
    dropZone.addEventListener('click', () => fileInput.click());

    // Drag events
    dropZone.addEventListener('dragenter', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });
    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        addFiles(e.dataTransfer.files);
    });

    // File input change
    fileInput.addEventListener('change', () => {
        addFiles(fileInput.files);
        fileInput.value = '';
    });

    // Analyze button
    document.getElementById('analyze-btn').addEventListener('click', handleAnalyze);

    // Export CSV button
    document.getElementById('export-csv-btn').addEventListener('click', handleExportCsv);

    // Clear button
    document.getElementById('clear-analyzer-btn').addEventListener('click', () => {
        selectedFiles = [];
        piiResults = {};
        analysisResults = [];
        renderFileList();
        document.getElementById('analyzer-results').innerHTML = '';
        document.getElementById('analyzer-results-section').style.display = 'none';
        document.getElementById('pii-warning-banner').style.display = 'none';
    });
}

function addFiles(fileList) {
    const config = window.APP_CONFIG;
    const supported = config ? config.supported_file_types : [];

    for (const file of fileList) {
        const ext = file.name.split('.').pop().toLowerCase();
        if (supported.length && !supported.includes(ext)) {
            showToast(`Unsupported file type: .${ext}`);
            continue;
        }
        // Avoid duplicates
        if (!selectedFiles.some((f) => f.name === file.name && f.size === file.size)) {
            selectedFiles.push(file);
            scanPII(file);
        }
    }
    renderFileList();
}

async function scanPII(file) {
    try {
        const formData = new FormData();
        formData.append('file', file);
        const res = await API.upload('/api/scan-pii', formData);
        const data = await res.json();
        piiResults[file.name] = data;
        renderFileList();
        updatePIIBanner();
    } catch {
        // Silently fail PII scan
    }
}

function renderFileList() {
    const list = document.getElementById('file-list');
    const section = document.getElementById('file-list-section');

    if (!selectedFiles.length) {
        section.style.display = 'none';
        return;
    }

    section.style.display = 'block';
    list.innerHTML = selectedFiles
        .map((file, idx) => {
            const pii = piiResults[file.name];
            let piiBadge = '';
            if (pii) {
                const count = pii.pii_items.length;
                if (count > 0) {
                    piiBadge = `<span class="pii-badge warning">${count} PII found</span>`;
                } else {
                    piiBadge = `<span class="pii-badge clean">No PII</span>`;
                }
            }
            return `
                <li class="file-item">
                    <div>
                        <span class="file-name">${file.name}</span>
                        <span class="file-size">${formatFileSize(file.size)}</span>
                        ${piiBadge}
                    </div>
                    <button class="remove-btn" data-idx="${idx}" title="Remove">&times;</button>
                </li>`;
        })
        .join('');

    // Remove buttons
    list.querySelectorAll('.remove-btn').forEach((btn) => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const idx = parseInt(btn.dataset.idx);
            const removed = selectedFiles.splice(idx, 1);
            if (removed[0]) delete piiResults[removed[0].name];
            renderFileList();
            updatePIIBanner();
        });
    });
}

function updatePIIBanner() {
    const banner = document.getElementById('pii-warning-banner');
    let totalPII = 0;
    const typeSummary = {};

    for (const data of Object.values(piiResults)) {
        for (const item of data.pii_items || []) {
            totalPII++;
            typeSummary[item.type] = (typeSummary[item.type] || 0) + 1;
        }
    }

    if (totalPII > 0) {
        const config = window.APP_CONFIG;
        const labels = config ? config.pii_entity_labels : {};
        const parts = Object.entries(typeSummary)
            .map(([type, count]) => `${labels[type] || type}: ${count}`)
            .join(', ');
        banner.innerHTML = `<strong>PII Detected:</strong> ${totalPII} item(s) found and will be scrubbed before AI analysis. (${parts})`;
        banner.style.display = 'block';
    } else {
        banner.style.display = 'none';
    }
}

async function handleAnalyze() {
    if (!selectedFiles.length) {
        showToast('Please select files first');
        return;
    }

    const provider = document.getElementById('ai-provider').value;
    const apiKey = document.getElementById('ai-api-key').value.trim();

    if (provider !== 'offline' && !apiKey) {
        const envHint = provider === 'gemini' ? 'OpenRouter' : 'Claude';
        showToast(`Please enter your ${envHint} API key`);
        return;
    }

    const progressContainer = document.getElementById('progress-container');
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');
    const analyzeBtn = document.getElementById('analyze-btn');

    progressContainer.style.display = 'block';
    analyzeBtn.disabled = true;
    analysisResults = [];

    for (let i = 0; i < selectedFiles.length; i++) {
        const file = selectedFiles[i];
        progressText.textContent = `Analyzing ${file.name}... (${i + 1}/${selectedFiles.length})`;
        progressBar.style.width = `${((i + 1) / selectedFiles.length) * 100}%`;

        try {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('provider', provider);
            if (apiKey) formData.append('api_key', apiKey);

            const res = await API.upload('/api/analyze', formData);
            const result = await res.json();
            analysisResults.push(result);
        } catch (err) {
            analysisResults.push({
                file: file.name,
                success: false,
                error: err.message,
            });
        }
    }

    progressText.textContent = 'Analysis complete!';
    analyzeBtn.disabled = false;
    setTimeout(() => {
        progressContainer.style.display = 'none';
    }, 2000);

    renderResults();
}

function renderResults() {
    const container = document.getElementById('analyzer-results');
    const section = document.getElementById('analyzer-results-section');

    if (!analysisResults.length) {
        section.style.display = 'none';
        return;
    }

    section.style.display = 'block';
    container.innerHTML = analysisResults
        .map((result, idx) => {
            if (!result.success) {
                return `
                    <div class="result-card">
                        <div class="result-label">Original: ${result.file}</div>
                        <div class="alert alert-error mb-0">${result.error || 'Analysis failed'}</div>
                    </div>`;
            }

            const analysis = result.analysis;
            const fields = analysis.extractedFields || {};
            const conf = result.confidence_level || { level: 'medium', message: '' };

            const fieldRows = Object.entries(fields)
                .filter(([, v]) => v)
                .map(([k, v]) => `<div><strong>${k}:</strong> ${v}</div>`)
                .join('');

            const piiCount = (result.pii_detected || []).length;
            const piiBadge = piiCount > 0
                ? `<span class="pii-badge warning">${piiCount} PII scrubbed</span>`
                : '';

            const cachedBadge = result.cached
                ? '<span class="pii-badge clean">Cached</span>'
                : '';

            return `
                <div class="result-card">
                    <div class="result-label">Original: ${result.file} ${piiBadge} ${cachedBadge}</div>
                    <div class="result-filename" id="suggested-${idx}">${analysis.suggestedName}</div>
                    <div class="mb-8">
                        <span class="confidence-badge ${conf.level}">${conf.level} confidence</span>
                        <span class="length-badge info">${analysis.formatUsed} format</span>
                    </div>
                    <button class="copy-btn" onclick="window._copyResult(${idx})">Copy filename</button>

                    <div class="expandable">
                        <div class="expandable-header" onclick="this.nextElementSibling.classList.toggle('open')">
                            &#9654; Extracted Fields
                        </div>
                        <div class="expandable-content">${fieldRows || 'No fields extracted'}</div>
                    </div>
                    <div class="expandable">
                        <div class="expandable-header" onclick="this.nextElementSibling.classList.toggle('open')">
                            &#9654; AI Reasoning
                        </div>
                        <div class="expandable-content">${analysis.reasoning || 'No reasoning provided'}</div>
                    </div>
                </div>`;
        })
        .join('');
}

// Global copy helper for inline onclick
window._copyResult = function (idx) {
    const el = document.getElementById(`suggested-${idx}`);
    if (el) {
        copyText(el.textContent, el.closest('.result-card').querySelector('.copy-btn'));
    }
};

async function handleExportCsv() {
    if (!analysisResults.length) {
        showToast('No results to export');
        return;
    }

    try {
        const res = await API.downloadPost('/api/export-csv', analysisResults);
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'cpe_analysis_results.csv';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        showToast('CSV exported');
    } catch {
        showToast('Export failed');
    }
}
