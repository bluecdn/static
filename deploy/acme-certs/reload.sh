#!/usr/bin/env bash
# acme.sh 续期钩子:证书已由 --install-cert 写入 /etc/caddy/certs/,这里让 Caddy 重新加载。
# Caddy 配置为 auto_https off + 手工加载证书文件,必须 reload 才会读取新证书。
set -euo pipefail
CERT=/etc/caddy/certs/bluecdn.com.fullchain.pem
KEY=/etc/caddy/certs/bluecdn.com.key
chown caddy:caddy "$CERT" "$KEY" 2>/dev/null || true
chmod 644 "$CERT"; chmod 640 "$KEY"
/usr/bin/caddy reload --config /etc/caddy/Caddyfile --force
echo "[acme-reload] $(date -Is) Caddy 已重载,证书到期: $(openssl x509 -in "$CERT" -noout -enddate)"
