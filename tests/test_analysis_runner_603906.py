from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.simulation.analysis_runner import AnalysisRunner
from src.simulation.realtime_generator import SingleDayRealtimeGenerator
from src.simulation.splitter import StockDataSplitter
from src.utils.config import get_config


def main() -> None:
    config = get_config()
    splitter = StockDataSplitter(config)
    splitter.split_stock("603906", overwrite=True)

    runner = AnalysisRunner(config)
    real_result = runner.run_real("603906")
    assert set(real_result.keys()) == {"d", "30", "5"}

    generator = SingleDayRealtimeGenerator(
        config=config,
        keep_step_files=True,
        step_callback=runner.build_step_callback(),
    )
    result = generator.simulate_day("603906", "2024-09-02")

    out_dir = config.get_stock_folder_path("603906") / "backtest" / "out"
    for period in ["d", "30", "5"]:
        assert (out_dir / "real" / period / f"603906_{period}_indicators.xlsx").exists()
        assert (out_dir / "real" / period / f"603906_{period}_chanlun.json").exists()
        assert (out_dir / "test" / period / f"603906_{period}_indicators.xlsx").exists()
        assert (out_dir / "test" / period / f"603906_{period}_chanlun.json").exists()
        assert (out_dir / "test" / "debug" / "2024-09-02" / "step_48" / period / f"603906_{period}_indicators.xlsx").exists()

    assert result["steps"][-1]["analysis_result"] is not None
    debug_indicator = pd.read_excel(out_dir / "test" / "debug" / "2024-09-02" / "step_48" / "5" / "603906_5_indicators.xlsx")
    assert not debug_indicator.empty
    assert len(pd.read_excel(out_dir / "test" / "d" / "603906_d_indicators.xlsx")) <= 30
    assert len(pd.read_excel(out_dir / "test" / "30" / "603906_30_indicators.xlsx")) <= 30 * 8
    assert len(pd.read_excel(out_dir / "test" / "5" / "603906_5_indicators.xlsx")) <= 30 * 48

    print("module3 analysis runner validation passed")


if __name__ == "__main__":
    main()
