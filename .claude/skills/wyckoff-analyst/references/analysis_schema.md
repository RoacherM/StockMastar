# Analysis JSON Schema

Claude 分析完成后，生成 `analysis.json` 文件，供图表渲染使用。

## 完整结构

```json
{
  "stock": {
    "code": "sh.601138",
    "name": "工业富联"
  },
  "quote": "当大众最贪婪的时候，往往是主力最想离开的时候。",
  "phases": [
    {
      "name": "Phase A",
      "start": "2024-01-02",
      "end": "2024-02-15",
      "description": "初步停止下跌趋势"
    },
    {
      "name": "Phase B",
      "start": "2024-02-16",
      "end": "2024-06-30",
      "description": "构建原因，主力吸筹"
    }
  ],
  "zones": [
    {
      "type": "accumulation",
      "label": "吸筹区 (Accumulation)",
      "top": 15.5,
      "bottom": 12.8,
      "start": "2024-01-18",
      "end": "2024-08-15"
    },
    {
      "type": "distribution",
      "label": "潜在派发区",
      "top": 28.0,
      "bottom": 24.5,
      "start": "2024-10-01",
      "end": "2024-12-31"
    }
  ],
  "events": [
    {
      "date": "2024-01-18",
      "price": 13.71,
      "type": "SC",
      "label": "恐慌抛售：放量急跌后强势反弹，显示承接力量入场"
    },
    {
      "date": "2024-01-22",
      "price": 14.94,
      "type": "AR",
      "label": "自动反弹：卖压释放后的首次回升"
    },
    {
      "date": "2024-02-05",
      "price": 13.81,
      "type": "ST",
      "label": "二次测试：回踩SC低点，成交量萎缩确认支撑"
    },
    {
      "date": "2024-04-08",
      "price": 12.86,
      "type": "Spring",
      "label": "弹簧效应：跌破支撑后快速收回，洗盘完成"
    },
    {
      "date": "2024-08-19",
      "price": 30.46,
      "type": "JAC",
      "label": "跳跃小溪：放量突破阻力区，确认趋势反转"
    },
    {
      "date": "2024-10-28",
      "price": 52.61,
      "type": "BC",
      "label": "抢购高潮：天量滞涨，警惕派发信号"
    }
  ],
  "summary": "<strong>当前判断：Phase D → Phase E 过渡期</strong><br><br>价格已成功突破吸筹区上沿，MA50金叉MA200确认中期趋势向上。<br><br>• <strong>支撑位:</strong> 25-28 元 (原阻力转支撑)<br>• <strong>阻力位:</strong> 35-38 元<br>• <strong>策略:</strong> 回踩支撑区可分批建仓，跌破25元止损"
}
```

## 字段说明

### stock (必填)
| 字段 | 类型 | 说明 |
|------|------|------|
| code | string | 股票代码 (sh.600000) |
| name | string | 股票名称 |

### quote (可选)
威科夫风格的一句话评论，显示在分析面板顶部。

### phases (必填)
威科夫阶段列表，按时间顺序排列。

| 字段 | 类型 | 说明 |
|------|------|------|
| name | string | 阶段名称: Phase A / B / C / D / E |
| start | string | 开始日期 YYYY-MM-DD |
| end | string | 结束日期 (可选) |
| description | string | 阶段描述 (可选) |

### zones (必填)
吸筹/派发区域，用于图表绘制阴影区。

| 字段 | 类型 | 说明 |
|------|------|------|
| type | string | `accumulation` 或 `distribution` |
| label | string | 显示标签 |
| top | number | 价格上沿 |
| bottom | number | 价格下沿 |
| start | string | 开始日期 |
| end | string | 结束日期 |

**Zone 定义规则 (CRITICAL):**

1. **高度 (top/bottom)**:
   - 选取 **Phase B 中量价最密集**的收盘价区间
   - **必须剔除** SC 的下影线极值和 AR 的上影线极值
   - 目标：体现价格"横向蓄力"的核心震荡区，而非全价位覆盖

2. **宽度 (start/end)**:
   - `start`: SC（恐慌抛售）发生日期
   - `end`: **带量突破**上沿（SOS/JAC）的日期
   - 如果尚未突破，`end` 设为最新日期

3. **多区域**:
   - 如果存在多个吸筹区和派发区，**必须全部定义**
   - 例如：先吸筹后派发、或多次吸筹

### events (必填)
关键威科夫事件列表。

| 字段 | 类型 | 说明 |
|------|------|------|
| date | string | 事件日期 YYYY-MM-DD |
| price | number | 事件价格 |
| type | string | 事件类型 (见下表) |
| label | string | 威科夫风格的解释 |

**事件类型:**
| 代码 | 英文 | 中文 | 说明 |
|------|------|------|------|
| PS | Preliminary Support | 初步支撑 | 下跌趋势中首次出现买盘 |
| SC | Selling Climax | 恐慌抛售 | 放量急跌，卖压宣泄 |
| BC | Buying Climax | 抢购高潮 | 放量急涨，买盘疯狂 |
| AR | Automatic Rally/Reaction | 自动反弹 | 高潮后的自然反向运动 |
| ST | Secondary Test | 二次测试 | 回测高潮价位 |
| Spring | Spring | 弹簧 | 跌破支撑后快速收回 (吸筹) |
| UTAD | Upthrust After Distribution | 上冲回落 | 突破阻力后快速回落 (派发) |
| SOS | Sign of Strength | 强势信号 | 放量突破，确认需求 |
| SOW | Sign of Weakness | 弱势信号 | 放量下跌，确认供应 |
| LPS | Last Point of Support | 最后支撑 | 突破前最后回踩 |
| LPSY | Last Point of Supply | 最后供应 | 下跌前最后反弹 |
| JAC | Jump Across the Creek | 跳跃小溪 | 突破交易区间 |
| BU | Back Up | 回踩确认 | 突破后回测 |

### summary (必填)
策略建议，支持 HTML 标签 (`<strong>`, `<br>`)。

## 示例：最小配置

```json
{
  "stock": { "code": "sh.601138", "name": "工业富联" },
  "phases": [
    { "name": "Phase B", "start": "2024-01-01" },
    { "name": "Phase C", "start": "2024-06-01" }
  ],
  "zones": [
    { "type": "accumulation", "top": 15, "bottom": 12, "start": "2024-01-01", "end": "2024-08-01" }
  ],
  "events": [
    { "date": "2024-04-08", "price": 12.86, "type": "Spring", "label": "弹簧洗盘" }
  ],
  "summary": "处于吸筹末期，等待突破确认"
}
```
