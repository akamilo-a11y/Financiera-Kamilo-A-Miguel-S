// Formularios, tabla de movimientos y filtros

const formMovimiento = document.getElementById('form-movimiento');
const selectTipo = document.getElementById('tipo');
const selectCategoria = document.getElementById('categoria');
const tablaMov = document.getElementById('tabla-movimientos');
const msgVacio = document.getElementById('msg-vacio');


// --- Cargar categorías en el select del formulario ---
async function cargarCategorias() {
    const categorias = await getCategorias();
    selectCategoria.innerHTML = categorias.map(c =>
        `<option value="${c.id_categoria}">${c.nombre}</option>`
    ).join('');
    // Reconstruir el select del filtro
    const filtroCat = document.getElementById('filtro-categoria');
    filtroCat.innerHTML = '<option value="">Todas</option>' +
        categorias.map(c => `<option value="${c.id_categoria}">${c.nombre}</option>`).join('');
    actualizarCategoriasDelTipo();
}

// Filtrar categorías por el tipo seleccionado
function actualizarCategoriasDelTipo() {
    const tipo = selectTipo.value;
    getCategorias().then(categorias => {
        const filtradas = categorias.filter(c => c.tipo === tipo);
        selectCategoria.innerHTML = filtradas.map(c =>
            `<option value="${c.id_categoria}">${c.nombre}</option>`).join('');
        if (filtradas.length === 0) {
            selectCategoria.innerHTML = '<option value="">Sin categorías de este tipo</option>';
        }
    });
}
selectTipo.addEventListener('change', actualizarCategoriasDelTipo);

// --- Guardar movimiento ---
formMovimiento.addEventListener('submit', async (e) => {
    e.preventDefault();
    const payload = {
        id_categoria: parseInt(selectCategoria.value, 10),
        tipo: selectTipo.value,
        monto: parseFloat(document.getElementById('monto').value),
        fecha: document.getElementById('fecha').value,
        descripcion: document.getElementById('descripcion').value || null
    };
    try {
        await crearMovimiento(payload);
        toast('Movimiento guardado correctamente');
        formMovimiento.reset();
        document.getElementById('fecha').value = new Date().toISOString().slice(0, 10);
        await Promise.all([cargarMovimientos(), recargarDashboard()]);
    } catch (err) {
        toast(err.message, 'error');
    }
});

// --- Crear categoría ---
document.getElementById('form-categoria').addEventListener('submit', async (e) => {
    e.preventDefault();
    const payload = {
        nombre: document.getElementById('nombre-categoria').value.trim(),
        tipo: document.getElementById('tipo-categoria').value
    };
    try {
        await crearCategoria(payload);
        toast('Categoría añadida');
        e.target.reset();
        await Promise.all([cargarCategorias(), listarCategorias()]);
    } catch (err) {
        toast(err.message, 'error');
    }
});

// --- Listar categorías (gestión) ---
async function listarCategorias() {
    const categorias = await getCategorias();
    const lista = document.getElementById('lista-categorias');
    lista.innerHTML = categorias.map(c =>
        `<li>
            <div>
                <span>${c.nombre}</span>
                <span class="cat-tag ${c.tipo}">${c.tipo}</span>
            </div>
            <div class="cat-actions">
                <button class="btn-icon btn-edit" onclick="editarCategoria(${c.id_categoria}, '${c.nombre}')">Editar</button>
                <button class="btn-icon btn-del" onclick="eliminarCategoria(${c.id_categoria})">Eliminar</button>
            </div>
        </li>`
    ).join('');
}

window.editarCategoria = async (id, nombreActual) => {
    const nuevoNombre = prompt('Nuevo nombre de la categoría:', nombreActual);
    if (nuevoNombre === null) return;
    const nombre = nuevoNombre.trim();
    if (!nombre) {
        toast('El nombre no puede estar vacío', 'error');
        return;
    }
    try {
        await actualizarCategoria(id, { nombre });
        toast('Categoría actualizada');
        await Promise.all([cargarCategorias(), listarCategorias()]);
    } catch (err) {
        toast(err.message, 'error');
    }
};

window.eliminarCategoria = async (id) => {
    if (!confirm('¿Eliminar esta categoría? (Las categorías con movimientos no se pueden eliminar)')) return;
    try {
        await eliminarCategoria(id);
        toast('Categoría eliminada');
        await Promise.all([cargarCategorias(), listarCategorias()]);
    } catch (err) {
        toast(err.message, 'error');
    }
};

// --- Renderizar tabla de movimientos ---
function formatearFecha(fecha) {
    const [y, m, d] = fecha.split('-');
    return `${d}/${m}/${y}`;
}

function renderMovimientos(movimientos) {
    if (!movimientos || movimientos.length === 0) {
        tablaMov.innerHTML = '';
        msgVacio.style.display = 'block';
        return;
    }
    msgVacio.style.display = 'none';
    tablaMov.innerHTML = movimientos.map(m => {
        const esGasto = m.tipo === 'gasto';
        const monto = Number(m.monto).toLocaleString('es-CO');
        return `<tr>
            <td>${formatearFecha(m.fecha)}</td>
            <td><span class="type-badge ${esGasto ? 'badge-gasto' : 'badge-ingreso'}">${m.tipo}</span></td>
            <td>${m.categoria || '—'}</td>
            <td>${m.descripcion || '—'}</td>
            <td class="text-right monto-${esGasto ? 'gasto' : 'ingreso'}">$ ${monto}</td>
            <td class="text-center">
                <button class="btn-icon btn-edit" onclick="editarMovimiento(${m.id_movimiento}, ${esGasto})">Editar</button>
                <button class="btn-icon btn-del" onclick="eliminarMovimiento(${m.id_movimiento})">Eliminar</button>
            </td>
        </tr>`;
    }).join('');
}

async function cargarMovimientos() {
    const desde = document.getElementById('filtro-desde').value;
    const hasta = document.getElementById('filtro-hasta').value;
    const categoria = document.getElementById('filtro-categoria').value;
    const movimientos = await getMovimientos({ desde, hasta, categoria });
    renderMovimientos(movimientos);
}

// --- Filtros ---
['filtro-desde', 'filtro-hasta', 'filtro-categoria'].forEach(id => {
    document.getElementById(id).addEventListener('change', cargarMovimientos);
});
document.getElementById('btn-limpiar-filtros').addEventListener('click', () => {
    document.getElementById('filtro-desde').value = '';
    document.getElementById('filtro-hasta').value = '';
    document.getElementById('filtro-categoria').value = '';
    cargarMovimientos();
});

// --- Editar / Eliminar (exposición global para los onclick de la tabla) ---
window.eliminarMovimiento = async (id) => {
    if (!confirm('¿Eliminar este movimiento?')) return;
    try {
        await eliminarMovimiento(id);
        toast('Movimiento eliminado');
        await Promise.all([cargarMovimientos(), recargarDashboard()]);
    } catch (err) {
        toast(err.message, 'error');
    }
};

window.editarMovimiento = async (id, esGasto) => {
    const nuevoMonto = prompt('Nuevo monto:', '');
    if (nuevoMonto === null) return;
    const monto = parseFloat(nuevoMonto.replace(/[^0-9.]/g, ''));
    if (isNaN(monto) || monto <= 0) {
        toast('Monto inválido', 'error');
        return;
    }
    try {
        await actualizarMovimiento(id, { monto });
        toast('Movimiento actualizado');
        await Promise.all([cargarMovimientos(), recargarDashboard()]);
    } catch (err) {
        toast(err.message, 'error');
    }
};
