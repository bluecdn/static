# bluecdn.static

`static.bluecdn.com` 的**页面部署 + Caddy 配置 + 字体清单**。自建静态资源 CDN:Web 字体、FontAwesome Pro 全版本、jsDelivr/cdnjs 二合一反代。

> ⚠️ **本仓库只管部署，不管字体构建。** 字体构建脚本在服务器上跑（依赖 `cn-font-split` 与字体目录），不在本仓库——见下方[字体构建](#字体构建在服务器进行)。

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

页面与 SEO 文件直接放在仓库**根目录**(扁平结构),部署时原样 rsync 到服务器根目录。

| 路径 | 说明 |
|---|---|
| `index.html` | **首页**(部署内容) |
| `*.txt` / `robots.txt` / `sitemap.xml` / `manifest.json` | SEO 文件(llms.txt、llms-full.txt 等) |
| `favicon.*` / `*.png` / `*.ico` | favicon 与图标(部署内容) |
| `deploy/caddy/` | 两台服务器的 Caddyfile(二合一反代配置) |
| `deploy/acme-certs/` | 证书自动续期 + 推百度 |
| `fonts.json` | 字体清单(事实源)。`base: https://static.bluecdn.com/fonts` |
| `fonts-candidates.md` | 字体候选/授权清单 |

> 字体二进制本身**不入 Git**(见 `.gitignore`),由服务器 `/root/` 脚本构建到 `/www/sites/.../fonts/`。

## 自动部署 (GitHub Actions)

push 到 `main` 且改动根目录的页面/favicon/SEO 文件(或 `deploy.yml`)→ 自动 rsync 到**两台源站**的 `/www/sites/static.bluecdn.com/`。用 `--include` 白名单精确同步这些文件(`--exclude='*'`,**无 `--delete`**),**绝不动服务器上的 fonts/ 目录**。

需要的仓库 Secrets:
- `DEPLOY_SSH_KEY` — 部署私钥(对应公钥已加到两台 authorized_keys)
- `SH_HOST` = 101.132.147.10
- `SV_HOST` = 47.254.125.87

手动触发:Actions → Deploy → Run workflow。

## 字体构建(在服务器进行)

字体 woff2/ttf 与 FontAwesome(**约 13G**)**不入 Git**(见 `.gitignore`),由**服务器**上的构建脚本 + `cn-font-split` 产出,常驻两台服务器的 `/www/sites/static.bluecdn.com/fonts/`。

- **构建工作区**:两台服务器的 `/root/`(脚本 + `fonts.json` + 临时下载目录)。
- **关键脚本**(`/root/` 下,按用途):
  - `build_gf_cn.py` / `github_cn.py` — 从 Google Fonts / GitHub 拉取字体
  - `slice_cn.py` — 对 >2MB 的字体用 cn-font-split 切片
  - `normalize_fa.py` — 规整 FontAwesome 各版本目录结构
  - `update_home*.py` / `sync_home_cn.py` — 更新首页字体卡片
  - `gen_manifest.py`(本仓库 `fonts.json` 的生成源)
- **产出目录**:`/www/sites/static.bluecdn.com/fonts/{slug}.css`(扁平),切片字体在其子目录。

> 在服务器上构建字体的具体操作,登录对应源站后在 `/root/` 下执行相关脚本即可。本仓库不维护这些服务器脚本——它们是服务器侧的运维代码。
