let presetsData = [];
let currentOutput = null;
let currentOutputTab = 'visual';
let currentInputTab = 'json';

// Initialize on page load
document.addEventListener('DOMContentLoaded', async () => {
    await fetchPresets();
    if (presetsData.length > 0) {
        loadPreset(0);
    }
});

async function fetchPresets() {
    try {
        const resp = await fetch('/api/presets');
        if (resp.ok) {
            presetsData = await resp.json();
        }
    } catch (e) {
        console.error('Ошибка загрузки пресетов:', e);
    }
}

function loadPreset(index) {
    if (!presetsData[index]) return;
    const item = presetsData[index];
    
    // Fill JSON editor
    const formatted = JSON.stringify(item, null, 2);
    document.getElementById('raw-json-input').value = formatted;

    // Fill Form inputs
    document.getElementById('form-name').value = item.name || '';
    document.getElementById('form-manufacturer').value = item.manufacturer || '';
    document.getElementById('form-specs').value = JSON.stringify(item.specs || {}, null, 2);
    document.getElementById('form-desc').value = item.description || '';

    showToast(`Загружен пресет: ${item.name.substring(0, 35)}...`);
}

function switchInputTab(tab) {
    currentInputTab = tab;
    const jsonBtn = document.getElementById('tab-btn-json');
    const formBtn = document.getElementById('tab-btn-form');
    const jsonContainer = document.getElementById('input-json-container');
    const formContainer = document.getElementById('input-form-container');

    if (tab === 'json') {
        jsonBtn.classList.add('active', 'text-blue-600');
        jsonBtn.classList.remove('text-slate-500');
        formBtn.classList.remove('active', 'text-blue-600');
        formBtn.classList.add('text-slate-500');
        jsonContainer.classList.remove('hidden');
        formContainer.classList.add('hidden');
    } else {
        formBtn.classList.add('active', 'text-blue-600');
        formBtn.classList.remove('text-slate-500');
        jsonBtn.classList.remove('active', 'text-blue-600');
        jsonBtn.classList.add('text-slate-500');
        formContainer.classList.remove('hidden');
        jsonContainer.classList.add('hidden');
        syncJsonToForm();
    }
}

function syncJsonToForm() {
    try {
        const parsed = JSON.parse(document.getElementById('raw-json-input').value);
        document.getElementById('form-name').value = parsed.name || '';
        document.getElementById('form-manufacturer').value = parsed.manufacturer || '';
        document.getElementById('form-specs').value = JSON.stringify(parsed.specs || {}, null, 2);
        document.getElementById('form-desc').value = parsed.description || '';
    } catch (e) {}
}

function syncFormToJson() {
    let specs = {};
    try {
        specs = JSON.parse(document.getElementById('form-specs').value || '{}');
    } catch (e) {
        specs = { "описание": document.getElementById('form-specs').value };
    }

    const item = {
        name: document.getElementById('form-name').value.trim(),
        manufacturer: document.getElementById('form-manufacturer').value.trim(),
        specs: specs,
        description: document.getElementById('form-desc').value.trim()
    };
    document.getElementById('raw-json-input').value = JSON.stringify(item, null, 2);
    return item;
}

function formatInputJson() {
    try {
        const parsed = JSON.parse(document.getElementById('raw-json-input').value);
        document.getElementById('raw-json-input').value = JSON.stringify(parsed, null, 2);
        showToast('JSON успешно отформатирован');
    } catch (e) {
        alert('Некорректный JSON синтаксис: ' + e.message);
    }
}

function switchOutputTab(tab) {
    currentOutputTab = tab;
    ['visual', 'markdown', 'text', 'json'].forEach(t => {
        const btn = document.getElementById(`out-tab-${t}`);
        const pane = document.getElementById(`pane-${t}`);
        if (t === tab) {
            btn.classList.add('active', 'text-blue-600');
            btn.classList.remove('text-slate-500');
            pane.classList.remove('hidden');
        } else {
            btn.classList.remove('active', 'text-blue-600');
            btn.classList.add('text-slate-500');
            pane.classList.add('hidden');
        }
    });

    const copyBtnLabel = document.getElementById('copy-btn-label');
    if (tab === 'visual') copyBtnLabel.textContent = 'Скопировать Markdown';
    else if (tab === 'markdown') copyBtnLabel.textContent = 'Скопировать MD';
    else if (tab === 'text') copyBtnLabel.textContent = 'Скопировать текст';
    else if (tab === 'json') copyBtnLabel.textContent = 'Скопировать JSON';
}

async function handleGenerate() {
    let payload = {};
    if (currentInputTab === 'form') {
        payload = syncFormToJson();
    } else {
        try {
            payload = JSON.parse(document.getElementById('raw-json-input').value);
        } catch (e) {
            alert('Пожалуйста, исправьте синтаксис входного JSON перед отправкой.');
            return;
        }
    }

    if (!payload.name) {
        alert('Поле "name" (название прибора) обязательно для заполнения!');
        return;
    }

    const provider = document.getElementById('provider-select').value;
    const btn = document.getElementById('btn-generate');
    const btnIcon = document.getElementById('btn-icon');
    const btnText = document.getElementById('btn-text');

    btn.disabled = true;
    btn.classList.add('opacity-75', 'cursor-not-allowed');
    btnIcon.className = 'fa-solid fa-spinner fa-spin';
    btnText.textContent = 'Генерация карточки...';

    try {
        const resp = await fetch(`/api/generate?provider=${provider}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!resp.ok) {
            const errData = await resp.json();
            throw new Error(errData.detail || 'Ошибка генерации');
        }

        const data = await resp.json();
        currentOutput = data;
        renderOutput(data);
        showToast('Черновик карточки успешно сформирован!');

    } catch (err) {
        alert('Ошибка: ' + err.message);
    } finally {
        btn.disabled = false;
        btn.classList.remove('opacity-75', 'cursor-not-allowed');
        btnIcon.className = 'fa-solid fa-wand-magic-sparkles';
        btnText.textContent = 'Сформировать карточку товара';
    }
}

function renderOutput(data) {
    // Hide placeholder, show content
    document.getElementById('placeholder-empty').classList.add('hidden');
    document.getElementById('card-content').classList.remove('hidden');

    // Update metrics bar
    const titleLen = data.seo_title_length || data.seo_title.length;
    const descLen = data.seo_description_length || data.seo_description.length;

    const titleMetric = document.getElementById('metric-title-len');
    titleMetric.textContent = `${titleLen} / 70 симв.`;
    if (titleLen <= 70) {
        titleMetric.className = 'font-bold px-2 py-0.5 rounded bg-emerald-100 text-emerald-800';
    } else {
        titleMetric.className = 'font-bold px-2 py-0.5 rounded bg-rose-100 text-rose-800';
    }

    const descMetric = document.getElementById('metric-desc-len');
    descMetric.textContent = `${descLen} / 800–1200 симв.`;
    if (descLen >= 800 && descLen <= 1200) {
        descMetric.className = 'font-bold px-2 py-0.5 rounded bg-emerald-100 text-emerald-800';
    } else {
        descMetric.className = 'font-bold px-2 py-0.5 rounded bg-amber-100 text-amber-800';
    }

    const guardMetric = document.getElementById('metric-guard-status');
    if (data.is_hallucination_free) {
        guardMetric.innerHTML = '<i class="fa-solid fa-check-double mr-1 text-emerald-600"></i> Анти-галлюцинация: OK';
        guardMetric.className = 'inline-flex items-center px-2 py-0.5 rounded font-medium bg-emerald-50 text-emerald-700';
    } else {
        guardMetric.innerHTML = '<i class="fa-solid fa-triangle-exclamation mr-1 text-amber-600"></i> Были скорректированы ТТХ';
        guardMetric.className = 'inline-flex items-center px-2 py-0.5 rounded font-medium bg-amber-50 text-amber-700';
    }

    // Warnings alert box
    const alertBox = document.getElementById('missing-alert-box');
    const alertList = document.getElementById('missing-alert-list');
    alertList.innerHTML = '';
    if (data.missing_fields && data.missing_fields.length > 0) {
        alertBox.classList.remove('hidden');
        data.missing_fields.forEach(m => {
            const li = document.createElement('li');
            li.innerHTML = `<strong>${m.field_name}:</strong> ${m.message}`;
            alertList.appendChild(li);
        });
    } else {
        alertBox.classList.add('hidden');
    }

    // Visual card fields
    document.getElementById('card-seo-title').textContent = data.seo_title;
    document.getElementById('card-seo-desc').textContent = data.seo_description;

    // Specs table
    const specsTable = document.getElementById('card-specs-table');
    specsTable.innerHTML = '';
    Object.entries(data.key_specs || {}).forEach(([k, v]) => {
        const tr = document.createElement('tr');
        tr.className = 'hover:bg-slate-50 transition';
        tr.innerHTML = `
            <td class="py-1.5 px-3 font-medium text-slate-600 bg-slate-50/50 w-2/5 border-r border-slate-100">${k}</td>
            <td class="py-1.5 px-3 text-slate-800 font-mono text-[11px]">${v}</td>
        `;
        specsTable.appendChild(tr);
    });

    // Search queries
    const queriesContainer = document.getElementById('card-queries');
    queriesContainer.innerHTML = '';
    (data.search_queries || []).forEach(q => {
        const span = document.createElement('span');
        span.className = 'inline-flex items-center px-2 py-1 rounded bg-slate-100 text-slate-700 text-[11px] font-mono border border-slate-200';
        span.innerHTML = `<i class="fa-solid fa-magnifying-glass text-slate-400 mr-1 text-[9px]"></i> ${q}`;
        queriesContainer.appendChild(span);
    });

    // Commercial block
    document.getElementById('card-commercial-audience').textContent = data.commercial_block?.target_audience || 'Данных нет';
    document.getElementById('card-commercial-problems').textContent = data.commercial_block?.solved_problems || 'Данных нет';

    // Raw tab values
    document.getElementById('raw-markdown-text').value = data.markdown || '';
    document.getElementById('raw-plain-text').value = data.plain_text || '';
    document.getElementById('raw-json-output').value = JSON.stringify(data, null, 2);
}

function copyCurrentOutput() {
    if (!currentOutput) {
        alert('Сначала сформируйте карточку товара');
        return;
    }

    let textToCopy = '';
    if (currentOutputTab === 'visual' || currentOutputTab === 'markdown') {
        textToCopy = currentOutput.markdown;
    } else if (currentOutputTab === 'text') {
        textToCopy = currentOutput.plain_text;
    } else if (currentOutputTab === 'json') {
        textToCopy = JSON.stringify(currentOutput, null, 2);
    }

    navigator.clipboard.writeText(textToCopy).then(() => {
        showToast('Текст скопирован в буфер обмена!');
    }).catch(err => {
        alert('Не удалось скопировать: ' + err);
    });
}

function showToast(msg) {
    const toast = document.getElementById('toast');
    const toastMsg = document.getElementById('toast-message');
    toastMsg.textContent = msg;
    toast.classList.remove('translate-y-20', 'opacity-0');
    toast.classList.add('translate-y-0', 'opacity-100');

    setTimeout(() => {
        toast.classList.remove('translate-y-0', 'opacity-100');
        toast.classList.add('translate-y-20', 'opacity-0');
    }, 2800);
}
