// ==========================================================================
// GRÁFICOS DO DASHBOARD DE INVESTIMENTOS
// ==========================================================================
document.addEventListener("DOMContentLoaded", function() {
    const allocCanvas = document.getElementById('allocationChart');
    if (allocCanvas && typeof allocationLabels !== 'undefined' && typeof allocationData !== 'undefined') {
        const ctx = allocCanvas.getContext('2d');
        
        const colorMap = {
            'Fundo Imobiliário': '#3b82f6', // Azul
            'Ação': '#f59e0b', // Laranja
            'Renda Fixa': '#10b981', // Verde
            'ETF': '#ef4444', // Vermelho
            'BDR': '#8b5cf6', // Roxo
            'Criptomoeda': '#ec4899', // Rosa
            'Outro': '#9ca3af' // Cinza
        };
        
        const bgColors = allocationLabels.map(label => colorMap[label] || '#9ca3af');
        
        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: allocationLabels,
                datasets: [{
                    data: allocationData,
                    backgroundColor: bgColors,
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
                            color: '#9ca3af',
                            font: {
                                family: "'Inter', sans-serif",
                                size: 12
                            },
                            usePointStyle: true,
                            padding: 20
                        }
                    },
                    tooltip: {
                        backgroundColor: '#1f2937',
                        titleColor: '#f3f4f6',
                        bodyColor: '#d1d5db',
                        borderColor: '#374151',
                        borderWidth: 1,
                        padding: 12,
                        callbacks: {
                            label: function(context) {
                                let label = context.label || '';
                                if (label) {
                                    label += ': ';
                                }
                                if (context.parsed !== null) {
                                    label += new Intl.NumberFormat('en-US', { style: 'currency', currency: 'BRL' }).format(context.parsed).replace('R$', 'R$').replace(/\s/g, '');
                                }
                                return label;
                            }
                        }
                    }
                }
            }
        });
    }

    // ==========================================================================
    // GRÁFICO DE BARRAS EMPILHADAS (PROVENTOS MENSAIS POR ATIVO)
    // ==========================================================================
    const divMonthlyCanvas = document.getElementById('dividendsMonthlyChart');
    if (divMonthlyCanvas && typeof dividendsMonthlyLabels !== 'undefined' && typeof dividendsMonthlyDatasets !== 'undefined') {
        const ctx = divMonthlyCanvas.getContext('2d');
        
        // Cores vibrantes e harmoniosas para os ativos
        const chartColors = [
            '#6366f1', // Indigo
            '#3b82f6', // Azul
            '#10b981', // Verde
            '#f59e0b', // Laranja
            '#8b5cf6', // Roxo
            '#ef4444', // Vermelho
            '#ec4899', // Rosa
            '#14b8a6', // Teal
            '#f43f5e', // Rose
            '#06b6d4', // Cyan
            '#84cc16', // Lime
            '#a855f7', // Purple
            '#64748b'  // Slate
        ];

        // Mapeia e colore cada dataset
        const datasetsWithColors = dividendsMonthlyDatasets.map((dataset, idx) => {
            const color = chartColors[idx % chartColors.length];
            return {
                label: dataset.label,
                data: dataset.data,
                backgroundColor: color,
                hoverBackgroundColor: color,
                borderRadius: 4,
                borderSkipped: false
            };
        });

        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: dividendsMonthlyLabels,
                datasets: datasetsWithColors
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            color: '#9ca3af',
                            font: {
                                family: "'Inter', sans-serif",
                                size: 11
                            },
                            usePointStyle: true,
                            boxWidth: 8,
                            padding: 15
                        }
                    },
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
                                if (label) {
                                    label += ': ';
                                }
                                if (context.raw !== null) {
                                    label += new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(context.raw);
                                }
                                return label;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        stacked: true,
                        grid: {
                            color: 'rgba(255, 255, 255, 0.05)',
                            borderColor: 'transparent'
                        },
                        ticks: {
                            color: '#9ca3af',
                            font: {
                                family: "'Inter', sans-serif",
                                size: 11
                            }
                        }
                    },
                    y: {
                        stacked: true,
                        grid: {
                            color: 'rgba(255, 255, 255, 0.05)',
                            borderColor: 'transparent'
                        },
                        ticks: {
                            color: '#9ca3af',
                            font: {
                                family: "'Inter', sans-serif",
                                size: 11
                            },
                            callback: function(value) {
                                return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 }).format(value);
                            }
                        }
                    }
                }
            }
        });
    }
});
