# CS2 CFG Viewer · 网页新版 v4.1.0

> 单文件 HTML 应用 · 零依赖 · 双击即用

本目录包含 `cs2cfgviewer.html`——CS2 CFG Viewer 的纯前端版本。整个应用就是一个 HTML 文件，包含全部样式、逻辑和数据字典，可以直接在浏览器中打开使用，也可以上传到任意静态托管（GitHub Pages、Cloudflare Pages、Vercel）直接访问。

---

## 文件信息

| 项 | 值 |
|---|---|
| 文件名 | `cs2cfgviewer.html` |
| 版本 | 4.1.0 |
| 大小 | 约 100 KB（单文件，无外部依赖） |
| 运行环境 | Chrome 90+ / Edge 90+（推荐）；Firefox 不支持目录选择 |
| 外部网络依赖 | `https://api.mymemory.translated.net/get`（可选，仅联网翻译时使用） |
| 外部资源 | CS2 图标（Valve Developer Community CDN） |

---

## 功能清单

### 数据源（三选一）

| 按钮 | 实现方式 | 说明 |
|---|---|---|
| 📁 选择 Steam / userdata 目录 | `<input webkitdirectory>` | 枚举整个目录树，通过 `webkitRelativePath` 解析账户和 cfg 文件 |
| 📂 手动加载配置文件 | `<input multiple>` | 直接多选 `.vcfg / .txt / .cfg` 文件，无需目录 |
| 📄 导入 autoexec.cfg | `<input accept=".cfg,.txt">` | 解析 `bind` 指令和设置项（自动去重） |

### 数据解析

- **VDF 解析器**（`class VDFParser`）：手写递归下降解析器，支持嵌套块、字符串转义、行内注释 `//`。
- **CFG tokenizer**（`tokenizeCfgLine`）：处理引号、反斜杠转义、行内注释 `//`、语句分隔符 `;`。
- **autoexec 解析**（`parseAutoexecCfg`）：提取 `bind` 指令和其余设置项，跳过 `echo / exec / alias` 等元命令。
- **多编码回退**（`readTextWithFallback`）：依次尝试 `utf-8 → utf-16le → utf-16be → gbk → gb18030 → big5 → shift_jis → latin1`，最后无损失回退 `utf-8`。

### 翻译系统

三级策略：

```
┌─────────────────────────────────────────────────┐
│ 层级 1：CONVAR_DESC_CN（预置中文，约 150 条）     │
│   → 表格打开即显示中文，零网络请求                │
├─────────────────────────────────────────────────┤
│ 层级 2：CONVAR_DESC_EN（官方英文描述，约 100 条） │
│   → 联网翻译时构造 "描述 (命令名)" 作为完整语义   │
├─────────────────────────────────────────────────┤
│ 层级 3：原始命令名                                │
│   → 无描述时的回退行为，与 v3.0.0 一致            │
└─────────────────────────────────────────────────┘
```

- **本地字典**：`KEY_NAME_CN`、`CMD_NAME_CN`、`VIDEO_NAME_CN`、`VIDEO_VALUE_CN` 四本。
- **官方描述增强**：`CONVAR_DESC_CN`（中文预翻译）和 `CONVAR_DESC_EN`（英文官方描述）。
- **cvarlist.md 导入**：从 SuGolYolLom / ArmynC 仓库下载后一键导入，可将英文描述库扩展到 4000+ 条。
- **联网翻译**：`startOnline()` 逐条串行请求 MyMemory，带 6 秒超时、内存缓存、取消令牌（`threadToken`）。

---

## 代码结构（按文件中顺序）

```
cs2cfgviewer.html
│
├── <style>                              # 液态玻璃 UI（约 300 行）
│
├── <body>                               # 骨架：header / toolbar / tabs / footer
│
└── <script>
    ├── 数据字典
    │   ├── KEY_NAME_CN                  # 按键名 → 中文（约 150 项）
    │   ├── CMD_NAME_CN                  # 命令 → 中文（约 200 项）
    │   ├── VIDEO_NAME_CN                # 设置项名 → 中文（约 200 项）
    │   ├── VIDEO_VALUE_CN               # 设置项值 → 中文（约 80 组）
    │   ├── CONVAR_DESC_CN               # 高频命令官方中文描述（约 150 项）⭐ v4.1.0 新增
    │   └── CONVAR_DESC_EN               # 官方英文描述（约 100 项，可导入扩展）⭐ v4.1.0 新增
    │
    ├── 翻译工具
    │   ├── normalizeKeyName             # 去掉 key_ 前缀并转小写
    │   ├── lookup                       # 大小写 + ±前缀兜底查找
    │   ├── translateKeyLocal            # 按键名翻译
    │   ├── translateCmdLocal            # 命令翻译（支持多词组合）
    │   ├── translateVideoKeyLocal       # 设置项名翻译
    │   ├── translateVideoValueLocal     # 设置项值翻译
    │   ├── lookupDescCN / lookupDescEN  # 描述查找（支持 setting.xxx / xxx）⭐
    │   └── cleanVideoKeyForTranslation  # 清洗 setting. 前缀与下划线
    │
    ├── cfg 解析
    │   ├── tokenizeCfgLine              # cfg 行 tokenizer
    │   ├── parseAutoexecCfg             # autoexec 专用解析
    │   └── dedupeSettings               # 设置项去重（保留最后值）
    │
    ├── VDF 解析
    │   ├── class VDFParser              # 递归下降解析器
    │   ├── findSection                  # 递归查找子块
    │   └── collectLeaves                # 展平嵌套块为点分路径
    │
    ├── 文件读取
    │   ├── readTextWithFallback         # 多编码回退
    │   ├── findFileInList               # 按关键词 + 扩展名 + 长度排序找最优匹配
    │   └── parseCvarlistMarkdown        # cvarlist.md 解析 ⭐ v4.1.0 新增
    │
    ├── Steam 扫描
    │   ├── steamId64ToAccountId         # BigInt 转换 SteamID64 → AccountID
    │   └── scanSteamUsers               # 从 fileMap 提取账户和 cfg 文件
    │
    ├── 数据源加载
    │   ├── processConvarData            # 提取 convars 块
    │   ├── processUserKeysData          # 提取 bindings 和 analogbindings
    │   ├── processVideoData             # 提取 video 叶子节点
    │   └── loadCs2ConfigsFromEntries    # 遍历 FILE_SPECS 加载 4 种文件
    │
    ├── 视图构建
    │   ├── makeKey / makeVideo          # 单条记录 → 视图对象
    │   ├── buildDiagnosis               # 诊断文本
    │   └── buildView                    # 完整视图（含 summary）
    │
    ├── 渲染层
    │   ├── renderSourceSelect           # 下拉框（保留当前选中）⭐ 修复
    │   ├── renderPath                   # 路径栏（显示当前账户）⭐ 修复
    │   ├── renderKeys / renderVideo     # 表格渲染（含官方描述列）
    │   ├── renderRaw / renderDiagnosis  # 原始文本 / 诊断
    │   └── renderAll                    # 统一入口：先下拉再路径再表格
    │
    ├── 数据源切换
    │   ├── applyVcfgSource              # 应用 VCFG 数据
    │   ├── loadSelectedSource           # 根据下拉框值加载
    │   ├── handleDirFiles               # 目录扫描入口
    │   ├── handleManualFiles            # 手动文件入口
    │   └── handleAutoexecFile           # autoexec 导入入口
    │
    ├── 联网翻译
    │   ├── translateOne                 # 单条请求（含描述增强、缓存、超时）
    │   ├── collectPending               # 收集待翻译条目（分层判断）
    │   ├── startOnline                  # 串行执行 + 进度推送
    │   └── stopOnline                   # 取消（threadToken）
    │
    ├── cvarlist 导入
    │   └── importCvarlist               # 解析并合并到 CONVAR_DESC_EN ⭐ v4.1.0 新增
    │
    └── 启动
        ├── bindEvents                   # 所有 DOM 事件绑定
        └── renderAll()                  # 首次渲染
```

---

## 关键实现说明

### 1. 为什么用 `webkitdirectory` 而不是 `showDirectoryPicker`？

`showDirectoryPicker`（File System Access API）只在 Chromium 内 HTTPS 环境可用，且无法跨平台兼容；`webkitdirectory` 兼容性更好，`file://` 协议也能用，代价是一次性枚举整个目录树。

**建议直接选择 `Steam/userdata` 而不是 `Steam` 根目录**——前者只需枚举几十个文件，后者可能枚举上万个。

### 2. 账户切换不跳回第一个（v4.1.0 修复）

`renderSourceSelect()` 在清空重建之前记录 `prev = sel.value`，重建后若该选项仍存在就恢复。`renderAll()` 顺序固定为：先 `renderSourceSelect()` 再 `renderPath()`，确保路径栏读到的是正确选中项。

### 3. 描述增强翻译的工作原理

以 `cl_crosshaircolor` 为例：

```js
// 原请求（无描述）
GET ?q=cl%20crosshaircolor&langpair=en|zh-CN
→ 返回 "cl 准星颜色"（残留碎片）

// 增强后（有描述）
GET ?q=Crosshair%20color%20(cl_crosshaircolor)&langpair=en|zh-CN
→ 返回 "准星颜色（cl_crosshaircolor）"
→ 正则清理末尾括号 → "准星颜色"
```

### 4. MyMemory 限流处理

- 缓存 key 使用完整 `query`，避免不同命令共享错误缓存。
- 6 秒超时 + `AbortController`。
- 返回 `MYMEMORY WARNING` 开头即丢弃。
- 失败条目**不标记**，下次点击「开始联网翻译」时 `collectPending()` 会重新收集，自动重试。

---

## 自定义与扩展

### 添加新的高频中文描述

在 `CONVAR_DESC_CN` 对象中追加键值：

```js
const CONVAR_DESC_CN = {
  // ... 已有
  "your_new_convar": "你的中文描述",
};
```

规则：
- `setting.xxx` 和 `xxx` 两种 key 都支持。
- 命中后该条目**不会**进入联网翻译队列。

### 添加新的官方英文描述

在 `CONVAR_DESC_EN` 中追加：

```js
const CONVAR_DESC_EN = {
  // ... 已有
  "your_new_convar": "Official English description",
};
```

下次联网翻译时，请求会变成 `"Official English description (your_new_convar)"`。

### 批量导入 cvarlist.md

1. 从 [SuGolYolLom/CS2-Cvars-Cmds](https://github.com/SuGolYolLom/CS2-Cvars-Cmds/blob/main/cs2/cvarlist.md) 下载
2. 点击「📥 导入 cvarlist.md」
3. 自动解析并合并到 `CONVAR_DESC_EN`

解析器兼容：
- Markdown 表格格式：`Name | Flags | Description`
- 制表符分隔格式
- 自动清理 `FCVAR_*` 和 `**Default:**` 残留

### 修改 UI 主题

所有颜色在 CSS `:root` 中定义：

```css
:root {
  --ink: #1a1d29;        /* 主文字色 */
  --ink2: #4a4f5c;       /* 次要文字色 */
  --glass: rgba(255,255,255,.58);  /* 玻璃背景 */
  --accent: #6aa0ff;     /* 主按钮渐变起始色 */
  --accent2: #a98bff;    /* 主按钮渐变结束色 */
  /* ... */
}
```

修改这些变量即可整体换色，无需改任何组件样式。

---

## 调试技巧

### 在浏览器控制台手动触发

```js
// 查看当前状态
console.log(state);

// 手动调用翻译
await translateOne("cl_crosshaircolor", state.online.threadToken, "Crosshair color");

// 查看收集到的待翻译条目
console.log(collectPending());

// 手动测试 cvarlist 解析
parseCvarlistMarkdown(`cl_test | FCVAR_CHEAT | Test description here`);

// 查看描述库大小
console.log("中文描述:", Object.keys(CONVAR_DESC_CN).length);
console.log("英文描述:", Object.keys(CONVAR_DESC_EN).length);
```

### 常用状态字段

| 字段 | 说明 |
|---|---|
| `state.source` | 原始解析结果（未翻译） |
| `state.view` | 构建后的视图（已翻译） |
| `state.users` | Steam 账户列表 |
| `state.autoexecFile` | 当前 autoexec 文件 |
| `state.online` | 联网翻译运行时状态 |
| `state.online.cache` | 翻译内存缓存（Map） |

---

## 版本历史

| 版本 | 日期 | 变化 |
|---|---|---|
| 4.1.0 | 当前 | 官方描述增强翻译、cvarlist.md 导入、账户切换修复、CS2 官方图标 |
| 3.0.0 | - | PyWebView 版同步的纯网页版，基础功能完整 |
| 2.x | - | PyWebView 桌面版 |
| 1.x | - | Tkinter 原生版 |

---

## 已知限制

| 限制 | 原因 | 解决方案 |
|---|---|---|
| Firefox 无法选目录 | Firefox 不支持 `webkitdirectory` | 用「手动加载配置文件」或换 Chrome / Edge |
| Steam 路径无法自动探测 | 浏览器无文件系统/注册表权限 | 手动选择 `Steam/userdata` 目录 |
| 大目录扫描慢 | `webkitdirectory` 一次性枚举整个树 | 直接选 `userdata`，而非 Steam 根 |
| 联网翻译受限于 MyMemory 免费额度 | 匿名用户 ~5000 字符/天 | 分多次运行，或改用自建翻译服务 |
| 无法写回配置文件 | 原版也无此功能 | 需要写回请用 Python 版本 |

---

## 相关链接

- **项目主页**：[d1irgger/CS2-CFG-view](https://github.com/d1irgger/CS2-CFG-view)
- **CS2 官方英文描述**：[SuGolYolLom/CS2-Cvars-Cmds](https://github.com/SuGolYolLom/CS2-Cvars-Cmds)
- **备选描述源**：[ArmynC/ArminC-CS2-Cvars](https://github.com/ArmynC/ArminC-CS2-Cvars)
- **翻译 API**：[MyMemory Translation API](https://mymemory.translated.net/doc/spec.php)
- **作者 Telegram**：[@timharrys](https://t.me/timharrys)
