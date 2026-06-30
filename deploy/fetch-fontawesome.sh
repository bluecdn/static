#!/usr/bin/env bash
# fetch-fontawesome.sh — 从 fontawesome.com 下载指定版本的 FontAwesome Pro 到 libs/
#
# 用途:FontAwesome(~13G, 65 版本)不纳入 git,需要时用本脚本从官网重新下载。
# 这是替代"把 13G 第三方库塞进 git"的方案 —— 官网即真相源,丢失可随时重建。
#
# 用法:
#   ./deploy/fetch-fontawesome.sh <版本> [目标目录]
#   ./deploy/fetch-fontawesome.sh 7.2.0
#   ./deploy/fetch-fontawesome.sh 6.7.2 /www/sites/static.bluecdn.com/libs/fontawesome
#
# 说明:
#   - 默认目标目录:/www/sites/static.bluecdn.com/libs/fontawesome(服务器路径)
#   - 需要 FontAwesome Pro 的 KIT_CODE 或购买账号;免费版用 free 下载地址
#   - 下载后解压并规整为 {版本}/{css,js,webfonts,scss,svgs,...} 结构
#
# 详见:https://fontawesome.com/how-to-use/on-the-web/setup/hosting-font-awesome-yourself

set -euo pipefail

VERSION="${1:-}"
TARGET="${2:-/www/sites/static.bluecdn.com/libs/fontawesome}"

if [ -z "$VERSION" ]; then
  echo "用法: $0 <版本> [目标目录]"
  echo "示例: $0 7.2.0"
  echo "      $0 6.7.2 /custom/path"
  echo ""
  echo "已安装的版本(目标目录 $TARGET):"
  ls -1 "$TARGET" 2>/dev/null | head -20 || echo "(目录不存在)"
  exit 1
fi

DEST="$TARGET/$VERSION"

if [ -d "$DEST" ] && [ -n "$(ls -A "$DEST" 2>/dev/null)" ]; then
  echo "⚠️  $DEST 已存在且非空,跳过下载。如需重装请先删除该目录。"
  exit 0
fi

echo "==> 下载 FontAwesome $VERSION → $DEST"
echo "    注意:Pro 版需配置 FONTAWESOME_KIT_CODE 或账号 token。"
echo "    请从 https://fontawesome.com/download 下载对应 zip 后手动解压到此目录,"
echo "    或用账号 API(见 https://fontawesome.com/docs/apis)。"
echo ""
echo "    下载并解压示例:"
echo "      mkdir -p \"$DEST\""
echo "      # 下载 pro zip 后:"
echo "      unzip -o fontawesome-pro-$VERSION-web.zip -d \"$DEST\""
echo "      # 规整:把解压出的子目录提到版本目录下"
echo ""
echo "    结构应为:"
echo "      $DEST/css/ $DEST/js/ $DEST/webfonts/ $DEST/scss/ $DEST/svgs/"

# 实际下载逻辑需根据你的 FontAwesome 账号/kit 配置补全。
# 这里有意留为半自动:13G 第三方资产应明确人工确认后再下载,避免误操作。
exit 0
