"""
历史数据合并模块

提供股票历史数据的读取、合并和处理功能。
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Union
from datetime import datetime

import pandas as pd
import numpy as np

from src.utils.config import get_config


class KLineDataLoader:
    """K线数据加载器"""

    # 标准列名映射（Excel列名 -> 标准列名）
    COLUMN_MAPPING = {
        # 中文列名
        "日期": "date",
        "时间": "date",
        "开盘": "open",
        "开盘价": "open",
        "最高": "high",
        "最高价": "high",
        "最低": "low",
        "最低价": "low",
        "收盘": "close",
        "收盘价": "close",
        "成交量": "volume",
        "成交额": "amount",
        "涨跌幅": "change_pct",
        "涨跌额": "change",
        "换手率": "turnover",
        # 英文列名
        "Date": "date",
        "Time": "date",
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Volume": "volume",
        "Amount": "amount",
    }

    # 必需列
    REQUIRED_COLUMNS = ["date", "open", "high", "low", "close", "volume"]

    def __init__(self):
        """初始化数据加载器"""
        self.config = get_config()

    def load_kline(
        self,
        symbol: str,
        period: str = "daily",
        columns: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        加载单只股票的K线数据

        Args:
            symbol: 股票代码
            period: 周期 (daily, min30, min5, weekly, monthly)
            columns: 需要加载的列，None 表示加载所有列

        Returns:
            K线数据 DataFrame
        """
        file_path = self.config.get_kline_file_path(symbol, period)

        if not file_path.exists():
            raise FileNotFoundError(f"K线数据文件不存在: {file_path}")

        # 读取 Excel 文件
        df = pd.read_excel(file_path)

        # 标准化列名
        df = self._normalize_columns(df)

        # 验证必需列
        self._validate_columns(df)

        # 选择指定列
        if columns:
            df = df[columns]

        # 添加元数据
        df["symbol"] = symbol
        df["period"] = period

        return df

    def load_multiple(
        self,
        symbols: List[str],
        period: str = "daily",
        merge: bool = True
    ) -> Union[pd.DataFrame, Dict[str, pd.DataFrame]]:
        """
        加载多只股票的K线数据

        Args:
            symbols: 股票代码列表
            period: 周期
            merge: 是否合并为单个 DataFrame

        Returns:
            合并后的 DataFrame 或股票代码到 DataFrame 的字典
        """
        data_dict = {}
        failed_symbols = []

        for symbol in symbols:
            try:
                df = self.load_kline(symbol, period)
                data_dict[symbol] = df
            except FileNotFoundError as e:
                failed_symbols.append(symbol)
                print(f"警告: {e}")

        if failed_symbols:
            print(f"以下股票数据加载失败: {failed_symbols}")

        if merge:
            return self._merge_dataframes(data_dict)
        return data_dict

    def load_all_periods(
        self,
        symbol: str,
        periods: Optional[List[str]] = None
    ) -> Dict[str, pd.DataFrame]:
        """
        加载单只股票所有周期的K线数据

        Args:
            symbol: 股票代码
            periods: 周期列表，None 表示加载所有可用周期

        Returns:
            周期到 DataFrame 的字典
        """
        if periods is None:
            periods = self.config.list_available_periods(symbol)

        data_dict = {}
        for period in periods:
            try:
                df = self.load_kline(symbol, period)
                data_dict[period] = df
            except FileNotFoundError:
                continue

        return data_dict

    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """标准化列名"""
        df = df.copy()

        # 应用列名映射
        df.columns = [self.COLUMN_MAPPING.get(col, col) for col in df.columns]

        # 处理日期列
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])

        return df

    def _validate_columns(self, df: pd.DataFrame) -> None:
        """验证必需列是否存在"""
        missing = [col for col in self.REQUIRED_COLUMNS if col not in df.columns]
        if missing:
            raise ValueError(f"缺少必需列: {missing}")

    def _merge_dataframes(self, data_dict: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """合并多个 DataFrame"""
        if not data_dict:
            return pd.DataFrame()

        dfs = []
        for symbol, df in data_dict.items():
            dfs.append(df)

        merged = pd.concat(dfs, ignore_index=True)
        return merged


class DataMerger:
    """数据合并器"""

    def __init__(self):
        """初始化数据合并器"""
        self.config = get_config()
        self.loader = KLineDataLoader()

    def merge_by_date(
        self,
        symbols: List[str],
        period: str = "daily",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fill_method: str = "ffill"
    ) -> pd.DataFrame:
        """
        按日期合并多只股票数据（横向合并，用于比较分析）

        Args:
            symbols: 股票代码列表
            period: 周期
            start_date: 开始日期
            end_date: 结束日期
            fill_method: 缺失值填充方法 (ffill, bfill, none)

        Returns:
            合并后的 DataFrame，每只股票的列带有股票代码前缀
        """
        # 加载所有股票数据
        data_dict = self.loader.load_multiple(symbols, period, merge=False)

        if not data_dict:
            return pd.DataFrame()

        # 设置日期索引
        indexed_data = {}
        for symbol, df in data_dict.items():
            df = df.set_index("date")
            # 选择数值列
            numeric_cols = ["open", "high", "low", "close", "volume"]
            available_cols = [col for col in numeric_cols if col in df.columns]
            df = df[available_cols]
            # 添加股票代码前缀
            df.columns = [f"{symbol}_{col}" for col in df.columns]
            indexed_data[symbol] = df

        # 合并所有数据
        merged = pd.concat(indexed_data.values(), axis=1)

        # 日期筛选
        if start_date:
            merged = merged[merged.index >= pd.to_datetime(start_date)]
        if end_date:
            merged = merged[merged.index <= pd.to_datetime(end_date)]

        # 填充缺失值
        if fill_method == "ffill":
            merged = merged.ffill()
        elif fill_method == "bfill":
            merged = merged.bfill()

        return merged

    def merge_by_symbol(
        self,
        symbols: List[str],
        period: str = "daily",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        按股票代码合并数据（纵向合并，用于批量分析）

        Args:
            symbols: 股票代码列表
            period: 周期
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            合并后的 DataFrame，包含 symbol 列标识
        """
        df = self.loader.load_multiple(symbols, period, merge=True)

        if df.empty:
            return df

        # 日期筛选
        if start_date:
            df = df[df["date"] >= pd.to_datetime(start_date)]
        if end_date:
            df = df[df["date"] <= pd.to_datetime(end_date)]

        # 排序
        df = df.sort_values(["symbol", "date"]).reset_index(drop=True)

        return df

    def merge_periods(
        self,
        symbol: str,
        periods: List[str],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        合并单只股票不同周期的数据

        Args:
            symbol: 股票代码
            periods: 周期列表
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            合并后的 DataFrame
        """
        data_dict = self.loader.load_all_periods(symbol, periods)

        if not data_dict:
            return pd.DataFrame()

        dfs = []
        for period, df in data_dict.items():
            df = df.copy()
            # 为每个周期的列添加周期标识
            value_cols = ["open", "high", "low", "close", "volume"]
            rename_map = {col: f"{col}_{period}" for col in value_cols if col in df.columns}
            df = df.rename(columns=rename_map)
            dfs.append(df)

        # 以第一个周期的数据为基础进行合并
        merged = dfs[0]
        for df in dfs[1:]:
            merged = pd.merge(merged, df, on="date", how="outer", suffixes=("", "_dup"))
            # 删除重复列
            dup_cols = [col for col in merged.columns if col.endswith("_dup")]
            merged = merged.drop(columns=dup_cols, errors="ignore")

        # 日期筛选
        if start_date:
            merged = merged[merged["date"] >= pd.to_datetime(start_date)]
        if end_date:
            merged = merged[merged["date"] <= pd.to_datetime(end_date)]

        merged = merged.sort_values("date").reset_index(drop=True)

        return merged

    def align_data(
        self,
        df: pd.DataFrame,
        reference_dates: Optional[pd.DatetimeIndex] = None,
        method: str = "reindex"
    ) -> pd.DataFrame:
        """
        对齐数据日期

        Args:
            df: K线数据 DataFrame
            reference_dates: 参考日期索引
            method: 对齐方法 (reindex, intersection)

        Returns:
            对齐后的 DataFrame
        """
        df = df.copy()

        if "date" in df.columns:
            df = df.set_index("date")

        if reference_dates is not None:
            if method == "reindex":
                df = df.reindex(reference_dates)
            elif method == "intersection":
                common_dates = df.index.intersection(reference_dates)
                df = df.loc[common_dates]

        return df


class DataExporter:
    """数据导出器"""

    def __init__(self):
        """初始化数据导出器"""
        self.config = get_config()

    def to_excel(
        self,
        df: pd.DataFrame,
        filename: str,
        output_dir: Optional[str] = None,
        sheet_name: str = "Sheet1"
    ) -> Path:
        """
        导出数据到 Excel 文件

        Args:
            df: 数据 DataFrame
            filename: 文件名
            output_dir: 输出目录，默认为数据目录下的 backtest 子目录
            sheet_name: 工作表名称

        Returns:
            导出文件的路径
        """
        if output_dir is None:
            output_dir = self.config.get_data_dir("backtest")

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        file_path = output_path / f"{filename}.xlsx"
        df.to_excel(file_path, sheet_name=sheet_name, index=False)

        return file_path

    def to_csv(
        self,
        df: pd.DataFrame,
        filename: str,
        output_dir: Optional[str] = None
    ) -> Path:
        """
        导出数据到 CSV 文件

        Args:
            df: 数据 DataFrame
            filename: 文件名
            output_dir: 输出目录

        Returns:
            导出文件的路径
        """
        if output_dir is None:
            output_dir = self.config.get_data_dir("backtest")

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        file_path = output_path / f"{filename}.csv"
        df.to_csv(file_path, index=False, encoding="utf-8-sig")

        return file_path


# 便捷函数
def load_kline(symbol: str, period: str = "daily") -> pd.DataFrame:
    """加载K线数据"""
    loader = KLineDataLoader()
    return loader.load_kline(symbol, period)


def load_multiple_klines(
    symbols: List[str],
    period: str = "daily"
) -> pd.DataFrame:
    """加载多只股票K线数据"""
    loader = KLineDataLoader()
    return loader.load_multiple(symbols, period, merge=True)


def merge_by_date(
    symbols: List[str],
    period: str = "daily",
    **kwargs
) -> pd.DataFrame:
    """按日期合并多只股票数据"""
    merger = DataMerger()
    return merger.merge_by_date(symbols, period, **kwargs)


def merge_by_symbol(
    symbols: List[str],
    period: str = "daily",
    **kwargs
) -> pd.DataFrame:
    """按股票代码合并数据"""
    merger = DataMerger()
    return merger.merge_by_symbol(symbols, period, **kwargs)