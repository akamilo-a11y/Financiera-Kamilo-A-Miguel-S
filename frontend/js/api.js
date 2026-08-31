// Cliente API - maneja todas las peticiones fetch al backend
const API_URL = '/api';

// Obtiene el token de la sesión guardada
function obtenerToken() {
    try {
        const sesion = JSON.parse(localStorage.getItem('finanzas_sesion'));
        return sesion ? sesion.token : null;
    } catch {
        return null;
    }
}

// Obtiene el id_usuario de la sesión guardada (en vez de un valor fijo)
function obtenerUsuarioId() {
    try {
        const sesion = JSON.parse(localStorage.getItem('finanzas_sesion'));
        return sesion ? sesion.id_usuario : 1;
    } catch {
        return 1;
    }
}

async function apiFetch(path, options = {}) {
    const headers = { 'Content-Type': 'application/json' };
    const token = obtenerToken();
    if (token) headers['Authorization'] = `Bearer ${token}`;

    try {
        const res = await fetch(`${API_URL}${path}`, { headers, ...options });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
            // Sesión expirada/inválida: cerrar sesión y redirigir al login
            if (res.status === 401) {
                cerrarSesion();
                window.location.href = '/login';
            }
            const detail = typeof data.detail === 'string' ? data.detail : 'Ocurrió un error en la petición';
            throw new Error(detail);
        }
        return data;
    } catch (err) {
        console.error('Error de red/API:', err);
        throw err;
    }
}

// --- Resumen / KPIs ---
const getResumen = (mes) => apiFetch(`/resumen?id_usuario=${obtenerUsuarioId()}${mes ? `&mes=${mes}` : ''}`);

// --- Predicción / Anomalías ---
const getPrediccion = () => apiFetch(`/analitica/prediccion?id_usuario=${obtenerUsuarioId()}`);
const getAnomalias = () => apiFetch(`/analitica/anomalias?id_usuario=${obtenerUsuarioId()}`);

// --- Gráficos ---
const getDistribucion = () => apiFetch(`/graficos/distribucion?id_usuario=${obtenerUsuarioId()}`);
const getTendencia = () => apiFetch(`/graficos/tendencia?id_usuario=${obtenerUsuarioId()}`);

// --- Categorías ---
const getCategorias = () => apiFetch(`/categorias?id_usuario=${obtenerUsuarioId()}`);
const crearCategoria = (data) => apiFetch('/categorias', {
    method: 'POST',
    body: JSON.stringify({ ...data, id_usuario: obtenerUsuarioId() })
});
const actualizarCategoria = (id, data) => apiFetch(`/categorias/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data)
});
const eliminarCategoria = (id) => apiFetch(`/categorias/${id}`, { method: 'DELETE' });

// --- Movimientos ---
const getMovimientos = (filtros = {}) => {
    const qs = new URLSearchParams({ id_usuario: obtenerUsuarioId() });
    if (filtros.desde) qs.set('desde', filtros.desde);
    if (filtros.hasta) qs.set('hasta', filtros.hasta);
    if (filtros.categoria) qs.set('categoria', filtros.categoria);
    return apiFetch(`/movimientos?${qs.toString()}`);
};
const crearMovimiento = (data) => apiFetch('/movimientos', {
    method: 'POST',
    body: JSON.stringify({ ...data, id_usuario: obtenerUsuarioId() })
});
const actualizarMovimiento = (id, data) => apiFetch(`/movimientos/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data)
});
const eliminarMovimiento = (id) => apiFetch(`/movimientos/${id}`, { method: 'DELETE' });
