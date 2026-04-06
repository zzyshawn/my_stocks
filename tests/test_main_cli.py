from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import main


class StubOrchestrator:
    def __init__(self):
        self.calls = []

    def run_simulation_day(self, **kwargs):
        self.calls.append(("simulation", kwargs))
        return {"mode": "simulation", **kwargs}

    def run_realtime_batch(self, **kwargs):
        self.calls.append(("realtime", kwargs))
        return {"mode": "realtime", **kwargs}


def test_cli_main_dispatches_simulation_mode(monkeypatch):
    orchestrator = StubOrchestrator()
    monkeypatch.setattr(main, "AnalysisOrchestrator", lambda: orchestrator)

    result = main.main([
        "--mode", "simulation",
        "--stock-code", "603906",
        "--trade-date", "2024-09-02",
        "--user-id", "u1",
        "--conversation-id", "c1",
    ])

    assert result["mode"] == "simulation"
    assert orchestrator.calls[0][0] == "simulation"


def test_cli_main_dispatches_realtime_mode(monkeypatch):
    orchestrator = StubOrchestrator()
    monkeypatch.setattr(main, "AnalysisOrchestrator", lambda: orchestrator)

    result = main.main([
        "--mode", "realtime",
        "--stock-code", "603906",
        "--trade-date", "2024-09-02",
        "--user-id", "u1",
        "--conversation-id", "c1",
    ])

    assert result["mode"] == "realtime"
    assert orchestrator.calls[0][0] == "realtime"
