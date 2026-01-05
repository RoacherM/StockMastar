# Command Reference

## 完整分析流程

```bash
# 1. 创建分析目录
WORK_DIR="workspace/sh_601138_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$WORK_DIR"

# 2. 获取K线数据 (使用 stock-data-fetcher)
uv run python .claude/skills/stock-data-fetcher/scripts/fetch_stock_data.py \
    sh.601138 --days 500 --cache-dir "$WORK_DIR"

# 3. 重命名数据文件
mv "$WORK_DIR"/sh_601138/*.csv "$WORK_DIR/kline.csv"

# 4. Claude 执行威科夫分析，生成 analysis.json
# (通过对话完成)

# 5. 复制图表模板
cp .claude/skills/wyckoff-analyst/assets/chart_template.html "$WORK_DIR/chart.html"

# 6. 启动预览服务器
cd "$WORK_DIR" && python -m http.server 8000
# 打开 http://localhost:8000/chart.html
```

## 单独获取数据

```bash
# K线数据
uv run python .claude/skills/stock-data-fetcher/scripts/fetch_stock_data.py sh.601138 --days 500

# 财务数据
uv run python .claude/skills/stock-data-fetcher/scripts/fetch_stock_data.py sh.601138 --type profit --year 2024 --quarter 3
```

## MCP 指标获取

```python
# 移动平均线
a-share-mcp_get_moving_averages(code="sh.601138", start_date="2024-01-01", end_date="2024-12-31", periods=[50, 200])

# 技术指标
a-share-mcp_get_technical_indicators(code="sh.601138", start_date="2024-01-01", end_date="2024-12-31")

# 风险指标
a-share-mcp_calculate_risk_metrics(code="sh.601138", period="1Y")
```

## 快速预览

```bash
# 直接用 Python 服务器
cd workspace/sh_601138_xxx && python -m http.server 8000
```
