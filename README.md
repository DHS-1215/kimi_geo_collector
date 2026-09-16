# KIMI GEO Collector

基于 Playwright + Chrome CDP 实现的 KIMI GEO 自动化采集系统。

系统面向 GEO（Generative Engine Optimization，生成式引擎优化）数据采集场景，自动完成 KIMI 网页端问题提交、回答获取、引用信源采集、任务状态记录、断点续跑以及标准 GEO 数据包导出。

当前支持：

- 鸿茅药酒
- 天益寿气血固本

---

## 1. 项目简介

KIMI GEO Collector 用于批量采集 KIMI 在不同回答模式下对指定问题的回答结果及引用信源，并将采集结果统一转换为标准 GEO 数据结构。

系统通过 Playwright 连接独立 Chrome CDP 浏览器会话，在保留真实登录状态的情况下完成自动化采集。

主要流程：

```text
选择采集产品
    ↓
读取问题 CSV
    ↓
构建 quick / expert 任务
    ↓
连接 KIMI Chrome
    ↓
创建新会话
    ↓
切换回答模式
    ↓
发送问题
    ↓
等待回答完成
    ↓
提取正文与引用信源
    ↓
保存 Checkpoint
    ↓
生成标准 GEO 数据包
    ↓
生成 ZIP
```

---

## 2. 核心功能

### KIMI 自动化采集

支持自动完成：

- KIMI 页面连接
- 新建会话
- 回答模式切换
- 自动输入问题
- 自动发送问题
- 流式回答完成检测
- 回答正文提取
- 引用信源提取
- 会话 URL 保存

### 双模式 GEO 采集

正式 GEO 任务支持：

```text
KIMI 标准模式 → quick
KIMI 进阶模式 → expert
```

每一道问题默认生成两个采集任务。

例如：

```text
6 道问题 × 2 个模式 = 12 个任务
```

---

## 3. 支持产品

当前支持两个正式采集产品：

```text
1. 鸿茅药酒
2. 天益寿气血固本
```

对应问题文件：

```text
input/
├── hongmao_questions.csv
├── tianyishou_questions.csv
└── kimi_w6_smoke.csv
```

产品信息由系统动态识别，并写入最终 GEO 数据包的 `manifest.json`。

---

## 4. GEO 标准数据包

每次完整采集结束后，系统会自动生成标准 GEO 数据目录及 ZIP 压缩包。

标准数据包包含：

```text
manifest.json
tasks.jsonl
answers.jsonl
sources.jsonl
checksums.json
```

### manifest.json

记录平台、产品、Batch、任务数、回答数、信源数及采集状态等信息。

### tasks.jsonl

记录每一个 GEO 采集任务，包括：

- task_id
- batch_id
- question_id
- question
- mode_code
- task_status
- error_code
- error_message

### answers.jsonl

记录 KIMI 回答，包括：

- question
- answer
- mode
- acquisition_status
- validation_status
- conversation_url
- source_count
- collected_at

### sources.jsonl

记录 KIMI 回答中实际展示的引用信源。

如果某次回答没有展示引用来源，则该回答的信源数量记为 0，不会人为补充或构造信源。

### checksums.json

保存标准数据文件的 SHA-256 校验值，用于检查数据包完整性。

---

## 5. Checkpoint 与断点续跑

系统支持任务级 Checkpoint。

每完成一个任务后都会立即保存结果。

如果采集过程中出现：

- KIMI 服务容量限制
- 浏览器异常
- 网络异常
- 程序中断
- 人工停止

已经完成的任务不会丢失。

重新运行系统并选择相同产品后，可以自动识别未完成 Batch：

```text
[RESUME] True
```

系统将跳过已经成功完成的任务，从未完成任务继续采集。

---

## 6. 服务容量限制处理

系统可以识别 KIMI 服务容量限制状态。

检测到服务容量限制后：

```text
当前任务结果保存
    ↓
Checkpoint 标记 interrupted
    ↓
停止继续请求
    ↓
不生成不完整正式数据包
```

等待 KIMI 服务恢复后重新启动程序，即可继续原 Batch。

---

## 7. 一键启动

Windows 环境下可直接运行：

```text
start_kimi.bat
```

一键启动脚本会自动：

```text
检查项目虚拟环境
    ↓
清除测试模式变量
    ↓
检查 Chrome
    ↓
检查 CDP 9224
    ↓
自动启动 KIMI Chrome（如需要）
    ↓
启动正式 GEO Pipeline
```

脚本直接调用：

```text
.venv\Scripts\python.exe
```

因此不依赖人工激活虚拟环境。

---

## 8. 手动启动

进入项目目录：

```powershell
cd D:\kimi_geo_collector
```

激活虚拟环境：

```powershell
.\.venv\Scripts\Activate.ps1
```

运行正式 Pipeline：

```powershell
python -m scripts.run_kimi_pipeline
```

程序会显示：

```text
============================================================
KIMI GEO Collection Pipeline
============================================================

请选择采集产品：

1. 鸿茅药酒
2. 天益寿气血固本

Q. 退出
```

选择产品后即可开始正式采集。

---

## 9. Chrome CDP

系统默认通过以下地址连接 Chrome：

```text
http://127.0.0.1:9224
```

独立 Chrome Profile：

```text
D:\kimi_profiles\profile_002
```

Chrome 启动参数示例：

```powershell
Start-Process "C:\Program Files\Google\Chrome\Application\chrome.exe" -ArgumentList @(
    "--remote-debugging-port=9224",
    "--user-data-dir=D:\kimi_profiles\profile_002",
    "https://www.kimi.com/"
)
```

使用独立 Profile 可以保留 KIMI 登录状态，同时避免干扰日常 Chrome 环境。

---

## 10. 测试模式

开发和 Smoke Test 时，可以限制只运行部分问题。

```powershell
$env:KIMI_QUESTION_LIMIT="1"
python -m scripts.run_kimi_pipeline
```

此时系统会显示：

```text
[TEST MODE] KIMI_QUESTION_LIMIT=1
[TEST MODE] 当前仅运行部分题目，不是正式全量采集。
```

正式采集前应清除测试变量：

```powershell
Remove-Item Env:KIMI_QUESTION_LIMIT -ErrorAction SilentlyContinue
```

使用 `start_kimi.bat` 时会自动清除此变量。

---

## 11. 项目结构

```text
kimi_geo_collector/
│
├── app/
│   ├── browser/
│   │   └── cdp.py
│   │
│   └── kimi/
│       ├── answer.py
│       ├── capacity.py
│       ├── checkpoint.py
│       ├── checksum.py
│       ├── client.py
│       ├── exporter.py
│       ├── extractor.py
│       ├── geo_contract.py
│       ├── loader.py
│       ├── manifest.py
│       ├── models.py
│       ├── packager.py
│       ├── result.py
│       ├── risk_control.py
│       ├── runner.py
│       ├── selectors.py
│       ├── source.py
│       └── types.py
│
├── input/
│   ├── hongmao_questions.csv
│   ├── tianyishou_questions.csv
│   └── kimi_w6_smoke.csv
│
├── scripts/
│   ├── run_kimi_pipeline.py
│   ├── smoke_cdp.py
│   └── probe_kimi_*.py
│
├── tests/
│   ├── test_cdp_page_selection.py
│   ├── test_kimi_checkpoint.py
│   ├── test_kimi_exporter.py
│   ├── test_kimi_geo_contract.py
│   ├── test_kimi_loader.py
│   └── test_kimi_packager.py
│
├── output/
│   ├── checkpoints/
│   └── package/
│
├── start_kimi.bat
├── .gitignore
└── README.md
```

---

## 12. 自动化测试

运行全部测试：

```powershell
python -m pytest -v
```

当前版本测试结果：

```text
15 passed
```

覆盖内容包括：

- CDP 页面选择
- GEO 模式映射
- 产品动态解析
- Question / Task / Answer ID
- UTF-8 CSV
- UTF-8 BOM CSV
- Checkpoint
- Interrupted Resume
- Force New Batch
- 动态产品 Manifest
- GEO 标准文件导出
- ZIP 标准包生成
- 缺失文件保护

---

## 13. 编译检查

可通过以下命令检查 Python 文件语法：

```powershell
python -m compileall .\app .\scripts
```

---

## 14. 输出目录

正式采集完成后：

```text
output/
├── checkpoints/
│   └── <product_id>/
│
└── package/
    ├── <batch_id>/
    │   ├── manifest.json
    │   ├── tasks.jsonl
    │   ├── answers.jsonl
    │   ├── sources.jsonl
    │   └── checksums.json
    │
    └── <batch_id>.zip
```

ZIP 文件可用于后续 GEO 分析系统导入。

---

## 15. 技术栈

主要技术：

```text
Python 3.11
Playwright
Chrome CDP
Pytest
JSON / JSONL
CSV
SHA-256
ZIP
```

---

## 16. 当前版本

```text
KIMI GEO Collector v1.0
```

当前版本已经完成：

- KIMI 正式采集主链
- quick / expert 双模式
- 双产品支持
- 回答正文采集
- 引用信源采集
- 风控处理
- 服务容量限制检测
- Checkpoint
- 断点续跑
- 标准 GEO 数据导出
- SHA-256 完整性校验
- ZIP 自动打包
- Windows 一键启动
- 自动化测试
- 元宝模板遗留代码清理

项目目前进入稳定维护阶段。
