/**
 * File Location Navigator tab logic.
 */

import { API, copyText } from './api.js';

export function initLocation() {
    const config = window.APP_CONFIG;
    if (!config) return;

    // Path type radio
    document.querySelectorAll('input[name="path-type"]').forEach((radio) => {
        radio.addEventListener('change', updateLocationFields);
    });

    // Populate CPE Internal block dropdown
    populateSelect('loc-cpe-block', config.cpe_internal_blocks);

    // CPE block change -> subcategory
    const blockSelect = document.getElementById('loc-cpe-block');
    if (blockSelect) {
        blockSelect.addEventListener('change', () => {
            const block = blockSelect.value;
            const subcats = config.cpe_internal_subcategories[block];
            const subcatGroup = document.getElementById('loc-cpe-subcat-group');
            if (subcats) {
                populateSelect('loc-cpe-subcat', subcats);
                subcatGroup.classList.remove('hidden');
            } else {
                subcatGroup.classList.add('hidden');
            }
        });
    }

    // Populate partner dropdown
    populateSelect('loc-partner', config.partners);

    // Phase change -> file type dropdown
    const phaseSelect = document.getElementById('loc-phase');
    if (phaseSelect) {
        phaseSelect.addEventListener('change', updatePhaseFields);
    }

    // Applies-to-all toggle
    const appliesToAll = document.getElementById('loc-applies-all');
    if (appliesToAll) {
        appliesToAll.addEventListener('change', () => {
            const occGroup = document.getElementById('loc-occurrence-group');
            occGroup.classList.toggle('hidden', appliesToAll.checked);
        });
    }

    // Show location button
    const showBtn = document.getElementById('loc-submit');
    if (showBtn) {
        showBtn.addEventListener('click', handleShowLocation);
    }

    updateLocationFields();
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

function getPathType() {
    const checked = document.querySelector('input[name="path-type"]:checked');
    return checked ? checked.value : 'internal';
}

function updateLocationFields() {
    const type = getPathType();
    document.getElementById('loc-internal-fields').classList.toggle('hidden', type !== 'internal');
    document.getElementById('loc-partner-fields').classList.toggle('hidden', type !== 'partner');
}

function updatePhaseFields() {
    const config = window.APP_CONFIG;
    const phase = document.getElementById('loc-phase').value;
    const defGroup = document.getElementById('loc-def-fields');
    const prodGroup = document.getElementById('loc-prod-fields');

    if (phase === 'Definition and Approvals') {
        defGroup.classList.remove('hidden');
        prodGroup.classList.add('hidden');
        populateSelect('loc-file-type-def', config.definition_approvals_blocks);
    } else if (phase === 'Production and Delivery') {
        defGroup.classList.add('hidden');
        prodGroup.classList.remove('hidden');
        populateSelect('loc-file-type-prod', config.production_delivery_blocks);
    } else {
        defGroup.classList.add('hidden');
        prodGroup.classList.add('hidden');
    }
}

async function handleShowLocation() {
    const resultEl = document.getElementById('loc-result');
    resultEl.style.display = 'none';

    const pathType = getPathType();
    const body = { is_partner_related: pathType === 'partner' };

    if (pathType === 'internal') {
        body.cpe_block = document.getElementById('loc-cpe-block').value;
        const subcatEl = document.getElementById('loc-cpe-subcat');
        body.cpe_subcat = subcatEl ? subcatEl.value : '';
    } else {
        body.partner = document.getElementById('loc-partner').value;
        body.phase = document.getElementById('loc-phase').value;

        if (body.phase === 'Definition and Approvals') {
            body.subject_area = document.getElementById('loc-subject-area')?.value || '';
            body.file_type = document.getElementById('loc-file-type-def').value;
        } else if (body.phase === 'Production and Delivery') {
            body.credential = document.getElementById('loc-credential')?.value || '';
            body.applies_to_all = document.getElementById('loc-applies-all')?.checked ?? true;
            body.occurrence = document.getElementById('loc-occurrence')?.value || '';
            body.file_type = document.getElementById('loc-file-type-prod').value;
        }
    }

    try {
        const res = await API.post('/api/file-location', body);
        const data = await res.json();

        resultEl.style.display = 'block';

        // Breadcrumb
        const breadcrumbEl = document.getElementById('loc-breadcrumb');
        breadcrumbEl.innerHTML = data.breadcrumb_path
            .split(' \u2192 ')
            .map((part) => `<span class="crumb">${part}</span>`)
            .join('<span class="arrow">\u2192</span>');

        // Folder path
        const folderEl = document.getElementById('loc-folder-path');
        folderEl.textContent = data.folder_path;

        // Copy button
        document.getElementById('loc-copy-path').onclick = function () {
            copyText(data.folder_path, this);
        };
    } catch (err) {
        console.error('Location error:', err);
    }
}
