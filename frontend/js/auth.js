// Gestión de sesión (sin JWT) - guarda el usuario en localStorage

const SESSION_KEY = 'finanzas_sesion';

function guardarSesion(usuario) {
    localStorage.setItem(SESSION_KEY, JSON.stringify(usuario));
}
function obtenerSesion() {
    try {
        return JSON.parse(localStorage.getItem(SESSION_KEY));
    } catch {
        return null;
    }
}
function cerrarSesion() {
    localStorage.removeItem(SESSION_KEY);
}

// Redirige al dashboard si ya hay sesión, o al login si no la hay
function verificarSesion() {
    const sesion = obtenerSesion();
    const enLogin = window.location.pathname.endsWith('/login') || window.location.pathname === '/login';
    if (enLogin && sesion) {
        window.location.href = '/';
    } else if (!enLogin && !sesion) {
        window.location.href = '/login';
    }
}

// --- Login y registro ---
async function doLogin(correo, contrasena) {
    const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ correo, contrasena })
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
        throw new Error(typeof data.detail === 'string' ? data.detail : 'Error al iniciar sesión');
    }
    guardarSesion({ id_usuario: data.id_usuario, nombre: data.nombre, correo: data.correo, token: data.token });
    return data;
}

async function doRegistro(payload) {
    const res = await fetch('/api/usuarios', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
        throw new Error(typeof data.detail === 'string' ? data.detail : 'Error al registrar');
    }
    // El servidor devuelve un token: iniciar sesión automáticamente
    guardarSesion({ id_usuario: data.id_usuario, nombre: payload.nombre, correo: payload.correo, token: data.token });
    return data;
}

// --- UI: pestañas y envío de formularios (solo en login.html) ---
document.addEventListener('DOMContentLoaded', () => {
    const tabLogin = document.getElementById('tab-login');
    const tabRegistro = document.getElementById('tab-registro');
    const formLogin = document.getElementById('form-login');
    const formRegistro = document.getElementById('form-registro');

    if (!tabLogin) return; // No estamos en login.html

    verificarSesion(); // Si ya hay sesión, ir al dashboard

    function mostrarFormulario(esLogin) {
        tabLogin.classList.toggle('active', esLogin);
        tabRegistro.classList.toggle('active', !esLogin);
        formLogin.style.display = esLogin ? 'block' : 'none';
        formRegistro.style.display = esLogin ? 'none' : 'block';
        document.getElementById(esLogin ? 'login-error' : 'registro-error').textContent = '';
    }
    tabLogin.addEventListener('click', () => mostrarFormulario(true));
    tabRegistro.addEventListener('click', () => mostrarFormulario(false));

    formLogin.addEventListener('submit', async (e) => {
        e.preventDefault();
        const err = document.getElementById('login-error');
        err.textContent = '';
        try {
            await doLogin(
                document.getElementById('login-correo').value.trim(),
                document.getElementById('login-contrasena').value
            );
            toast('¡Bienvenido de nuevo!');
            window.location.href = '/';
        } catch (ex) {
            err.textContent = ex.message;
        }
    });

    formRegistro.addEventListener('submit', async (e) => {
        e.preventDefault();
        const err = document.getElementById('registro-error');
        err.textContent = '';
        try {
            await doRegistro({
                nombre: document.getElementById('reg-nombre').value.trim(),
                correo: document.getElementById('reg-correo').value.trim(),
                contrasena: document.getElementById('reg-contrasena').value
            });
            toast('Cuenta creada correctamente');
            window.location.href = '/';
        } catch (ex) {
            err.textContent = ex.message;
        }
    });
});
