#!/usr/bin/env python3
"""可选：把证书上传到 Bunny CDN 的 Pull Zone（自定义证书）。
多数情况建议直接用 Bunny 控制台的 Free SSL（Bunny 自动签发+续期），无需此脚本。
仅当你想三家用同一张证书时才用它。

接口: POST https://api.bunny.net/pullzone/{pullZoneId}/addCertificate
Header: AccessKey: <BUNNY_API_KEY>
Body  : {"Hostname","Certificate"(base64 PEM),"CertificateKey"(base64 PEM)}

用法:
  python3 push_bunny.py <pullZoneId> <hostname> <fullchain.pem> <privkey.pem>
环境变量: BUNNY_API_KEY
"""
import os, sys, json, base64, urllib.request, urllib.error

API = "https://api.bunny.net"
KEY = os.environ["BUNNY_API_KEY"]


def b64(path):
    return base64.b64encode(open(path, "rb").read()).decode()


def push(zone_id, hostname, fullchain, key):
    body = json.dumps({
        "Hostname": hostname,
        "Certificate": b64(fullchain),
        "CertificateKey": b64(key),
    }).encode()
    req = urllib.request.Request(f"{API}/pullzone/{zone_id}/addCertificate", data=body, method="POST")
    req.add_header("AccessKey", KEY)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            print(f"[bunny] {hostname} OK {r.status}")
            return 0
    except urllib.error.HTTPError as e:
        print(f"[bunny] {hostname} FAILED {e.code}: {e.read().decode()}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    if len(sys.argv) != 5:
        sys.exit("usage: push_bunny.py <pullZoneId> <hostname> <fullchain.pem> <privkey.pem>")
    sys.exit(push(*sys.argv[1:5]))
