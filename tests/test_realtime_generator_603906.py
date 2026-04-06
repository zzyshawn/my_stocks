from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.simulation.realtime_generator import SingleDayRealtimeGenerator
from src.simulation.splitter import StockDataSplitter
from src.utils.config import get_config


def main() -> None:
    config = get_config()
    splitter = StockDataSplitter(config)
    splitter.split_stock("603906", overwrite=True)

    generator = SingleDayRealtimeGenerator(config=config, keep_step_files=True)
    trade_date = "2024-09-02"
    result = generator.simulate_day("603906", trade_date)

    assert result["trade_date"] == trade_date
    assert result["total_steps"] == 48
    assert len(result["steps"]) == 48

    stock_dir = config.get_stock_folder_path("603906")
    realtime_dir = stock_dir / "realtime"
    backtest_dir = stock_dir / "backtest"

    assert (realtime_dir / "603906_rt_5.xlsx").exists()
    assert (realtime_dir / "603906_rt_30.xlsx").exists()
    assert (realtime_dir / "603906_rt_d.xlsx").exists()
    assert (backtest_dir / "603906_5.xlsx").exists()
    assert (backtest_dir / "603906_30.xlsx").exists()
    assert (backtest_dir / "603906_d.xlsx").exists()

    base_5 = pd.read_excel(backtest_dir / "603906_5_1.xlsx")
    base_30 = pd.read_excel(backtest_dir / "603906_30_1.xlsx")
    base_d = pd.read_excel(backtest_dir / "603906_d_1.xlsx")

    for step in range(1, 49):
        info = result["steps"][step - 1]
        assert info["step"] == step
        assert info["realtime_5_count"] == step
        assert info["realtime_30_count"] == (step - 1) // 6 + 1
        assert info["realtime_d_count"] == 1
        assert info["backtest_5_count"] == len(base_5) + step
        assert info["backtest_30_count"] == len(base_30) + ((step - 1) // 6 + 1)
        assert info["backtest_d_count"] == len(base_d) + 1

        step_dir = realtime_dir / "steps" / trade_date / f"step_{step:02d}"
        for name in [
            "603906_rt_5.xlsx",
            "603906_rt_30.xlsx",
            "603906_rt_d.xlsx",
            "603906_5.xlsx",
            "603906_30.xlsx",
            "603906_d.xlsx",
        ]:
            assert (step_dir / name).exists(), f"missing {step_dir / name}"

    final_rt_5 = pd.read_excel(realtime_dir / "603906_rt_5.xlsx")
    final_rt_30 = pd.read_excel(realtime_dir / "603906_rt_30.xlsx")
    final_rt_d = pd.read_excel(realtime_dir / "603906_rt_d.xlsx")
    final_bt_5 = pd.read_excel(backtest_dir / "603906_5.xlsx")
    final_bt_30 = pd.read_excel(backtest_dir / "603906_30.xlsx")
    final_bt_d = pd.read_excel(backtest_dir / "603906_d.xlsx")

    assert len(final_rt_5) == 48
    assert len(final_rt_30) == 8
    assert len(final_rt_d) == 1
    assert len(final_bt_5) == len(base_5) + 48
    assert len(final_bt_30) == len(base_30) + 8
    assert len(final_bt_d) == len(base_d) + 1

    source_5_2 = pd.read_excel(backtest_dir / "603906_5_2.xlsx")
    source_day = source_5_2[pd.to_datetime(source_5_2["日期"]).dt.strftime("%Y-%m-%d") == trade_date].copy()
    source_day = source_day.sort_values("日期").reset_index(drop=True)

    assert pd.to_datetime(final_rt_5["日期"]).equals(pd.to_datetime(source_day["日期"]))
    assert final_rt_5["开盘"].tolist() == source_day["开盘"].tolist()
    assert final_rt_5["收盘"].tolist() == source_day["收盘"].tolist()

    assert pd.to_datetime(final_bt_5["日期"]).is_monotonic_increasing
    assert pd.to_datetime(final_bt_30["日期"]).is_monotonic_increasing
    assert pd.to_datetime(final_bt_d["日期"]).is_monotonic_increasing

    print("module2 realtime validation passed")


if __name__ == "__main__":
    main()
