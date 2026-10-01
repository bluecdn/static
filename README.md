# BlueCDN Static

面向网站开发者的静态资源加速服务，提供 Web 字体、图标资源，以及 jsDelivr / cdnjs 镜像访问。

[服务首页](https://static.bluecdn.com) · [问题反馈](https://github.com/bluecdn/static/issues)

## 使用方式

### JavaScript 与 CSS 镜像

将上游域名替换为 `static.bluecdn.com`，保留对应资源路径：

| 路径 | 上游 |
| --- | --- |
| `/npm/`、`/gh/`、`/wp/`、`/combine/`、`/esm/` | jsDelivr |
| `/ajax/libs/` | cdnjs |

### Web 字体

字体 CSS 入口为 `https://static.bluecdn.com/fonts/{slug}.css`。字体列表见服务首页与 [`fonts.json`](fonts.json)。较大的字体使用 `cn-font-split` 切片，字体文件由 CSS 按需加载。

### 图标资源

- FontAwesome Pro：`/libs/fontawesome/{版本}/css/all.min.css`。
- FontAwesome Pro+：`/libs/fontawesome-pro-plus/{版本}/css/all.min.css`。
- Pro+ 的额外渲染家族需要单独引入对应的 `css/{家族名}.min.css`。

字体与图标属于第三方资源，使用时请遵循对应资源的许可。

## 本地资源与项目结构

| 路径 | 内容 |
| --- | --- |
| `index.html` | 服务首页 |
| `robots.txt`、`sitemap.xml`、`llms*.txt`、`manifest.json` | 站点索引与说明 |
| `favicon.*`、`*.png`、`*.ico` | 站点图标 |
| `fonts/` | 由 Git LFS 管理的字体资源 |
| `fonts.json` | 字体清单 |
| `fonts-candidates.md` | 字体候选与授权记录 |
| `deploy/caddy/` | Caddy 反向代理配置参考 |
| `deploy/acme-certs/` | 证书续期脚本 |

## 获取字体文件

字体资源由 Git LFS 管理。需要字体文件时，在安装 Git LFS 后执行：

```bash
git lfs install
git lfs pull
```

如果只需要页面与配置，可使用 `git lfs install --skip-smudge` 跳过下载字体文件，之后再通过 `git lfs pull` 获取。LFS 下载会消耗账户的相应存储与带宽额度。

## 部署说明

项目包含页面部署工作流与 Caddy 配置参考。字体构建需另行准备字体源文件和 `cn-font-split` 工具；第三方图标库需按许可自行准备。

GitHub Actions 使用以下仓库 Secrets：

- `ORIGIN_HOST`：源站地址。
- `DEPLOY_SSH_KEY`：部署用 SSH 私钥。
- `ORIGIN_USER`：SSH 用户，可选，默认 `root`。
- `ORIGIN_KNOWN_HOSTS`：SSH 主机公钥，可选，用于固定主机身份。

符合工作流路径条件的 `main` 分支更新会同步页面、图标和索引文件；也可在 Actions 中手动运行 Deploy。同步使用文件白名单，不删除源站现有的 `fonts/` 与 `libs/` 目录。部署后会检查首页、`llms.txt` 与 `manifest.json` 是否可访问。

使用 CDN 时，页面更新后可能需要刷新边缘缓存。图标库使用版本化路径和长期缓存，更新版本时请同步调整引用地址。

## 反馈

遇到资源访问、字体显示或镜像兼容问题，请[提交 Issue](https://github.com/bluecdn/static/issues)，并附上资源 URL、浏览器版本和重现步骤。
