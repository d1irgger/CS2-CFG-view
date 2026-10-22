# CS2 CFG Viewer · 网页新版 v4.1.0

> 单文件 HTML 应用 · 零依赖 · 双击即用 针对最新版本CS2更新！！

本目录包含 `cs2cfgviewer.html`——CS2 CFG Viewer 的纯前端版本。整个应用就是一个 HTML 文件，可以直接在浏览器中打开使用，也可以上传到任意静态托管（GitHub Pages、Cloudflare Pages、Vercel）直接访问。

---

## 文件信息

| 项 | 值 |
|---|---|
| 文件名 | `cs2cfgviewer.html` |
| 版本 | 4.1.0 |
| 运行环境 | Chrome / Edge 推荐；Firefox 部分功能受限 |
| 外部依赖 | 仅联网翻译需要访问 MyMemory |

---

## 功能清单

### 数据源（三选一）

| 按钮 | 说明 |
|---|---|
| 📁 选择 Steam / userdata 目录 | 推荐。直接选 `Steam/userdata`，枚举更快 |
| 📂 手动加载配置文件 | 不需要目录权限，直接多选 `.vcfg / .txt / .cfg` |
| 📄 导入 autoexec.cfg | 解析 `bind` 指令和设置项（自动去重） |

### 翻译系统

三级翻译策略：

1. **预置中文**：约 150 条高频命令，表格打开即显示中文，零网络请求。
2. **官方描述增强**：约 100 条官方英文描述作为翻译上下文，机翻准确度显著提升。
3. **原始命令名**：无描述时的回退行为。

### 其他特性

- **多账户支持**：自动识别同一 Steam 下的多个账户，下拉框切换，路径栏同步显示当前选中账户。
- **实时搜索**：按键、命令、设置项、官方英文描述均可即时过滤。
- **联网翻译**：随时启动 / 停止，进度可见，失败条目自动重试。
- **cvarlist.md 导入**：一键扩展到 4000+ 条官方英文描述。
- **液态玻璃风格**：CS2 官方图标，轻量、干净、聚焦内容。

---

## 使用说明

### 数据源切换

工具栏的「数据源」下拉框支持三种类型：

| 数据源 | 说明 |
|---|---|
| **Steam 账户** | 选择 `userdata` 目录后自动列出所有账户，显示名为「昵称 (账号) [AccountID]」 |
| **autoexec** | 导入 `autoexec.cfg` 后可用，解析 `bind` 和设置项（自动去重） |
| **手动文件** | 通过「📂 手动加载配置文件」载入，不依赖 Steam 目录 |

切换数据源时，下拉框、路径栏、表格内容三者保持同步。

### 官方描述库扩展

1. 从 [SuGolYolLom/CS2-Cvars-Cmds](https://github.com/SuGolYolLom/CS2-Cvars-Cmds) 下载 `cvarlist.md`
2. 点击工具栏「📥 导入 cvarlist.md」
3. 设置项表格的「官方英文描述」列会显示对应描述
4. 后续联网翻译时，这些描述会作为上下文发送给翻译引擎

---

## 自定义

### 添加新的中文描述

打开 `cs2cfgviewer.html`，搜索 `CONVAR_DESC_CN`，在对象中追加键值：

```js
const CONVAR_DESC_CN = {
  // ... 已有
  "your_new_convar": "你的中文描述",
};
```

命中后该条目**不会**进入联网翻译队列。

### 添加新的官方英文描述

搜索 `CONVAR_DESC_EN`，同样追加：

```js
const CONVAR_DESC_EN = {
  // ... 已有
  "your_new_convar": "Official English description",
};
```

### 修改 UI 主题

所有颜色在 CSS `:root` 中定义：

```css
:root {
  --ink: #1a1d29;        /* 主文字色 */
  --ink2: #4a4f5c;       /* 次要文字色 */
  --glass: rgba(255,255,255,.58);  /* 玻璃背景 */
  --accent: #6aa0ff;     /* 主按钮渐变起始色 */
  --accent2: #a98bff;    /* 主按钮渐变结束色 */
}
```

修改这些变量即可整体换色，无需改动任何组件样式。

---

## 版本历史

| 版本 | 变化 |
|---|---|
| 4.1.0 | 官方描述增强翻译、cvarlist.md 导入、账户切换修复、CS2 官方图标 |
| 3.0.0 | 纯网页版，基础功能完整 |
| 2.x | PyWebView 桌面版 |
| 1.x | Tkinter 原生版 |

---

## 已知限制

| 限制 | 解决方案 |
|---|---|
| Firefox 无法选目录 | 用「手动加载配置文件」或换 Chrome / Edge |
| Steam 路径无法自动探测 | 手动选择 `Steam/userdata` 目录 |
| 大目录扫描慢 | 直接选 `userdata`，而非 Steam 根 |
| 联网翻译受限于 MyMemory 免费额度 | 分多次运行，或改用自建翻译服务 |
| 无法写回配置文件 | 需要写回请用 Python 版本 |

---

## 相关链接

- **项目主页**：[d1irgger/CS2-CFG-view](https://github.com/d1irgger/CS2-CFG-view)
- **CS2 官方英文描述**：[SuGolYolLom/CS2-Cvars-Cmds](https://github.com/SuGolYolLom/CS2-Cvars-Cmds)
- **备选描述源**：[ArmynC/ArminC-CS2-Cvars](https://github.com/ArmynC/ArminC-CS2-Cvars)
- **翻译 API**：[MyMemory Translation API](https://mymemory.translated.net/doc/spec.php)
