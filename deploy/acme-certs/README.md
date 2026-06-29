# 证书自动续期 + 自动同步（acme.sh）

目标：**一次配置，Let's Encrypt 证书自动续期，自动推送到百度 CDN，永不手动。**
Cloudflare 和 Bunny 各自有自动方案，无需此脚本（见下）。

## 三家 CDN 各自怎么办

| CDN | 做法 | 需要这套脚本？ |
|---|---|---|
| **Cloudflare** | Universal SSL，CF 全自动签发+续期 | ❌ 不用，什么都不做 |
| **Bunny** | 控制台给自定义域名点 **Load Free Certificate**，Bunny 自动签 LE + 自动续 | ❌ 不用（除非要统一一张证书 → 用 `push_bunny.py`） |
| **百度 CDN** | 不会自动、免费证书仅 90 天 | ✅ **就它需要**：acme.sh 续期后用 `push_baidu.py` 自动推送 |

## 在哪跑

跑在**服务器 B**（常开、能访问 Let's Encrypt）。用 **DNS-01 验证**，所以不要求 B 是该域名的 Web 服务器——只要能改 Cloudflare DNS 即可。

## 步骤

```bash
cd deploy/acme-certs
cp certs.env.example certs.env     # 填：DOMAINS、CF_Token、BAIDU_AK/SK（重置后的新密钥）
bash setup.sh
```

`setup.sh` 会：
1. 装 acme.sh（自带每日 cron，到期前自动续）
2. 用 Cloudflare DNS-01 签发各域名证书
3. `--install-cert ... --reloadcmd` 绑定续期钩子：**每次续期后自动跑 `push_baidu.py`** 把新证书推到百度 CDN

之后全自动，你不用再碰。

## 证书链路回顾（一个域名多张证书是正常的）

```
用户 ─海外→ Cloudflare 边缘 (CF 自动证书)
     ─国内→ 百度 CDN 边缘   (本脚本推送的 LE 证书，自动续)
              ↓ 回源
            服务器 B (Caddy 自动签的源站证书)
```
每个“TLS 解密点”各一张证书，互不共用——这是多 CDN 的正常形态。

## Bunny（可选，API 上传）

优先用 Bunny 控制台 Free SSL（自动）。若坚持用同一张证书：
```bash
source certs.env
python3 push_bunny.py <pullZoneId> <hostname> /etc/acme-certs/<domain>.fullchain.pem /etc/acme-certs/<domain>.key
```
并把这行也加进 `setup.sh` 的 `--reloadcmd` 即可一并自动推送。

## 安全

- 所有密钥只在 `certs.env`（已 .gitignore，不提交）。
- ⚠️ 之前在聊天里贴过的百度 AK/SK、Bunny API Key **务必先重置**，再把新值填进 `certs.env`。
- Cloudflare 用**限定 Zone.DNS 权限**的 API Token，别用 Global Key。
