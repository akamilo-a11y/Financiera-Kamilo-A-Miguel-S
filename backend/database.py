"""
Capa de Acceso a Datos - Conexión con MySQL.
Ajusta credenciales si tu servidor usa otro usuario/contraseña.
"""
import mysql.connector

DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "",
    "database": "finanzas_personales"
}


def get_db():
    """Retorna una conexión a MySQL."""
    return mysql.connector.connect(**DB_CONFIG)
