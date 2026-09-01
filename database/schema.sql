-- En Supabase no se usa CREATE DATABASE ni USE.
-- Si deseas organizar tus tablas en un esquema propio (opcional), creamos el esquema:
CREATE SCHEMA IF NOT EXISTS finanzas_personales;
SET search_path TO finanzas_personales, public;

-- 1. Tabla de Usuarios
CREATE TABLE usuarios (
    id_usuario      INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre          VARCHAR(100) NOT NULL,
    correo          VARCHAR(150) NOT NULL UNIQUE,
    contrasena_hash VARCHAR(255) NOT NULL,
    fecha_registro  TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_nombre_usuario CHECK (nombre <> ''),
    CONSTRAINT chk_correo_usuario CHECK (correo ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
    CONSTRAINT chk_contrasena_hash CHECK (CHAR_LENGTH(contrasena_hash) >= 8)
);

-- 2. Tipo Personalizado ENUM para Categorías y Movimientos
CREATE TYPE tipo_movimiento AS ENUM ('ingreso', 'gasto');

-- 3. Tabla de Categorías
CREATE TABLE categorias (
    id_categoria    INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre          VARCHAR(50) NOT NULL,
    tipo            tipo_movimiento NOT NULL,
    id_usuario      INT NOT NULL,
    CONSTRAINT chk_nombre_categoria CHECK (nombre <> ''),
    CONSTRAINT fk_categoria_usuario FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario) ON DELETE CASCADE
);

-- 4. Tabla de Ingresos y Gastos
CREATE TABLE ingresos_gastos (
    id_movimiento   INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_usuario      INT NOT NULL,
    id_categoria    INT NOT NULL,
    tipo            tipo_movimiento NOT NULL,
    monto           NUMERIC(12,2) NOT NULL,
    fecha           DATE NOT NULL,
    descripcion     VARCHAR(255),
    fecha_creacion  TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_monto_positivo CHECK (monto > 0),
    CONSTRAINT fk_movimiento_usuario FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario) ON DELETE CASCADE,
    CONSTRAINT fk_movimiento_categoria FOREIGN KEY (id_categoria) REFERENCES categorias(id_categoria) ON DELETE RESTRICT
);

-- 5. Índices
CREATE INDEX idx_mov_usuario_fecha ON ingresos_gastos (id_usuario, fecha);
CREATE INDEX idx_mov_categoria ON ingresos_gastos (id_categoria);