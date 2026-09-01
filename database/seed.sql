-- Usuario de prueba (contraseña: "clave1234" hasheada con bcrypt)
INSERT INTO usuarios (nombre, correo, contrasena_hash)
VALUES ('Ana Torres', 'ana@example.com', '$2b$12$wgZLhNJa6yELmHkfjGRIM.MPnP6SnfjlH7n7DH4o4XSi6kkr8645u');

-- Categorías del usuario 1 (2 de ingreso + 6 de gasto)
INSERT INTO categorias (nombre, tipo, id_usuario) VALUES
('Salario', 'ingreso', 1),
('Freelance', 'ingreso', 1),
('Alimentación', 'gasto', 1),
('Transporte', 'gasto', 1),
('Entretenimiento', 'gasto', 1),
('Salud', 'gasto', 1),
('Servicios Públicos', 'gasto', 1),
('Educación', 'gasto', 1);

-- Registros de junio a octubre 2026
INSERT INTO ingresos_gastos (id_usuario, id_categoria, tipo, monto, fecha, descripcion) VALUES
-- Junio 2026
(1, 1, 'ingreso', 2500000.00, '2026-06-01', 'Pago mensual'),
(1, 2, 'ingreso', 400000.00, '2026-06-12', 'Proyecto freelance'),
(1, 3, 'gasto', 320000.00, '2026-06-05', 'Mercado del mes'),
(1, 3, 'gasto', 150000.00, '2026-06-18', 'Mercado quincenal'),
(1, 4, 'gasto', 90000.00,  '2026-06-07', 'Transporte semanal'),
(1, 5, 'gasto', 150000.00, '2026-06-10', 'Cine y salidas'),
(1, 7, 'gasto', 210000.00, '2026-06-15', 'Energía y agua'),
(1, 8, 'gasto', 250000.00, '2026-06-20', 'Curso online'),
-- Julio 2026
(1, 1, 'ingreso', 2500000.00, '2026-07-01', 'Pago mensual'),
(1, 2, 'ingreso', 350000.00, '2026-07-14', 'Proyecto freelance'),
(1, 3, 'gasto', 300000.00, '2026-07-04', 'Mercado del mes'),
(1, 3, 'gasto', 140000.00, '2026-07-19', 'Mercado quincenal'),
(1, 4, 'gasto', 95000.00,  '2026-07-08', 'Transporte semanal'),
(1, 5, 'gasto', 120000.00, '2026-07-11', 'Salidas'),
(1, 6, 'gasto', 800000.00, '2026-07-15', 'Consulta médica de urgencia'),
(1, 7, 'gasto', 205000.00, '2026-07-16', 'Energía y agua'),
-- Agosto 2026
(1, 1, 'ingreso', 2600000.00, '2026-08-01', 'Pago mensual'),
(1, 2, 'ingreso', 320000.00, '2026-08-10', 'Proyecto freelance'),
(1, 3, 'gasto', 310000.00, '2026-08-05', 'Mercado del mes'),
(1, 3, 'gasto', 145000.00, '2026-08-20', 'Mercado quincenal'),
(1, 4, 'gasto', 88000.00,  '2026-08-09', 'Transporte semanal'),
(1, 5, 'gasto', 130000.00, '2026-08-14', 'Concierto'),
(1, 7, 'gasto', 215000.00, '2026-08-17', 'Energía y agua'),
(1, 8, 'gasto', 200000.00, '2026-08-22', 'Libros de estudio'),