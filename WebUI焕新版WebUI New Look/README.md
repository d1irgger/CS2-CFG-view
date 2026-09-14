# 🎮 CS2 CFG Viewer · WebUI 焕新版

> v3.0 · 白色液态玻璃 · 更轻、更净、更好看

从原生 Tkinter 全面迁移到 **PyWebView + 现代 WebUI**。  
界面灵感来自 WinUI / Fluent Design，字典大幅精简，只保留真正高频的核心项。

---

## ✨ 这一版改了什么

- **界面重做** — 白色液态玻璃风格，圆角、柔和阴影、流畅动效
- **字典精简** — 设置项只保留高频核心翻译，加载更快、更干净
- **按键 / 命令全保留** — 绑定翻译依然完整
- **原生体验** — DPI 感知、Segoe UI / SF Pro 字体、无边框现代窗口
- **功能完整保留** — Steam 多账户扫描、VCFG 解析、autoexec 导入、ProSettings 下载、可选机翻、诊断信息

---

## 🚀 快速开始

```bash
git clone https://github.com/d1irgger/CS2-CFG-view.git
cd "CS2-CFG-view/WebUI焕新版WebUI New Look"
pip install pywebview
python cs2cfgviewernew.py
选择 Steam 目录，或访问(https://prosettings.net/games/cs2/)搜索ID直接/ 下载 autoexec，即可查看职业哥同款设定。

📂 目录结构
textWebUI焕新版WebUI New Look/
├── cs2cfgviewernew.py   # 主程序（后端 + API）
├── web/
│   └── index.html       # 前端界面
└── dabao.txt            # 打包命令参考

🛠️ 技术栈
Python 3.10+ · PyWebView · 原生 HTML/CSS/JS · 本地词典 + 可选机翻

📬 反馈
由 @d1irgger 设计开发。

欢迎 Issue / PR。
如果喜欢这版新界面，给一颗 Star — 这是最大的鼓励。
