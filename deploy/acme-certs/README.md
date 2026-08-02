# 证书自动续期（acme.sh + 阿里云 ESA DNS-01）

`bluecdn.com` 的 `*.bluecdn.com` 泛域名证书，用 acme.sh 走 DNS-01 自动续期。
**2026-08-02 全链路已修复并实测跑通**，下面是最终形态与当初踩的坑。

## 为什么不能用 acme.sh 自带的 dns_ali

`bluecdn.com` / `yite.net` 的 NS 是 `taurus.ns.atrustdns.com` / `baikal.ns.atrustdns.com` —— **阿里云 ESA**（边缘安全加速）的域名服务器。

坑在于：这些域名在 **Alidns 控制台里能看到，但记录数是 0**。真正的解析记录托管在 ESA，必须走 ESA 的 OpenAPI。
自带的 `dns_ali` 插件会把 TXT 写进 Alidns，而全世界的解析器都去问 atrustdns —— 记录永远查不到，DNS-01 只会静默超时。

所以本目录提供自建插件：

| 文件 | 装到哪 | 作用 |
|---|---|---|
| `dns_aliesa.sh` | `~/.acme.sh/dnsapi/dns_aliesa.sh` | acme.sh 插件入口（bash） |
| `esa_dns.py` | `/etc/acme-certs/esa_dns.py` | 实际调 ESA API（ACS3-HMAC-SHA256 签名太复杂，不用纯 shell 写） |

`esa_dns.py` 会自动把 `_acme-challenge.x.y.com` 逐级向上匹配到对应的 ESA 站点，
并且**同名 TXT 只增不覆盖、删除时按值精确匹配** —— apex 与泛域名两条挑战记录同时存在时不会互相踩。

## 当前状态

```
Le_Webroot        = dns_aliesa
证书              = *.bluecdn.com + bluecdn.com（ECC-256，Let's Encrypt）
到期              = 2026-10-30
下次续期          = 2026-10-01（acme.sh 依 ARI 窗口自动选定）
cron              = 4 8 * * * "/root/.acme.sh"/acme.sh --cron --home "/root/.acme.sh"
reloadcmd         = bash /etc/acme-certs/reload.sh
ESA SiteId        = 165565416192216 (bluecdn.com)
```

## 当初坏在哪（三处同时坏，缺一不可）

修之前，续期是**完全不可能成功**的，而且不会有任何报错——因为它根本不会被触发：

1. **没有任何 cron / systemd timer 会调用 acme.sh。** `crontab -l` 是空的。
2. **`Le_ReloadCmd` 指向的 `/etc/acme-certs/reload.sh` 不存在**，连目录都没有。
   即使续期成功，Caddy（`auto_https off`，只加载文件）也不会重新读取新证书。
3. **DNS 提供商整个对不上。** 配置里是 `dns_dp`（DNSPod），凭据本身有效，
   但那个 DNSPod 账号下只有 `pancn.com` / `pancn.net` / `xifeng.net`，**没有 `bluecdn.com`**。

> 教训：**只检查「cron 在不在」是不够的**。这次三处独立故障叠在一起，
> 任何单项检查都会给出"看起来没问题"的假象。

## 首次配置

```bash
# 1) 装插件
install -m 700 esa_dns.py    /etc/acme-certs/esa_dns.py
install -m 700 dns_aliesa.sh /root/.acme.sh/dnsapi/dns_aliesa.sh

# 2) 签发（凭据首次用后会被 acme.sh 存进 account.conf，之后自动读取）
export Ali_Key="<AccessKey ID>" Ali_Secret="<AccessKey Secret>"
~/.acme.sh/acme.sh --issue --dns dns_aliesa -d bluecdn.com -d '*.bluecdn.com' --server letsencrypt

# 3) 绑定安装路径与 reload 钩子
~/.acme.sh/acme.sh --install-cert -d bluecdn.com --ecc \
  --key-file       /etc/caddy/certs/bluecdn.com.key \
  --fullchain-file /etc/caddy/certs/bluecdn.com.fullchain.pem \
  --reloadcmd      "bash /etc/acme-certs/reload.sh"

# 4) 装 cron
~/.acme.sh/acme.sh --install-cronjob
```

> ⚠️ `--issue --force` **不会**执行 install-cert，只有 `--renew`（即 cron 走的路径）会。
> 手工强制签发之后，记得补跑一次第 3 步，否则 Caddy 用的还是旧证书。

## 健康自检（六项齐全才算真的自动）

```bash
crontab -l | grep acme                                                        # 1 cron
ls -l /etc/acme-certs/reload.sh                                               # 2 reload 钩子
ls -l ~/.acme.sh/dnsapi/dns_aliesa.sh /etc/acme-certs/esa_dns.py              # 3 DNS 插件
grep Le_Webroot ~/.acme.sh/bluecdn.com_ecc/bluecdn.com.conf                   # 4 提供商匹配
grep Le_NextRenewTimeStr ~/.acme.sh/bluecdn.com_ecc/bluecdn.com.conf          # 5 下次续期
openssl x509 -in /etc/caddy/certs/bluecdn.com.fullchain.pem -noout -enddate   # 6 实际到期
~/.acme.sh/acme.sh --cron --home /root/.acme.sh                               # 干跑，应"Skipping"且退出码 0
bash /etc/acme-certs/reload.sh                                                # 钩子能否跑通
```

## 顺带：ESA 缓存刷新

改完 `static.bluecdn.com` 的页面推到源站后，**必须刷 ESA 缓存**才会对外生效
（实测 `X-Swift-CacheTime: 2592000`，30 天）。`/libs/` 下的新版本路径是新 URL，无旧缓存，不受影响。

API：`PurgeCaches`（`esa.cn-hangzhou.aliyuncs.com`，版本 `2024-09-10`）。
注意 `Content` **必须**是 `{"Files": ["https://..."]}` 这种形式，
直接传数组或换行分隔的字符串都会报 `InvalidContent`。

## 安全

- 凭据由 acme.sh 存在 `~/.acme.sh/account.conf`（`SAVED_Ali_Key` / `SAVED_Ali_Secret`），不进 git。
- ⚠️ **当前用的是阿里云主账号 AccessKey**（`Arn: acs:ram::…:root`），权限是全账户最高级。
  应改为 RAM 子账号，自定义策略只给这几个动作：
  `esa:ListSites` `esa:ListRecords` `esa:CreateRecord` `esa:DeleteRecord` `esa:PurgeCaches`。
- 在聊天/工单里贴过的密钥，用完立即去控制台轮换。

## 历史

原本这里放的是「Cloudflare DNS-01 签发 + `push_baidu.py` 推送到百度 CDN」的方案。
CDN 早已换成阿里云 ESA 单边缘，那套已无使用场景，`push_baidu.py` / `push_bunny.py` 于 2026-08-02 删除。
`setup.sh` 与 `certs.env.example` 暂留作参考，但其中的 `--dns dns_cf` 步骤**已不适用**。
