#!/usr/bin/env python3
"""
A股数据获取脚本 - 将baostock数据保存到本地CSV文件

用法:
    uv run python fetch_stock_data.py sh.601138 --days 730
    uv run python fetch_stock_data.py sh.600000 --start 2024-01-01 --end 2024-12-31
    uv run python fetch_stock_data.py sh.601138 --type profit --year 2024 --quarter 3
    uv run python fetch_stock_data.py sh.601138 --cache-dir ./my_data
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Generator, Literal


# ============================================================================
# Data Contracts (Schema First)
# ============================================================================
class DataType(str, Enum):
    KLINE = "kline"
    PROFIT = "profit"
    GROWTH = "growth"
    BALANCE = "balance"
    CASHFLOW = "cashflow"
    DUPONT = "dupont"
    DIVIDEND = "dividend"


class Frequency(str, Enum):
    DAILY = "d"
    WEEKLY = "w"
    MONTHLY = "m"
    MIN_5 = "5"
    MIN_15 = "15"
    MIN_30 = "30"
    MIN_60 = "60"


class AdjustFlag(str, Enum):
    FORWARD = "1"  # 后复权
    BACKWARD = "2"  # 前复权
    NONE = "3"  # 不复权


@dataclass(frozen=True)
class FetchResult:
    """数据获取结果"""

    filepath: Path
    rows: int
    date_min: str
    date_max: str


@dataclass(frozen=True)
class CachedFile:
    """缓存文件信息"""

    name: str
    size_kb: float


@dataclass(frozen=True)
class CacheStats:
    """缓存统计"""

    code: str
    file_count: int
    files: list[CachedFile]


# ============================================================================
# Soul: Core Logic (Pure, No Print, Returns Objects/Generators)
# ============================================================================
class StockDataFetcher:
    """A股数据获取器 - 核心逻辑层"""

    KLINE_FIELDS = (
        "date,code,open,high,low,close,preclose,volume,amount,"
        "adjustflag,turn,tradestatus,pctChg,peTTM,pbMRQ,psTTM,pcfNcfTTM,isST"
    )

    FREQ_NAME_MAP = {
        Frequency.DAILY: "daily",
        Frequency.WEEKLY: "weekly",
        Frequency.MONTHLY: "monthly",
        Frequency.MIN_5: "5min",
        Frequency.MIN_15: "15min",
        Frequency.MIN_30: "30min",
        Frequency.MIN_60: "60min",
    }

    NUMERIC_COLS = [
        "open",
        "high",
        "low",
        "close",
        "preclose",
        "volume",
        "amount",
        "turn",
        "pctChg",
        "peTTM",
        "pbMRQ",
        "psTTM",
        "pcfNcfTTM",
    ]

    def __init__(self, cache_dir: Path) -> None:
        self.cache_dir = cache_dir

    def _get_stock_cache_dir(self, code: str) -> Path:
        """获取股票缓存目录"""
        stock_dir = self.cache_dir / code.replace(".", "_")
        stock_dir.mkdir(parents=True, exist_ok=True)
        return stock_dir

    @staticmethod
    def _query_to_dataframe(rs):
        """将baostock结果集转换为DataFrame"""
        import pandas as pd

        data_list = []
        while rs.next():
            data_list.append(rs.get_row_data())
        return pd.DataFrame(data_list, columns=rs.fields)

    def fetch_kline(
        self,
        code: str,
        start_date: date,
        end_date: date,
        frequency: Frequency = Frequency.DAILY,
        adjust: AdjustFlag = AdjustFlag.BACKWARD,
    ) -> FetchResult:
        """获取K线数据"""
        import baostock as bs
        import pandas as pd

        bs.login()
        try:
            rs = bs.query_history_k_data_plus(
                code,
                self.KLINE_FIELDS,
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat(),
                frequency=frequency.value,
                adjustflag=adjust.value,
            )
            if rs.error_code != "0":
                raise RuntimeError(f"查询失败: {rs.error_msg}")

            df = self._query_to_dataframe(rs)

            for col in self.NUMERIC_COLS:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")

            freq_name = self.FREQ_NAME_MAP[frequency]
            filename = f"{freq_name}_{start_date}_{end_date}.csv"
            filepath = self._get_stock_cache_dir(code) / filename
            df.to_csv(filepath, index=False, encoding="utf-8")

            return FetchResult(
                filepath=filepath,
                rows=len(df),
                date_min=str(df["date"].min()) if len(df) > 0 else "",
                date_max=str(df["date"].max()) if len(df) > 0 else "",
            )
        finally:
            bs.logout()

    def fetch_financial(
        self,
        code: str,
        year: int,
        quarter: int,
        data_type: DataType,
    ) -> FetchResult:
        """获取财务数据"""
        import baostock as bs

        query_funcs = {
            DataType.PROFIT: bs.query_profit_data,
            DataType.GROWTH: bs.query_growth_data,
            DataType.BALANCE: bs.query_balance_data,
            DataType.CASHFLOW: bs.query_cash_flow_data,
            DataType.DUPONT: bs.query_dupont_data,
        }

        bs.login()
        try:
            rs = query_funcs[data_type](code=code, year=year, quarter=quarter)
            if rs.error_code != "0":
                raise RuntimeError(f"查询失败: {rs.error_msg}")

            df = self._query_to_dataframe(rs)

            filename = f"{data_type.value}_{year}Q{quarter}.csv"
            filepath = self._get_stock_cache_dir(code) / filename
            df.to_csv(filepath, index=False, encoding="utf-8")

            return FetchResult(
                filepath=filepath,
                rows=len(df),
                date_min=f"{year}Q{quarter}",
                date_max=f"{year}Q{quarter}",
            )
        finally:
            bs.logout()

    def fetch_dividend(self, code: str, year: int) -> FetchResult:
        """获取分红数据"""
        import baostock as bs

        bs.login()
        try:
            rs = bs.query_dividend_data(code=code, year=str(year), yearType="report")
            if rs.error_code != "0":
                raise RuntimeError(f"查询失败: {rs.error_msg}")

            df = self._query_to_dataframe(rs)

            filename = f"dividend_{year}.csv"
            filepath = self._get_stock_cache_dir(code) / filename
            df.to_csv(filepath, index=False, encoding="utf-8")

            return FetchResult(
                filepath=filepath,
                rows=len(df),
                date_min=str(year),
                date_max=str(year),
            )
        finally:
            bs.logout()

    def list_cache(self, code: str | None = None) -> Generator[CacheStats, None, None]:
        """列出缓存文件"""
        if not self.cache_dir.exists():
            return

        if code:
            stock_dir = self._get_stock_cache_dir(code)
            if stock_dir.exists():
                files = [
                    CachedFile(name=f.name, size_kb=f.stat().st_size / 1024)
                    for f in sorted(stock_dir.glob("*.csv"))
                ]
                yield CacheStats(code=code, file_count=len(files), files=files)
        else:
            for stock_dir in sorted(self.cache_dir.iterdir()):
                if stock_dir.is_dir():
                    files = [
                        CachedFile(name=f.name, size_kb=f.stat().st_size / 1024)
                        for f in sorted(stock_dir.glob("*.csv"))
                    ]
                    yield CacheStats(
                        code=stock_dir.name,
                        file_count=len(files),
                        files=files,
                    )


# ============================================================================
# Body: CLI Layer (Handles Print, User Interaction)
# ============================================================================
def _print_result(result: FetchResult, label: str = "数据") -> None:
    print(f"✓ {label}已保存: {result.filepath}")
    print(f"  共 {result.rows} 条记录, 日期: {result.date_min} ~ {result.date_max}")


def _print_cache_stats(stats_iter: Generator[CacheStats, None, None]) -> None:
    has_any = False
    for stats in stats_iter:
        has_any = True
        if stats.files:
            print(f"\n{stats.code} 缓存文件:")
            for f in stats.files:
                print(f"  {f.name} ({f.size_kb:.1f}KB)")
        else:
            print(f"\n{stats.code}: {stats.file_count} 个文件")
    if not has_any:
        print("缓存目录为空")


def main() -> None:
    parser = argparse.ArgumentParser(description="A股数据获取与缓存工具")
    parser.add_argument("code", nargs="?", help="股票代码 (如 sh.601138)")
    parser.add_argument(
        "--type",
        choices=[t.value for t in DataType],
        default=DataType.KLINE.value,
        help="数据类型",
    )
    parser.add_argument("--start", help="开始日期 YYYY-MM-DD")
    parser.add_argument("--end", help="结束日期 YYYY-MM-DD")
    parser.add_argument(
        "--days", type=int, default=365, help="获取最近N天数据 (默认365)"
    )
    parser.add_argument("--freq", default="d", help="K线频率: d/w/m/5/15/30/60")
    parser.add_argument(
        "--adjust",
        default="2",
        choices=["1", "2", "3"],
        help="复权: 1后复权 2前复权 3不复权",
    )
    parser.add_argument("--year", type=int, help="年份 (财务数据用)")
    parser.add_argument("--quarter", type=int, choices=[1, 2, 3, 4], help="季度")
    parser.add_argument("--list", action="store_true", help="列出已缓存的文件")
    parser.add_argument(
        "--cache-dir",
        default=os.environ.get("STOCK_CACHE_DIR", "./data/cache"),
        help="缓存目录 (默认 ./data/cache)",
    )

    args = parser.parse_args()

    fetcher = StockDataFetcher(cache_dir=Path(args.cache_dir))

    # List cache
    if args.list:
        _print_cache_stats(fetcher.list_cache(args.code))
        return

    # Require code for fetch operations
    if not args.code:
        parser.print_help()
        sys.exit(1)

    data_type = DataType(args.type)

    # Fetch kline
    if data_type == DataType.KLINE:
        end_date = date.fromisoformat(args.end) if args.end else date.today()
        start_date = (
            date.fromisoformat(args.start)
            if args.start
            else end_date - timedelta(days=args.days)
        )
        frequency = Frequency(args.freq)
        adjust = AdjustFlag(args.adjust)

        result = fetcher.fetch_kline(args.code, start_date, end_date, frequency, adjust)
        _print_result(result, "K线数据")

    # Fetch financial data
    elif data_type in (
        DataType.PROFIT,
        DataType.GROWTH,
        DataType.BALANCE,
        DataType.CASHFLOW,
        DataType.DUPONT,
    ):
        if not args.year or not args.quarter:
            print("错误: 财务数据需要指定 --year 和 --quarter")
            sys.exit(1)

        result = fetcher.fetch_financial(args.code, args.year, args.quarter, data_type)
        _print_result(result, f"{data_type.value}数据")

    # Fetch dividend
    elif data_type == DataType.DIVIDEND:
        if not args.year:
            print("错误: 分红数据需要指定 --year")
            sys.exit(1)

        result = fetcher.fetch_dividend(args.code, args.year)
        _print_result(result, "分红数据")


if __name__ == "__main__":
    main()
