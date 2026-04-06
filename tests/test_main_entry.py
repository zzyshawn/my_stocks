from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.simulation.main_entry import run_generation_analysis


class StubOrchestrator:
    def __init__(self):
        self.calls = []

    def run_simulation_day(self, **kwargs):
        self.calls.append(("simulation", kwargs))
        return {"mode": "simulation", **kwargs}

    def run_realtime_batch(self, **kwargs):
        self.calls.append(("realtime", kwargs))
        return {"mode": "realtime", **kwargs}


def test_dispatches_simulation_mode():
    orchestrator = StubOrchestrator()

    result = run_generation_analysis(
        mode="simulation",
        stock_code="603906",
        trade_date="2024-09-02",
        user_id="u1",
        conversation_id="c1",
        orchestrator=orchestrator,
    )

    assert result["mode"] == "simulation"
    assert orchestrator.calls == [(
        "simulation",
        {
            "stock_code": "603906",
            "trade_date": "2024-09-02",
            "user_id": "u1",
            "conversation_id": "c1",
        },
    )]


def test_dispatches_realtime_mode():
    orchestrator = StubOrchestrator()

    result = run_generation_analysis(
        mode="realtime",
        stock_code="603906",
        trade_date="2024-09-02",
        user_id="u1",
        conversation_id="c1",
        orchestrator=orchestrator,
    )

    assert result["mode"] == "realtime"
    assert orchestrator.calls == [(
        "realtime",
        {
            "stock_code": "603906",
            "trade_date": "2024-09-02",
            "user_id": "u1",
            "conversation_id": "c1",
        },
    )]


def test_rejects_unknown_mode():
    orchestrator = StubOrchestrator()

    try:
        run_generation_analysis(
            mode="unknown",
            stock_code="603906",
            trade_date="2024-09-02",
            user_id="u1",
            conversation_id="c1",
            orchestrator=orchestrator,
        )
    except ValueError as exc:
        assert "unknown" in str(exc)
    else:
        raise AssertionError("expected ValueError")
