from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.simulation.splitter import StockDataSplitter
from src.utils.config import get_config


def main() -> None:
    splitter = StockDataSplitter(get_config())
    result = splitter.split_stock("603906", overwrite=True)

    assert result["stock_code"] == "603906"
    assert set(result["periods"].keys()) == {"d", "30", "5"}

    for period, info in result["periods"].items():
        assert info["status"] == "success"
        assert Path(info["part1_file"]).exists()
        assert Path(info["part2_file"]).exists()
        assert info["part1_count"] + info["part2_count"] == info["source_count"]

    source_file = splitter.config.get_kline_file_path("603906", "5")
    source_df = splitter.load_kline_data(source_file)
    info_5 = result["periods"]["5"]
    part1_df = pd.read_excel(info_5["part1_file"])
    part2_df = pd.read_excel(info_5["part2_file"])
    merged_df = pd.concat([part1_df, part2_df], ignore_index=True)

    assert len(merged_df) == len(source_df)
    assert pd.to_datetime(merged_df["日期"]).equals(pd.to_datetime(source_df["日期"]))
    assert merged_df["开盘"].tolist() == source_df["开盘"].tolist()
    assert merged_df["收盘"].tolist() == source_df["收盘"].tolist()

    test_start = pd.Timestamp(splitter.test_start)
    for period in ["d", "30", "5"]:
        info = result["periods"][period]
        part1_df = pd.read_excel(info["part1_file"])
        part2_df = pd.read_excel(info["part2_file"])
        if not part1_df.empty:
            assert pd.to_datetime(part1_df["日期"]).max() < test_start
        if not part2_df.empty:
            assert pd.to_datetime(part2_df["日期"]).min() >= test_start

    print("module1 splitter validation passed")


if __name__ == "__main__":
    main()
