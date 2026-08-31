"""
API REST - Finanzas Personales (FastAPI)
Arquitectura por capas: Rutas -> Lógica de Negocio -> Acceso a Datos.
Sive también el frontend estático desde /frontend.
Ejecutar:  uvicorn app:app --reload  (puerto 8000)
"""
import os
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

import bcrypt
import jwt
import mysql.connector
import pandas as pd

from database import get_db
from analitica import cargar_datos, predecir_gasto_proximo_mes, detectar_anomalias

# ------------------------- Autenticación JWT -------------------------

# En producción usa una variable de entorno; esto es para desarrollo local.
SECRET_KEY = os.environ.get("FINANZAS_SECRET", "clave-secreta-de-desarrollo-cambiar")
ALGORITHM = "HS256"
TOKEN_EXPIRACION_HORAS = 12

seguridad = HTTPBearer(auto_error=False)


def crear_token(id_usuario: int) -> str:
    """Genera un JWT firmado con el id_usuario y fecha de expiración."""
    payload = {
        "sub": str(id_usuario),
        "exp": datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRACION_HORAS),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verificar_token(
    credenciales: HTTPAuthorizationCredentials = Depends(seguridad),
) -> int:
    """Valida el token Bearer y devuelve el id_usuario autenticado."""
    if credenciales is None:
        raise HTTPException(status_code=401, detail="Autenticación requerida")
    try:
        payload = jwt.decode(credenciales.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        return int(payload["sub"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Sesión expirada, inicie sesión de nuevo")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")


def autorizar_usuario(id_usuario_solicitado: int, id_usuario_autenticado: int) -> None:
    """Lanza 403 si el usuario del token no es dueño del recurso solicitado."""
    if id_usuario_solicitado != id_usuario_autenticado:
        raise HTTPException(
            status_code=403,
            detail="No tienes permiso para acceder a los datos de otro usuario",
        )

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "..", "frontend")

app = FastAPI(title="Finanzas Personales API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------- Schemas (Pydantic) -------------------------

class UsuarioCreate(BaseModel):
    nombre: str = Field(..., min_length=1)
    correo: str
    contrasena: str = Field(..., min_length=8)


class LoginSchema(BaseModel):
    correo: str
    contrasena: str


class CategoriaCreate(BaseModel):
    nombre: str = Field(..., min_length=1)
    tipo: str
    id_usuario: int


class MovimientoCreate(BaseModel):
    id_usuario: int
    id_categoria: int
    tipo: str
    monto: float = Field(..., gt=0)
    fecha: date
    descripcion: Optional[str] = None


class MovimientoUpdate(BaseModel):
    id_categoria: Optional[int] = None
    tipo: Optional[str] = None
    monto: Optional[float] = Field(None, gt=0)
    fecha: Optional[date] = None
    descripcion: Optional[str] = None


# ------------------------- Módulo: Auth -------------------------

# Categorías por defecto que se crean al registrar un nuevo usuario
CATEGORIAS_DEFECTO = [
    ("Salario", "ingreso"),
    ("Freelance", "ingreso"),
    ("Alimentación", "gasto"),
    ("Transporte", "gasto"),
    ("Entretenimiento", "gasto"),
    ("Salud", "gasto"),
    ("Servicios Públicos", "gasto"),
]


@app.post("/api/usuarios", status_code=201)
def crear_usuario(u: UsuarioCreate):
    """RF01: Registrar un nuevo usuario (hash bcrypt) y crear categorías por defecto."""
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("SELECT id_usuario FROM usuarios WHERE correo = %s", (u.correo,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="El correo ya está registrado")

        hash_pw = bcrypt.hashpw(u.contrasena.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        cursor.execute(
            "INSERT INTO usuarios (nombre, correo, contrasena_hash) VALUES (%s, %s, %s)",
            (u.nombre, u.correo, hash_pw)
        )
        id_usuario = cursor.lastrowid

        # Crear categorías por defecto para el nuevo usuario
        for nombre, tipo in CATEGORIAS_DEFECTO:
            cursor.execute(
                "INSERT INTO categorias (nombre, tipo, id_usuario) VALUES (%s, %s, %s)",
                (nombre, tipo, id_usuario)
            )
        db.commit()
        return {"id_usuario": id_usuario, "token": crear_token(id_usuario), "mensaje": "Usuario creado con éxito"}
    except HTTPException:
        db.rollback()
        raise
    except mysql.connector.Error as err:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(err))
    finally:
        db.close()


@app.post("/api/auth/login")
def iniciar_sesion(l: LoginSchema):
    """Verifica correo/contraseña y devuelve los datos del usuario autenticado."""
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT id_usuario, nombre, correo, contrasena_hash FROM usuarios WHERE correo = %s",
            (l.correo,)
        )
        usuario = cursor.fetchone()
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        if not bcrypt.checkpw(l.contrasena.encode("utf-8"), usuario["contrasena_hash"].encode("utf-8")):
            raise HTTPException(status_code=401, detail="Contraseña incorrecta")

        return {
            "id_usuario": usuario["id_usuario"],
            "nombre": usuario["nombre"],
            "correo": usuario["correo"],
            "token": crear_token(usuario["id_usuario"]),
            "mensaje": "Inicio de sesión exitoso"
        }
    except HTTPException:
        raise
    finally:
        db.close()


# ------------------------- Módulo: Categorías -------------------------

@app.post("/api/categorias", status_code=201)
def crear_categoria(c: CategoriaCreate, id_usuario_autenticado: int = Depends(verificar_token)):
    """RF02: Crear una categoría."""
    autorizar_usuario(c.id_usuario, id_usuario_autenticado)
    if c.tipo not in ("ingreso", "gasto"):
        raise HTTPException(status_code=422, detail="El tipo debe ser 'ingreso' o 'gasto'")
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(
            "INSERT INTO categorias (nombre, tipo, id_usuario) VALUES (%s, %s, %s)",
            (c.nombre, c.tipo, c.id_usuario)
        )
        db.commit()
        return {"id_categoria": cursor.lastrowid, "mensaje": "Categoría creada"}
    except mysql.connector.Error as err:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(err))
    finally:
        db.close()


@app.get("/api/categorias")
def listar_categorias(id_usuario: int, id_usuario_autenticado: int = Depends(verificar_token)):
    """RF02: Obtener categorías asociadas a un usuario."""
    autorizar_usuario(id_usuario, id_usuario_autenticado)
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM categorias WHERE id_usuario = %s ORDER BY nombre",
        (id_usuario,)
    )
    res = cursor.fetchall()
    db.close()
    return res


class CategoriaUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=1)
    tipo: Optional[str] = None


@app.put("/api/categorias/{id_categoria}")
def actualizar_categoria(id_categoria: int, c: CategoriaUpdate, id_usuario_autenticado: int = Depends(verificar_token)):
    """RF02: Actualizar una categoría."""
    if c.tipo is not None and c.tipo not in ("ingreso", "gasto"):
        raise HTTPException(status_code=422, detail="El tipo debe ser 'ingreso' o 'gasto'")

    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(
            "SELECT id_categoria FROM categorias WHERE id_categoria = %s AND id_usuario = %s",
            (id_categoria, id_usuario_autenticado)
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Categoría no encontrada")

        campos = []
        params = []
        if c.nombre is not None:
            campos.append("nombre = %s")
            params.append(c.nombre)
        if c.tipo is not None:
            campos.append("tipo = %s")
            params.append(c.tipo)

        if not campos:
            raise HTTPException(status_code=422, detail="No hay campos para actualizar")

        params.append(id_categoria)
        cursor.execute(
            f"UPDATE categorias SET {', '.join(campos)} WHERE id_categoria = %s",
            tuple(params)
        )
        db.commit()
        return {"id_categoria": id_categoria, "mensaje": "Categoría actualizada"}
    except HTTPException:
        db.rollback()
        raise
    except mysql.connector.Error as err:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(err))
    finally:
        db.close()


@app.delete("/api/categorias/{id_categoria}", status_code=200)
def eliminar_categoria(id_categoria: int, id_usuario_autenticado: int = Depends(verificar_token)):
    """RF02: Eliminar una categoría."""
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(
            "SELECT id_categoria FROM categorias WHERE id_categoria = %s AND id_usuario = %s",
            (id_categoria, id_usuario_autenticado)
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Categoría no encontrada")

        # Evitar eliminar categorías con movimientos asociados (FK RESTRICT)
        cursor.execute(
            "SELECT id_movimiento FROM ingresos_gastos WHERE id_categoria = %s LIMIT 1",
            (id_categoria,)
        )
        if cursor.fetchone():
            raise HTTPException(
                status_code=400,
                detail="No se puede eliminar: la categoría tiene movimientos asociados"
            )

        cursor.execute(
            "DELETE FROM categorias WHERE id_categoria = %s",
            (id_categoria,)
        )
        db.commit()
        return {"id_categoria": id_categoria, "mensaje": "Categoría eliminada"}
    except HTTPException:
        db.rollback()
        raise
    except mysql.connector.Error as err:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(err))
    finally:
        db.close()


# ------------------------- Módulo: Movimientos -------------------------

@app.post("/api/movimientos", status_code=201)
def registrar_movimiento(m: MovimientoCreate, id_usuario_autenticado: int = Depends(verificar_token)):
    """RF03: Registrar un ingreso o gasto."""
    autorizar_usuario(m.id_usuario, id_usuario_autenticado)
    db = get_db()
    cursor = db.cursor()
    try:
        # Verificar que la categoría pertenece al usuario autenticado
        cursor.execute(
            "SELECT id_categoria FROM categorias WHERE id_categoria = %s AND id_usuario = %s",
            (m.id_categoria, id_usuario_autenticado)
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Categoría no encontrada para este usuario")
        cursor.execute(
            """INSERT INTO ingresos_gastos
               (id_usuario, id_categoria, tipo, monto, fecha, descripcion)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (m.id_usuario, m.id_categoria, m.tipo, m.monto, m.fecha, m.descripcion)
        )
        db.commit()
        return {"id_movimiento": cursor.lastrowid, "mensaje": "Movimiento registrado"}
    except mysql.connector.Error as err:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(err))
    finally:
        db.close()


@app.get("/api/movimientos")
def listar_movimientos(
    id_usuario: int,
    desde: Optional[date] = None,
    hasta: Optional[date] = None,
    categoria: Optional[int] = None,
    id_usuario_autenticado: int = Depends(verificar_token),
):
    """RF04: Listar movimientos con filtros por rango de fechas y categoría."""
    autorizar_usuario(id_usuario, id_usuario_autenticado)
    db = get_db()
    cursor = db.cursor(dictionary=True)
    query = (
        "SELECT m.*, c.nombre AS categoria, c.tipo AS tipo_categoria "
        "FROM ingresos_gastos m "
        "JOIN categorias c ON m.id_categoria = c.id_categoria "
        "WHERE m.id_usuario = %s"
    )
    params = [id_usuario_autenticado]

    if desde:
        query += " AND m.fecha >= %s"
        params.append(desde)
    if hasta:
        query += " AND m.fecha <= %s"
        params.append(hasta)
    if categoria:
        query += " AND m.id_categoria = %s"
        params.append(categoria)

    query += " ORDER BY m.fecha DESC, m.id_movimiento DESC"
    cursor.execute(query, tuple(params))
    res = cursor.fetchall()
    db.close()
    return res


@app.put("/api/movimientos/{id_movimiento}")
def actualizar_movimiento(id_movimiento: int, m: MovimientoUpdate, id_usuario_autenticado: int = Depends(verificar_token)):
    """RF03: Actualizar un movimiento existente."""
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(
            "SELECT id_movimiento, id_categoria FROM ingresos_gastos WHERE id_movimiento = %s AND id_usuario = %s",
            (id_movimiento, id_usuario_autenticado)
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Movimiento no encontrado")

        # Si se cambia la categoría, verificar que pertenezca al usuario
        if m.id_categoria is not None:
            cursor.execute(
                "SELECT id_categoria FROM categorias WHERE id_categoria = %s AND id_usuario = %s",
                (m.id_categoria, id_usuario_autenticado)
            )
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Categoría no encontrada para este usuario")

        campos = []
        params = []
        for campo in ("id_categoria", "tipo", "monto", "fecha", "descripcion"):
            valor = getattr(m, campo)
            if valor is not None:
                campos.append(f"{campo} = %s")
                params.append(valor)

        if not campos:
            raise HTTPException(status_code=422, detail="No hay campos para actualizar")

        params.append(id_movimiento)
        cursor.execute(
            f"UPDATE ingresos_gastos SET {', '.join(campos)} WHERE id_movimiento = %s",
            tuple(params)
        )
        db.commit()
        return {"id_movimiento": id_movimiento, "mensaje": "Movimiento actualizado"}
    except HTTPException:
        db.rollback()
        raise
    except mysql.connector.Error as err:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(err))
    finally:
        db.close()


@app.delete("/api/movimientos/{id_movimiento}", status_code=200)
def eliminar_movimiento(id_movimiento: int, id_usuario_autenticado: int = Depends(verificar_token)):
    """RF03: Eliminar un movimiento por ID."""
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(
            "DELETE FROM ingresos_gastos WHERE id_movimiento = %s AND id_usuario = %s",
            (id_movimiento, id_usuario_autenticado)
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Movimiento no encontrado")
        db.commit()
        return {"id_movimiento": id_movimiento, "mensaje": "Movimiento eliminado"}
    except HTTPException:
        db.rollback()
        raise
    finally:
        db.close()


# ------------------------- Módulo: Resumen / KPIs -------------------------

@app.get("/api/resumen")
def obtener_resumen(
    id_usuario: int,
    mes: Optional[str] = None,
    id_usuario_autenticado: int = Depends(verificar_token),
):
    """RF05: Total ingresos, gastos y balance neto (con filtro opcional por mes YYYY-MM)."""
    autorizar_usuario(id_usuario, id_usuario_autenticado)
    db = get_db()
    cursor = db.cursor(dictionary=True)
    query = """
        SELECT
            SUM(CASE WHEN tipo = 'ingreso' THEN monto ELSE 0 END) AS total_ingresos,
            SUM(CASE WHEN tipo = 'gasto' THEN monto ELSE 0 END) AS total_gastos
        FROM ingresos_gastos
        WHERE id_usuario = %s
    """
    params = [id_usuario_autenticado]
    if mes:
        query += " AND DATE_FORMAT(fecha, '%Y-%m') = %s"
        params.append(mes)

    cursor.execute(query, tuple(params))
    data = cursor.fetchone()
    db.close()

    ingresos = float(data['total_ingresos'] or 0)
    gastos = float(data['total_gastos'] or 0)
    balance = ingresos - gastos

    return {
        "total_ingresos": ingresos,
        "total_gastos": gastos,
        "balance": balance,
        "porcentaje_ahorro": round((balance / ingresos * 100), 2) if ingresos > 0 else 0
    }


@app.get("/api/graficos/distribucion")
def distribucion_por_categoria(id_usuario: int, id_usuario_autenticado: int = Depends(verificar_token)):
    """RF06: Distribución de gastos por categoría (para el gráfico de dona)."""
    autorizar_usuario(id_usuario, id_usuario_autenticado)
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        """SELECT c.nombre AS categoria, SUM(m.monto) AS total
           FROM ingresos_gastos m
           JOIN categorias c ON m.id_categoria = c.id_categoria
           WHERE m.id_usuario = %s AND m.tipo = 'gasto'
           GROUP BY c.id_categoria, c.nombre
           ORDER BY total DESC""",
        (id_usuario_autenticado,)
    )
    res = cursor.fetchall()
    db.close()
    return {"labels": [r['categoria'] for r in res],
            "data": [float(r['total'] or 0) for r in res]}


@app.get("/api/graficos/tendencia")
def tendencia_mensual(id_usuario: int, id_usuario_autenticado: int = Depends(verificar_token)):
    """RF07: Tendencia de ingresos vs gastos por mes (para el gráfico de líneas)."""
    autorizar_usuario(id_usuario, id_usuario_autenticado)
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        """SELECT DATE_FORMAT(fecha, '%Y-%m') AS mes,
                  tipo,
                  SUM(monto) AS total
           FROM ingresos_gastos
           WHERE id_usuario = %s
           GROUP BY mes, tipo
           ORDER BY mes""",
        (id_usuario_autenticado,)
    )
    res = cursor.fetchall()
    db.close()

    meses = sorted({r['mes'] for r in res})
    ingresos_por_mes = {r['mes']: float(r['total']) for r in res if r['tipo'] == 'ingreso'}
    gastos_por_mes = {r['mes']: float(r['total']) for r in res if r['tipo'] == 'gasto'}

    return {
        "labels": meses,
        "ingresos": [ingresos_por_mes.get(m, 0) for m in meses],
        "gastos": [gastos_por_mes.get(m, 0) for m in meses]
    }


# ------------------------- Módulo: Analítico (ML) -------------------------

@app.get("/api/analitica/prediccion")
def api_prediccion(id_usuario: int, mes: Optional[str] = None, id_usuario_autenticado: int = Depends(verificar_token)):
    """RF08: Predicción del gasto del próximo mes (Regresión Lineal)."""
    autorizar_usuario(id_usuario, id_usuario_autenticado)
    db = get_db()
    try:
        df = cargar_datos(db, id_usuario_autenticado)
        resultado = predecir_gasto_proximo_mes(df)
        return {"id_usuario": id_usuario_autenticado, **resultado}
    finally:
        db.close()


@app.get("/api/analitica/anomalias")
def api_anomalias(id_usuario: int, id_usuario_autenticado: int = Depends(verificar_token)):
    """RF09: Detectar anomalías en consumos fuera del patrón histórico."""
    autorizar_usuario(id_usuario, id_usuario_autenticado)
    db = get_db()
    try:
        df = cargar_datos(db, id_usuario_autenticado)
        anomalias = detectar_anomalias(df)
        return {"id_usuario": id_usuario_autenticado, "anomalias": anomalias}
    finally:
        db.close()


# ------------------------- Frontend estático -------------------------

# Archivos servidos desde /frontend (mismo origen -> sin bloqueos CORS)
app.mount("/css", StaticFiles(directory=os.path.join(FRONTEND_DIR, "css")), name="css")
app.mount("/js", StaticFiles(directory=os.path.join(FRONTEND_DIR, "js")), name="js")


@app.get("/")
def index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


@app.get("/login")
def login_page():
    return FileResponse(os.path.join(FRONTEND_DIR, "login.html"))
