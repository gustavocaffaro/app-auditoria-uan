let autoSaveInterval = null;
let redFlagsAtivas = [];

document.addEventListener('DOMContentLoaded', function () {
    iniciarAutoSave();
    verificarRedFlags();

    document.querySelectorAll('.question-input').forEach(input => {
        input.addEventListener('change', function () {
            const card = this.closest('.question-card');
            if (card) {
                card.classList.add('has-response');
            }
            if (typeof processarCondicional === 'function') {
                processarCondicional(this);
            }
            if (typeof atualizarScore === 'function') {
                atualizarScore();
            }
            if (typeof verificarRedFlag === 'function') {
                verificarRedFlag(this);
            }
        });
    });

    if (typeof initCondicionais === 'function') initCondicionais();
    if (typeof initFotos === 'function') initFotos();
    if (typeof atualizarScore === 'function') atualizarScore();

    document.querySelectorAll('[data-depends]').forEach(el => {
        const parentCodigo = el.dataset.depends;
        const parentInputs = document.querySelectorAll(`[data-codigo="${parentCodigo}"]`);
        parentInputs.forEach(p => {
            p.addEventListener('change', function () {
                const show = this.value === el.dataset.dependsValue || (
                    this.tagName === 'INPUT' && this.type === 'radio' && this.checked &&
                    this.value === el.dataset.dependsValue
                );
                el.style.display = show ? 'block' : 'none';
            });
        });
    });
});

async function logout() {
    try {
        const resp = await fetch('/auth/logout', { method: 'POST' });
        const data = await resp.json();
        window.location.href = data.redirect || '/auth/login';
    } catch (e) {
        window.location.href = '/auth/login';
    }
}

function mostrarToast(mensagem, tipo) {
    tipo = tipo || 'success';
    const container = document.getElementById('toastContainer');
    const icons = { success: 'bi-check-circle-fill', danger: 'bi-x-circle-fill', warning: 'bi-exclamation-circle-fill', info: 'bi-info-circle-fill' };
    const toast = document.createElement('div');
    toast.className = 'toast-custom toast align-items-center border-0 show';
    toast.role = 'alert';
    toast.innerHTML = `<div class="d-flex p-2">
        <i class="bi ${icons[tipo] || icons.info} text-${tipo} me-2 fs-5"></i>
        <div class="toast-body p-1">${mensagem}</div>
        <button type="button" class="btn-close me-1 m-auto" data-bs-dismiss="toast"></button>
    </div>`;
    container.appendChild(toast);
    setTimeout(() => { toast.remove(); }, 4000);
}

function getRespostas() {
    const respostas = [];
    document.querySelectorAll('.question-card:not([style*="display: none"])').forEach(card => {
        const qId = parseInt(card.dataset.questionId);
        const codigo = card.dataset.codigo;
        if (!qId) return;

        let resposta = '';
        const input = card.querySelector('.question-input');
        if (input) {
            if (input.type === 'radio') {
                const checked = card.querySelector('input[type="radio"]:checked');
                resposta = checked ? checked.value : '';
            } else if (input.tagName === 'SELECT' || input.type === 'date') {
                resposta = input.value;
            } else if (input.type === 'file') {
                return;
            }
        }

        const extraDiv = document.getElementById('extra_' + codigo);
        const observacao = extraDiv ? (extraDiv.querySelector('.extra-observacao') ? extraDiv.querySelector('.extra-observacao').value : '') : '';
        const fotoInput = extraDiv ? extraDiv.querySelector('.foto-input') : null;
        const fotoPath = fotoInput ? (fotoInput.dataset.uploadedPath || '') : '';

        const item = { question_id: qId, resposta: resposta };
        if (observacao) item.observacao = observacao;
        if (fotoPath) item.foto_path = fotoPath;
        respostas.push(item);
    });
    return respostas;
}

async function salvarRespostas() {
    const indicator = document.getElementById('saveIndicator');
    if (indicator) {
        indicator.className = 'badge bg-warning';
        indicator.textContent = 'Salvando...';
        indicator.classList.remove('d-none');
    }

    const data = { respostas: getRespostas() };

    try {
        const resp = await fetch(`/audit/${SESSION_ID}/save`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const result = await resp.json();
        if (resp.ok && indicator) {
            indicator.className = 'badge bg-success';
            indicator.textContent = 'Salvo \u2713';
            setTimeout(() => { indicator.classList.add('d-none'); }, 3000);
        }
    } catch (e) {
        if (indicator) {
            indicator.className = 'badge bg-danger';
            indicator.textContent = 'Erro';
        }
    }
}

function iniciarAutoSave() {
    if (autoSaveInterval) clearInterval(autoSaveInterval);
    autoSaveInterval = setInterval(salvarRespostas, 30000);
}

function navigateModule(direction) {
    const tabs = document.querySelectorAll('.module-tab');
    const active = document.querySelector('.module-tab.active');
    let idx = Array.from(tabs).indexOf(active);
    const next = idx + direction;
    if (next >= 0 && next < tabs.length) {
        tabs[next].click();
        tabs[next].scrollIntoView({ behavior: 'smooth', inline: 'center' });
    }
}

function verificarRedFlags() {
    const bar = document.getElementById('redFlagBar');
    if (redFlagsAtivas.length > 0) {
        bar.classList.remove('d-none');
        document.getElementById('redFlagText').textContent =
            `Falhas Graves (${redFlagsAtivas.length}) detectadas`;
    } else {
        bar.classList.add('d-none');
    }
}

async function finalizarAuditoria() {
    const hasRedFlags = redFlagsAtivas.length > 0;
    const warning = document.getElementById('redFlagsWarning');
    const list = document.getElementById('redFlagsList');

    if (hasRedFlags) {
        warning.classList.remove('d-none');
        list.innerHTML = redFlagsAtivas.map(rf =>
            `<div class="alert alert-danger py-1 mb-1"><strong>${rf.code}:</strong> ${rf.label}</div>`
        ).join('');
    } else {
        warning.classList.add('d-none');
        list.innerHTML = '';
    }

    document.getElementById('confirmText').textContent = hasRedFlags ?
        'Existem Red Flags ativas. Registre as observações antes de finalizar.' :
        'Tem certeza que deseja finalizar esta auditoria?';

    new bootstrap.Modal(document.getElementById('confirmModal')).show();
}

async function confirmarFinalizar() {
    const hasRedFlags = redFlagsAtivas.length > 0;
    const obs = document.getElementById('observacoesFinais').value.trim();

    if (hasRedFlags && !obs) {
        alert('É obrigatório registrar observações quando há Red Flags.');
        return;
    }

    if (hasRedFlags) {
        const confirmItems = redFlagsAtivas.map(rf => ({
            question_id: null, resposta: '', observacao: `[RED FLAG ${rf.code}] ${obs}`
        }));
        try {
            await fetch(`/audit/${SESSION_ID}/save`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ respostas: confirmItems })
            });
        } catch (e) {}
    }

    try {
        const resp = await fetch(`/audit/${SESSION_ID}/finalizar`, { method: 'POST' });
        const result = await resp.json();
        if (resp.ok) {
            bootstrap.Modal.getInstance(document.getElementById('confirmModal')).hide();
            window.location.href = result.redirect;
        } else {
            alert(result.error || 'Erro ao finalizar');
        }
    } catch (e) {
        alert('Erro de conexão ao finalizar');
    }
}
