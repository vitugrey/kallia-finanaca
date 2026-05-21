// ==========================================================================
// GRÁFICOS DE EVOLUÇÃO DE PATRIMÔNIO (INVESTIMENTOS)
// ==========================================================================
document.addEventListener("DOMContentLoaded", function() {
    const monthlyCanvas = document.getElementById('monthlyChart');
    const yearlyCanvas = document.getElementById('yearlyChart');

    if (monthlyCanvas && typeof monthlyLabels !== 'undefined' && typeof monthlyData !== 'undefined') {
        const commonOptions = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: '#1f2937',
                    titleColor: '#f3f4f6',
                    bodyColor: '#d1d5db',
                    borderColor: '#374151',
                    borderWidth: 1,
                    padding: 12,
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) { label += ': '; }
                            if (context.parsed.y !== null) {
                                label += new Intl.NumberFormat('en-US', { style: 'currency', currency: 'BRL' }).format(context.parsed.y).replace('R$', 'R$').replace(/\s/g, '');
                            }
                            return label;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: {
                        color: '#9ca3af',
                        callback: function(value) {
                            return 'R$' + new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 }).format(value);
                        }
                    }
                },
                x: {
                    grid: { display: false },
                    ticks: {
                        color: '#9ca3af',
                        maxRotation: 45,
                        minRotation: 45
                    }
                }
            }
        };

        // Gráfico de Linha Mensal
        new Chart(monthlyCanvas.getContext('2d'), {
            type: 'line',
            data: {
                labels: monthlyLabels,
                datasets: [{
                    label: 'Acumulado Mês a Mês',
                    data: monthlyData,
                    backgroundColor: 'rgba(56, 189, 248, 0.1)',
                    borderColor: '#38bdf8',
                    borderWidth: 3,
                    pointBackgroundColor: '#38bdf8',
                    pointRadius: 2,
                    fill: true,
                    tension: 0.3
                }]
            },
            options: commonOptions
        });

        // Gráfico de Barra Anual
        if (yearlyCanvas && typeof yearlyLabels !== 'undefined' && typeof yearlyData !== 'undefined') {
            new Chart(yearlyCanvas.getContext('2d'), {
                type: 'bar',
                data: {
                    labels: yearlyLabels,
                    datasets: [{
                        label: 'Acumulado por Ano',
                        data: yearlyData,
                        backgroundColor: 'rgba(99, 102, 241, 0.6)',
                        borderColor: '#6366f1',
                        borderWidth: 1,
                        borderRadius: 4
                    }]
                },
                options: {
                    ...commonOptions,
                    scales: {
                        ...commonOptions.scales,
                        y: {
                            ...commonOptions.scales.y,
                            ticks: {
                                ...commonOptions.scales.y.ticks,
                                callback: function(value) {
                                    return 'R$' + new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 }).format(value);
                                }
                            }
                        },
                        x: {
                            ...commonOptions.scales.x,
                            ticks: { color: '#9ca3af' } // Normal rotation for years
                        }
                    }
                }
            });
        }
    }
});
