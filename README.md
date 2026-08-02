# bluecdn.static

`static.bluecdn.com` 的**页面部署 + Caddy 配置 + 字体清单**。自建静态资源 CDN:Web 字体、FontAwesome Pro 全版本、jsDelivr/cdnjs 二合一反代。

> ⚠️ **本仓库只管部署，不管字体构建。** 字体构建脚本在服务器上跑（依赖 `cn-font-split` 与字体目录），不在本仓库——见下方[字体构建](#字体构建在服务器进行)。

## 架构

```
                      static.bluecdn.com  (DNS: 阿里云 ESA, NS = *.atrustdns.com)
                                   │
                            阿里云 ESA 边缘
                                   │ 回源 https
                                   ▼
                      芬兰 Hetzner 单源站 (secrets.ORIGIN_HOST)
                Caddy: 静态 + jsDelivr/cdnjs 二合一反代 + 节点探针
```

> 2026-08 现状核对:历史上的「百度 CDN + Cloudflare 双线、上海 + 硅谷双源站」架构**已不存在**。
> 上海 101.132.147.10 已改作他用(证书是 `fortune.gptjxt.online`),硅谷 47.254.125.87 443 不通。
> 当前唯一源站是芬兰 Hetzner 机,CDN 是阿里云 ESA(响应头 `Server: ESA` / `EagleId`)。

- **二合一反代(域名替换即用)**:`/npm /gh /wp /combine /esm` → cdn.jsdelivr.net;`/ajax/libs` → cdnjs.cloudflare.com。
- **字体方案**:`/fonts/{slug}.css`(扁平,CSS 名=字体名)。单文件 >2MB 用 cn-font-split 切片(每块 <2MB)。
- **FontAwesome Pro**:`/libs/fontawesome/{版本}/css/all.min.css`,65 个版本(5.0.1 → 7.3.1)。
- **FontAwesome Pro+**:`/libs/fontawesome-pro-plus/{版本}/css/all.min.css`,6 个版本(7.0.0 → 7.3.1)。
  Pro+ 的 `all.min.css` 与 Pro **字节相同**;其价值是额外 20 个独占渲染家族,不在 `all.min.css` 内,
  须单独引 `/libs/fontawesome-pro-plus/{版本}/css/{家族名}.min.css`。图标条目数与 Pro 一致。
- **证书**:源站 Caddy `auto_https off`,加载 acme.sh 签发的 `*.bluecdn.com` 泛域名证书。
  DNS-01 走**自建的 `dns_aliesa` 插件**(见 `deploy/acme-certs/`)——域名 NS 在阿里云 ESA,
  记录不在 Alidns,acme.sh 自带的 `dns_ali` / `dns_dp` 都写不进去。

## 仓库结构

页面与 SEO 文件直接放在仓库**根目录**(扁平结构),部署时原样 rsync 到服务器根目录。

| 路径 | 说明 |
|---|---|
| `index.html` | **首页**(部署内容) |
| `*.txt` / `robots.txt` / `sitemap.xml` / `manifest.json` | SEO 文件(llms.txt、llms-full.txt 等) |
| `favicon.*` / `*.png` / `*.ico` | favicon 与图标(部署内容) |
| `deploy/caddy/` | 源站 Caddyfile 参考(二合一反代配置) |
| `deploy/acme-certs/` | 证书自动续期 + 推百度 |
| `fonts/` | **字体资产**(2454 文件,~567M),由 **Git LFS** 管理(见 `.gitattributes`)。clone/pull 默认只下载指针 |
| `fonts.json` | 字体清单(事实源)。`base: https://static.bluecdn.com/fonts` |
| `fonts-candidates.md` | 字体候选/授权清单 |

> 字体资产由 **Git LFS** 管理:clone 或 `git pull` 默认**不下载** woff2 本体(只留指针,仓库保持轻量);需要本地预览/使用字体时执行 `git lfs pull` 取回。详见[字体资产管理](#字体资产管理git-lfs)。

## 自动部署 (GitHub Actions)

push 到 `main` 且改动根目录的页面/favicon/SEO 文件(或 `deploy.yml`)→ 自动 rsync 到**单源站**的 `/www/sites/static.bluecdn.com/`。用 `--include` 白名单精确同步这些文件(`--exclude='*'`,**无 `--delete`**),**绝不动服务器上的 fonts/ 与 libs/ 目录**(合计约 20G)。

需要的仓库 Secrets:
- `ORIGIN_HOST` — 源站地址(本仓库 public,故不写进代码)
- `DEPLOY_SSH_KEY` — 部署私钥,对应公钥须已在源站 `/root/.ssh/authorized_keys`
- `ORIGIN_USER`(可选,默认 `root`)
- `ORIGIN_KNOWN_HOSTS`(可选)— 源站 SSH 主机公钥,填了才做主机密钥固定

工作流带前置检查:Secret 缺失、源站不可达、目标目录不存在都会直接失败并给出明确报错;
部署后会直连源站(`--resolve`,绕过边缘缓存)校验 `/`、`/llms.txt`、`/manifest.json` 均为 200。

手动触发:Actions → Deploy → Run workflow。

> ⚠️ 边缘缓存:阿里云 ESA 对静态文件缓存较久(实测 `X-Swift-CacheTime: 2592000`),
> 页面推到源站后**需在 ESA 控制台刷新缓存**才会对外生效。

## 字体资产管理(Git LFS)

`fonts/` 目录(2454 个文件,~567M 实际内容)由 **Git LFS** 版本管理,这是"资产在 GitHub 有备份、但日常同步不背 567M 包袱"的方案。

- **clone/pull 默认不下载本体**:设置 `git lfs install --skip-smudge` 后,`git pull` 只拿 LFS 指针(每个 ~130 字节),仓库保持轻量(几 MB)。
- **需要字体本体时**:`git lfs pull`(从 GitHub LFS 存储下载,会消耗 LFS 带宽配额)。
- **规则**:见 `.gitattributes`(`fonts/** filter=lfs`)。`.gitignore` 已放开 `fonts/` 下的字体(改由 LFS 管理)。

> ⚠️ LFS 配额:GitHub Pro 含 2GB 存储 + 2GB/月 带宽。当前 fonts ~156M,远低于上限。频繁 `git lfs pull` 会消耗带宽配额,服务器侧字体仍由本地文件直接服务,**不依赖 git pull 部署**。

## 字体构建(在服务器进行)

字体切片/CSS 由**服务器**上的构建脚本 + `cn-font-split` 产出:

- **构建工作区**:源站的 `/root/`(脚本 + `fonts.json` + 临时下载目录)。
- **关键脚本**(`/root/` 下,按用途):
  - `build_gf_cn.py` / `github_cn.py` — 从 Google Fonts / GitHub 拉取字体
  - `slice_cn.py` — 对 >2MB 的字体用 cn-font-split 切片
  - `update_home*.py` / `sync_home_cn.py` — 更新首页字体卡片
- **产出**:`/www/sites/static.bluecdn.com/fonts/{slug}/`(切片字体),`/fonts/{slug}.css`(扁平入口)。
- **同步到 git**:构建完成后,在服务器 `/root/bluecdn.static` 里 `git add fonts/ && git commit && git push` 即可把新字体纳入 LFS 版本管理。

## FontAwesome(不入 git)

FontAwesome 是第三方成品库,**不纳入 git**。原始 zip 归档在 Cloudflare R2 桶 `fontawesome`(账户 GENTPAN),
服务器上是解压后的可直接访问版本:

| | 路径 | 版本数 | 占用 | R2 归档命名 |
|---|---|---|---|---|
| Pro | `/www/sites/static.bluecdn.com/libs/fontawesome/{版本}/` | 65 (5.0.1 → 7.3.1) | 14G | `fontawesome-pro-{版本}-web.zip` |
| Pro+ | `/www/sites/static.bluecdn.com/libs/fontawesome-pro-plus/{版本}/` | 6 (7.0.0 → 7.3.1) | 6.2G | `fontawesome-pro-plus-{版本}-web.zip` |

- 丢失可从 R2 归档重建,或用 `deploy/fetch-fontawesome.sh` 从官网重新下载(见脚本注释)。
- Caddy 的 `@imm path /libs/*` 规则对两个路径都生效(`Cache-Control: public, max-age=31536000, immutable`),新增路径无需改配置。
