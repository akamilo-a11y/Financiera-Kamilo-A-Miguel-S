"""
Capa de Acceso a Datos - Conexión con PostgreSQL (Supabase).
"""
import os
import psycopg2

DB_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres.jzsjfmtyutlzanddrvdn:Kamilo255005@aws-0-us-east-2.pooler.supabase.com:5432/postgres"
)


def get_db():
    """Retorna una conexión a PostgreSQL con el esquema finanzas_personales activo."""
    conn = psycopg2.connect(DB_URL)
    conn.cursor().execute("SET search_path TO finanzas_personales, public")
    conn.commit()
    return conn
