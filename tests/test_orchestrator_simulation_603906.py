from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.simulation.orchestrator import AnalysisOrchestrator
from src.utils.config import get_config


class RecordingNotifier:
    def __init__(self):
        self.requests = []

    def send(self, request):
        self.requests.append(request)


class StubSplitter:
    def __init__(self):
        self.calls = []

    def split_stock(self, stock_code, overwrite=False):
        self.calls.append((stock_code, overwrite))
        return {"stock_code": stock_code}


class StubRunner:
    def __init__(self):
        self.calls = []

    def run_real(self, stock_code):
        self.calls.append(("real", stock_code))
        return {}

    def run_test_step(self, stock_code, trade_date, step):
        self.calls.append(("test", stock_code, trade_date, step))
        return {
            "d": {
                "indicator_df": [
                    {"日期": "2024-09-02", "收盘": 10.5, "成交量": 120, "最低": 10.1, "最高": 10.8, "MACD_DIF": 0.2},
                ],
                "chanlun_summary": {"last_zs_range": {"zd": 9.8, "zg": 10.8}},
            },
            "30": {
                "indicator_df": [
                    {"日期": "2024-09-02 10:05:00", "收盘": 10.2, "成交量": 32, "最低": 10.1, "最高": 10.4, "RSI6": 53},
                ],
                "chanlun_summary": {"last_zs_range": {"zd": 10.0, "zg": 10.4}},
            },
            "5": {
                "indicator_df": [
                    {"日期": "2024-09-02 10:05:00", "收盘": 10.12, "成交量": 6, "最低": 10.08, "最高": 10.20},
                ],
                "chanlun_summary": {"last_zs_range": {"zd": 10.05, "zg": 10.2}},
            },
        }


class StubGenerator:
    def __init__(self, config=None, keep_step_files=True, step_callback=None):
        self.step_callback = step_callback

    def simulate_day(self, stock_code, trade_date):
        steps = []
        for step in [1, 2]:
            payload = {"stock_code": stock_code, "trade_date": trade_date, "step": step}
            analysis_result = self.step_callback(payload)
            steps.append({"step": step, "analysis_result": analysis_result})
        return {"stock_code": stock_code, "trade_date": trade_date, "total_steps": 2, "steps": steps}


def main() -> None:
    config = get_config()
    notifier = RecordingNotifier()
    output_dirs = {
        "real": Path("tests/.tmp/real"),
        "simulation": Path("tests/.tmp/backtest"),
    }

    orchestrator = AnalysisOrchestrator(
        config=config,
        notifier=notifier,
        packager_output_dirs=output_dirs,
    )
    orchestrator.splitter = StubSplitter()
    orchestrator.runner = StubRunner()
    orchestrator.generator_cls = StubGenerator

    result = orchestrator.run_simulation_day(
        stock_code="603906",
        trade_date="2024-09-02",
        user_id="test_user",
        conversation_id="test_conv",
        overwrite_split=True,
        run_real=False,
        keep_step_files=False,
    )

    assert result["trade_date"] == "2024-09-02"
    assert result["total_steps"] == 2
    assert len(notifier.requests) == 2

    first_request = notifier.requests[0]
    assert first_request["type"] == "DATA_READY"
    assert first_request["user_id"] == "test_user"
    assert first_request["conversation_id"] == "test_conv"

    data_path = Path(first_request["data_path"])
    assert data_path.exists()
    assert data_path.parent == output_dirs["simulation"]

    last_step = result["steps"][-1]
    assert Path(last_step["data_path"]).exists()
    assert last_step["notify_request"]["type"] == "DATA_READY"
    assert last_step["notify_request"]["data_path"] == last_step["data_path"]

    print("orchestrator simulation notification validation passed")


if __name__ == "__main__":
    main()
