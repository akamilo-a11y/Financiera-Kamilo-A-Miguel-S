// Carga inicial y refresco del dashboard (KPIs, predicción, anomalías)

const fmt = (v) => '$' + Number(v).toLocaleString('es-CO');

async function cargarResumen() {
    const data = await getResumen();
    document.getElementById('card-ingresos').innerText = fmt(data.total_ingresos);
    document.getElementById('card-gastos').innerText = fmt(data.total_gastos);
    document.getElementById('card-balance').innerText = fmt(data.balance);
    document.getElementById('card-porcentaje').innerText = `Ahorro: ${data.porcentaje_ahorro}%`;
}

async function cargarPrediccion() {
    const data = await getPrediccion();
    document.getElementById('card-prediccion').innerText = fmt(data.prediccion);
}

async function cargarAnomalias() {
    const data = await getAnomalias();
    const alertBox = document.getElementById('alerta-anomalias');
    const lista = document.getElementById('lista-anomalias');
    if (data.anomalias && data.anomalias.length > 0) {
        alertBox.style.display = 'block';
        lista.innerHTML = data.anomalias.map(a => {
            const fecha = a.fecha ? a.fecha.split('-').reverse().join('/') : '—';
            return `<li>
                Gasto inusual el <strong>${fecha}</strong>: <strong>$ ${Number(a.monto).toLocaleString('es-CO')}</strong>
                (Promedio categoría: $ ${Number(a.promedio_categoria).toLocaleString('es-CO')} · Z=${a.z_score})
            </li>`;
        }).join('');
    } else {
        alertBox.style.display = 'none';
    }
}

// Refresca KPIs, predicción y anomalías (usado tras crear/editar/eliminar)
async function recargarDashboard() {
    await Promise.all([
        cargarResumen(),
        cargarPrediccion(),
        cargarAnomalias(),
        inicializarGraficos()
    ]);
}

// Mostrar el nombre del usuario logueado en el encabezado
function mostrarUsuario() {
    const sesion = obtenerSesion();
    if (!sesion) return;
    const nombre = sesion.nombre || 'Usuario';
    document.getElementById('user-nombre').textContent = nombre;
    const iniciales = nombre.trim().split(/\s+/).slice(0, 2).map(p => p[0]).join('').toUpperCase();
    document.getElementById('user-avatar').textContent = iniciales || 'U';
}

// Cerrar sesión
document.getElementById('btn-logout').addEventListener('click', () => {
    cerrarSesion();
    window.location.href = '/login';
});

document.addEventListener('DOMContentLoaded', async () => {
    // Redirigir al login si no hay sesión iniciada
    if (!obtenerSesion()) {
        window.location.href = '/login';
        return;
    }
    mostrarUsuario();
    document.getElementById('fecha').value = new Date().toISOString().slice(0, 10);
    try {
        await Promise.all([
            cargarCategorias(),
            listarCategorias(),
            cargarResumen(),
            cargarPrediccion(),
            cargarAnomalias(),
            cargarMovimientos()
        ]);
        await inicializarGraficos();
    } catch (err) {
        toast('No se pudo conectar con el backend. Revisa que esté ejecutándose.', 'error');
    }
});
