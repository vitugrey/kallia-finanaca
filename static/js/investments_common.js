// ==========================================================================
// FUNÇÕES REUTILIZÁVEIS E COMUNS - INVESTIMENTOS
// ==========================================================================

// Alternância de Abas (Tabs)
function openTab(evt, tabId) {
    var i, tabcontent, tablinks;
    
    // Ocultar todos os conteúdos de abas
    tabcontent = document.getElementsByClassName("tab-content");
    for (i = 0; i < tabcontent.length; i++) {
        tabcontent[i].style.display = "none";
        tabcontent[i].classList.remove("active");
    }
    
    // Desativar botões de abas
    tablinks = document.getElementsByClassName("tab-btn");
    for (i = 0; i < tablinks.length; i++) {
        tablinks[i].classList.remove("active");
    }
    
    // Ativar aba atual
    const activeTab = document.getElementById(tabId);
    if (activeTab) {
        activeTab.style.display = "block";
        activeTab.classList.add("active");
    }
    if (evt && evt.currentTarget) {
        evt.currentTarget.classList.add("active");
    }
}

// Botão para Atualização de Cotações Yahoo Finance
document.addEventListener("DOMContentLoaded", function() {
    const btnUpdatePrices = document.getElementById('btnUpdatePrices');
    if (btnUpdatePrices) {
        btnUpdatePrices.addEventListener('click', function() {
            const btn = this;
            const icon = btn.querySelector('i');
            const span = btn.querySelector('span');
            
            if (icon) icon.classList.add('bx-spin');
            if (span) span.innerText = 'Buscando Cotações...';
            btn.style.opacity = '0.7';
            btn.style.pointerEvents = 'none';

            // Lê csrf token dinâmico passado no atributo do botão ou no window
            const csrfToken = typeof csrfTokenVal !== 'undefined' ? csrfTokenVal : '';
            const updateUrl = typeof updatePricesUrl !== 'undefined' ? updatePricesUrl : '/investimentos/atualizar-cotacoes/';

            fetch(updateUrl, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    window.location.reload();
                } else {
                    alert('Erro ao atualizar preços.');
                    window.location.reload();
                }
            })
            .catch(err => {
                console.error(err);
                alert('Erro de conexão.');
                window.location.reload();
            });
        });
    }
});
