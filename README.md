# IDA 通用汉化工具 (macOS)

一键汉化 macOS 上所有 IDA Professional 9.x 版本（基于 Qt 6.x）。

## 使用方法

### 方法一：双击 .app（推荐）

1. 从 [Releases](https://github.com/yizhengchan/ida-zh-mac/releases) 下载 `IDA汉化工具.app`
2. 双击打开
3. 自动检测已安装的 IDA，选择版本 → 一键汉化

### 方法二：命令行

```bash
python3 ida_zh_installer.py --list          # 列出检测到的 IDA
python3 ida_zh_installer.py --install        # 交互选择后安装
python3 ida_zh_installer.py --uninstall      # 交互选择后卸载
python3 ida_zh_installer.py --install --path "/Applications/IDA Professional 9.4.app"  # 指定路径
```

## 原理

- 基于 **DYLD_INSERT_LIBRARIES** 注入 `libIdaTranslateLib.dylib`
- dylib 拦截 Qt 控件的 setter（QLabel、QAction、QWidget 等共 12 种）
- 对照 `ida_translations.json`（3059+ 条）替换 UI 文本
- **不修改 IDA 原始二进制**，零风险

## 兼容性

| IDA 版本 | Qt 版本 | 支持 |
|----------|---------|:----:|
| 9.x     | Qt 6.x  | ✅   |
| 8.x     | Qt 5.x  | ❌   |
| arm64 (Apple Silicon) | —  | ✅   |
| x86_64 (Intel)        | —  | ✅   |
| Windows / Linux       | —  | ❌   |

## 扩充翻译表

如发现仍有英文 UI 文本，欢迎提交 PR 扩充 `assets/ida_translations.json`：

```json
{
  "File": "文件",
  "Edit": "编辑",
  "新发现的英文文本": "对应的中文翻译"
}
```

## 项目来源

| 来源 | 贡献 |
|------|------|
| 52pojie [RedFree](https://www.52pojie.cn/thread-2091950-1-1.html) | 原创 dylib Hook 方案 + 翻译表 |
| 52pojie [m ra cry](https://www.52pojie.cn/thread-2082966-1-3.html) | 初版一键安装 App（硬编码 9.2 路径） |
| Justin Chan（本项目） | 通用化改造：去硬编码 → 自动扫描多版本、重写安装器 + AppleScript UI、适配 macOS 15 签名机制 |

## 构建（开发者）

```bash
./build_app.sh
# 输出: build/IDA汉化工具.app
```

## 许可

MIT
