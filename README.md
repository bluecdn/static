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
| `fonts/` | **字体资产**(2454 文件,~567M),由 **Git LFS** 管理(见 `.gitattributes`)。clone/pull 默认只下载指针 |
| `fonts.json` | 字体清单(事实源)。`base: https://static.bluecdn.com/fonts` |
| `fonts-candidates.md` | 字体候选/授权清单 |

> 字体资产由 **Git LFS** 管理:clone 或 `git pull` 默认**不下载** woff2 本体(只留指针,仓库保持轻量);需要本地预览/使用字体时执行 `git lfs pull` 取回。详见[字体资产管理](#字体资产管理git-lfs)。

## 自动部署 (GitHub Actions)

push 到 `main` 且改动根目录的页面/favicon/SEO 文件(或 `deploy.yml`)→ 自动 rsync 到**两台源站**的 `/www/sites/static.bluecdn.com/`。用 `--include` 白名单精确同步这些文件(`--exclude='*'`,**无 `--delete`**),**绝不动服务器上的 fonts/ 目录**。

需要的仓库 Secrets:
- `DEPLOY_SSH_KEY` — 部署私钥(对应公钥已加到两台 authorized_keys)
- `SH_HOST` = 101.132.147.10
- `SV_HOST` = 47.254.125.87

手动触发:Actions → Deploy → Run workflow。

## 字体资产管理(Git LFS)

`fonts/` 目录(2454 个文件,~567M 实际内容)由 **Git LFS** 版本管理,这是"资产在 GitHub 有备份、但日常同步不背 567M 包袱"的方案。

- **clone/pull 默认不下载本体**:设置 `git lfs install --skip-smudge` 后,`git pull` 只拿 LFS 指针(每个 ~130 字节),仓库保持轻量(几 MB)。
- **需要字体本体时**:`git lfs pull`(从 GitHub LFS 存储下载,会消耗 LFS 带宽配额)。
- **规则**:见 `.gitattributes`(`fonts/** filter=lfs`)。`.gitignore` 已放开 `fonts/` 下的字体(改由 LFS 管理)。

> ⚠️ LFS 配额:GitHub Pro 含 2GB 存储 + 2GB/月 带宽。当前 fonts ~156M,远低于上限。频繁 `git lfs pull` 会消耗带宽配额,服务器侧字体仍由本地文件直接服务,**不依赖 git pull 部署**。

## 字体构建(在服务器进行)

字体切片/CSS 由**服务器**上的构建脚本 + `cn-font-split` 产出:

- **构建工作区**:两台服务器的 `/root/`(脚本 + `fonts.json` + 临时下载目录)。
- **关键脚本**(`/root/` 下,按用途):
  - `build_gf_cn.py` / `github_cn.py` — 从 Google Fonts / GitHub 拉取字体
  - `slice_cn.py` — 对 >2MB 的字体用 cn-font-split 切片
  - `update_home*.py` / `sync_home_cn.py` — 更新首页字体卡片
- **产出**:`/www/sites/static.bluecdn.com/fonts/{slug}/`(切片字体),`/fonts/{slug}.css`(扁平入口)。
- **同步到 git**:构建完成后,在服务器 `/root/bluecdn.static` 里 `git add fonts/ && git commit && git push` 即可把新字体纳入 LFS 版本管理。

## FontAwesome(不入 git)

FontAwesome(**约 13G**,65 个版本)是第三方成品库,**不纳入 git**——fontawesome.com 官网可重新下载任意版本。

- 服务器常驻 `/www/sites/static.bluecdn.com/libs/fontawesome/{版本}/`。
- 需要时用 `deploy/fetch-fontawesome.sh` 从官网拉取指定版本(见脚本注释)。
