#!/usr/bin/env sh
# acme.sh DNS API 插件:阿里云 ESA(边缘安全加速)
#
# 为什么不用自带的 dns_ali:bluecdn.com / yite.net 的 NS 指向 ESA 的
# *.atrustdns.com,记录由 ESA 托管;这些域名在 Alidns 里记录数为 0,
# 用 dns_ali 写的 TXT 不会被解析到,DNS-01 必然超时失败。
#
# 需要的变量:
#   Ali_Key    — 阿里云 AccessKey ID
#   Ali_Secret — 阿里云 AccessKey Secret
# 首次使用后会被 acme.sh 存进 account.conf,之后自动读取。
#
# 实际的 API 调用在 /etc/acme-certs/esa_dns.py(ESA 用 ACS3-HMAC-SHA256 签名,
# 纯 shell 实现代价过高,故用 python3 承担签名与增删)。

ESA_DNS_HELPER="${ESA_DNS_HELPER:-/etc/acme-certs/esa_dns.py}"

_aliesa_prepare() {
  Ali_Key="${Ali_Key:-$(_readaccountconf_mutable Ali_Key)}"
  Ali_Secret="${Ali_Secret:-$(_readaccountconf_mutable Ali_Secret)}"
  if [ -z "$Ali_Key" ] || [ -z "$Ali_Secret" ]; then
    Ali_Key=""
    Ali_Secret=""
    _err "缺少 Ali_Key / Ali_Secret,请先 export 后再执行。"
    return 1
  fi
  _saveaccountconf_mutable Ali_Key "$Ali_Key"
  _saveaccountconf_mutable Ali_Secret "$Ali_Secret"

  if [ ! -f "$ESA_DNS_HELPER" ]; then
    _err "找不到 $ESA_DNS_HELPER"
    return 1
  fi
  return 0
}

# 用法: dns_aliesa_add   _acme-challenge.www.domain.com   "txt-value"
dns_aliesa_add() {
  fulldomain=$1
  txtvalue=$2
  _info "使用 ESA DNS 添加 TXT: $fulldomain"
  _aliesa_prepare || return 1
  if Ali_Key="$Ali_Key" Ali_Secret="$Ali_Secret" python3 "$ESA_DNS_HELPER" add "$fulldomain" "$txtvalue"; then
    return 0
  fi
  _err "ESA 添加 TXT 记录失败"
  return 1
}

# 用法: dns_aliesa_rm    _acme-challenge.www.domain.com   "txt-value"
dns_aliesa_rm() {
  fulldomain=$1
  txtvalue=$2
  _info "使用 ESA DNS 删除 TXT: $fulldomain"
  _aliesa_prepare || return 1
  if Ali_Key="$Ali_Key" Ali_Secret="$Ali_Secret" python3 "$ESA_DNS_HELPER" rm "$fulldomain" "$txtvalue"; then
    return 0
  fi
  _err "ESA 删除 TXT 记录失败"
  return 1
}
