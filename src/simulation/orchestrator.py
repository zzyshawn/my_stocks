from __future__ import annotations

import json
import math
import time
from datetime import datetime
from multiprocessing.connection import Client
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.simulation.analysis_runner import AnalysisRunner
from src.simulation.multi_stock_aggregator import MultiStockJsonAggregator
from src.simulation.realtime_generator import SingleDayRealtimeGenerator
from src.simulation.splitter import StockDataSplitter
from src.utils.config import ConfigManager, get_config


PERIOD_KEY_MAP = {
    "d": "day",
    "30": "min30",
    "5": "min5",
}


class StepDataPackager:
    def __init__(
        self,
        config: Optional[ConfigManager] = None,
        output_dirs: Optional[Dict[str, Path]] = None,
    ):
        self.config = config or get_config()
        self.output_dirs = output_dirs or {
            "real": Path("H:/股票信息/监控清单/test_data/real"),
            "simulation": Path("H:/股票信息/监控清单/test_data/backtest"),
        }

    def _format_number(self, value: Any, is_price: bool = False, decimals: int = 2) -> Any:
        if value is None or value == "":
            return None
        if isinstance(value, (int,)):
            return value
        if not isinstance(value, (float, int)):
            return value
        if math.isnan(value):
            return None
        if is_price:
            return round(float(value), 2)
        abs_value = abs(float(value))
        if abs_value >= 10:
            return int(round(value))
        return round(float(value), decimals)

    def _format_series(self, values: List[Any], is_price: bool = False, decimals: int = 2) -> List[Any]:
        return [self._format_number(value, is_price=is_price, decimals=decimals) for value in values]

    def _normalize_series(self, rows: List[Dict[str, Any]], field: str, limit: int = 10) -> List[Any]:
        return [row.get(field) for row in rows[-limit:]]

    def _build_indicator_map(self, rows: List[Dict[str, Any]], limit: int = 10) -> Dict[str, List[Any]]:
        excluded = {"日期", "收盘", "成交量", "开盘", "最高", "最低", "股票代码", "成交额"}
        excluded_indicators = {"KDJ_K", "KDJ_D", "KDJ_J", "RSI6", "RSI12", "RSI24", "VOL", "MA120", "MA250"}
        macd_keys = {"MACD", "MACD_SIGNAL", "MACD_BAR"}
        keys = set()
        for row in rows:
            keys.update(row.keys())
        indicator_keys = sorted(keys - excluded - excluded_indicators)
        result = {}
        for key in indicator_keys:
            decimals = 3 if key in macd_keys else 2
            result[key] = self._format_series(self._normalize_series(rows, key, limit), decimals=decimals)
        return result

    def _build_chanlun_payload(self, period_result: Dict[str, Any], bi_limit: int, start_time: Optional[datetime] = None) -> Dict[str, Any]:
        chanlun_rows = period_result.get("chanlun_excel_rows") or []
        if chanlun_rows:
            valid_fx_rows = [row for row in chanlun_rows if row.get("分型类型") in {"顶分型", "底分型"}]
            valid_bi_rows = [row for row in chanlun_rows if row.get("顶底") in {"上顶", "下底"}]
            last_zs_rows = [row for row in chanlun_rows if row.get("中枢顶ZG") not in (None, "") and row.get("中枢底ZD") not in (None, "")]
            last_zs = last_zs_rows[-1] if last_zs_rows else {}

            if start_time:
                valid_fx_rows = [row for row in valid_fx_rows if self._parse_time_value(row.get("日期")) >= start_time]
                valid_bi_rows = [row for row in valid_bi_rows if self._parse_time_value(row.get("日期")) >= start_time]

            return {
                "zs_range": [
                    self._format_number(last_zs.get("中枢底ZD"), is_price=True),
                    self._format_number(last_zs.get("中枢顶ZG"), is_price=True),
                ],
                "fx_times": [row.get("日期") for row in valid_fx_rows],
                "fx_types": [row.get("分型类型") for row in valid_fx_rows],
                "bi_times": [row.get("日期") for row in valid_bi_rows[-bi_limit:]],
                "bi_types": [row.get("顶底") for row in valid_bi_rows[-bi_limit:]],
                "bi_values": [
                    self._format_number(row.get("最高价") if row.get("顶底") == "上顶" else row.get("最低价"), is_price=True)
                    for row in valid_bi_rows[-bi_limit:]
                ],
            }

        chanlun = period_result.get("chanlun_summary", {})
        last_zs_range = chanlun.get("last_zs_range", {}) or {}
        fx_times = chanlun.get("fx_times", [])
        fx_types = chanlun.get("fx_types", [])
        bi_times = chanlun.get("bi_times", [])
        bi_types = chanlun.get("bi_types", [])
        bi_values = chanlun.get("bi_values", [])

        if start_time:
            filtered_fx_indices = [i for i, t in enumerate(fx_times) if self._parse_time_value(t) >= start_time]
            filtered_bi_indices = [i for i, t in enumerate(bi_times) if self._parse_time_value(t) >= start_time]
            fx_times = [fx_times[i] for i in filtered_fx_indices]
            fx_types = [fx_types[i] for i in filtered_fx_indices]
            bi_times = [bi_times[i] for i in filtered_bi_indices[-bi_limit:]]
            bi_types = [bi_types[i] for i in filtered_bi_indices[-bi_limit:]]
            bi_values = [bi_values[i] for i in filtered_bi_indices[-bi_limit:]]
        else:
            fx_times = fx_times[-10:]
            fx_types = fx_types[-10:]
            bi_times = bi_times[-bi_limit:]
            bi_types = bi_types[-bi_limit:]
            bi_values = bi_values[-bi_limit:]

        return {
            "zs_range": [self._format_number(last_zs_range.get("zd"), is_price=True), self._format_number(last_zs_range.get("zg"), is_price=True)],
            "fx_times": fx_times,
            "fx_types": fx_types,
            "bi_times": bi_times,
            "bi_types": bi_types,
            "bi_values": self._format_series(bi_values, is_price=True),
        }

    def _build_period_payload(self, period: str, period_result: Dict[str, Any], bi_limit: int = 6, start_time: Optional[datetime] = None) -> Dict[str, Any]:
        rows = period_result.get("indicator_df", [])
        if not rows:
            return {
                "kline_range": [None, None],
                "time": [],
                "close": [],
                "value": [],
                "chanlun": {
                    "zs_range": [None, None],
                    "fx_times": [],
                    "fx_types": [],
                    "bi_times": [],
                    "bi_types": [],
                    "bi_values": [],
                },
                "indicators": {},
            }

        high_window = rows[-10:] if period == "d" else rows[-20:]
        low_value = min(row.get("最低") for row in high_window if row.get("最低") is not None)
        high_value = max(row.get("最高") for row in high_window if row.get("最高") is not None)

        chanlun_payload = self._build_chanlun_payload(period_result, bi_limit, start_time)

        return {
            "kline_range": [self._format_number(low_value, is_price=True), self._format_number(high_value, is_price=True)],
            "time": self._normalize_series(rows, "日期", 10),
            "close": self._format_series(self._normalize_series(rows, "收盘", 10), is_price=True),
            "value": self._format_series(self._normalize_series(rows, "成交量", 10)),
            "chanlun": chanlun_payload,
            "indicators": self._build_indicator_map(rows, 10),
        }

    def _resolve_output_dir(self, mode: str) -> Path:
        path = self.output_dirs[mode]
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _parse_time_value(self, value: Any) -> datetime:
        if isinstance(value, datetime):
            return value
        return datetime.fromisoformat(str(value))

    def _get_second_last_bi_time(self, period_result: Dict[str, Any]) -> Optional[datetime]:
        chanlun_rows = period_result.get("chanlun_excel_rows") or []
        if chanlun_rows:
            valid_bi_rows = [row for row in chanlun_rows if row.get("顶底") in {"上顶", "下底"}]
            if len(valid_bi_rows) >= 2:
                return self._parse_time_value(valid_bi_rows[-2].get("日期"))
        else:
            chanlun = period_result.get("chanlun_summary", {})
            bi_times = chanlun.get("bi_times", [])
            if len(bi_times) >= 2:
                return self._parse_time_value(bi_times[-2])
        return None

    def build_step_payload(
        self,
        stock_code: str,
        user_id: str,
        conversation_id: str,
        analysis_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "stock_code": stock_code,
        }

        result_d = analysis_result.get("d", {})
        result_30 = analysis_result.get("30", {})
        result_5 = analysis_result.get("5", {})

        payload["day"] = self._build_period_payload("d", result_d, bi_limit=6, start_time=None)

        day_bi_time = self._get_second_last_bi_time(result_d)
        payload["min30"] = self._build_period_payload("30", result_30, bi_limit=8, start_time=day_bi_time)

        min30_bi_time = self._get_second_last_bi_time(result_30)
        payload["min5"] = self._build_period_payload("5", result_5, bi_limit=10, start_time=min30_bi_time)

        return payload

    def pack_step_data(
        self,
        stock_code: str,
        mode: str,
        step: int,
        user_id: str,
        conversation_id: str,
        analysis_result: Dict[str, Any],
    ) -> Path:
        payload = self.build_step_payload(
            stock_code=stock_code,
            user_id=user_id,
            conversation_id=conversation_id,
            analysis_result=analysis_result,
        )
        output_dir = self._resolve_output_dir(mode)
        output_path = output_dir / f"{stock_code}_step_{step:02d}.json"
        output_path.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        return output_path

    def build_data_ready_request(self, data_path: Path, user_id: str, conversation_id: str) -> Dict[str, Any]:
        return {
            "type": "DATA_READY",
            "data_path": str(data_path),
            "user_id": user_id,
            "conversation_id": conversation_id,
        }


class ClientNotifier:
    def __init__(self, config: Optional[ConfigManager] = None, send_callable=None):
        self.config = config or get_config()
        self._send_callable = send_callable
        self._conn = None

    def close(self) -> None:
        if self._conn is not None:
            try:
                self._conn.close()
            finally:
                self._conn = None

    def _get_connection(self):
        if self._send_callable is not None:
            return None
        if self._conn is None:
            host = self.config.get("simulation.ipc.host", "localhost")
            port = int(self.config.get("simulation.ipc.port", 6000))
            authkey = str(self.config.get("simulation.ipc.authkey", "secret")).encode("utf-8")
            retry_count = int(self.config.get("simulation.ipc.retry_count", 0))
            retry_interval = float(self.config.get("simulation.ipc.retry_interval", 1))
            last_error = None
            for attempt in range(retry_count + 1):
                try:
                    self._conn = Client((host, port), authkey=authkey)
                    break
                except OSError as exc:
                    last_error = exc
                    if attempt >= retry_count:
                        raise
                    print(f"IPC 连接失败，等待重试 ({attempt + 1}/{retry_count + 1}): {exc}")
                    time.sleep(retry_interval)
            if self._conn is None and last_error is not None:
                raise last_error
        return self._conn

    def send(self, request: Dict[str, Any]) -> Dict[str, Any]:
        if self._send_callable is not None:
            response = self._send_callable(request)
            return response or {}
        conn = self._get_connection()
        conn.send(request)
        return conn.recv()


class AnalysisOrchestrator:
    def __init__(
        self,
        config: Optional[ConfigManager] = None,
        notifier: Optional[Any] = None,
        packager_output_dirs: Optional[Dict[str, Path]] = None,
    ):
        self.config = config or get_config()
        self.notifier = notifier or ClientNotifier(config=self.config)
        self.packager = StepDataPackager(config=self.config, output_dirs=packager_output_dirs)
        self.multi_stock_aggregator = MultiStockJsonAggregator(config=self.config)
        self.splitter = StockDataSplitter(self.config)
        self.runner = AnalysisRunner(self.config)
        self.generator_cls = SingleDayRealtimeGenerator

    def _handle_step_result(
        self,
        mode: str,
        user_id: str,
        conversation_id: str,
        payload: Dict[str, Any],
        analysis_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        step_payload = self.packager.build_step_payload(
            stock_code=payload["stock_code"],
            user_id=user_id,
            conversation_id=conversation_id,
            analysis_result=analysis_result,
        )
        data_path = self.multi_stock_aggregator.write_single_stock_history(
            mode=mode,
            trade_date=payload["trade_date"],
            stock_code=payload["stock_code"],
            step=int(payload["step"]),
            stock_payload=step_payload,
        )
        return {
            "analysis_result": analysis_result,
            "single_stock_payload": step_payload,
            "data_path": str(data_path),
            "notify_request": None,
            "notify_response": None,
        }

    def run_simulation_day(
        self,
        stock_code: str,
        trade_date: str,
        user_id: str,
        conversation_id: str,
        overwrite_split: bool = False,
        run_real: bool = False,
        keep_step_files: bool = True,
    ) -> Dict[str, Any]:
        split_started_at = time.perf_counter()
        self.splitter.split_stock(stock_code, overwrite=True)
        print(f"[SPLIT] {stock_code} elapsed={time.perf_counter() - split_started_at:.2f}s", flush=True)
        if run_real:
            self.runner.run_real(stock_code)

        def _step_callback(payload: Dict[str, Any]) -> Dict[str, Any]:
            step_started_at = time.perf_counter()
            analysis_result = self.runner.run_test_step(payload["stock_code"], payload["trade_date"], int(payload["step"]))
            result = self._handle_step_result("simulation", user_id, conversation_id, payload, analysis_result)
            print(f"[STEP] {payload['stock_code']} {payload['trade_date']} step={payload['step']} elapsed={time.perf_counter() - step_started_at:.2f}s", flush=True)
            return result

        generator = self.generator_cls(
            config=self.config,
            keep_step_files=keep_step_files,
            step_callback=_step_callback,
        )
        result = generator.simulate_day(stock_code, trade_date)
        for step_info in result["steps"]:
            callback_result = step_info.get("analysis_result") or {}
            step_info["data_path"] = callback_result.get("data_path")
            step_info["notify_request"] = callback_result.get("notify_request")
            step_info["notify_response"] = callback_result.get("notify_response")
        return result

    def run_realtime_batch(
        self,
        stock_code: str,
        trade_date: str,
        user_id: str,
        conversation_id: str,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        return {
            "mode": "realtime",
            "stock_code": stock_code,
            "trade_date": trade_date,
            "user_id": user_id,
            "conversation_id": conversation_id,
            "kwargs": kwargs,
        }

    def notify_multi_stock_step(self, mode: str, trade_date: str, step: int, stock_payloads: Dict[str, Dict[str, Any]], user_id: str, conversation_id: str) -> Dict[str, Any]:
        data_path = self.multi_stock_aggregator.write_multi_stock_step(mode, trade_date, step, stock_payloads)
        request = self.packager.build_data_ready_request(data_path, user_id, conversation_id)
        response = self.notifier.send(request)
        
        return {
            "data_path": str(data_path),
            "notify_request": request,
            "notify_response": response,
        }
