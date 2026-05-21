// ==========================================================================
// CONTROLE DE MODAIS (CARTEIRA)
// ==========================================================================
function openModal(id) {
    const modal = document.getElementById(id);
    if (modal) {
        modal.style.display = 'flex';
    }
}

function closeModal(id) {
    const modal = document.getElementById(id);
    if (modal) {
        modal.style.display = 'none';
    }
}

// Fecha modais automaticamente ao clicar fora deles (no overlay)
window.addEventListener('click', function(event) {
    if (event.target.classList.contains('modal-overlay')) {
        event.target.style.display = 'none';
    }
});

// Modal de Edição Dinâmico
function openEditModal(btn) {
    const id = btn.getAttribute('data-id');
    const description = btn.getAttribute('data-description');
    const value = btn.getAttribute('data-value');
    const date = btn.getAttribute('data-date');
    const type = btn.getAttribute('data-type');
    const categoryId = btn.getAttribute('data-category');
    const isCredit = btn.getAttribute('data-credit') === 'True';
    const isFixedExpense = btn.getAttribute('data-fixed-expense') === 'True';
    const isFixedIncome = btn.getAttribute('data-fixed-income') === 'True';

    // Preenche campos
    document.getElementById('edit_description').value = description;
    document.getElementById('edit_value').value = value.replace('.', ',');
    document.getElementById('edit_date').value = date;
    document.getElementById('edit_transaction_type').value = type;
    document.getElementById('edit_category').value = categoryId;
    document.getElementById('edit_is_credit').checked = isCredit;
    document.getElementById('edit_is_fixed_expense').checked = isFixedExpense;
    document.getElementById('edit_is_fixed_income').checked = isFixedIncome;

    // Ajusta checkboxes visíveis
    handleEditTypeChange();

    // Configura action do form
    const form = document.getElementById('editForm');
    if (form) {
        form.action = `/carteira/transacoes/${id}/editar/`;
    }

    openModal('editTransactionModal');
}

// Toggle de inputs nos modais dependendo do tipo selecionado
function handleTypeChange() {
    const typeSelect = document.getElementById('transaction_type');
    const expenseFixedDiv = document.getElementById('fixed-expense-container');
    const incomeFixedDiv = document.getElementById('fixed-income-container');

    if (typeSelect && expenseFixedDiv && incomeFixedDiv) {
        if (typeSelect.value === 'expense') {
            expenseFixedDiv.style.display = 'block';
            incomeFixedDiv.style.display = 'none';
        } else {
            expenseFixedDiv.style.display = 'none';
            incomeFixedDiv.style.display = 'block';
        }
    }
}

function handleEditTypeChange() {
    const typeSelect = document.getElementById('edit_transaction_type');
    const expenseFixedDiv = document.getElementById('edit-fixed-expense-container');
    const incomeFixedDiv = document.getElementById('edit-fixed-income-container');

    if (typeSelect && expenseFixedDiv && incomeFixedDiv) {
        if (typeSelect.value === 'expense') {
            expenseFixedDiv.style.display = 'block';
            incomeFixedDiv.style.display = 'none';
        } else {
            expenseFixedDiv.style.display = 'none';
            incomeFixedDiv.style.display = 'block';
        }
    }
}
