#!/usr/bin/env bash
set -euo pipefail
: "${TAILSCALE_NODE_IP:?Configure /etc/examen-node.env}"
for ((attempt=0; attempt<60; attempt++)); do
  if ip -4 -o addr show dev tailscale0 2>/dev/null | awk '{print $4}' | cut -d/ -f1 | grep -Fxq "$TAILSCALE_NODE_IP"; then
    exit 0
  fi
  sleep 2
done
echo 'Tailscale no obtuvo la IP esperada; no se iniciará el servicio.' >&2
exit 1
