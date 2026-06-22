function initCondicionais() {
    document.querySelectorAll('.question-card').forEach(card => {
        const condStr = card.dataset.condicao;
        if (!condStr || condStr === '{}') return;

        try {
            const cond = JSON.parse(condStr);
            if (cond.depends) {
                const parentInput = document.querySelector(`[data-codigo="${cond.depends.question}"]`);
                if (parentInput) {
                    const parentCard = parentInput.closest('.question-card');
                    if (parentCard) {
                        const parentRadios = parentCard.querySelectorAll('input[type="radio"]');
                        let parentValue = '';
                        parentRadios.forEach(r => { if (r.checked) parentValue = r.value; });
                        if (parentRadios.length === 0 && parentInput.tagName === 'SELECT') {
                            parentValue = parentInput.value;
                        }
                        card.style.display = (parentValue === cond.depends.value) ? 'block' : 'none';
                    }
                }
            }
        } catch (e) {
            console.warn('Erro ao processar condicional de', card.dataset.codigo, e);
        }
    });
}

function processarCondicional(input) {
    const card = input.closest('.question-card');
    if (!card) return;

    const codigo = card.dataset.codigo;
    const condStr = card.dataset.condicao;
    if (!condStr || condStr === '{}') return;

    let value = '';
    if (input.type === 'radio') {
        const checked = card.querySelector('input[type="radio"]:checked');
        value = checked ? checked.value : '';
    } else if (input.tagName === 'SELECT' || input.type === 'date') {
        value = input.value;
    }

    try {
        const cond = JSON.parse(condStr);

        // Handle depends - show/hide child questions
        if (cond.depends) {
            const dependentQuestions = document.querySelectorAll(`[data-depends="${codigo}"]`);
            dependentQuestions.forEach(dq => {
                dq.style.display = (value === cond.depends.value) ? 'block' : 'none';
            });
        }

        // Handle extra fields
        const extraDiv = document.getElementById('extra_' + codigo);
        if (cond.extra && extraDiv) {
            let shouldShow = false;
            const trigger = cond.extra.trigger;
            if (Array.isArray(trigger)) {
                shouldShow = trigger.includes(value);
            } else {
                shouldShow = value === trigger;
            }

            if (shouldShow) {
                renderExtraFields(extraDiv, cond.extra.fields, codigo, card.dataset.questionId);
            } else {
                extraDiv.innerHTML = '';
            }
        }

        // Handle sub-questions
        if (cond.extra && extraDiv) {
            const subQField = cond.extra.fields ? cond.extra.fields.find(f => f.type === 'subquestions') : null;
            if (subQField) {
                let shouldShow = false;
                const trigger = cond.extra.trigger;
                if (Array.isArray(trigger)) {
                    shouldShow = trigger.includes(value);
                } else {
                    shouldShow = value === trigger;
                }
                subQField.questions.forEach(qCodigo => {
                    const qCard = document.querySelector(`[data-codigo="${qCodigo}"]`);
                    if (qCard) {
                        qCard.style.display = shouldShow ? 'block' : 'none';
                    }
                });
            }
        }

        // Handle red flag
        if (cond.red_flag) {
            const alertDiv = card.querySelector('.red-flag-alert');
            if (alertDiv) {
                const trigger = cond.red_flag.trigger;
                let isTriggered = false;
                if (Array.isArray(trigger)) {
                    isTriggered = trigger.includes(value);
                } else {
                    isTriggered = value === trigger;
                }

                alertDiv.classList.toggle('d-none', !isTriggered);
                card.classList.toggle('has-red-flag', isTriggered);

                const rfCode = cond.red_flag.code;
                if (isTriggered) {
                    if (!redFlagsAtivas.find(rf => rf.code === rfCode)) {
                        redFlagsAtivas.push(cond.red_flag);
                    }
                } else {
                    redFlagsAtivas = redFlagsAtivas.filter(rf => rf.code !== rfCode);
                }
                verificarRedFlags();
            }
        }

        // Handle require_observacao
        if (cond.require_obs) {
            const triggers = Array.isArray(cond.require_obs) ? cond.require_obs : [cond.require_obs];
            const extraDiv2 = document.getElementById('extra_' + codigo);
            if (triggers.includes(value) && extraDiv2) {
                if (!extraDiv2.querySelector('.extra-observacao')) {
                    renderExtraFields(extraDiv2, [{ type: 'observacao', required: true }], codigo, card.dataset.questionId);
                }
                const obsField = extraDiv2.querySelector('.extra-observacao');
                if (obsField) obsField.required = true;
            } else if (extraDiv2 && !triggers.includes(value)) {
                const obsField = extraDiv2.querySelector('.extra-observacao');
                if (obsField) obsField.remove();
            }
        }
    } catch (e) {
        console.warn('Erro ao processar condicional de', codigo, e);
    }
}

function renderExtraFields(container, fields, codigo, questionId) {
    container.innerHTML = '';
    fields.forEach(field => {
        const wrapper = document.createElement('div');
        wrapper.className = 'extra-field mt-2';

        if (field.type === 'foto') {
            wrapper.innerHTML = `
                <label class="form-label small text-muted">Foto${field.required ? ' <span class="text-danger">*</span>' : ''}</label>
                <input type="file" accept="image/*" capture="environment"
                       class="form-control form-control-sm foto-input"
                       data-codigo="${codigo}" data-question-id="${questionId}"
                       ${field.required ? 'required' : ''}>
                <div class="foto-preview-container mt-1"></div>`;
        } else if (field.type === 'observacao') {
            wrapper.innerHTML = `
                <label class="form-label small text-muted">${field.label || 'Observação'}${field.required ? ' <span class="text-danger">*</span>' : ''}</label>
                <textarea class="form-control form-control-sm extra-observacao" rows="2"
                          ${field.required ? 'required' : ''}></textarea>`;
        } else if (field.type === 'date') {
            wrapper.innerHTML = `
                <label class="form-label small text-muted">${field.label || 'Data'}${field.required ? ' <span class="text-danger">*</span>' : ''}</label>
                <input type="date" class="form-control form-control-sm"
                       ${field.required ? 'required' : ''}>`;
        }

        container.appendChild(wrapper);

        if (field.type === 'foto') {
            const fotoInput = wrapper.querySelector('.foto-input');
            if (fotoInput) {
                fotoInput.addEventListener('change', function () {
                    const previewDiv = this.closest('.extra-field').querySelector('.foto-preview-container');
                    if (this.files && this.files[0]) {
                        const reader = new FileReader();
                        reader.onload = function (e) {
                            previewDiv.innerHTML = `<img src="${e.target.result}" class="foto-preview img-thumbnail">`;
                        };
                        reader.readAsDataURL(this.files[0]);
                        uploadFoto(this.files[0], this);
                    }
                });
            }
        }
    });
}

async function uploadFoto(file, inputElement) {
    const formData = new FormData();
    formData.append('foto', file);

    try {
        const resp = await fetch(`/audit/${SESSION_ID}/upload-foto`, {
            method: 'POST',
            body: formData
        });
        const result = await resp.json();
        if (resp.ok) {
            inputElement.dataset.uploadedPath = result.path;
        }
    } catch (e) {
        console.error('Erro ao fazer upload da foto:', e);
    }
}
