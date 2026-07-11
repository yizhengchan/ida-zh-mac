#!/bin/bash
# 构建 IDA汉化工具.app
# 用法: ./build_app.sh
# 输出: build/IDA汉化工具.app

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
BUILD_DIR="$PROJECT_DIR/build"
APP_NAME="IDA汉化工具.app"
APP_DIR="$BUILD_DIR/$APP_NAME"
RESOURCES_DIR="$APP_DIR/Contents/Resources"
TMP_APP="/tmp/ida_zh_$(date +%s).app"

echo "=== 构建 IDA 汉化工具.app ==="

# 清理旧构建
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

# 1. osacompile 对中文绝对路径有 bug, 先编译到 /tmp 再移动
echo "[1/4] 编译 AppleScript → .app ..."
cd "$PROJECT_DIR"
osacompile -l AppleScript -o "$TMP_APP" "IDA汉化工具.applescript" || {
    echo "❌ 编译失败"
    rm -rf "$TMP_APP" "$BUILD_DIR"
    exit 1
}
mv "$TMP_APP" "$APP_DIR"

# 2. 复制 Python 安装脚本和资源
echo "[2/4] 复制安装脚本和资源 ..."
mkdir -p "$RESOURCES_DIR/assets"
cp "$PROJECT_DIR/ida_zh_installer.py" "$RESOURCES_DIR/"
cp "$PROJECT_DIR/assets/libIdaTranslateLib.dylib" "$RESOURCES_DIR/assets/"
cp "$PROJECT_DIR/assets/ida_translations.json" "$RESOURCES_DIR/assets/"

# 3. 替换图标（用 IDA 自带图标）
echo "[3/5] 替换图标 ..."
IDA_ICON="/Applications/IDA Professional 9.4.app/Contents/Resources/appico.icns"
if [ -f "$IDA_ICON" ]; then
    cp "$IDA_ICON" "$RESOURCES_DIR/applet.icns"
    echo "  使用: $IDA_ICON"
else
    echo "  未找到 IDA 图标, 使用默认"
fi

# 4. 签名
echo "[4/5] 签名 ..."
codesign --force --sign - "$APP_DIR" 2>/dev/null || echo "  (签名警告, 不影响使用)"

# 5. 完成
echo "[5/5] 完成"
echo ""
echo "输出: $APP_DIR"
echo "大小: $(du -sh "$APP_DIR" | cut -f1)"
