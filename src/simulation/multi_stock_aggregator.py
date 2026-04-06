from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.utils.config import ConfigManager, get_config


FIELD_DESCRIPTIONS = {
    "now": "本次多股票合并数据的最后时间戳",
    "stocks": "按股票代码聚合的单股票结构",
    "stock_code": "股票代码",
    "day": "日线维度数据",
    "min30": "30分钟维度数据",
    "min5": "5分钟维度数据",
    "kline_range": "最近窗口K线最低价到最高价区间",
    "time": "最后时间序列",
    "close": "最后收盘价序列",
    "value": "最后成交量序列",
    "chanlun": "缠论摘要字段",
    "indicators": "技术指标序列字段，包含MA/MACD/KDJ/RSI/BOLL等。RSI_H6: 最高点取6周期RSI用于上顶判断; RSI_L6: 最低点取6周期RSI用于下底判断",
    "zs_range": "最后一个中枢范围[ZD, ZG]，ZD为中枢底，ZG为中枢顶",
    "fx_times": "最后若干分型对应时间",
    "fx_types": "最后若干分型类型，顶分型(局部高点)或底分型(局部低点)",
    "bi_times": "最后若干笔顶点时间",
    "bi_types": "最后若干笔顶点类型，上顶或下底",
    "bi_values": "最后若干笔顶点值",
}


class MultiStockJsonAggregator:
    def __init__(self, config: Optional[ConfigManager] = None):
        self.config = config or get_config()

    def _base_output_dir(self, mode: str) -> Path:
        if mode == "realtime":
            return Path("H:/股票信息/监控清单/test_data/real")
        return Path("H:/股票信息/监控清单/test_data/backtest")

    def _history_dir(self, mode: str, trade_date: str) -> Path:
        path = self._base_output_dir(mode) / "history" / trade_date
        path.mkdir(parents=True, exist_ok=True)
        return path

    def write_multi_stock_step(self, mode: str, trade_date: str, step: int, stock_payloads: Dict[str, Dict[str, Any]]) -> Path:
        latest_times = []
        for payload in stock_payloads.values():
            for period_key in ("day", "min30", "min5"):
                period_payload = payload.get(period_key, {})
                latest_times.extend([t for t in period_payload.get("time", []) if t])
        latest = max(latest_times) if latest_times else trade_date
        payload = {
            "now": latest,
            "field_descriptions": FIELD_DESCRIPTIONS,
            "stocks": stock_payloads,
        }
        output_dir = self._base_output_dir(mode)
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / f"multi_stock_{trade_date}_step_{step:02d}.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        return path

    def write_single_stock_history(self, mode: str, trade_date: str, stock_code: str, step: int, stock_payload: Dict[str, Any]) -> Path:
        output_dir = self._history_dir(mode, trade_date)
        path = output_dir / f"{stock_code}_step_{step:02d}.json"
        path.write_text(json.dumps(stock_payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        return path
