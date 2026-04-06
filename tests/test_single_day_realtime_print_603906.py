from pathlib import Path
import sys
from typing import Any, Dict

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.decision.realtime_agent_interface import RealtimeAgentInterface
from src.simulation.realtime_generator import SingleDayRealtimeGenerator
from src.simulation.splitter import StockDataSplitter
from src.utils.config import get_config


def normalize_df(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "日期" in out.columns:
        out["日期"] = pd.to_datetime(out["日期"])
    return out


def format_row(row: pd.Series, width: int = 160) -> str:
    parts = []
    for key, value in row.items():
        if isinstance(value, pd.Timestamp):
            text = value.strftime("%Y-%m-%d %H:%M:%S") if value.time() != pd.Timestamp("00:00:00").time() else value.strftime("%Y-%m-%d")
        else:
            text = str(value)
        parts.append(f"{key}={text}")
    return " | ".join(parts).ljust(width)


class PrintingAgent(RealtimeAgentInterface):
    def __init__(self, source_day_5: pd.DataFrame, source_day_30: pd.DataFrame, source_day_d: pd.DataFrame):
        self.source_day_5 = source_day_5.reset_index(drop=True)
        self.source_day_30 = source_day_30.reset_index(drop=True)
        self.source_day_d = source_day_d.reset_index(drop=True)

    def on_step(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        step = payload["step"]
        visible_30_count = (step - 1) // 6 + 1
        source_5 = self.source_day_5.iloc[:step].reset_index(drop=True)
        source_30 = self.source_day_30.iloc[:visible_30_count].reset_index(drop=True)
        source_d = self.source_day_d.iloc[:1].reset_index(drop=True)
        gen_5 = normalize_df(payload["realtime_5"]).reset_index(drop=True)
        gen_30 = normalize_df(payload["realtime_30"]).reset_index(drop=True)
        gen_d = normalize_df(payload["realtime_d"]).reset_index(drop=True)

        print(f"\n{'=' * 36} STEP {step:02d} {'=' * 36}")
        print("文件路径:")
        for key, path in payload["realtime_files"].items():
            print(f"{key:<8} {path}")
        for key, path in payload["backtest_files"].items():
            print(f"{key:<8} {path}")

        print("\n[日线]")
        print(f"{'原始':<8}{format_row(source_d.iloc[0])}")
        print(f"{'生成':<8}{format_row(gen_d.iloc[0])}")

        print("\n[30分钟]")
        for i in range(max(len(source_30), len(gen_30))):
            left = format_row(source_30.iloc[i]) if i < len(source_30) else ""
            right = format_row(gen_30.iloc[i]) if i < len(gen_30) else ""
            print(f"原始[{i+1:02d}] {left}")
            print(f"生成[{i+1:02d}] {right}")

        print("\n[5分钟]")
        for i in range(max(len(source_5), len(gen_5))):
            left = format_row(source_5.iloc[i]) if i < len(source_5) else ""
            right = format_row(gen_5.iloc[i]) if i < len(gen_5) else ""
            print(f"原始[{i+1:02d}] {left}")
            print(f"生成[{i+1:02d}] {right}")

        return super().on_step(payload)


def main() -> None:
    stock_code = "603906"
    trade_date = "2024-09-02"

    config = get_config()
    splitter = StockDataSplitter(config)
    splitter.split_stock(stock_code, overwrite=True)

    backtest_dir = config.get_stock_folder_path(stock_code) / "backtest"
    source_5_2 = pd.read_excel(backtest_dir / f"{stock_code}_5_2.xlsx")
    source_5_2["日期"] = pd.to_datetime(source_5_2["日期"])
    source_day_5 = source_5_2[source_5_2["日期"].dt.strftime("%Y-%m-%d") == trade_date].copy()
    source_day_5 = source_day_5.sort_values("日期").reset_index(drop=True)

    source_30_2 = pd.read_excel(backtest_dir / f"{stock_code}_30_2.xlsx")
    source_30_2["日期"] = pd.to_datetime(source_30_2["日期"])
    source_day_30 = source_30_2[source_30_2["日期"].dt.strftime("%Y-%m-%d") == trade_date].copy()
    source_day_30 = source_day_30.sort_values("日期").reset_index(drop=True)

    source_d_2 = pd.read_excel(backtest_dir / f"{stock_code}_d_2.xlsx")
    source_d_2["日期"] = pd.to_datetime(source_d_2["日期"])
    source_day_d = source_d_2[source_d_2["日期"].dt.strftime("%Y-%m-%d") == trade_date].copy()
    source_day_d = source_day_d.sort_values("日期").reset_index(drop=True)

    generator = SingleDayRealtimeGenerator(config=config, keep_step_files=True)
    agent = PrintingAgent(source_day_5, source_day_30, source_day_d)
    generator.step_callback = agent.on_step
    generator.simulate_day(stock_code, trade_date)


if __name__ == "__main__":
    main()
