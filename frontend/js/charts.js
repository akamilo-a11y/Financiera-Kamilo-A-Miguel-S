// Visualizaciones con Chart.js - datos consumidos de la API
let chartCategorias = null;
let chartTendencia = null;

const PALETA = ['#6366f1', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#3b82f6', '#14b8a6', '#f43f5e'];

const formatoCOP = (v) => '$' + Number(v).toLocaleString('es-CO');

async function cargarDistribucion() {
    const data = await getDistribucion();
    const ctx = document.getElementById('chartCategorias').getContext('2d');

    if (chartCategorias) chartCategorias.destroy();

    chartCategorias = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: data.labels,
            datasets: [{
                data: data.data,
                backgroundColor: data.labels.map((_, i) => PALETA[i % PALETA.length]),
                borderWidth: 3,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '62%',
            plugins: {
                title: { display: true, text: 'Distribución de Gastos por Categoría', font: { weight: '700', size: 14 } },
                legend: { position: 'bottom' },
                tooltip: { callbacks: { label: (ctx) => ` ${ctx.label}: ${formatoCOP(ctx.raw)}` } }
            }
        }
    });
}

async function cargarTendencia() {
    const data = await getTendencia();
    const ctx = document.getElementById('chartTendencia').getContext('2d');

    if (chartTendencia) chartTendencia.destroy();

    chartTendencia = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.labels,
            datasets: [
                {
                    label: 'Ingresos',
                    data: data.ingresos,
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16,185,129,.1)',
                    fill: true,
                    tension: .35,
                    borderWidth: 3,
                    pointRadius: 4
                },
                {
                    label: 'Gastos',
                    data: data.gastos,
                    borderColor: '#ef4444',
                    backgroundColor: 'rgba(239,68,68,.08)',
                    fill: true,
                    tension: .35,
                    borderWidth: 3,
                    pointRadius: 4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: { display: true, text: 'Tendencia Mensual: Ingresos vs Gastos', font: { weight: '700', size: 14 } },
                legend: { position: 'bottom' },
                tooltip: { callbacks: { label: (ctx) => ` ${ctx.dataset.label}: ${formatoCOP(ctx.raw)}` } }
            },
            scales: {
                y: { ticks: { callback: (v) => formatoCOP(v) } }
            }
        }
    });
}

async function inicializarGraficos() {
    await Promise.all([cargarDistribucion(), cargarTendencia()]);
}
