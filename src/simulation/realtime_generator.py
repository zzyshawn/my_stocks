from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import pandas as pd

from src.utils.config import ConfigManager, get_config

TRADING_TIME_LIST = [
    "09:35", "09:40", "09:45", "09:50", "09:55",
    "10:00", "10:05", "10:10", "10:15", "10:20", "10:25", "10:30", "10:35", "10:40", "10:45", "10:50", "10:55",
    "11:00", "11:05", "11:10", "11:15", "11:20", "11:25", "11:30",
    "13:05", "13:10", "13:15", "13:20", "13:25", "13:30", "13:35", "13:40", "13:45", "13:50", "13:55",
    "14:00", "14:05", "14:10", "14:15", "14:20", "14:25", "14:30", "14:35", "14:40", "14:45", "14:50", "14:55", "15:00",
]


class SingleDayRealtimeGenerator:
    def __init__(self, config: Optional[ConfigManager] = None, keep_step_files: bool = True, step_callback: Optional[Callable[[Dict[str, Any]], None]] = None):
        self.config = config or get_config()
        self.keep_step_files = keep_step_files
        self.step_callback = step_callback

    def _stock_dir(self, stock_code: str) -> Path:
        return self.config.get_stock_folder_path(stock_code)

    def _realtime_dir(self, stock_code: str) -> Path:
        path = self._stock_dir(stock_code) / "realtime"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _backtest_dir(self, stock_code: str) -> Path:
        path = self._stock_dir(stock_code) / "backtest"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _load_excel(self, path: Path) -> pd.DataFrame:
        df = pd.read_excel(path)
        if "日期" in df.columns:
            df["日期"] = pd.to_datetime(df["日期"])
        return df

    def _write_excel(self, df: pd.DataFrame, path: Path) -> None:
        export_df = df.copy()
        if "日期" in export_df.columns:
            if self._has_time(export_df["日期"]):
                export_df["日期"] = pd.to_datetime(export_df["日期"]).dt.strftime("%Y-%m-%d %H:%M:%S")
            else:
                export_df["日期"] = pd.to_datetime(export_df["日期"]).dt.strftime("%Y-%m-%d")
        export_df.to_excel(path, index=False)

    def _has_time(self, series: pd.Series) -> bool:
        if series.empty:
            return False
        values = pd.to_datetime(series)
        return bool((values.dt.time != pd.Timestamp("00:00:00").time()).any())

    def _load_day_5min(self, stock_code: str, trade_date: str) -> pd.DataFrame:
        backtest_dir = self._backtest_dir(stock_code)
        path = backtest_dir / f"{stock_code}_5_2.xlsx"
        df = self._load_excel(path)
        if df.empty:
            raise ValueError(f"{stock_code} 5分钟测试数据为空")

        df = df.copy()
        df["时间"] = df["日期"].dt.strftime("%H:%M")
        target = df[df["日期"].dt.strftime("%Y-%m-%d") == trade_date].copy()
        target = target[target["时间"].isin(TRADING_TIME_LIST)].sort_values("日期").reset_index(drop=True)
        if len(target) != 48:
            raise ValueError(f"{stock_code} {trade_date} 5分钟数据不是48根，实际 {len(target)}")
        return target.drop(columns=["时间"])

    def _aggregate_30m(self, bars_5: pd.DataFrame) -> pd.DataFrame:
        rows: List[Dict[str, object]] = []
        stock_code = bars_5.iloc[0]["股票代码"] if not bars_5.empty and "股票代码" in bars_5.columns else None
        for start in range(0, len(bars_5), 6):
            chunk = bars_5.iloc[start:start + 6]
            if chunk.empty:
                continue
            close_time = pd.to_datetime(chunk.iloc[-1]["日期"])
            row = {
                "日期": close_time,
                "开盘": chunk.iloc[0]["开盘"],
                "最高": chunk["最高"].max(),
                "最低": chunk["最低"].min(),
                "收盘": chunk.iloc[-1]["收盘"],
                "成交量": chunk["成交量"].sum(),
            }
            if "成交额" in chunk.columns:
                row["成交额"] = chunk["成交额"].sum()
            if stock_code is not None:
                row["股票代码"] = stock_code
            rows.append(row)
        columns = ["日期", "股票代码", "开盘", "收盘", "最高", "最低", "成交量", "成交额"] if stock_code is not None and any("成交额" in row for row in rows) else None
        if columns is None:
            columns = ["日期", "股票代码", "开盘", "收盘", "最高", "最低", "成交量"] if stock_code is not None else ["日期", "开盘", "收盘", "最高", "最低", "成交量"]
        return pd.DataFrame(rows, columns=columns)

    def _aggregate_daily(self, bars_5: pd.DataFrame) -> pd.DataFrame:
        if bars_5.empty:
            return pd.DataFrame(columns=["日期", "股票代码", "开盘", "收盘", "最高", "最低", "成交量", "成交额"])
        row = {
            "日期": pd.to_datetime(bars_5.iloc[0]["日期"]).normalize(),
            "开盘": bars_5.iloc[0]["开盘"],
            "收盘": bars_5.iloc[-1]["收盘"],
            "最高": bars_5["最高"].max(),
            "最低": bars_5["最低"].min(),
            "成交量": bars_5["成交量"].sum(),
        }
        if "成交额" in bars_5.columns:
            row["成交额"] = bars_5["成交额"].sum()
        if "股票代码" in bars_5.columns:
            row["股票代码"] = bars_5.iloc[0]["股票代码"]
            columns = ["日期", "股票代码", "开盘", "收盘", "最高", "最低", "成交量", "成交额"] if "成交额" in row else ["日期", "股票代码", "开盘", "收盘", "最高", "最低", "成交量"]
            return pd.DataFrame([row], columns=columns)
        return pd.DataFrame([row])

    def _merge_backtest(self, stock_code: str, period: str, realtime_df: pd.DataFrame) -> pd.DataFrame:
        backtest_dir = self._backtest_dir(stock_code)
        base_df = self._load_excel(backtest_dir / f"{stock_code}_{period}_1.xlsx")
        merged = pd.concat([base_df, realtime_df], ignore_index=True)
        merged["日期"] = pd.to_datetime(merged["日期"])
        merged = merged.drop_duplicates(subset=["日期"], keep="last").sort_values("日期").reset_index(drop=True)
        self._write_excel(merged, backtest_dir / f"{stock_code}_{period}.xlsx")
        return merged

    def _save_step_files(self, stock_code: str, trade_date: str, step: int, files: Dict[str, pd.DataFrame]) -> None:
        if not self.keep_step_files:
            return
        step_dir = self._realtime_dir(stock_code) / "steps" / trade_date / f"step_{step:02d}"
        step_dir.mkdir(parents=True, exist_ok=True)
        for name, df in files.items():
            self._write_excel(df, step_dir / name)

    def _prepare_step_dir(self, stock_code: str, trade_date: str) -> None:
        step_root = self._realtime_dir(stock_code) / "steps" / trade_date
        step_root.mkdir(parents=True, exist_ok=True)

    def simulate_day(self, stock_code: str, trade_date: str) -> Dict[str, object]:
        realtime_dir = self._realtime_dir(stock_code)
        self._backtest_dir(stock_code)
        self._prepare_step_dir(stock_code, trade_date)

        day_5 = self._load_day_5min(stock_code, trade_date)
        results = []

        debug_step_limit = int(self.config.get("simulation.debug_step_limit", 0) or 0)
        total_steps = len(day_5)
        if debug_step_limit > 0:
            total_steps = min(debug_step_limit, total_steps)

        for step in range(1, total_steps + 1):
            current_5 = day_5.iloc[:step].copy().reset_index(drop=True)
            current_30 = self._aggregate_30m(current_5)
            current_d = self._aggregate_daily(current_5)

            rt_5_file = realtime_dir / f"{stock_code}_rt_5.xlsx"
            rt_30_file = realtime_dir / f"{stock_code}_rt_30.xlsx"
            rt_d_file = realtime_dir / f"{stock_code}_rt_d.xlsx"
            self._write_excel(current_5, rt_5_file)
            self._write_excel(current_30, rt_30_file)
            self._write_excel(current_d, rt_d_file)

            merged_5 = self._merge_backtest(stock_code, "5", current_5)
            merged_30 = self._merge_backtest(stock_code, "30", current_30)
            merged_d = self._merge_backtest(stock_code, "d", current_d)

            self._save_step_files(stock_code, trade_date, step, {
                f"{stock_code}_rt_5.xlsx": current_5,
                f"{stock_code}_rt_30.xlsx": current_30,
                f"{stock_code}_rt_d.xlsx": current_d,
                f"{stock_code}_5.xlsx": merged_5,
                f"{stock_code}_30.xlsx": merged_30,
                f"{stock_code}_d.xlsx": merged_d,
            })

            step_payload = {
                "stock_code": stock_code,
                "trade_date": trade_date,
                "step": step,
                "realtime_5": current_5.copy(),
                "realtime_30": current_30.copy(),
                "realtime_d": current_d.copy(),
                "backtest_5": merged_5.copy(),
                "backtest_30": merged_30.copy(),
                "backtest_d": merged_d.copy(),
                "realtime_files": {
                    "rt_5": rt_5_file,
                    "rt_30": rt_30_file,
                    "rt_d": rt_d_file,
                },
                "backtest_files": {
                    "bt_5": self._backtest_dir(stock_code) / f"{stock_code}_5.xlsx",
                    "bt_30": self._backtest_dir(stock_code) / f"{stock_code}_30.xlsx",
                    "bt_d": self._backtest_dir(stock_code) / f"{stock_code}_d.xlsx",
                },
            }
            if self.step_callback:
                callback_result = self.step_callback(step_payload)
                step_payload["analysis_result"] = callback_result

            results.append({
                "step": step,
                "realtime_5_count": len(current_5),
                "realtime_30_count": len(current_30),
                "realtime_d_count": len(current_d),
                "backtest_5_count": len(merged_5),
                "backtest_30_count": len(merged_30),
                "backtest_d_count": len(merged_d),
                "analysis_result": step_payload.get("analysis_result"),
            })

        return {
            "stock_code": stock_code,
            "trade_date": trade_date,
            "total_steps": len(day_5),
            "steps": results,
        }
