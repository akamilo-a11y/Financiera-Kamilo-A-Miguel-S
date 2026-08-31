# 💸 Aplicación Web de Finanzas Personales con Dashboard Analítico

Aplicación web full-stack que permite registrar ingresos y gastos por categoría, visualizar el ahorro, analizar tendencias mensuales, **predecir el gasto del próximo mes** con Machine Learning y **detectar anomalías** en los movimientos financieros.

## 📋 Tabla de Contenidos
- [Tecnologías](#-tecnologías)
- [Arquitectura](#-arquitectura)
- [Funcionalidades](#-funcionalidades)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Requisitos Previos](#-requisitos-previos)
- [Configuración de la Base de Datos](#-configuración-de-la-base-de-datos)
- [Ejecución del Backend](#-ejecución-del-backend)
- [Abrir la Aplicación](#-abrir-la-aplicación)
- [Especificación de la API REST](#-especificación-de-la-api-rest)
- [Módulo Analítico (Machine Learning)](#-módulo-analítico-machine-learning)
- [Posibles Errores](#-posibles-errores)

---

## 🚀 Tecnologías

| Capa | Tecnología |
|---|---|
| Frontend | HTML5, CSS3, JavaScript (fetch), Chart.js |
| Backend | Python, FastAPI, Uvicorn |
| Datos / Análisis | MySQL, Pandas, Scikit-learn |
| Seguridad | bcrypt (hash de contraseñas) + JWT (tokens de sesión) |

> Compatible con **Python 3.14+**. Las dependencias se instalan con las últimas versiones estables.

---

## 🏗️ Arquitectura

```text
[ Frontend: HTML/CSS/JS + Chart.js ]
              |  fetch() / JSON (mismo origen)
              v
[ Backend/API: Python (FastAPI) ]
              |  mysql-connector-python
              v
[ Base de Datos: MySQL ]
              |
              v
[ Módulo Analítico: Pandas + Scikit-learn ]
              |  (resultados en JSON)
              v
[ Frontend: Dashboard con gráficos ]
```

*El frontend se sirve desde el propio backend (mismo origen), por lo que no hay problemas de CORS. Basta con abrir `http://127.0.0.1:8000`.*

---

## ✨ Funcionalidades

- **Inicio de sesión y registro:** cada usuario crea su cuenta y accede con correo y contraseña. Cada usuario ve **solo sus propios** datos (categorías y movimientos aislados).
- Al **registrarse**, se crean automáticamente categorías por defecto (Salario, Alimentación, Transporte, etc.).
- **KPIs:** Total de ingresos, total de gastos, balance (ahorro) y porcentaje de ahorro.
- **Predicción:** Gasto estimado del próximo mes mediante **regresión lineal**.
- **Anomalías:** Alertas sobre movimientos que se desvían estadísticamente del patrón histórico (Z-score).
- **Gráficos interactivos (Chart.js):**
  - Dona: distribución de gastos por categoría.
  - Líneas: tendencia mensual de ingresos vs. gastos.
- **CRUD de movimientos:** crear, listar (con filtros por fecha y categoría), editar y eliminar.
- **Gestión de categorías:** crear y listar categorías de ingreso/gasto.
- **Diseño responsive** y moderno.

---

## 📁 Estructura del Proyecto

```text
finanzas-personales/
├── backend/
│   ├── app.py            # API REST (FastAPI) - rutas por módulo
│   ├── analitica.py      # Módulo ML (predicción y anomalías)
│   ├── database.py       # Configuración de la conexión MySQL
│   └── requirements.txt  # Dependencias Python
├── database/
│   ├── schema.sql        # DDL: creación de tablas e índices
│   └── seed.sql          # DML: datos de prueba (seed ampliado)
├── frontend/
│   ├── index.html        # Dashboard principal (requiere sesión)
│   ├── login.html        # Inicio de sesión / registro
│   ├── css/
│   │   └── style.css     # Estilos (diseño responsive)
│   └── js/
│       ├── auth.js       # Gestión de sesión (login, registro, logout)
│       ├── api.js        # Cliente fetch / llamadas al backend
│       ├── charts.js     # Gráficos Chart.js
│       ├── forms.js      # Formularios y tabla de movimientos
│       └── app.js        # Carga inicial y refresco del dashboard
├── .gitignore
└── README.md
```

---

## ✅ Requisitos Previos

- [Python 3.9+](https://www.python.org/downloads/) (probado con 3.14)
- [MySQL Server 8.0+](https://dev.mysql.com/downloads/mysql/) corriendo en `localhost:3306`
- Git (opcional)

---

## 🗄️ Configuración de la Base de Datos

1. Ejecuta el script de esquema en tu cliente MySQL (MySQL Workbench, línea de comandos, etc.):

   ```bash
   mysql -u root -p < database/schema.sql
   ```

2. (Opcional) Carga los datos de prueba:

   ```bash
   mysql -u root -p < database/seed.sql
   ```

3. Verifica las credenciales de conexión en **`backend/database.py`**:

   ```python
   DB_CONFIG = {
       "host": "localhost",
       "port": 3306,
       "user": "root",
       "password": "",
       "database": "finanzas_personales"
   }
   ```

   Cambia `user` y `password` si tu servidor MySQL usa otras credenciales.

---

## ⚙️ Ejecución del Backend

1. Crea y activa el entorno virtual (dentro de `backend/`):

   ```bash
   cd backend
   python -m venv venv

   # En Windows:
   venv\Scripts\activate
   # En Linux / macOS:
   source venv/bin/activate
   ```

2. Instala las dependencias:

   ```bash
   pip install -r requirements.txt
   ```

3. Inicia el servidor:

   ```bash
   uvicorn app:app --reload
   ```

   La API arrancará en `http://127.0.0.1:8000` (con `--reload` se recarga sola al guardar cambios).

---

## 🌐 Abrir la Aplicación

Abre el navegador en:

```
http://127.0.0.1:8000
```

Al entrar verás la **pantalla de inicio de sesión**:

- **Inicia sesión** con un usuario existente.
- **Regístrate** para crear una cuenta nueva (se crean categorías por defecto).

### Usuario de prueba

Con el seed cargado, puedes entrar como:

| Correo | Contraseña |
|---|---|
| `ana@example.com` | `clave1234` |

La documentación interactiva de la API está disponible en:

```
http://127.0.0.1:8000/docs
```

> **Nota:** para cerrar sesión usa el botón **"Salir"** en la esquina superior derecha del dashboard.

---

## 📡 Especificación de la API REST

> **Autenticación:** salvo `/api/usuarios` (registro) y `/api/auth/login`, todos los endpoints requieren un token JWT en la cabecera `Authorization: Bearer <token>`. El token (12h de validez) se obtiene al iniciar sesión o registrarse, y protege los datos de cada usuario: un usuario solo puede acceder a **sus propios** categorías y movimientos (se verifica el `id_usuario` del token). Si el token expira o es inválido se devuelve `401`.

| Método | Endpoint | Descripción |
|---|---|---|
| `POST` | `/api/usuarios` | Registrar un nuevo usuario (hash bcrypt + categorías por defecto) |
| `POST` | `/api/auth/login` | Iniciar sesión: verifica correo y contraseña |
| `POST` | `/api/categorias` | Crear una categoría |
| `GET` | `/api/categorias?id_usuario=` | Listar categorías de un usuario |
| `POST` | `/api/movimientos` | Registrar un ingreso/gasto |
| `GET` | `/api/movimientos?id_usuario=&desde=&hasta=&categoria=` | Listar movimientos con filtros |
| `PUT` | `/api/movimientos/{id}` | Actualizar un movimiento |
| `DELETE` | `/api/movimientos/{id}` | Eliminar un movimiento |
| `GET` | `/api/resumen?id_usuario=&mes=` | Totales: ingresos, gastos y balance |
| `GET` | `/api/graficos/distribucion?id_usuario=` | Gasto por categoría (dona) |
| `GET` | `/api/graficos/tendencia?id_usuario=` | Tendencia mensual ingresos vs gastos (líneas) |
| `GET` | `/api/analitica/prediccion?id_usuario=` | Predicción del gasto del próximo mes |
| `GET` | `/api/analitica/anomalias?id_usuario=` | Movimientos anómalos detectados |

**Ejemplo – registrar un movimiento:**

```json
POST /api/movimientos
{
  "id_usuario": 1,
  "id_categoria": 3,
  "tipo": "gasto",
  "monto": 85000,
  "fecha": "2026-08-20",
  "descripcion": "Mercado quincenal"
}
```

**Ejemplo – respuesta de `GET /api/analitica/prediccion?id_usuario=1`:**

```json
{
  "id_usuario": 1,
  "prediccion": 1180000,
  "confianza": "media",
  "razon": "Calculado con Regresión Lineal (5 meses procesados)"
}
```

---

## 🧠 Módulo Analítico (Machine Learning)

Procesa los registros con **Pandas** y **Scikit-learn**:

1. **Predicción con Regresión Lineal** (`LinearRegression`): agrupa los gastos por mes y estima el gasto acumulado del siguiente mes a partir de la tendencia temporal. Si hay menos de 2 meses de datos, usa un promedio simple.
2. **Detección de Anomalías (Z-score):** compara cada gasto con el promedio y la desviación estándar de su categoría. Si `|Z| > 1.5`, el movimiento se marca como anomalía.

---

## 🐛 Posibles Errores

- **`No se pudo conectar con el backend`:** verifica que uvicorn esté ejecutándose y que la base de datos esté creada.
- **Errores de conexión MySQL:** revisa `backend/database.py` (usuario/contraseña).
- **Dependencias que fallan en Python viejo:** asegúrate de actualizar pip y usar Python 3.9+ (el `requirements.txt` instala versiones actuales). Incluye `PyJWT` para la autenticación por tokens.
- **`__pycache__`:** son archivos de caché de Python que se generan automáticamente; no requieren acción y están ignorados en git.
- **Seguridad (producción):** cambia la variable de entorno `FINANZAS_SECRET` por un secreto robusto; en desarrollo se usa una clave por defecto.

---

> Proyecto de aula · Finanzas Personales con Dashboard Analítico
