const respostasPositivas = [
    'Sim', 'Íntegro', 'Bom estado', 'Completo', 'Limpo e funcionando',
    'Sim, em todos', 'Sim, todos válidos', 'Cabelos totalmente protegidos',
    'Sapatos fechados', 'Adequada – natural', 'Adequada – exaustores',
    'Sim, com nome e validade', 'Sim, todas em dia',
    'Em prateleiras/estrados afastados do piso e das paredes',
    'Sob refrigeração na geladeira', 'Imersão em solução clorada + enxágue',
    'Álcool 70%', 'Lavagem com água e sabão', 'Rede pública', 'Poço artesiano',
    'Água mineral', 'Filtro de água', 'Fervura da água'
];

function atualizarScore() {
    let totalPeso = 0;
    let somaPontos = 0;
    let totalRespondidas = 0;
    let totalVisiveis = 0;

    document.querySelectorAll('.question-card:not([style*="display: none"])').forEach(card => {
        const peso = parseInt(card.dataset.peso);
        if (peso === 0) return;

        totalVisiveis++;

        const codigo = card.dataset.codigo;
        const input = card.querySelector('.question-input');

        let resposta = '';
        if (input) {
            if (input.type === 'radio') {
                const checked = card.querySelector('input[type="radio"]:checked');
                resposta = checked ? checked.value : '';
            } else if (input.tagName === 'SELECT') {
                resposta = input.value;
            }
        }

        if (resposta) {
            totalRespondidas++;
            totalPeso += peso;

            if (resposta === '— Não se aplica') {
                return;
            }

            if (respostasPositivas.includes(resposta)) {
                somaPontos += peso;
            }
        }
    });

    const pct = totalPeso > 0 ? Math.round((somaPontos / totalPeso) * 100) : 0;
    const progresso = totalVisiveis > 0 ? Math.round((totalRespondidas / totalVisiveis) * 100) : 0;

    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');

    if (progressBar) progressBar.style.width = progresso + '%';
    if (progressText) progressText.textContent = progresso + '%';

    // Update per-module counts
    document.querySelectorAll('.q-count').forEach(badge => {
        const modId = parseInt(badge.dataset.module);
        const qCards = document.querySelectorAll(`.question-card[data-module="${modId}"]:not([style*="display: none"])`);
        const answered = document.querySelectorAll(`.question-card[data-module="${modId}"]:not([style*="display: none"]) .question-input`);

        let answeredCount = 0;
        answered.forEach(input => {
            if (input.type === 'radio') {
                const card = input.closest('.question-card');
                if (card && card.querySelector('input[type="radio"]:checked')) answeredCount++;
            } else if (input.tagName === 'SELECT') {
                if (input.value) answeredCount++;
            }
        });

        badge.textContent = `${answeredCount}/${qCards.length}`;
    });
}

// Auto-update on input changes
document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.question-input').forEach(input => {
        input.addEventListener('change', atualizarScore);
    });
});
