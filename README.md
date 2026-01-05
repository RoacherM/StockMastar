# StockAgent - A股威科夫分析助手

基于 Claude AI 的 A 股市场分析工具，专注于威科夫（Wyckoff）市场结构分析。

## 功能特性

- **威科夫市场结构分析**: 自动识别吸筹/派发形态、Phase A-E 阶段、关键事件（SC/AR/Spring/SOS 等）
- **交互式图表**: 生成带有详细中文标注的 ECharts 可视化图表
- **A股数据支持**: 通过 Baostock MCP 获取实时和历史行情数据

## 项目结构

```
StockAgent/
├── .claude/skills/           # Claude Skills 定义
│   ├── wyckoff-analyst/      # 威科夫分析 Skill
│   │   ├── SKILL.md          # Skill 主文件
│   │   ├── assets/           # 图表模板
│   │   ├── scripts/          # 数据获取脚本
│   │   └── references/       # 参考文档
│   └── stock-data-fetcher/   # 数据获取 Skill
├── workspace/                # 分析输出目录
├── main.py                   # 入口文件
└── pyproject.toml            # 项目配置
```

## 快速开始

### 环境要求

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) 包管理器
- Claude Desktop 或 OpenCode CLI

### 安装

```bash
# 克隆项目
git clone <repo-url>
cd StockAgent

# 安装依赖
uv sync
```

### 使用方式

#### 1. 威科夫分析

在 Claude 对话中触发威科夫分析：

```
分析 sh.600601 的威科夫结构
```

或

```
对方正科技做一个 Wyckoff 分析
```

#### 2. 查看图表

分析完成后，启动本地服务器查看图表：

```bash
cd workspace/<stock_code>_<date>
python -m http.server 8000
# 浏览器打开 http://localhost:8000/chart.html
```

## Skills 说明

### wyckoff-analyst

执行威科夫市场结构分析并生成交互式图表。

**触发场景:**
- 分析股票吸筹/派发形态
- 识别威科夫阶段 (Phase A-E)
- 标注 SC/AR/Spring/SOS 等事件
- 用户提到"威科夫分析"或"Wyckoff"

**输出文件:**
- `kline.csv` - K线历史数据
- `analysis.json` - 分析配置
- `chart.html` - 交互式图表

### stock-data-fetcher

获取 A 股数据并缓存到本地 CSV 文件。

**使用场景:**
- 获取超过 100 条的 K 线数据
- 需要多次查询同一股票数据
- 避免 MCP 返回大量数据占用上下文

## 图表功能

- **价格线**: 黑色收盘价曲线
- **均线**: MA50（蓝虚线）、MA200（红虚线）
- **Phase 标签**: 图表上方固定区域竖排显示
- **Zone 背景**: 吸筹区（淡绿）、派发区（淡红）
- **事件标注**: 智能防重叠，高价事件显示在下方，低价事件显示在上方
- **DataZoom**: 支持缩放和平移查看不同时间范围

## 开发说明

### 添加新 Skill

参考 `.claude/skills/skill-creator/SKILL.md` 创建新的 Skill。

### 修改图表模板

图表模板位于 `.claude/skills/wyckoff-analyst/assets/chart_template.html`，基于 ECharts 5.4.3。

## 注意事项

1. **数据获取**: K 线数据必须通过 Python 脚本获取（保存为 CSV），不要使用 MCP 直接获取大量数据
2. **分析范围**: 威科夫分析建议使用 500-750 个交易日（2-3 年）的数据
3. **工作目录**: 每次分析会在 `workspace/` 下创建独立目录

## License

MIT
