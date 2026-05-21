// ==========================================================================
// GRÁFICOS DO DASHBOARD DE CARTEIRA (BUDGET)
// ==========================================================================
document.addEventListener("DOMContentLoaded", function() {
    // 1. Gráfico de Rosca: Despesas por Categoria
    const catCanvas = document.getElementById('categoryChart');
    if (catCanvas && typeof categoryLabels !== 'undefined' && typeof categoryValues !== 'undefined') {
        const catCtx = catCanvas.getContext('2d');
        const colors = [
            '#6366f1', '#3b82f6', '#10b981', '#f59e0b', '#ef4444',
            '#8b5cf6', '#ec4899', '#14b8a6', '#06b6d4', '#f43f5e'
        ];

        new Chart(catCtx, {
            type: 'doughnut',
            data: {
                labels: categoryLabels,
                datasets: [{
                    data: categoryValues,
                    backgroundColor: colors.slice(0, categoryLabels.length),
                    borderWidth: 0,
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '75%',
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            color: '#94a3b8',
                            font: { family: "'Inter', sans-serif", size: 11 },
                            usePointStyle: true,
                            padding: 10
                        }
                    },
                    tooltip: {
                        backgroundColor: '#111827',
                        titleColor: '#f8fafc',
                        bodyColor: '#cbd5e1',
                        borderColor: 'rgba(255, 255, 255, 0.1)',
                        borderWidth: 1,
                        padding: 12,
                        callbacks: {
                            label: function(context) {
                                let val = context.parsed;
                                return ' ' + context.label + ': R$' + val.toLocaleString('pt-BR', {minimumFractionDigits: 2});
                            }
                        }
                    }
                }
            }
        });
    }

    // 2. Gráfico de Barras: Evolução Mensal (Fluxo Mensal)
    const evoCanvas = document.getElementById('evolutionChart');
    if (evoCanvas && typeof evolutionLabels !== 'undefined' && typeof evolutionIncome !== 'undefined' && typeof evolutionExpense !== 'undefined') {
        const evoCtx = evoCanvas.getContext('2d');

        new Chart(evoCtx, {
            type: 'bar',
            data: {
                labels: evolutionLabels,
                datasets: [
                    {
                        label: 'Receitas',
                        data: evolutionIncome,
                        backgroundColor: '#10b981',
                        borderRadius: 4
                    },
                    {
                        label: 'Despesas',
                        data: evolutionExpense,
                        backgroundColor: '#ef4444',
                        borderRadius: 4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { color: '#94a3b8', font: { size: 10 } }
                    },
                    y: {
                        grid: { color: 'rgba(255, 255, 255, 0.05)' },
                        ticks: {
                            color: '#94a3b8',
                            font: { size: 10 },
                            callback: function(value) { return 'R$' + value; }
                        }
                    }
                },
                plugins: {
                    legend: {
                        labels: {
                            color: '#94a3b8',
                            font: { family: "'Inter', sans-serif", size: 11 }
                        }
                    },
                    tooltip: {
                        backgroundColor: '#111827',
                        titleColor: '#f8fafc',
                        bodyColor: '#cbd5e1',
                        borderColor: 'rgba(255, 255, 255, 0.1)',
                        borderWidth: 1,
                        padding: 12
                    }
                }
            }
        });
    }
});
