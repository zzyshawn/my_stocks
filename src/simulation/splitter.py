from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

import pandas as pd

from src.utils.config import ConfigManager, get_config


@dataclass
class SplitResult:
    stock_code: str
    periods: Dict[str, Dict[str, object]]


class StockDataSplitter:
    def __init__(self, config: Optional[ConfigManager] = None):
        self.config = config or get_config()
        self.test_start = self.config.get("backtest.start_time")

    def get_backtest_dir(self, stock_code: str) -> Path:
        path = self.config.get_stock_folder_path(stock_code) / "backtest"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def load_kline_data(self, file_path: Path) -> pd.DataFrame:
        if not file_path.exists():
            raise FileNotFoundError(f"K线数据文件不存在: {file_path}")

        df = pd.read_excel(file_path)
        if "日期" not in df.columns:
            raise ValueError(f"K线数据缺少'日期'列: {file_path}")

        df = df.copy()
        raw_dates = df["日期"]
        df["日期"] = pd.to_datetime(raw_dates)
        df.attrs["date_has_time"] = self._detect_time_component(raw_dates, df["日期"])
        return df.sort_values("日期").reset_index(drop=True)

    def _detect_time_component(self, raw_dates: pd.Series, parsed_dates: pd.Series) -> bool:
        if raw_dates.empty:
            return False

        if pd.api.types.is_datetime64_any_dtype(raw_dates):
            return bool((parsed_dates.dt.time != pd.Timestamp("00:00:00").time()).any())

        raw_as_str = raw_dates.astype(str).str.strip()
        return raw_as_str.str.contains(":", regex=False).any()

    def split_dataframe(self, df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
        test_start = pd.Timestamp(self.test_start)
        part1 = df[df["日期"] < test_start].copy().reset_index(drop=True)
        part2 = df[df["日期"] >= test_start].copy().reset_index(drop=True)
        return part1, part2

    def save_split_data(self, stock_code: str, period: str, part1: pd.DataFrame, part2: pd.DataFrame) -> tuple[Path, Path]:
        backtest_dir = self.get_backtest_dir(stock_code)
        part1_file = backtest_dir / f"{stock_code}_{period}_1.xlsx"
        part2_file = backtest_dir / f"{stock_code}_{period}_2.xlsx"
        self._write_dataframe(part1, part1_file)
        self._write_dataframe(part2, part2_file)
        return part1_file, part2_file

    def _write_dataframe(self, df: pd.DataFrame, file_path: Path) -> None:
        export_df = df.copy()
        if "日期" in export_df.columns and not export_df.attrs.get("date_has_time", False):
            export_df["日期"] = pd.to_datetime(export_df["日期"]).dt.strftime("%Y-%m-%d")
        export_df.to_excel(file_path, index=False)

    def split_period(self, stock_code: str, period: str, overwrite: bool = False) -> Dict[str, object]:
        source_file = self.config.get_kline_file_path(stock_code, period)
        source_df = self.load_kline_data(source_file)
        part1_df, part2_df = self.split_dataframe(source_df)
        saved_part1, saved_part2 = self.save_split_data(stock_code, period, part1_df, part2_df)

        return {
            "status": "success",
            "source_file": str(source_file),
            "part1_file": str(saved_part1),
            "part2_file": str(saved_part2),
            "source_count": len(source_df),
            "part1_count": len(part1_df),
            "part2_count": len(part2_df),
        }

    def split_stock(self, stock_code: str, overwrite: bool = False) -> Dict[str, object]:
        periods = {}
        for period in ["d", "30", "5"]:
            periods[period] = self.split_period(stock_code, period, overwrite=overwrite)
        return {"stock_code": stock_code, "periods": periods}


def split_stock_data(stock_code: str, overwrite: bool = False, config: Optional[ConfigManager] = None) -> Dict[str, object]:
    splitter = StockDataSplitter(config)
    return splitter.split_stock(stock_code, overwrite=overwrite)
