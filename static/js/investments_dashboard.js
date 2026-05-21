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
});
