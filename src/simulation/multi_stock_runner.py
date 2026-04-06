from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from src.simulation.orchestrator import AnalysisOrchestrator
from src.utils.config import ConfigManager, get_config


class MultiStockSimulationRunner:
    def __init__(self, config: Optional[ConfigManager] = None, orchestrator: Optional[AnalysisOrchestrator] = None):
        self.config = config or get_config()
        self.orchestrator = orchestrator or AnalysisOrchestrator(config=self.config)

    def _load_target_codes(self) -> List[str]:
        target_dir = self.config.get("backtest.target_list.dir")
        target_file = self.config.get("backtest.target_list.file")
        code_column = self.config.get("backtest.target_list.code_column", "股票代码")
        file_path = Path(target_dir) / target_file
        df = pd.read_excel(file_path, dtype={code_column: str})
        codes = [str(code).zfill(6) for code in df[code_column].tolist()]
        debug_limit = int(self.config.get("simulation.multi_stock.debug_limit", 0) or 0)
        if debug_limit > 0:
            return codes[:debug_limit]
        return codes

    def _load_trade_dates(self) -> List[str]:
        start = pd.Timestamp(self.config.get("backtest.start_time", "2024-09-01"))
        end = pd.Timestamp(self.config.get("backtest.end_time", "2024-12-31"))
        if end < start:
            raise ValueError("backtest.end_time 不能早于 backtest.start_time")
        return [d.strftime("%Y-%m-%d") for d in pd.date_range(start=start, end=end, freq="D")]

    def _run_single_stock_day(self, stock_code: str, trade_date: str, user_id: str, conversation_id: str) -> Dict[str, Any]:
        return self.orchestrator.run_simulation_day(
            stock_code=stock_code,
            trade_date=trade_date,
            user_id=user_id,
            conversation_id=conversation_id,
            overwrite_split=False,
            run_real=False,
            keep_step_files=False,
        )

    def run(self, user_id: str, conversation_id: str) -> Dict[str, Any]:

        codes = self._load_target_codes()
        if not codes:
            raise ValueError("未找到回测目标股票")

        trade_dates = self._load_trade_dates()

        workers = int(self.config.get("simulation.multi_stock.max_workers", 4))
        print(f"模拟模式启动: 股票数={len(codes)}, 日期数={len(trade_dates)}, 线程数={workers}", flush=True)
        if trade_dates:
            print(f"模拟日期范围: {trade_dates[0]} -> {trade_dates[-1]}", flush=True)
        all_results: Dict[str, Dict[str, Any]] = {}
 
        for trade_date in trade_dates:
            print(f"\n开始处理交易日: {trade_date}", flush=True)
            day_results: Dict[str, Any] = {}
            with ThreadPoolExecutor(max_workers=workers) as executor:
                futures = {
                    executor.submit(self._run_single_stock_day, code, trade_date, user_id, conversation_id): code
                    for code in codes
                }
                for future in as_completed(futures):
                    code = futures[future]
                    try:
                        day_results[code] = future.result()
                        print(f"  [OK] {code} {trade_date} 单股结果完成", flush=True)
                    except Exception as exc:
                        day_results[code] = {"error": str(exc), "stock_code": code, "trade_date": trade_date}
                        print(f"  [FAIL] {code} {trade_date}: {exc}", flush=True)

            notify_results = {}
            valid_results = {code: result for code, result in day_results.items() if "steps" in result}
            if valid_results:
                step_total = min(len(result["steps"]) for result in valid_results.values())
                print(f"  开始发送多股票 step 数据: 有效股票={len(valid_results)}, step数={step_total}", flush=True)
                for step_index in range(step_total):
                    stock_payloads = {}
                    for code, result in valid_results.items():
                        analysis_result = result["steps"][step_index].get("analysis_result") or {}
                        stock_payload = analysis_result.get("single_stock_payload")
                        if stock_payload:
                            stock_payloads[code] = stock_payload
                    if stock_payloads:
                        print(f"    发送 step {step_index + 1:02d}, 股票数={len(stock_payloads)}", flush=True)
                        notify_results[f"step_{step_index + 1:02d}"] = self.orchestrator.notify_multi_stock_step(
                            mode="simulation",
                            trade_date=trade_date,
                            step=step_index + 1,
                            stock_payloads=stock_payloads,
                            user_id=user_id,
                            conversation_id=conversation_id,
                        )
                        print(f"    step {step_index + 1:02d} 已收到agent响应", flush=True)
            self.orchestrator.notifier.close()
            all_results[trade_date] = {"stocks": day_results, "notifications": notify_results}
        return all_results


class MultiStockRealtimeRunner:
    def __init__(self, config: Optional[ConfigManager] = None, orchestrator: Optional[AnalysisOrchestrator] = None):
        self.config = config or get_config()
        self.orchestrator = orchestrator or AnalysisOrchestrator(config=self.config)

    def _load_target_codes(self) -> List[str]:
        target_dir = self.config.get("realtime.target_list.dir")
        target_file = self.config.get("realtime.target_list.file")
        code_column = self.config.get("realtime.target_list.code_column", "股票代码")
        file_path = Path(target_dir) / target_file
        df = pd.read_excel(file_path, dtype={code_column: str})
        codes = [str(code).zfill(6) for code in df[code_column].tolist()]
        debug_limit = int(self.config.get("realtime.fetcher.debug_limit", 0) or 0)
        if debug_limit > 0:
            return codes[:debug_limit]
        return codes

    def run_once(self, user_id: str, conversation_id: str) -> Dict[str, Any]:
        codes = self._load_target_codes()
        workers = int(self.config.get("realtime.fetcher.max_workers", 10))
        trade_date = datetime.now().strftime("%Y-%m-%d")
        results: Dict[str, Any] = {}

        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(
                    self.orchestrator.run_realtime_batch,
                    stock_code=code,
                    trade_date=trade_date,
                    user_id=user_id,
                    conversation_id=conversation_id,
                ): code
                for code in codes
            }
            for future in as_completed(futures):
                code = futures[future]
                try:
                    results[code] = future.result()
                except Exception as exc:
                    results[code] = {"error": str(exc), "stock_code": code, "trade_date": trade_date}
        return results
