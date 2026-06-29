#!/usr/bin/env python3
"""acme.sh reloadcmd 钩子：把续期后的证书推送到百度 CDN。
调用百度 CDN「增加&修改域名证书」接口  PUT /v2/{domain}/certificates
（已绑定则替换旧证书并重新绑定，等同自动续期落地）。

用法:
  python3 push_baidu.py <domain> <fullchain.pem> <privkey.pem>

密钥从环境变量读取（由 certs.env 提供）:
  BAIDU_AK / BAIDU_SK
"""
import os, sys, re, json, hmac, hashlib, datetime, urllib.request, urllib.error

HOST = "cdn.baidubce.com"
AK = os.environ["BAIDU_AK"]
SK = os.environ["BAIDU_SK"]


def uri_encode(s, keep_slash=False):
    out = []
    for b in s.encode("utf-8"):
        c = chr(b)
        if c.isalnum() or c in "-_.~" or (c == "/" and keep_slash):
            out.append(c)
        else:
            out.append("%{:02X}".format(b))
    return "".join(out)


def auth(method, path):
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    prefix = f"bce-auth-v1/{AK}/{ts}/1800"
    signing_key = hmac.new(SK.encode(), prefix.encode(), hashlib.sha256).hexdigest()
    canon = "\n".join([method, uri_encode(path, keep_slash=True), "", f"host:{uri_encode(HOST)}"])
    sig = hmac.new(signing_key.encode(), canon.encode(), hashlib.sha256).hexdigest()
    return f"{prefix}/host/{sig}"


def push(domain, fullchain, key):
    cert_name = re.sub(r"[^a-zA-Z0-9\-/_.*]", "-", f"acme-{domain}")[:65]
    body = json.dumps({
        "httpsEnable": "ON",
        "certificate": {
            "certName": cert_name,
            "certServerData": fullchain,   # 服务器证书 + 中间链 (PEM 原文)
            "certPrivateData": key,        # 私钥 (PEM 原文)
            "certType": 1,
        },
    }).encode("utf-8")

    path = f"/v2/{domain}/certificates"
    req = urllib.request.Request(f"https://{HOST}{path}", data=body, method="PUT")
    req.add_header("Host", HOST)
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", auth("PUT", path))
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            print(f"[baidu] {domain} OK {r.status}: {r.read().decode()}")
            return 0
    except urllib.error.HTTPError as e:
        print(f"[baidu] {domain} FAILED {e.code}: {e.read().decode()}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit("usage: push_baidu.py <domain> <fullchain.pem> <privkey.pem>")
    dom, fc, k = sys.argv[1], sys.argv[2], sys.argv[3]
    sys.exit(push(dom, open(fc).read(), open(k).read()))
