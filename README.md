# CS2 CFG Viewer

> 把复杂的 CS2 配置文件，变成一眼能读懂的中文界面。

一款专为 **Counter-Strike 2** 打造的 **CFG / VCFG 可视化解析器**。支持按键绑定、控制台命令、视频设置的智能中文翻译，让你快速理解自己（或别人）的配置。

[![Version](https://img.shields.io/badge/version-4.1.0-6aa0ff)](https://github.com/d1irgger/CS2-CFG-view)
[![Online](https://img.shields.io/badge/🌐_在线使用-d1irgger.github.io/CS2--CFG--view-a98bff)](https://d1irgger.github.io/CS2-CFG-view/)
[![License](https://img.shields.io/badge/license-MIT-lightgrey)](LICENSE)

---

## 🌐 在线使用（推荐）

**无需下载、无需安装，打开浏览器即可使用：**

### 👉 **[https://d1irgger.github.io/CS2-CFG-view/](https://d1irgger.github.io/CS2-CFG-view/)**

推荐使用 **Chrome / Edge**。打开后点击「📁 选择 Steam / userdata 目录」或「📄 导入 autoexec.cfg」即可开始。

> 💡 **提示**：直接选 `Steam/userdata` 目录比选 Steam 根目录快很多。浏览器会请求读取你选择的目录，数据全部在本地处理，**不会上传到任何服务器**。

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

## ✨ 功能一览

### 网页版（v4.1.0）

- **🧠 官方描述增强翻译**：内置约 150 条高频命令中文描述，打开即显示；其余项调用 CS2 官方英文描述作为上下文，机翻准确度显著提升。
- **📥 cvarlist.md 导入**：一键导入社区维护的 CS2 命令列表，把英文描述库扩展到 4000+ 条。
- **📂 三种数据源**：Steam `userdata` 目录扫描 / 手动加载 `.vcfg` 文件 / 导入 `autoexec.cfg`。
- **👥 多账户支持**：自动识别同一 Steam 下的多个账户，下拉框切换，路径栏同步显示当前选中账户。
- **🔍 实时搜索**：按键、命令、设置项、官方英文描述均可即时过滤。
- **🌐 可选联网翻译**：随时启动 / 停止，进度可见，失败条目自动重试。
- **🪟 液态玻璃风格**：CS2 官方图标，轻量、干净、聚焦内容。

### 桌面版

- **🖥️ 系统文件对话框**：像本地应用一样选择文件。
- **🔍 注册表读取 Steam 路径**：自动定位 Steam 安装目录。

---

## 🧠 翻译机制

三种使用方式共享同一套翻译逻辑：

1. **本地字典**：内置常用按键、命令、设置项的中英对照。
2. **联网翻译**：本地未命中的条目，调用 [MyMemory Translation API](https://mymemory.translated.net/) 英译中。
3. **描述增强**（仅网页版）：调用官方 ConVar 英文描述作为翻译上下文，显著提升机翻准确度。

---

## 📚 数据来源

官方英文描述来自社区维护的 CS2 ConVar 列表：

- [SuGolYolLom/CS2-Cvars-Cmds](https://github.com/SuGolYolLom/CS2-Cvars-Cmds)
- [ArmynC/ArminC-CS2-Cvars](https://github.com/ArmynC/ArminC-CS2-Cvars)

> Valve 没有提供公开的 CS2 ConVar 中文官方文档，因此翻译层完全依赖本地字典 + 社区数据 + MyMemory 的组合。

---

## 🔒 隐私说明

- 所有配置文件解析、翻译查询都在**浏览器本地**完成。
- 只有点击「🌐 开始联网翻译」时，会把**待翻译的命令名/描述文本**发送给 MyMemory API。
- 不会上传你的配置文件、Steam ID 或任何个人信息。

---

## ⚠️ 已知限制

- **Steam 路径自动探测**：仅 Python 桌面版支持；网页版需手动选择目录。
- **MyMemory 免费额度**：匿名用户约 5000 字符/天，超出后请求会被跳过。
- **Firefox 目录选择**：Firefox 不支持目录选择功能，网页版请改用「手动加载配置文件」或换用 Chrome / Edge。

---

## 🤝 反馈与贡献

- **Issue / PR**：[GitHub Issues](https://github.com/d1irgger/CS2-CFG-view/issues)
- **作者**：[@d1irgger](https://github.com/d1irgger)
- **Telegram**：[@timharrys](https://t.me/timharrys)

如果这个工具帮你省下了翻配置的时间，给一颗 ⭐ Star 就是最大的鼓励。

---

## 📄 许可

MIT License
