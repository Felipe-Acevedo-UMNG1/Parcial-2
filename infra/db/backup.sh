#!/usr/bin/env bash
# Configurar AGE_RECIPIENT en /etc/mesa-backup.env (clave PUBLICA).
# /root/.my.cnf debe contener las credenciales del usuario de respaldo,
# distinto de app_mesa, con permisos 0600 y sin estar en el repositorio.
set -euo pipefail
umask 077
source /etc/mesa-backup.env
: "${AGE_RECIPIENT:?Configure la clave publica de age}"
install -d -m 0700 /var/backups/mesa_ayuda
out="/var/backups/mesa_ayuda/$(date -u +%Y%m%dT%H%M%SZ).sql.age"
trap 'rm -f "$out.tmp"' EXIT
mysqldump --defaults-extra-file=/root/.my.cnf --single-transaction \
  --skip-lock-tables --no-tablespaces mesa_ayuda \
  | age -r "$AGE_RECIPIENT" > "$out.tmp"
mv "$out.tmp" "$out"
echo "Respaldo cifrado: $out"
