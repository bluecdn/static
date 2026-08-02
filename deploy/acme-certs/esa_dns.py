#!/usr/bin/env python3
"""acme.sh DNS-01 钩子后端:在阿里云 ESA 上增删 _acme-challenge TXT 记录。

为什么需要它:bluecdn.com / yite.net 的 NS 指向 ESA(*.atrustdns.com),
记录由 ESA 托管而非 Alidns —— Alidns 里这些域名记录数为 0,
所以 acme.sh 自带的 dns_ali 插件写进去的 TXT 根本不会被解析到。

用法:
  esa_dns.py add <_acme-challenge.example.com> <txtvalue>
  esa_dns.py rm  <_acme-challenge.example.com> <txtvalue>

凭据从环境变量读:Ali_Key / Ali_Secret(acme.sh 的习惯命名)
"""
import os, sys, json, uuid, hmac, hashlib, datetime
import urllib.parse, urllib.request, urllib.error

ENDPOINT = "esa.cn-hangzhou.aliyuncs.com"
VERSION = "2024-09-10"

AK = os.environ.get("Ali_Key") or os.environ.get("ALIYUN_ACCESS_KEY_ID")
SK = os.environ.get("Ali_Secret") or os.environ.get("ALIYUN_ACCESS_KEY_SECRET")
if not AK or not SK:
    print("缺少 Ali_Key / Ali_Secret", file=sys.stderr)
    sys.exit(2)


def _pct(s):
    return urllib.parse.quote(str(s), safe="~")


def call(action, body=None, query=None, method="POST"):
    query = query or {}
    payload = json.dumps(body).encode() if body is not None else b""
    hashed = hashlib.sha256(payload).hexdigest()
    h = {
        "host": ENDPOINT,
        "x-acs-action": action,
        "x-acs-version": VERSION,
        "x-acs-date": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "x-acs-signature-nonce": uuid.uuid4().hex,
        "x-acs-content-sha256": hashed,
    }
    if payload:
        h["content-type"] = "application/json; charset=utf-8"
    cq = "&".join(f"{_pct(k)}={_pct(query[k])}" for k in sorted(query))
    sh = sorted(h)
    canon = "\n".join([method, "/", cq, "".join(f"{k}:{h[k]}\n" for k in sh), ";".join(sh), hashed])
    sts = "ACS3-HMAC-SHA256\n" + hashlib.sha256(canon.encode()).hexdigest()
    sig = hmac.new(SK.encode(), sts.encode(), hashlib.sha256).hexdigest()
    h["Authorization"] = f"ACS3-HMAC-SHA256 Credential={AK},SignedHeaders={';'.join(sh)},Signature={sig}"
    url = f"https://{ENDPOINT}/" + (f"?{cq}" if cq else "")
    req = urllib.request.Request(url, data=payload or None, method=method)
    for k, v in h.items():
        if k != "host":
            req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            d = json.loads(raw)
        except Exception:
            d = {"__raw": raw[:400]}
        d["__http_status"] = e.code
        return d


def find_site(fulldomain):
    """把 _acme-challenge.a.b.com 逐级向上匹配到 ESA 站点。"""
    r = call("ListSites", query={"PageSize": "100"}, method="GET")
    sites = {s["SiteName"]: s["SiteId"] for s in (r.get("Sites") or [])}
    if not sites:
        print(f"ListSites 失败: {json.dumps(r, ensure_ascii=False)[:300]}", file=sys.stderr)
        sys.exit(1)
    parts = fulldomain.split(".")
    for i in range(len(parts)):
        cand = ".".join(parts[i:])
        if cand in sites:
            return sites[cand], cand
    print(f"没有匹配 {fulldomain} 的 ESA 站点。已有:{list(sites)}", file=sys.stderr)
    sys.exit(1)


def list_txt(site_id, name):
    out, page = [], 1
    while True:
        r = call("ListRecords", query={"SiteId": str(site_id), "Type": "TXT",
                                       "PageNumber": str(page), "PageSize": "500"}, method="GET")
        recs = r.get("Records") or []
        if not recs:
            break
        out += [x for x in recs if x.get("RecordName") == name]
        if len(recs) < 500:
            break
        page += 1
    return out


def main():
    if len(sys.argv) != 4 or sys.argv[1] not in ("add", "rm"):
        print(__doc__)
        sys.exit(2)
    op, fulldomain, txt = sys.argv[1], sys.argv[2].rstrip("."), sys.argv[3]
    site_id, site_name = find_site(fulldomain)

    if op == "add":
        # 同名 TXT 可以有多条(apex 与泛域名各一条),这里只新增,不覆盖别人的。
        r = call("CreateRecord", body={
            "SiteId": site_id, "RecordName": fulldomain, "Type": "TXT",
            "Data": {"Value": txt}, "Ttl": 60, "Comment": "acme.sh DNS-01",
        })
        if r.get("RecordId"):
            print(f"[esa-dns] 已添加 TXT {fulldomain} (site={site_name}, RecordId={r['RecordId']})")
            return 0
        print(f"[esa-dns] 添加失败: {json.dumps(r, ensure_ascii=False)[:300]}", file=sys.stderr)
        return 1

    # rm:只删值匹配的那一条,避免误删同名的另一条挑战记录
    hit = [x for x in list_txt(site_id, fulldomain)
           if (x.get("Data") or {}).get("Value", "").strip('"') == txt]
    if not hit:
        print(f"[esa-dns] 未找到待删除的 TXT {fulldomain} = {txt[:16]}…(可能已被清理)")
        return 0
    rc = 0
    for x in hit:
        d = call("DeleteRecord", body={"RecordId": x["RecordId"]})
        if d.get("RequestId") and "__http_status" not in d:
            print(f"[esa-dns] 已删除 RecordId={x['RecordId']}")
        else:
            print(f"[esa-dns] 删除失败 {x['RecordId']}: {json.dumps(d, ensure_ascii=False)[:200]}", file=sys.stderr)
            rc = 1
    return rc


if __name__ == "__main__":
    sys.exit(main())
