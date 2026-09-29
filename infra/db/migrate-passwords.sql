-- Administrador LOCAL, después de un respaldo. No borra filas ni tickets.
ALTER TABLE mesa_ayuda.usuarios MODIFY password_hash VARCHAR(255) NOT NULL;
-- Identifica cuentas que requieren nueva contraseña, sin imprimir los hashes.
SELECT id, username FROM mesa_ayuda.usuarios
WHERE password_hash NOT LIKE '$argon2%';
