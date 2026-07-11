#!/usr/bin/env python3
"""IDA Pro macOS 通用汉化安装器
支持 Qt 6.x 的 IDA 9.x 系列，arm64。
"""

import os
import sys
import shutil
import subprocess
import argparse
import glob

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(SCRIPT_DIR, "assets")
DYLIB_SRC = os.path.join(ASSETS_DIR, "libIdaTranslateLib.dylib")
JSON_SRC = os.path.join(ASSETS_DIR, "ida_translations.json")

WRAPPER_CONTENT = """#!/bin/bash
APP_DIR="$(cd "$(dirname "$0")" && pwd)"
export DYLD_INSERT_LIBRARIES="$APP_DIR/libIdaTranslateLib.dylib"
exec "$APP_DIR/ida_orig" "$@"
"""


def detect_ida_apps():
    """扫描 /Applications 下所有 IDA Professional 版本, 返回 [(路径, 版本号, 状态)]"""
    results = []
    for app in sorted(glob.glob("/Applications/IDA Professional*.app")):
        name = os.path.basename(app)
        version = name.replace("IDA Professional", "").replace(".app", "").strip()
        macos_dir = os.path.join(app, "Contents", "MacOS")
        ida_bin = os.path.join(macos_dir, "ida")
        ida_orig = os.path.join(macos_dir, "ida_orig")

        if not os.path.isfile(ida_bin):
            continue

        if os.path.exists(ida_orig) and is_wrapper(ida_bin):
            status = "已安装汉化"
        else:
            status = "未安装"

        results.append((app, version, status))
    return results


def is_wrapper(path):
    """检查文件是否为 bash wrapper 脚本"""
    try:
        with open(path, "r") as f:
            return f.readline().startswith("#!/bin/bash")
    except Exception:
        return False


def check_qt_version(ida_path):
    """通过 otool -L 检查链接的 QtCore 主版本号, 返回 5 / 6 / None"""
    try:
        result = subprocess.run(
            ["otool", "-L", ida_path], capture_output=True, text=True, timeout=30
        )
        for line in result.stdout.splitlines():
            if "QtCore" in line:
                if "version 5." in line:
                    return 5
                elif "version 6." in line:
                    return 6
        return None
    except Exception:
        return None


def install(app_path):
    """安装汉化到指定 IDA, 返回 (成功: bool, 消息: str)"""
    macos_dir = os.path.join(app_path, "Contents", "MacOS")
    ida_bin = os.path.join(macos_dir, "ida")
    ida_orig = os.path.join(macos_dir, "ida_orig")
    ida_backup = os.path.join(macos_dir, "ida.backup")
    dylib_dst = os.path.join(macos_dir, "libIdaTranslateLib.dylib")
    json_dst = os.path.join(macos_dir, "ida_translations.json")

    # 校验
    if not os.path.isfile(ida_bin):
        return False, f"未找到 ida 可执行文件: {ida_bin}"

    if is_wrapper(ida_bin) and os.path.exists(ida_orig):
        return False, "汉化已安装"

    qt_ver = check_qt_version(ida_bin if not is_wrapper(ida_bin) else ida_orig)
    if qt_ver != 6:
        msg = f"不兼容的 Qt 版本: Qt {qt_ver}" if qt_ver else "无法检测 Qt 版本"
        return False, msg

    if not os.path.isfile(DYLIB_SRC):
        return False, f"dylib 不存在: {DYLIB_SRC}"
    if not os.path.isfile(JSON_SRC):
        return False, f"翻译表不存在: {JSON_SRC}"

    # 备份原始二进制
    if not is_wrapper(ida_bin):
        shutil.copy2(ida_bin, ida_backup)
        os.rename(ida_bin, ida_orig)
    else:
        return False, "ida 入口异常（已是 wrapper 但 ida_orig 丢失）"

    # 复制资源
    shutil.copy2(DYLIB_SRC, dylib_dst)
    shutil.copy2(JSON_SRC, json_dst)

    # 写入 bash wrapper
    with open(ida_bin, "w") as f:
        f.write(WRAPPER_CONTENT)
    os.chmod(ida_bin, 0o755)

    # 重新签名
    sign_result = subprocess.run(
        ["codesign", "--force", "--sign", "-", app_path],
        capture_output=True, text=True
    )

    msg = "汉化安装完成"
    if sign_result.returncode != 0:
        msg += "（签名警告：某些文件可能未被签名，不影响使用）"

    return True, msg


def uninstall(app_path):
    """卸载汉化, 恢复原始 ida, 返回 (成功: bool, 消息: str)"""
    macos_dir = os.path.join(app_path, "Contents", "MacOS")
    ida_bin = os.path.join(macos_dir, "ida")
    ida_orig = os.path.join(macos_dir, "ida_orig")
    dylib_dst = os.path.join(macos_dir, "libIdaTranslateLib.dylib")
    json_dst = os.path.join(macos_dir, "ida_translations.json")

    if not (is_wrapper(ida_bin) and os.path.exists(ida_orig)):
        return False, "未检测到已安装的汉化"

    # 恢复原始二进制
    os.remove(ida_bin)
    os.rename(ida_orig, ida_bin)

    # 删除汉化文件
    for f in [dylib_dst, json_dst]:
        if os.path.exists(f):
            os.remove(f)

    # 重新签名
    sign_result = subprocess.run(
        ["codesign", "--force", "--sign", "-", app_path],
        capture_output=True, text=True
    )

    msg = "汉化已卸载"
    if sign_result.returncode != 0:
        msg += "（签名警告，不影响使用）"

    return True, msg


def main():
    parser = argparse.ArgumentParser(description="IDA Pro macOS 通用汉化安装器")
    parser.add_argument("--install", action="store_true", help="安装汉化")
    parser.add_argument("--uninstall", action="store_true", help="卸载汉化")
    parser.add_argument("--path", type=str, help="指定 IDA.app 路径（可选，不指定则交互选择）")
    parser.add_argument("--list", action="store_true", help="列出检测到的 IDA")
    args = parser.parse_args()

    # 验证资源文件
    if not os.path.isfile(DYLIB_SRC):
        print(f"[错误] dylib 缺失: {DYLIB_SRC}")
        sys.exit(1)

    apps = detect_ida_apps()
    if not apps:
        print("未在 /Applications 下检测到 IDA Professional")
        sys.exit(1)

    # --list: 列出所有检测到的 IDA
    if args.list:
        print("检测到的 IDA:")
        for i, (path, ver, status) in enumerate(apps, 1):
            print(f"  [{i}] IDA Professional {ver} — {status}")
        sys.exit(0)

    # --path: 直接指定目标
    if args.path:
        target = args.path
        if not os.path.isdir(target):
            print(f"[错误] 路径不存在: {target}")
            sys.exit(1)
    else:
        # 交互选择
        print("\n检测到的 IDA:\n")
        for i, (path, ver, status) in enumerate(apps, 1):
            print(f"  [{i}] IDA Professional {ver} — {status}")
        if not sys.stdin.isatty():
            print("[错误] --install/--uninstall 必须配合 --path 或交互终端使用")
            sys.exit(1)
        print()
        try:
            choice = input("请选择 (输入序号): ").strip()
            idx = int(choice) - 1
            if idx < 0 or idx >= len(apps):
                print("[错误] 无效选择")
                sys.exit(1)
        except (ValueError, EOFError):
            print("[错误] 无效输入")
            sys.exit(1)
        target = apps[idx][0]

    # show banner
    print(f"\n{'='*50}")
    print(f"  IDA 汉化工具 — {os.path.basename(target).replace('.app', '')}")
    print(f"{'='*50}\n")

    if args.uninstall:
        ok, msg = uninstall(target)
        print(f"[{'✓' if ok else '✗'}] {msg}" if ok else f"[✗] {msg}")
        sys.exit(0 if ok else 1)

    if args.install:
        ok, msg = install(target)
        symbol = "✓" if ok else "✗"
        print(f"[{symbol}] {msg}")
        if ok:
            print(f"\n提示: 首次打开 IDA 较慢, 属于正常现象。")
        sys.exit(0 if ok else 1)

    # no operation mode specified, promote help
    print("请指定操作: --install 或 --uninstall")
    print("使用 --help 查看完整帮助")
    sys.exit(1)


if __name__ == "__main__":
    main()
