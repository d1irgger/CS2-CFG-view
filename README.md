# CS2 CFG Viewer

> 把复杂的 CS2 配置文件，变成一眼能读懂的中文界面。

一款专为 **Counter-Strike 2** 打造的 **CFG / VCFG 可视化解析器**。支持按键绑定、控制台命令、视频设置的智能中文翻译，让你快速理解自己（或别人）的配置。

[![Version](https://img.shields.io/badge/version-4.1.0-6aa0ff)](https://github.com/d1irgger/CS2-CFG-view)
[![License](https://img.shields.io/badge/license-MIT-lightgrey)](LICENSE)

---

## 📌 这是什么

CS2 的配置以纯文本形式存放在以下位置：

- **个人配置**：`Steam/userdata/<SteamID>/730/local/cfg/`
- **全局配置**：`游戏安装目录/game/csgo/cfg/`
- **常用文件**：`machine_convars.vcfg`、`user_convars.vcfg`、`user_keys.vcfg`、`video.txt`

这些文件内部是大量形如 `bind "key" "+command"` 和 `setting.cl_crosshaircolor 1` 的键值对。对不熟悉 CS2 命令的人来说，读起来像天书。

**CS2 CFG Viewer** 就是把这些"天书"翻译成中文的桥梁：

- 把 `bind "kp_ins" "+jump"` 显示为「小键盘 0 → 跳跃」
- 把 `cl_crosshaircolor 4` 显示为「准星颜色 → 青」
- 把 `setting.r_low_latency 2` 显示为「低延迟模式 → 超低延迟」

---

## 🚀 三种版本，任选其一

仓库包含三个独立版本，功能相似，部署方式不同：

| 版本 | 位置 | 适合谁 |
|---|---|---|
| **网页新版**（推荐） | `网页新版New Web Version/` | 零安装、双击即用、跨平台 |
| **WebUI 焕新版** | `WebUI焕新版WebUI New Look/` | 想要桌面窗口和系统文件对话框 |
| **原生 UI 版本** | `原生UI版本Native UI version/` | 只有 Python、不想装第三方依赖 |

### 版本对比

| 特性 | 网页新版 v4.1.0 | WebUI 焕新版 | 原生 UI 版本 |
|---|---|---|---|
| 安装步骤 | 双击 HTML | 需装 pywebview | 需装 Python |
| Steam 路径自动探测 | ❌ 手动选择 | ✅ | ✅ |
| 官方描述增强翻译 | ✅ | ❌ | ❌ |
| cvarlist.md 导入 | ✅ | ❌ | ❌ |
| 液态玻璃 UI | ✅ | ✅ | ❌ |
| 联网翻译 | ✅ | ✅ | ✅ |

---

## 📂 仓库结构

```
CS2-CFG-view/
├── README.md                              # 本文件
│
├── 网页新版New Web Version/                # ⭐ 推荐
│   ├── cs2cfgviewer.html                  # 单文件应用（双击即用）
│   └── README.md                          # 该版本的详细说明
│
├── WebUI焕新版WebUI New Look/
│   └── cs2cfgviewernew.py                 # PyWebView 版本
│
└── 原生UI版本Native UI version/
    └── cs2_cfg_viewer.py                  # Tkinter 版本
```

---

## ⚡ 快速开始

### 网页新版（推荐）跟随CS2最新版本更新

1. 下载 `网页新版New Web Version/cs2cfgviewer.html`
2. 用 Chrome / Edge 双击打开
3. 点击「📁 选择 Steam / userdata 目录」或「📄 导入 autoexec.cfg」
4. 开始浏览、搜索、翻译

详见 [网页新版说明](网页新版New%20Web%20Version/README.md)

### WebUI 焕新版

```bash
pip install pywebview
python "WebUI焕新版WebUI New Look/cs2cfgviewernew.py"
```

### 原生 UI 版本

```bash
python "原生UI版本Native UI version/cs2_cfg_viewer.py"
```

---

## 🧠 翻译机制（通用）

三个版本共享同一套翻译逻辑：

1. **本地字典**：内置常用按键、命令、设置项的中英对照。
2. **联网翻译**：本地未命中的条目，调用 [MyMemory Translation API](https://mymemory.translated.net/) 英译中。
3. **描述增强**（仅网页新版）：调用官方 ConVar 英文描述作为翻译上下文，显著提升机翻准确度。

---

## 📚 数据来源

官方英文描述来自社区维护的 CS2 ConVar 列表：

- [SuGolYolLom/CS2-Cvars-Cmds](https://github.com/SuGolYolLom/CS2-Cvars-Cmds)
- [ArmynC/ArminC-CS2-Cvars](https://github.com/ArmynC/ArminC-CS2-Cvars)

> Valve 没有提供公开的 CS2 ConVar 中文官方文档，因此翻译层完全依赖本地字典 + 社区数据 + MyMemory 的组合。

---

## ⚠️ 已知限制

- **Steam 路径自动探测**：仅 WebUI 焕新版和原生 UI 版本支持；网页新版需手动选择目录。
- **MyMemory 免费额度**：匿名用户约 5000 字符/天，超出后请求会被跳过。
- **Firefox 目录选择**：Firefox 不支持目录选择功能，网页新版请改用「手动加载配置文件」或换用 Chrome / Edge。

---

## 🤝 反馈与贡献

- **Issue / PR**：[GitHub Issues](https://github.com/d1irgger/CS2-CFG-view/issues)
- **作者**：[@d1irgger](https://github.com/d1irgger)
- **Telegram**：[@timharrys](https://t.me/timharrys)

如果这个工具帮你省下了翻配置的时间，给一颗 ⭐ Star 就是最大的鼓励。

---

## 📄 许可

MIT License
