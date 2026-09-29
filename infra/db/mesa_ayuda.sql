-- Ejecutar una sola vez en sg-db como administrador local, antes del backend.
CREATE DATABASE IF NOT EXISTS mesa_ayuda CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE mesa_ayuda;
CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(120) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    rol VARCHAR(20) NOT NULL DEFAULT 'usuario',
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS tickets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    titulo VARCHAR(150) NOT NULL,
    descripcion TEXT NOT NULL,
    prioridad VARCHAR(10) NOT NULL DEFAULT 'media',
    estado VARCHAR(20) NOT NULL DEFAULT 'abierto',
    usuario_id INT NOT NULL,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);
-- Para una instalación previa a la corrección, ejecutar después del respaldo:
-- ALTER TABLE mesa_ayuda.usuarios MODIFY password_hash VARCHAR(255) NOT NULL;
-- Las contraseñas MD5 heredadas deben restablecerse antes de permitir el login.
