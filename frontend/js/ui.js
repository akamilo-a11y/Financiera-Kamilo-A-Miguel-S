// Utilidades UI compartidas (toast, formato de moneda)

function toast(mensaje, tipo = 'success') {
    const el = document.getElementById('toast');
    if (!el) return;
    el.textContent = mensaje;
    el.className = `toast show ${tipo}`;
    clearTimeout(el._t);
    el._t = setTimeout(() => el.classList.remove('show'), 2600);
}
