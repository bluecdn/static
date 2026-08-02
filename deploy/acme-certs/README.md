# 证书续期（acme.sh）

> **2026-08-02 现状核对：本目录原先描述的「Cloudflare DNS-01 签发 + 推送百度 CDN」流程与线上实际情况已完全不符。**
> 下面先写实际情况，再写待办。历史脚本（`setup.sh` / `push_baidu.py` / `push_bunny.py`）暂时保留，但**不要照着旧步骤跑**。

## 线上实际情况

CDN 早已从「百度 + Cloudflare 双线」换成**阿里云 ESA 单边缘**，源站也从上海/硅谷双机换成**芬兰 Hetzner 单机**。
因此 `push_baidu.py` / `push_bunny.py` 目前**没有使用场景**。

源站 `/etc/caddy/Caddyfile` 是 `auto_https off`，Caddy 不自签、不自动续，只加载文件：

| 域名 | 证书文件 | 签发方 | 到期 |
|---|---|---|---|
| `bluecdn.com` + `*.bluecdn.com` | `/etc/caddy/certs/bluecdn.com.{fullchain.pem,key}` | acme.sh → Let's Encrypt | 2026-09-28 |
| `*.yite.net` | `/etc/caddy/certs/yite.net/` | 商业证书 | 2027-03-01 |
| `markitdown.io` | `/etc/caddy/certs/markitdown.io/` | — | 2028-10-28 |
| `mapcdn.io` | `/etc/caddy/certs/mapcdn.io.*` | Cloudflare Origin CA | 2041-06-27 |

只有第一行需要 acme.sh 续期。

## 已修复（2026-08-02）

1. **没有任何 cron / systemd timer 会触发 acme.sh** → 已执行 `acme.sh --install-cronjob`，
   现在 `crontab -l` 有 `4 8 * * * "/root/.acme.sh"/acme.sh --cron --home "/root/.acme.sh"`。
2. **续期钩子指向的脚本根本不存在** —— 证书 conf 里 `Le_ReloadCmd` 是 `bash /etc/acme-certs/reload.sh`，
   但 `/etc/acme-certs/` 整个目录都没有。就算续期成功，Caddy 也不会加载新证书。
   → 已重建 `/etc/acme-certs/reload.sh`（修正属主权限 + `caddy reload --force`），并实测能成功重载。

## ⚠️ 仍未解决：DNS 提供商不匹配

证书 conf 里 `Le_Webroot='dns_dp'`，即用 **DNSPod** 做 DNS-01 验证。但：

- `bluecdn.com` 的 NS 现在是 `taurus.ns.atrustdns.com` / `baikal.ns.atrustdns.com` —— **阿里云 ESA 的 DNS**；
- 服务器上保存的 DNSPod 凭据本身**有效**（API 返回 code 1），但该账号下只有
  `pancn.com` / `pancn.net` / `xifeng.net`，**没有 `bluecdn.com`**。

所以到 2026-08-30 触发续期时，acme.sh 无法写入 `_acme-challenge.bluecdn.com` 的 TXT 记录，
**续期必定失败**，2026-09-28 证书过期后 bluecdn.com 全线 TLS 失效。

可选修法（任选其一，都需要额外凭据或决策）：

1. **切到阿里云 DNS API**：acme.sh 自带 `dns_ali`，需要 `Ali_Key` / `Ali_Secret`（阿里云 AccessKey）。
   注意 ESA 托管的域名记录是否能由 Alidns OpenAPI 管理需先验证；若不能，要为 ESA 写自定义 hook。
2. **把 `bluecdn.com` 的 DNS 迁回 DNSPod 或迁到 Cloudflare**，再对应换 `--dns dns_dp` / `dns_cf`。
3. **改用 HTTP-01**：apex 与 `status.bluecdn.com` 本来就直连源站，可直接验证；
   但 `*.bluecdn.com` 泛域名**只能**用 DNS-01，改 HTTP-01 就得逐个列出子域名签发。

## 手动应急续期

在拿到可用的 DNS 凭据后：

```bash
export Ali_Key="..." Ali_Secret="..."          # 或对应提供商的变量
~/.acme.sh/acme.sh --issue --dns dns_ali -d bluecdn.com -d '*.bluecdn.com' --force
~/.acme.sh/acme.sh --install-cert -d bluecdn.com \
  --key-file       /etc/caddy/certs/bluecdn.com.key \
  --fullchain-file /etc/caddy/certs/bluecdn.com.fullchain.pem \
  --reloadcmd      "bash /etc/acme-certs/reload.sh"
```

## 检查续期是否真的健康

```bash
crontab -l | grep acme                                   # 1. cron 在不在
ls -l /etc/acme-certs/reload.sh                          # 2. 钩子脚本在不在
~/.acme.sh/acme.sh --list                                # 3. 下次续期时间
openssl x509 -in /etc/caddy/certs/bluecdn.com.fullchain.pem -noout -enddate   # 4. 实际到期
bash /etc/acme-certs/reload.sh                           # 5. 钩子能不能跑通
```

四项齐全 + DNS 提供商对得上，才算真的自动。**只有 cron 是不够的** —— 这次就是三处同时坏。

## 安全

- 所有密钥只放 `certs.env`（已 .gitignore，不提交）。
- 用**限定权限**的 API Token（Cloudflare 用 Zone.DNS Edit，阿里云用只含 DNS 权限的 RAM 子账号），
  不要用 Global Key / 主账号 AccessKey。
- 在聊天或工单里贴过的任何密钥，用完立即去控制台轮换。
