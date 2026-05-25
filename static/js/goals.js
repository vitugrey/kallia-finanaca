document.addEventListener("DOMContentLoaded", function() {
    // ==========================================================================
    // PARTE 1: CALCULADORA DE METAS (JUROS COMPOSTOS INTERATIVA)
    // ==========================================================================
    const patrimonyInput = document.getElementById('calc-patrimony');
    const contributionInput = document.getElementById('calc-contribution');
    const rateSlider = document.getElementById('calc-rate');

    const labelPatrimony = document.getElementById('label-patrimony');
    const labelContribution = document.getElementById('label-contribution');
    const labelRate = document.getElementById('label-rate');

    const time50k = document.getElementById('time-50k');
    const time100k = document.getElementById('time-100k');
    const time1m = document.getElementById('time-1m');

    const card50k = document.getElementById('card-50k');
    const card100k = document.getElementById('card-100k');
    const card1m = document.getElementById('card-1m');

    const proj1y = document.getElementById('proj-1y');
    const proj5y = document.getElementById('proj-5y');
    const proj10y = document.getElementById('proj-10y');

    // Utilitários de Formatação
    function formatCurrency(value) {
        return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value);
    }

    function parseFormattedFloat(str) {
        if (!str) return 0;
        // Limpa separadores de milhar e de decimais para converter para float
        const clean = str.replace(/\./g, '').replace(',', '.');
        const num = parseFloat(clean);
        return isNaN(num) ? 0 : num;
    }

    // Máscara básica para os campos de texto monetários
    function applyMaskAndValue(input, onUpdate) {
        input.addEventListener('input', function() {
            let val = input.value.replace(/\D/g, '');
            if (val === '') {
                val = '0';
            }
            const floatVal = parseFloat(val) / 100;
            // Atualiza o valor textual formatado sem travar o cursor
            const formatted = floatVal.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
            input.value = formatted;
            onUpdate();
        });
    }

    // Inicializa valores iniciais mascarados nos inputs
    function setupInputFormatting() {
        const pVal = parseFloat(patrimonyInput.value) || 0;
        const cVal = parseFloat(contributionInput.value) || 0;
        patrimonyInput.value = pVal.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        contributionInput.value = cVal.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }

    // Matemática Financeira
    function calculateCompoundInterest(P, A, r, months) {
        if (r === 0) return P + A * months;
        return P * Math.pow(1 + r, months) + A * ((Math.pow(1 + r, months) - 1) / r);
    }

    function calculateMonthsToTarget(P, A, r, target) {
        if (P >= target) return 0;
        if (A <= 0 && r <= 0) return Infinity;
        if (P * r + A <= 0) return Infinity; // Sem crescimento possível
        if (r === 0) return (target - P) / A;
        
        const numerator = target + A / r;
        const denominator = P + A / r;
        if (denominator <= 0 || numerator <= 0) return Infinity;
        return Math.log(numerator / denominator) / Math.log(1 + r);
    }

    function formatTime(months) {
        if (months === Infinity || isNaN(months)) return "Impossível";
        if (months === 0) return "Já alcançado!";
        
        const rounded = Math.ceil(months);
        const years = Math.floor(rounded / 12);
        const remainingMonths = rounded % 12;
        
        let result = "";
        if (years > 0) {
            result += `${years} ano${years > 1 ? 's' : ''}`;
        }
        if (remainingMonths > 0) {
            if (result !== "") result += " e ";
            result += `${remainingMonths} mê${remainingMonths > 1 ? 'ses' : 's'}`;
        }
        return result;
    }

    function updateCalculator() {
        if (!patrimonyInput || !contributionInput || !rateSlider) return;
        const P = parseFormattedFloat(patrimonyInput.value);
        const A = parseFormattedFloat(contributionInput.value);
        const ratePercent = parseFloat(rateSlider.value) || 0;
        const r = ratePercent / 100;

        // Atualiza Labels dos inputs
        if (labelPatrimony) labelPatrimony.innerText = formatCurrency(P);
        if (labelContribution) labelContribution.innerText = formatCurrency(A);
        if (labelRate) labelRate.innerText = `${ratePercent.toFixed(2)}% ao mês`;

        // Calcula Metas
        const m50 = calculateMonthsToTarget(P, A, r, 50000);
        const m100 = calculateMonthsToTarget(P, A, r, 100000);
        const m1m = calculateMonthsToTarget(P, A, r, 1000000);

        if (time50k) time50k.innerText = formatTime(m50);
        if (time100k) time100k.innerText = formatTime(m100);
        if (time1m) time1m.innerText = formatTime(m1m);

        // Estilos das bordas das metas alcançadas
        if (card50k) {
            if (m50 === 0) card50k.classList.add('target-reached'); else card50k.classList.remove('target-reached');
        }
        if (card100k) {
            if (m100 === 0) card100k.classList.add('target-reached'); else card100k.classList.remove('target-reached');
        }
        if (card1m) {
            if (m1m === 0) card1m.classList.add('target-reached'); else card1m.classList.remove('target-reached');
        }

        // Calcula Projeções
        const proj1 = calculateCompoundInterest(P, A, r, 12);
        const proj5 = calculateCompoundInterest(P, A, r, 60);
        const proj10 = calculateCompoundInterest(P, A, r, 120);

        if (proj1y) proj1y.innerText = formatCurrency(proj1);
        if (proj5y) proj5y.innerText = formatCurrency(proj5);
        if (proj10y) proj10y.innerText = formatCurrency(proj10);
    }

    // Inicialização da calculadora
    if (patrimonyInput && contributionInput && rateSlider) {
        setupInputFormatting();
        applyMaskAndValue(patrimonyInput, updateCalculator);
        applyMaskAndValue(contributionInput, updateCalculator);
        rateSlider.addEventListener('input', updateCalculator);
        updateCalculator();
    }


    // ==========================================================================
    // PARTE 2: PASSO A PASSO DO SALÁRIO (CHECKLIST SALVO EM LOCALSTORAGE)
    // ==========================================================================
    const checklistItems = document.querySelectorAll('.checklist-item');
    const counterSpan = document.getElementById('checklist-counter');
    const progressFill = document.getElementById('checklist-progress');

    // Recupera estado salvo
    let checklistState = JSON.parse(localStorage.getItem('kallia_salary_checklist')) || {};

    function updateChecklistProgress() {
        let checkedCount = 0;
        checklistItems.forEach((item, idx) => {
            const isChecked = !!checklistState[idx];
            if (isChecked) {
                item.classList.add('checked');
                checkedCount++;
            } else {
                item.classList.remove('checked');
            }
        });

        // Atualiza contador e barra de progresso
        if (counterSpan && progressFill) {
            const total = checklistItems.length;
            counterSpan.innerText = `${checkedCount}/${total} concluídos`;
            const percentage = total > 0 ? (checkedCount / total) * 100 : 0;
            progressFill.style.width = `${percentage}%`;
        }
    }

    checklistItems.forEach(item => {
        item.addEventListener('click', function() {
            const idx = item.getAttribute('data-idx');
            checklistState[idx] = !checklistState[idx];
            localStorage.setItem('kallia_salary_checklist', JSON.stringify(checklistState));
            updateChecklistProgress();
        });
    });

    if (checklistItems.length > 0) {
        updateChecklistProgress();
    }


    // ==========================================================================
    // PARTE 3: ANOTAÇÕES SCRATCHPAD (SALVAMENTO AUTOMÁTICO DEBOUNCED EM LOCALSTORAGE)
    // ==========================================================================
    const scratchpad = document.getElementById('scratchpad');
    const saveIndicator = document.getElementById('save-indicator');
    
    if (scratchpad && saveIndicator) {
        // Recupera anotações anteriores
        scratchpad.value = localStorage.getItem('kallia_scratchpad_notes') || '';

        let saveTimeout = null;
        scratchpad.addEventListener('input', function() {
            saveIndicator.innerHTML = "<i class='bx bx-loader-alt bx-spin'></i> Editando...";
            saveIndicator.style.color = "var(--warning)";

            if (saveTimeout) {
                clearTimeout(saveTimeout);
            }

            saveTimeout = setTimeout(() => {
                localStorage.setItem('kallia_scratchpad_notes', scratchpad.value);
                saveIndicator.innerHTML = "<i class='bx bx-check-circle'></i> Salvo no navegador";
                saveIndicator.style.color = "var(--success)";
            }, 1000); // Salva após 1 segundo sem digitar
        });
    }
});
