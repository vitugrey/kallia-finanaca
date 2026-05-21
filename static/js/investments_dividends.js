// ==========================================================================
// GRÁFICOS DE EVOLUÇÃO DE PROVENTOS (INVESTIMENTOS)
// ==========================================================================
document.addEventListener("DOMContentLoaded", function() {
    const monthlyCanvas = document.getElementById('monthlyChart');
    const yearlyCanvas = document.getElementById('yearlyChart');
    const allTimeCanvas = document.getElementById('allTimeChart');

    if (monthlyCanvas && typeof yearlyLabels !== 'undefined' && typeof yearlyData !== 'undefined') {
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
                    ticks: { color: '#9ca3af' }
                }
            }
        };

        // Gráfico Mensal (Últimos 24 meses)
        if (typeof monthlyLabels !== 'undefined' && typeof monthlyData !== 'undefined') {
            new Chart(monthlyCanvas.getContext('2d'), {
                type: 'line',
                data: {
                    labels: monthlyLabels,
                    datasets: [{
                        label: 'Dividendos',
                        data: monthlyData,
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        borderColor: '#10b981',
                        borderWidth: 2,
                        pointBackgroundColor: '#10b981',
                        fill: true,
                        tension: 0.3
                    }]
                },
                options: {
                    ...commonOptions,
                    scales: {
                        ...commonOptions.scales,
                        x: {
                            ...commonOptions.scales.x,
                            ticks: { color: '#9ca3af', maxRotation: 45, minRotation: 45 }
                        }
                    }
                }
            });
        }

        // Gráfico Anual
        if (yearlyCanvas) {
            new Chart(yearlyCanvas.getContext('2d'), {
                type: 'bar',
                data: {
                    labels: yearlyLabels,
                    datasets: [{
                        label: 'Dividendos por Ano',
                        data: yearlyData,
                        backgroundColor: 'rgba(16, 185, 129, 0.6)',
                        borderColor: '#10b981',
                        borderWidth: 1,
                        borderRadius: 4
                    }]
                },
                options: commonOptions
            });
        }

        // Gráfico Desde o Início
        if (allTimeCanvas && typeof allTimeLabels !== 'undefined' && typeof allTimeData !== 'undefined') {
            new Chart(allTimeCanvas.getContext('2d'), {
                type: 'line',
                data: {
                    labels: allTimeLabels,
                    datasets: [{
                        label: 'Dividendos',
                        data: allTimeData,
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        borderColor: '#10b981',
                        borderWidth: 2,
                        pointBackgroundColor: '#10b981',
                        fill: true,
                        tension: 0.3
                    }]
                },
                options: {
                    ...commonOptions,
                    scales: {
                        ...commonOptions.scales,
                        x: {
                            ...commonOptions.scales.x,
                            ticks: { color: '#9ca3af', maxRotation: 45, minRotation: 45 }
                        }
                    }
                }
            });
        }
    }
});
