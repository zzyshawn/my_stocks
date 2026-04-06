from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from src.analysis.indicators import bollinger, kdj, ma, macd, rsi
from src.utils.config import ConfigManager, get_config

PYTHON_BIDUAN_DIR = Path(__file__).resolve().parent.parent / "python-biduan"
if str(PYTHON_BIDUAN_DIR) not in sys.path:
    sys.path.append(str(PYTHON_BIDUAN_DIR))

from stock_analysis import analyze_stock, load_config, load_stock_data
from excel_export.export_to_excel import export_analysis_to_excel


class AnalysisRunner:
    def __init__(self, config: Optional[ConfigManager] = None):
        self.config = config or get_config()
        self.analysis_config = self.config.get("analysis", {})
        self.runner_config = self.analysis_config.get("runner", {})

    def _stock_dir(self, stock_code: str) -> Path:
        return self.config.get_stock_folder_path(stock_code)

    def _backtest_dir(self, stock_code: str) -> Path:
        path = self._stock_dir(stock_code) / "backtest"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _out_dir(self, stock_code: str) -> Path:
        path = self._backtest_dir(stock_code) / self.runner_config.get("output_subdir", "out")
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _target_dir(
        self,
        stock_code: str,
        source_type: str,
        period: str,
        trade_date: Optional[str] = None,
        step: Optional[int] = None,
    ) -> Tuple[Path, Optional[Path]]:
        root = self._out_dir(stock_code)
        if source_type == "real":
            path = root / self.runner_config.get("real_subdir", "real") / period
        else:
            path = root / self.runner_config.get("test_subdir", "test") / period
        path.mkdir(parents=True, exist_ok=True)
        if source_type == "test" and self.runner_config.get("save_debug_steps", True) and trade_date and step is not None:
            debug_dir = root / self.runner_config.get("test_subdir", "test") / self.runner_config.get("debug_subdir", "debug") / trade_date / f"step_{step:02d}" / period
            debug_dir.mkdir(parents=True, exist_ok=True)
            return path, debug_dir
        return path, None

    def _resolve_input_path(self, stock_code: str, period: str, source_type: str) -> Path:
        stock_dir = self._stock_dir(stock_code)
        backtest_dir = self._backtest_dir(stock_code)
        if source_type == "real":
            return stock_dir / f"{stock_code}_{period}.xlsx"
        return backtest_dir / f"{stock_code}_{period}.xlsx"

    def _load_dataframe(self, path: Path) -> pd.DataFrame:
        df = pd.read_excel(path)
        if "日期" in df.columns:
            df["日期"] = pd.to_datetime(df["日期"])
        return df

    def _write_dataframe(self, df: pd.DataFrame, path: Path) -> None:
        export_df = df.copy()
        if "日期" in export_df.columns:
            values = pd.to_datetime(export_df["日期"])
            has_time = bool((values.dt.time != pd.Timestamp("00:00:00").time()).any())
            export_df["日期"] = values.dt.strftime("%Y-%m-%d %H:%M:%S" if has_time else "%Y-%m-%d")
        export_df.to_excel(path, index=False)

    def _slice_test_window(self, df: pd.DataFrame, period: str) -> pd.DataFrame:
        if df.empty:
            return df
        window_config = self.runner_config.get("lookback_window", {})
        trading_days = int(window_config.get("trading_days", 30))
        multipliers = window_config.get("period_multipliers", {})
        multiplier = int(multipliers.get(str(period), multipliers.get(period, 1)))
        keep_rows = trading_days * multiplier
        if keep_rows <= 0:
            return df
        return df.tail(keep_rows).reset_index(drop=True)

    def _calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        result = df.copy()
        enabled = set(self.analysis_config.get("enabled_indicators", []))
        close = pd.to_numeric(result["收盘"], errors="coerce")
        high = pd.to_numeric(result["最高"], errors="coerce")
        low = pd.to_numeric(result["最低"], errors="coerce")
        volume = pd.to_numeric(result.get("成交量", pd.Series([0] * len(result), index=result.index)), errors="coerce")

        if "ma" in enabled:
            ma_periods = []
            for values in self.analysis_config.get("ma_periods", {}).values():
                ma_periods.extend(values)
            for period_value in sorted(set(ma_periods)):
                result[f"MA{period_value}"] = ma(close, period_value)

        result["VOL"] = volume
        result["VOL_MA5"] = ma(volume, 5)
        result["VOL_MA20"] = ma(volume, 20)
        result["VWAP"] = (pd.to_numeric(result.get("成交额", volume * close), errors="coerce") / volume.replace(0, pd.NA)).fillna(close)
        result["量比"] = (volume / result["VOL_MA5"].replace(0, pd.NA)).fillna(0)
        if "换手率" in result.columns:
            result["换手率"] = pd.to_numeric(result["换手率"], errors="coerce")

        if "macd" in enabled:
            macd_cfg = self.analysis_config.get("macd", {})
            dif, dea, macd_bar = macd(
                close,
                fast=macd_cfg.get("fast_period", 12),
                slow=macd_cfg.get("slow_period", 26),
                signal=macd_cfg.get("signal_period", 9),
            )
            result["MACD_DIF"] = dif
            result["MACD_DEA"] = dea
            result["MACD_BAR"] = macd_bar

        if "kdj" in enabled:
            kdj_cfg = self.analysis_config.get("kdj", {})
            k_value, d_value, j_value = kdj(
                high,
                low,
                close,
                n=kdj_cfg.get("n", 9),
                m1=kdj_cfg.get("m1", 3),
                m2=kdj_cfg.get("m2", 3),
            )
            result["KDJ_K"] = k_value
            result["KDJ_D"] = d_value
            result["KDJ_J"] = j_value

        if "rsi" in enabled:
            for period_value in self.analysis_config.get("rsi_periods", [6, 12, 24]):
                result[f"RSI{period_value}"] = rsi(close, period_value)
            result["RSI_L6"] = rsi(low, 6)
            result["RSI_H6"] = rsi(high, 6)

        if "bollinger" in enabled:
            boll_cfg = self.analysis_config.get("bollinger", {})
            upper, middle, lower = bollinger(
                close,
                period=boll_cfg.get("period", 20),
                std_dev=boll_cfg.get("std_dev", 2),
            )
            result["BOLL_UPPER"] = upper
            result["BOLL_MIDDLE"] = middle
            result["BOLL_LOWER"] = lower

        if len(volume) == len(result):
            result["成交量"] = volume
        return result

    def _save_indicator_outputs(
        self,
        indicator_df: pd.DataFrame,
        target_dir: Path,
        stock_code: str,
        period: str,
        source_type: str,
        debug_dir: Optional[Path] = None,
    ) -> Dict[str, Path]:
        main_xlsx = target_dir / f"{stock_code}_{period}_indicators.xlsx"
        main_json = target_dir / f"{stock_code}_{period}_indicators.json"
        self._write_dataframe(indicator_df, main_xlsx)
        main_json.write_text(
            indicator_df.tail(1).to_json(force_ascii=False, orient="records", date_format="iso", indent=2),
            encoding="utf-8",
        )
        outputs = {"xlsx": main_xlsx, "json": main_json}
        if source_type == "test" and debug_dir is not None:
            debug_xlsx = debug_dir / f"{stock_code}_{period}_indicators.xlsx"
            debug_json = debug_dir / f"{stock_code}_{period}_indicators.json"
            self._write_dataframe(indicator_df, debug_xlsx)
            debug_json.write_text(
                indicator_df.tail(1).to_json(force_ascii=False, orient="records", date_format="iso", indent=2),
                encoding="utf-8",
            )
            outputs["debug_xlsx"] = debug_xlsx
            outputs["debug_json"] = debug_json
        return outputs

    def _save_chanlun_outputs(
        self,
        chanlun_result: Dict[str, Any],
        target_dir: Path,
        stock_code: str,
        period: str,
        source_type: str,
        debug_dir: Optional[Path] = None,
    ) -> Dict[str, Path]:
        outputs: Dict[str, Path] = {}
        if self.runner_config.get("save_chanlun_excel", True):
            excel_path = target_dir / f"{stock_code}_{period}_chanlun.xlsx"
            export_analysis_to_excel(chanlun_result, str(excel_path))
            outputs["excel"] = excel_path
            if source_type == "test" and debug_dir is not None:
                debug_excel = debug_dir / f"{stock_code}_{period}_chanlun.xlsx"
                export_analysis_to_excel(chanlun_result, str(debug_excel))
                outputs["debug_excel"] = debug_excel

        summary = self._build_chanlun_summary(chanlun_result, stock_code, period)
        summary_path = target_dir / f"{stock_code}_{period}_chanlun.json"
        summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        outputs["json"] = summary_path
        if source_type == "test" and debug_dir is not None:
            debug_summary = debug_dir / f"{stock_code}_{period}_chanlun.json"
            debug_summary.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
            outputs["debug_json"] = debug_summary
        return outputs

    def _build_chanlun_summary(self, chanlun_result: Dict[str, Any], stock_code: str, period: str) -> Dict[str, Any]:
        pivots = chanlun_result.get("pivot_series", []) or []
        fractals = chanlun_result.get("fractal_series", []) or []
        pens = chanlun_result.get("pen_series", []) or []

        last_pivot = pivots[-1] if pivots else {}
        last_zs_range = {
            "zd": last_pivot.get("ZD") if isinstance(last_pivot, dict) else None,
            "zg": last_pivot.get("ZG") if isinstance(last_pivot, dict) else None,
        }

        fx_times: List[Any] = []
        fx_types: List[Any] = []
        for item in fractals[-10:]:
            if isinstance(item, dict):
                fx_times.append(item.get("time") or item.get("date") or item.get("日期"))
                fx_types.append(item.get("type") or item.get("fx_type") or item.get("分型类型"))

        bi_times: List[Any] = []
        bi_types: List[Any] = []
        bi_values: List[Any] = []
        for item in pens[-10:]:
            if isinstance(item, dict):
                bi_times.append(item.get("time") or item.get("date") or item.get("日期"))
                pen_type = item.get("type") or item.get("bi_type") or item.get("方向")
                bi_types.append(pen_type)
                if pen_type in {"top", "顶", "顶分型"}:
                    bi_values.append(item.get("high") or item.get("最高") or item.get("value"))
                else:
                    bi_values.append(item.get("low") or item.get("最低") or item.get("value"))

        return {
            "stock_code": stock_code,
            "period": period,
            "pen_count": len(pens),
            "segment_count": len(chanlun_result.get("segment_series", []) or []),
            "pivot_count": len(pivots),
            "last_zs_range": last_zs_range,
            "fx_times": fx_times,
            "fx_types": fx_types,
            "bi_times": bi_times,
            "bi_types": bi_types,
            "bi_values": bi_values,
        }

    def _records_from_dataframe(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        records = df.replace({pd.NA: None}).to_dict(orient="records")
        normalized: List[Dict[str, Any]] = []
        for row in records:
            normalized_row: Dict[str, Any] = {}
            for key, value in row.items():
                if isinstance(value, pd.Timestamp):
                    normalized_row[key] = value.strftime("%Y-%m-%d %H:%M:%S") if value.time() != pd.Timestamp("00:00:00").time() else value.strftime("%Y-%m-%d")
                else:
                    normalized_row[key] = value
            normalized.append(normalized_row)
        return normalized

    def _load_json(self, path: Path) -> Any:
        return json.loads(path.read_text(encoding="utf-8"))

    def _load_chanlun_excel_rows(self, chanlun_outputs: Dict[str, Path]) -> List[Dict[str, Any]]:
        excel_path = chanlun_outputs.get("excel") if chanlun_outputs else None
        if not excel_path or not Path(excel_path).exists():
            return []
        df = pd.read_excel(excel_path)
        records = df.replace({pd.NA: None}).to_dict(orient="records")
        normalized: List[Dict[str, Any]] = []
        for row in records:
            normalized_row: Dict[str, Any] = {}
            for key, value in row.items():
                if isinstance(value, pd.Timestamp):
                    normalized_row[key] = value.strftime("%Y-%m-%d %H:%M:%S") if value.time() != pd.Timestamp("00:00:00").time() else value.strftime("%Y-%m-%d")
                else:
                    normalized_row[key] = value
            normalized.append(normalized_row)
        return normalized

    def _attach_result_summary(
        self,
        result: Dict[str, Any],
        indicator_df: pd.DataFrame,
        indicator_outputs: Dict[str, Path],
        chanlun_outputs: Dict[str, Path],
    ) -> None:
        result["indicator_df"] = self._records_from_dataframe(indicator_df)
        result["indicator_snapshot"] = self._load_json(indicator_outputs["json"])
        result["chanlun_summary"] = self._load_json(chanlun_outputs["json"]) if chanlun_outputs else {}
        result["chanlun_excel_rows"] = self._load_chanlun_excel_rows(chanlun_outputs)

    def _build_chanlun_config(self, source_path: Path) -> Dict[str, Any]:
        chanlun_config = load_config(str(PYTHON_BIDUAN_DIR / "config.yaml")) or {}
        chanlun_config.setdefault("analysis", {})
        chanlun_config["analysis"]["min_klines"] = self.analysis_config.get("min_klines", 10)
        chanlun_config["analysis"]["max_records"] = self.analysis_config.get("max_records", 3000)
        chanlun_config.setdefault("data", {})
        chanlun_config["data"]["base_dir"] = str(self._stock_dir(source_path.stem.split("_")[0]).parent)
        chanlun_config.setdefault("naming", {})
        chanlun_config["naming"].setdefault("files", {})
        chanlun_config["naming"]["files"].setdefault("kline", {})
        chanlun_config["naming"]["files"]["kline"]["pattern"] = "{symbol}_{period}"
        chanlun_config["naming"]["files"]["kline"]["extension"] = ".xlsx"
        chanlun_config["naming"]["files"]["kline"]["period_map"] = {
            "daily": "d",
            "min30": "30",
            "min5": "5",
        }
        return chanlun_config

    def _run_chanlun_analysis(self, stock_code: str, period: str, working_df: pd.DataFrame) -> Optional[Dict[str, Any]]:
        if not self.runner_config.get("enable_chanlun_analysis", False):
            return None
        import sys
        python_biduan_path = Path(__file__).parent.parent / "python-biduan"
        if str(python_biduan_path) not in sys.path:
            sys.path.insert(0, str(python_biduan_path))
        from stock_analysis import convert_dataframe_to_klines, analyze_stock

        klines = convert_dataframe_to_klines(working_df, stock_code)
        if not klines:
            return None

        chanlun_config = {}
        return analyze_stock(chanlun_config, stock_code, klines, data_type=period, enable_html=False)

    def run_for_period(
        self,
        stock_code: str,
        period: str,
        source_type: str,
        trade_date: Optional[str] = None,
        step: Optional[int] = None,
    ) -> Dict[str, Any]:
        started_at = time.perf_counter()
        source_path = self._resolve_input_path(stock_code, period, source_type)
        if not source_path.exists():
            raise FileNotFoundError(f"数据文件不存在: {source_path}")

        target_dir, debug_dir = self._target_dir(stock_code, source_type, period, trade_date, step)
        source_df = self._load_dataframe(source_path)
        working_df = self._slice_test_window(source_df, period) if source_type == "test" else source_df
        indicator_df = self._calculate_indicators(working_df)
        indicator_outputs = self._save_indicator_outputs(indicator_df, target_dir, stock_code, period, source_type, debug_dir)

        chanlun_result = self._run_chanlun_analysis(stock_code, period, working_df)
        chanlun_outputs = self._save_chanlun_outputs(chanlun_result, target_dir, stock_code, period, source_type, debug_dir) if chanlun_result else {}

        result = {
            "period": period,
            "source_path": source_path,
            "indicator_outputs": indicator_outputs,
            "chanlun_outputs": chanlun_outputs,
            "rows": len(working_df),
        }
        self._attach_result_summary(result, indicator_df, indicator_outputs, chanlun_outputs)
        elapsed = time.perf_counter() - started_at
        print(f"[ANALYSIS] {stock_code} {source_type} {period} rows={len(working_df)} elapsed={elapsed:.2f}s", flush=True)
        return result

    def run_real(self, stock_code: str) -> Dict[str, Any]:
        results = {}
        for period in self.analysis_config.get("data_types", ["d", "30", "5"]):
            results[period] = self.run_for_period(stock_code, period, "real")
        return results

    def run_test_step(self, stock_code: str, trade_date: str, step: int) -> Dict[str, Any]:
        results = {}
        for period in self.analysis_config.get("data_types", ["d", "30", "5"]):
            results[period] = self.run_for_period(stock_code, period, "test", trade_date=trade_date, step=step)
        return results

    def build_step_callback(self):
        def _callback(payload: Dict[str, Any]) -> Dict[str, Any]:
            return self.run_test_step(
                payload["stock_code"],
                payload["trade_date"],
                int(payload["step"]),
            )

        return _callback
