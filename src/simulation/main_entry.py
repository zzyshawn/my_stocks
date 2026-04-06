from __future__ import annotations

from typing import Any, Optional

from src.simulation.orchestrator import AnalysisOrchestrator


def run_generation_analysis(
    mode: str,
    stock_code: str,
    trade_date: str,
    user_id: str,
    conversation_id: str,
    orchestrator: Optional[AnalysisOrchestrator] = None,
    **kwargs: Any,
) -> Any:
    orchestrator = orchestrator or AnalysisOrchestrator()

    if mode == "simulation":
        return orchestrator.run_simulation_day(
            stock_code=stock_code,
            trade_date=trade_date,
            user_id=user_id,
            conversation_id=conversation_id,
            **kwargs,
        )

    if mode == "realtime":
        return orchestrator.run_realtime_batch(
            stock_code=stock_code,
            trade_date=trade_date,
            user_id=user_id,
            conversation_id=conversation_id,
            **kwargs,
        )

    raise ValueError(f"unsupported mode: {mode}")
