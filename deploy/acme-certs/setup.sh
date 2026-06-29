#!/usr/bin/env bash
# 在服务器 B 上一次性配置：acme.sh 用 Cloudflare DNS 签发 Let's Encrypt 证书，
# 并在每次续期后自动推送到百度 CDN（reloadcmd）。acme.sh 自带 cron，60 天自动续。
#
# 用法:
#   cp certs.env.example certs.env   # 填好真实值
#   bash setup.sh
set -euo pipefail
cd "$(dirname "$0")"

[ -f certs.env ] || { echo "缺少 certs.env，请先 cp certs.env.example certs.env 并填值"; exit 1; }
# shellcheck disable=SC1091
source ./certs.env

HERE="$(pwd)"
CERT_DIR="/etc/acme-certs"
mkdir -p "$CERT_DIR"

# 1) 安装 acme.sh（已装则跳过）
if [ ! -d "$HOME/.acme.sh" ]; then
  curl -s https://get.acme.sh | sh -s email="admin@bluecdn.com"
fi
ACME="$HOME/.acme.sh/acme.sh"
"$ACME" --set-default-ca --server letsencrypt

for DOMAIN in $DOMAINS; do
  echo "==== $DOMAIN ===="
  KEY="$CERT_DIR/$DOMAIN.key"
  FULL="$CERT_DIR/$DOMAIN.fullchain.pem"

  # 2) DNS-01 签发（Cloudflare）
  "$ACME" --issue --dns dns_cf -d "$DOMAIN" || \
    [ "$?" = 2 ] # 退出码 2 = 证书还没到续期点，跳过，不算失败

  # 3) 安装证书 + 续期钩子：每次续期后自动把新证书推到百度 CDN
  "$ACME" --install-cert -d "$DOMAIN" \
    --key-file       "$KEY" \
    --fullchain-file "$FULL" \
    --reloadcmd      "cd '$HERE' && source ./certs.env && python3 push_baidu.py '$DOMAIN' '$FULL' '$KEY'"
done

echo "完成。acme.sh 已写入自动续期 cron；续期后会自动推送百度 CDN。"
echo "查看 cron:  crontab -l | grep acme"
echo "手动测试推送:  source certs.env && python3 push_baidu.py <domain> $CERT_DIR/<domain>.fullchain.pem $CERT_DIR/<domain>.key"
