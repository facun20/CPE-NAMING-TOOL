/**
 * Manual Filename Generator tab logic.
 */

import { API, copyText } from './api.js';

export function initGenerator() {
    const config = window.APP_CONFIG;
    if (!config) return;

    // Populate dropdowns
    populateSelect('gen-revision', config.revision_statuses);
    populateSelect('gen-extension', config.file_extensions);
    populateSelect('gen-document-form', config.document_forms);
    populateSelect('gen-faculty-school', config.partners);

    // Set default date to today
    const dateInput = document.getElementById('gen-date');
    if (dateInput) {
        dateInput.value = new Date().toISOString().split('T')[0];
    }

    // Format type radio change
    document.querySelectorAll('input[name="format-type"]').forEach((radio) => {
        radio.addEventListener('change', () => updateFieldVisibility());
    });
    updateFieldVisibility();

    // Help dropdown
    const helpSelect = document.getElementById('gen-help-select');
    if (helpSelect) {
        helpSelect.addEventListener('change', () => {
            const key = helpSelect.value;
            const helpContent = document.getElementById('gen-help-content');
            if (key && config.help_content[key]) {
                const h = config.help_content[key];
                helpContent.innerHTML = `<h4>${h.title}</h4><p>${h.content}</p>`;
                helpContent.style.display = 'block';
            } else {
                helpContent.style.display = 'none';
            }
        });
    }

    // Generate button
    const genBtn = document.getElementById('gen-submit');
    if (genBtn) {
        genBtn.addEventListener('click', handleGenerate);
    }
}

function populateSelect(id, options) {
    const select = document.getElementById(id);
    if (!select) return;
    select.innerHTML = '';
    for (const [value, label] of Object.entries(options)) {
        const opt = document.createElement('option');
        opt.value = value;
        opt.textContent = label;
        select.appendChild(opt);
    }
}

function getFormatType() {
    const checked = document.querySelector('input[name="format-type"]:checked');
    return checked ? checked.value : 'basic';
}

function updateFieldVisibility() {
    const format = getFormatType();
    const advancedFields = document.getElementById('gen-advanced-fields');
    const courseFields = document.getElementById('gen-course-fields');

    if (advancedFields) {
        advancedFields.classList.toggle('hidden', format === 'basic');
    }
    if (courseFields) {
        courseFields.classList.toggle('hidden', format !== 'course');
    }
}

async function handleGenerate() {
    const format = getFormatType();
    const errorEl = document.getElementById('gen-errors');
    const resultEl = document.getElementById('gen-result');
    errorEl.innerHTML = '';
    errorEl.style.display = 'none';
    resultEl.style.display = 'none';

    const body = {
        format_type: format,
        subject: document.getElementById('gen-subject').value.trim(),
        date: document.getElementById('gen-date').value,
        revision: document.getElementById('gen-revision').value,
        extension: document.getElementById('gen-extension').value,
    };

    if (format === 'advanced' || format === 'course') {
        body.project_code = document.getElementById('gen-project-code').value.trim();
        body.document_form = document.getElementById('gen-document-form').value;
    }

    if (format === 'course') {
        body.faculty_school = document.getElementById('gen-faculty-school').value;
        body.course_code = document.getElementById('gen-course-code').value.trim();
        body.term = document.getElementById('gen-term').value.trim();
    }

    try {
        const res = await API.post('/api/generate-filename', body);
        const data = await res.json();

        if (res.status === 422 && data.errors) {
            errorEl.innerHTML = data.errors
                .map((e) => `<div class="alert alert-${e.level}">${e.message}</div>`)
                .join('');
            errorEl.style.display = 'block';
            return;
        }

        if (!res.ok) {
            errorEl.innerHTML = '<div class="alert alert-error">An error occurred.</div>';
            errorEl.style.display = 'block';
            return;
        }

        // Show result
        resultEl.style.display = 'block';
        document.getElementById('gen-standard-name').textContent = data.standard_name;
        document.getElementById('gen-sharepoint-name').textContent = data.sharepoint_name;

        // Length badge
        const badge = document.getElementById('gen-length-badge');
        badge.textContent = data.length_check.message;
        badge.className = `length-badge ${data.length_check.level}`;

        // Copy buttons
        document.getElementById('gen-copy-standard').onclick = function () {
            copyText(data.standard_name, this);
        };
        document.getElementById('gen-copy-sharepoint').onclick = function () {
            copyText(data.sharepoint_name, this);
        };
    } catch (err) {
        errorEl.innerHTML = `<div class="alert alert-error">Error: ${err.message}</div>`;
        errorEl.style.display = 'block';
    }
}
