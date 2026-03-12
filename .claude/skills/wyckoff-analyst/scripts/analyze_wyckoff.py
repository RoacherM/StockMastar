#!/usr/bin/env python3
"""
威科夫结构分析脚本 - 通过 OpenRouter 调用 Gemini 分析原始 K线数据

用法:
    uv run python analyze_wyckoff.py kline.csv -o analysis.json --code sh.601138 --name 工业富联
    uv run python analyze_wyckoff.py kline.csv -o analysis.json --code sh.601138 --name 工业富联 --model google/gemini-2.5-pro
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path

DEFAULT_MODEL = "google/gemini-2.5-pro"

SYSTEM_PROMPT = """你是理查德·D·威科夫（Richard D. Wyckoff），交易史上最伟大的市场分析师。
请以大师级视角，对提供的A股K线数据进行深度威科夫结构分析。

## 分析要求

运用威科夫三大定律（供求、因果、努力与结果），完成以下分析：

### 1. 价格周期背景
定义当前处于哪个大周期：吸筹 Accumulation / 派发 Distribution / 上升趋势 Mark Up / 下降趋势 Mark Down

### 2. 阶段划分 (Phase A-E)
- Phase A: 初步停止 (PS → SC/BC → AR → ST)
- Phase B: 构建原因，主力吸筹/派发 (6-8个月典型)
- Phase C: 测试 (Spring/UTAD)
- Phase D: 趋势确认 (SOS/SOW/LPS/LPSY)
- Phase E: 趋势延续 (Mark Up/Mark Down)
- **不要强行凑齐5个阶段**，走到哪步标到哪步

### 3. 关键事件识别
找出以下事件（必须基于价格行为和成交量）：

| 代码 | 英文 | 中文 | 识别规则 |
|------|------|------|----------|
| PS | Preliminary Support | 初步支撑 | 下跌趋势中首次出现买盘 |
| SC | Selling Climax | 恐慌抛售 | 放量急跌(成交量>2倍均量)，卖压宣泄 |
| BC | Buying Climax | 抢购高潮 | 放量急涨，买盘疯狂 |
| AR | Automatic Rally/Reaction | 自动反弹 | 高潮后2-5根K线内的反向运动 |
| ST | Secondary Test | 二次测试 | 回测高潮价位，成交量萎缩 |
| Spring | Spring | 弹簧 | 跌破支撑后快速收回(吸筹信号) |
| UTAD | Upthrust After Distribution | 上冲回落 | 突破阻力后快速回落(派发信号) |
| SOS | Sign of Strength | 强势信号 | 放量突破，确认需求 |
| SOW | Sign of Weakness | 弱势信号 | 放量下跌，确认供应 |
| LPS | Last Point of Support | 最后支撑 | 突破前最后回踩，缩量 |
| LPSY | Last Point of Supply | 最后供应 | 下跌前最后反弹 |
| JAC | Jump Across the Creek | 跳跃小溪 | 突破交易区间 |
| BU | Back Up | 回踩确认 | 突破后回测 |

**价量关系判断：**
- 上涨 + 放量 = 需求吸收供应 (看涨)
- 上涨 + 缩量 = 无需求 (弱势)
- 下跌 + 放量 = 供应压倒需求 (看跌)
- 下跌 + 缩量 = 无供应 (强势)

### 4. 区域定义 (Zones)
- **type**: accumulation(吸筹) 或 distribution(派发)
- **高度(top/bottom)**: Phase B 中量价最密集的收盘价波动区间。剔除 SC 下影线和 AR 上影线的极值干扰
- **宽度(start/end)**: 从 SC 日期开始，到带量突破上沿(SOS/JAC)日期结束。如果尚未突破，end 设为最新日期
- 如果存在多个吸筹区和派发区，**必须全部绘制**

### 5. 事件标注格式
每个事件的 label 必须是 **中文威科夫风格的理由说明**，格式: `[中文术语]：[理由]`

好的标注示例：
- "恐慌抛售：放量急跌后强势反弹，显示承接力量入场，聪明钱正在吸收恐慌盘"
- "弹簧效应：快速击穿支撑后V型反转，清洗最后浮筹"
- "跳跃小溪：放量突破阻力区，巨大的成交量说明主力正在消耗挂单"

## 输出格式

严格输出以下 JSON 结构，不要输出任何其他内容（不要markdown代码块标记）：

{
  "stock": { "code": "<股票代码>", "name": "<股票名称>" },
  "quote": "<威科夫风格的一句话市场评语>",
  "phases": [
    { "name": "Phase A", "start": "YYYY-MM-DD", "end": "YYYY-MM-DD", "description": "阶段描述" }
  ],
  "zones": [
    { "type": "accumulation|distribution", "label": "显示标签", "top": 价格上沿, "bottom": 价格下沿, "start": "YYYY-MM-DD", "end": "YYYY-MM-DD" }
  ],
  "events": [
    { "date": "YYYY-MM-DD", "price": 价格, "type": "事件类型代码", "label": "中文威科夫风格解释" }
  ],
  "summary": "<strong>市场解读标题</strong><br><br>分析正文，包含支撑位/阻力位/策略建议。支持HTML标签。"
}"""


def call_openrouter(csv_data: str, stock_code: str, stock_name: str, model: str) -> dict:
    """调用 OpenRouter API 进行威科夫分析"""
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("错误: 未设置 OPENROUTER_API_KEY 环境变量", file=sys.stderr)
        sys.exit(1)

    user_prompt = f"""请分析以下 {stock_name}({stock_code}) 的K线数据，执行完整的威科夫结构分析。

CSV 数据列说明：date(日期), code(代码), open(开盘), high(最高), low(最低), close(收盘), preclose(昨收), volume(成交量), amount(成交额), turn(换手率), pctChg(涨跌幅%)

数据如下：
{csv_data}

请严格按照 JSON 格式输出分析结果。stock.code 为 "{stock_code}"，stock.name 为 "{stock_name}"。"""

    payload = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.3,
        "max_tokens": 16384,
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/stockagent",
        },
        method="POST",
    )

    print(f"  调用 {model} 分析中...", file=sys.stderr)

    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"API 错误 ({e.code}): {body}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"网络错误: {e.reason}", file=sys.stderr)
        sys.exit(1)

    content = result["choices"][0]["message"]["content"]
    usage = result.get("usage", {})
    print(f"  tokens: {usage.get('prompt_tokens', '?')} in / {usage.get('completion_tokens', '?')} out", file=sys.stderr)

    # 清理可能的 markdown 代码块标记
    content = content.strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[1] if "\n" in content else content[3:]
    if content.endswith("```"):
        content = content[:-3]
    content = content.strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        print(f"JSON 解析失败，尝试修复截断的 JSON...", file=sys.stderr)
        # Try to fix truncated JSON by closing open structures
        fixed = _try_fix_truncated_json(content)
        if fixed:
            print(f"  JSON 修复成功", file=sys.stderr)
            return fixed
        print(f"JSON 修复失败: {e}", file=sys.stderr)
        print(f"原始输出:\n{content[:500]}...", file=sys.stderr)
        sys.exit(1)


def _try_fix_truncated_json(content: str) -> dict | None:
    """Try to fix truncated JSON by closing open structures."""
    import re

    # Find the last complete field before truncation
    # Strategy: try progressively shorter substrings and close brackets
    for trim in [0, 50, 100, 200, 500, 1000]:
        attempt = content[:len(content) - trim] if trim else content
        # Remove any trailing partial string/value
        # Find last complete key-value or array element
        last_comma = attempt.rfind(',')
        last_brace = attempt.rfind('}')
        last_bracket = attempt.rfind(']')

        # Try closing from the last comma
        if last_comma > max(last_brace, last_bracket):
            attempt = attempt[:last_comma]

        # Count open/close braces and brackets
        open_braces = attempt.count('{') - attempt.count('}')
        open_brackets = attempt.count('[') - attempt.count(']')

        # Check if we're inside a string (odd number of unescaped quotes)
        in_string = False
        for i, ch in enumerate(attempt):
            if ch == '"' and (i == 0 or attempt[i-1] != '\\'):
                in_string = not in_string
        if in_string:
            # Close the string
            attempt += '"'

        # Close brackets and braces
        attempt += ']' * max(0, open_brackets)
        attempt += '}' * max(0, open_braces)

        try:
            return json.loads(attempt)
        except json.JSONDecodeError:
            continue

    return None


def validate_analysis(data: dict) -> list[str]:
    """验证分析结果的基本结构"""
    errors = []
    required = ["stock", "phases", "zones", "events", "summary"]
    for key in required:
        if key not in data:
            errors.append(f"缺少必填字段: {key}")

    if "stock" in data:
        if "code" not in data["stock"]:
            errors.append("stock 缺少 code")
        if "name" not in data["stock"]:
            errors.append("stock 缺少 name")

    if "phases" in data:
        for i, p in enumerate(data["phases"]):
            if "name" not in p or "start" not in p:
                errors.append(f"phases[{i}] 缺少 name 或 start")

    if "zones" in data:
        for i, z in enumerate(data["zones"]):
            for f in ["type", "top", "bottom", "start", "end"]:
                if f not in z:
                    errors.append(f"zones[{i}] 缺少 {f}")

    if "events" in data:
        for i, e in enumerate(data["events"]):
            for f in ["date", "price", "type", "label"]:
                if f not in e:
                    errors.append(f"events[{i}] 缺少 {f}")

    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="威科夫结构分析 (via OpenRouter)")
    parser.add_argument("csv", help="K线 CSV 文件路径")
    parser.add_argument("-o", "--output", required=True, help="输出 analysis.json 路径")
    parser.add_argument("--code", required=True, help="股票代码 (如 sh.601138)")
    parser.add_argument("--name", required=True, help="股票名称 (如 工业富联)")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"模型 (默认 {DEFAULT_MODEL})")

    args = parser.parse_args()

    csv_path = Path(args.csv)
    if not csv_path.exists():
        print(f"错误: CSV 文件不存在: {csv_path}", file=sys.stderr)
        sys.exit(1)

    csv_data = csv_path.read_text(encoding="utf-8")
    lines = csv_data.strip().split("\n")
    print(f"✓ 读取 {csv_path}: {len(lines) - 1} 条记录", file=sys.stderr)

    analysis = call_openrouter(csv_data, args.code, args.name, args.model)

    errors = validate_analysis(analysis)
    if errors:
        print(f"⚠ 验证警告:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(analysis, ensure_ascii=False, indent=2), encoding="utf-8")

    n_phases = len(analysis.get("phases", []))
    n_zones = len(analysis.get("zones", []))
    n_events = len(analysis.get("events", []))
    print(f"✓ 已保存: {output_path}", file=sys.stderr)
    print(f"  {n_phases} phases, {n_zones} zones, {n_events} events", file=sys.stderr)


if __name__ == "__main__":
    main()
