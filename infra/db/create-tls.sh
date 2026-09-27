#!/usr/bin/env bash
# Uso EN sg-db: sudo bash infra/db/create-tls.sh IP_TAILSCALE_DB
# Primera instalación: no reemplaza certificados ni claves existentes.
set -euo pipefail
[[ $EUID -eq 0 && $# -eq 1 ]] || { echo 'Uso: sudo bash create-tls.sh IP_DB'; exit 1; }
python3 -c 'import ipaddress,sys; ipaddress.IPv4Address(sys.argv[1])' "$1"
[[ ! -e /etc/mysql/tls && ! -e /root/mesa-ca ]] || { echo 'Ya existe material TLS; revisar su renovación manualmente.'; exit 1; }
umask 077
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
openssl req -x509 -newkey rsa:3072 -nodes -days 365 -sha256 \
  -keyout "$work/ca-key.pem" -out "$work/ca.pem" -subj '/CN=Mesa Ayuda CA' \
  -addext 'basicConstraints=critical,CA:TRUE' -addext 'keyUsage=critical,keyCertSign,cRLSign'
openssl req -newkey rsa:3072 -nodes -sha256 -keyout "$work/server-key.pem" \
  -out "$work/server.csr" -subj "/CN=$1"
cat > "$work/server.ext" <<EOF
basicConstraints=critical,CA:FALSE
keyUsage=critical,digitalSignature,keyEncipherment
extendedKeyUsage=serverAuth
subjectAltName=IP:$1
EOF
openssl x509 -req -in "$work/server.csr" -CA "$work/ca.pem" -CAkey "$work/ca-key.pem" \
  -CAcreateserial -out "$work/server-cert.pem" -days 90 -sha256 -extfile "$work/server.ext"
install -d -m 0750 -o root -g mysql /etc/mysql/tls
install -m 0644 "$work/ca.pem" "$work/server-cert.pem" /etc/mysql/tls/
install -m 0640 -o root -g mysql "$work/server-key.pem" /etc/mysql/tls/
install -d -m 0700 /root/mesa-ca
install -m 0600 "$work/ca-key.pem" /root/mesa-ca/
echo 'Copie SOLO /etc/mysql/tls/ca.pem al backend. Mantenga la clave CA fuera de Git.'
