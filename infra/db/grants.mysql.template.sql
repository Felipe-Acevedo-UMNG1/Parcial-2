-- Ejecutar como administrador local. Sustituir las marcas en una copia LOCAL,
-- no subir la copia ni la salida del comando con contraseña a GitHub.
CREATE USER 'app_mesa'@'<IP_TAILSCALE_BACKEND>'
  IDENTIFIED WITH caching_sha2_password BY '<CLAVE_NUEVA>' REQUIRE SSL;
GRANT SELECT, INSERT, UPDATE, DELETE ON mesa_ayuda.*
  TO 'app_mesa'@'<IP_TAILSCALE_BACKEND>';
SHOW GRANTS FOR 'app_mesa'@'<IP_TAILSCALE_BACKEND>';
