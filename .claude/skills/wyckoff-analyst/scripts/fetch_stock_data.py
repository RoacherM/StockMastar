#!/usr/bin/env python3
"""
A股K线数据获取脚本

用法:
    uv run python fetch_stock_data.py sh.601138 -o ./kline.csv
    uv run python fetch_stock_data.py sh.601138 -o ./kline.csv --days 730
    uv run python fetch_stock_data.py sh.600000 -o ./data.csv --start 2024-01-01 --end 2024-12-31
"""

from __future__ import annotations

import argparse
import sys
from datetime import date, timedelta
from pathlib import Path


def fetch_kline(
    code: str,
    output: Path,
    start_date: date,
    end_date: date,
    frequency: str = "d",
    adjust: str = "2",
) -> None:
    """获取K线数据并保存到CSV"""
    import baostock as bs
    import pandas as pd

    FIELDS = (
        "date,code,open,high,low,close,preclose,volume,amount,"
        "adjustflag,turn,tradestatus,pctChg,peTTM,pbMRQ,psTTM,pcfNcfTTM,isST"
    )
    NUMERIC_COLS = [
        "open", "high", "low", "close", "preclose",
        "volume", "amount", "turn", "pctChg",
        "peTTM", "pbMRQ", "psTTM", "pcfNcfTTM",
    ]

    bs.login()
    try:
        rs = bs.query_history_k_data_plus(
            code,
            FIELDS,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
            frequency=frequency,
            adjustflag=adjust,
        )
        if rs.error_code != "0":
            print(f"错误: {rs.error_msg}", file=sys.stderr)
            sys.exit(1)

        data = []
        while rs.next():
            data.append(rs.get_row_data())
        df = pd.DataFrame(data, columns=rs.fields)

        for col in NUMERIC_COLS:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        output.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output, index=False, encoding="utf-8")

        print(f"✓ 已保存: {output}")
        print(f"  {len(df)} 条记录, {df['date'].min()} ~ {df['date'].max()}")
    finally:
        bs.logout()


def main() -> None:
    parser = argparse.ArgumentParser(description="A股K线数据获取")
    parser.add_argument("code", help="股票代码 (如 sh.601138, sz.002475)")
    parser.add_argument("-o", "--output", required=True, help="输出文件路径")
    parser.add_argument("--days", type=int, default=730, help="获取最近N天 (默认730)")
    parser.add_argument("--start", help="开始日期 YYYY-MM-DD")
    parser.add_argument("--end", help="结束日期 YYYY-MM-DD")
    parser.add_argument("--freq", default="d", help="频率: d/w/m/5/15/30/60 (默认d)")
    parser.add_argument("--adjust", default="2", choices=["1", "2", "3"],
                        help="复权: 1后复权 2前复权 3不复权 (默认2)")

    args = parser.parse_args()

    end_date = date.fromisoformat(args.end) if args.end else date.today()
    start_date = (
        date.fromisoformat(args.start)
        if args.start
        else end_date - timedelta(days=args.days)
    )

    fetch_kline(
        args.code,
        Path(args.output),
        start_date,
        end_date,
        args.freq,
        args.adjust,
    )


if __name__ == "__main__":
    main()
