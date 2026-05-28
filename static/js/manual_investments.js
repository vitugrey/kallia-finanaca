/**
 * Lógica da Página de Lançamento Manual
 */
function toggleAssetChoice(choice) {
    const existingSection = document.getElementById('section-existing-asset');
    const newSection = document.getElementById('section-new-asset');
    
    if (choice === 'existing') {
        existingSection.classList.add('active');
        newSection.classList.remove('active');
    } else {
        existingSection.classList.remove('active');
        newSection.classList.add('active');
    }
}

// Define a data de hoje por padrão no formulário caso esteja vazia
document.addEventListener("DOMContentLoaded", function() {
    const dateInput = document.getElementById("date");
    if (dateInput && !dateInput.value) {
        const today = new Date().toISOString().split('T')[0];
        dateInput.value = today;
    }
});
