# 🎮 CS2 CFG Viewer

> 把复杂的 CS2 配置文件，变成一眼能读懂的中文界面。

一款专为 Counter-Strike 2 打造的 **CFG / VCFG 可视化解析器**。  
支持按键绑定、命令、视频设置的智能中文翻译，让你秒懂自己（或别人）的配置。

---

## ✨ 核心亮点

- **智能中文翻译** — 按键、命令、设置项全部本地字典优先，未命中才可选机翻
- **多格式支持** — `.vcfg` / `.txt` / `autoexec.cfg` 全兼容
- **Steam 目录一键扫描** — 自动识别多账户配置
- **ProSettings 联动** — 直接下载并解析职业选手 autoexec
- **双版本可选**
  - **WebUI 焕新版**（推荐）— 白色液态玻璃风格，PyWebView 驱动
  - **原生 UI 版** — 纯 Tkinter，零额外依赖

---

## 🚀 快速开始

### WebUI 焕新版（推荐）

```bash
git clone https://github.com/d1irgger/CS2-CFG-view.git
cd "CS2-CFG-view/WebUI焕新版WebUI New Look"
pip install pywebview
python cs2cfgviewernew.py
原生 UI 版
Bashcd "CS2-CFG-view/原生UI版本Native UI version"
python cs2_cfg_viewer.py
选择 Steam 目录，或直接拖入 / 下载 autoexec，即可开始探索。

🛠️ 技术栈
Python 3.10+ · PyWebView / Tkinter · 本地词典 + 可选机翻

📬 反馈
由 @d1irgger 设计开发。

欢迎 Issue / PR。
如果觉得好用，给一颗 Star — 这是最大的鼓励。
