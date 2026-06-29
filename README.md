# bluecdn.static

`static.bluecdn.com` 的源码 + 构建脚本 + 部署配置。自建静态资源 CDN:Web 字体、FontAwesome Pro 全版本、fancybox 等。

## 架构

```
                      static.bluecdn.com  (DNS 分线, DNSPod)
        ┌──────────────────────────┴──────────────────────────┐
   中国大陆线                                      境外 + 默认线(含港澳台/海外)
        ▼                                                       ▼
   百度云 CDN                                            Cloudflare
        ▼ 回源 http                                            ▼ 回源 https(full)
   上海 阿里云 (101.132.147.10)                       硅谷 阿里云 (47.254.125.87)
        └────── Caddy: 静态 + jsDelivr/cdnjs 二合一反代 ──────┘
```

- **二合一反代(域名替换即用)**:`/npm /gh /wp /combine /esm` → cdn.jsdelivr.net;`/ajax/libs` → cdnjs.cloudflare.com。
- **字体方案**:`/fonts/{slug}.css`(扁平,CSS 名=字体名)。单文件 >2MB 用 cn-font-split 切片(每块 <2MB)。
- **FontAwesome**:`/libs/fontawesome/{版本}/css/all.min.css`,64 个版本(5.0.1 → 7.3.0)。
- **证书**:CF Universal SSL(海外自动);百度边缘用 acme.sh 签 LE + 自动推送(见 `deploy/acme-certs`)。

## 仓库结构

| 路径 | 说明 |
|---|---|
| `site/` | **部署的网页内容**(index.html + favicon)。GHA 推送这个目录到两台源站 |
| `build/` | 字体/页面构建脚本(EN 从 Google Fonts、CN 切片、首页生成等) |
| `deploy/caddy/` | 两台服务器的 Caddyfile |
| `deploy/acme-certs/` | 证书自动续期 + 推百度 |
| `fonts.json` | 字体清单(事实源) |
| `fonts-candidates.md` | 字体候选/授权清单 |

> ⚠️ 字体 woff2 与 FontAwesome(13G)**不入 Git**(见 .gitignore),由 `build/` 脚本生成 + R2 备份,常驻两台服务器。

## 自动部署 (GitHub Actions)

push 到 `main` 且改动 `site/**` → 自动 rsync 到**两台源站**的 `/www/sites/static.bluecdn.com/`(仅同步页面/favicon,不动字体目录)。

需要的仓库 Secrets:
- `DEPLOY_SSH_KEY` — 部署私钥(对应公钥已加到两台 authorized_keys)
- `SH_HOST` = 101.132.147.10
- `SV_HOST` = 47.254.125.87

手动触发:Actions → Deploy → Run workflow。
