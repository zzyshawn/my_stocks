from __future__ import annotations

from typing import Any, Optional

from src.simulation.multi_stock_runner import MultiStockRealtimeRunner, MultiStockSimulationRunner
from src.simulation.orchestrator import AnalysisOrchestrator
from src.utils.config import get_config


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


def main() -> Any:
    config = get_config()
    user_id = config.get("simulation.user_id", "test_user")
    conversation_id = config.get("simulation.conversation_id", "test_conv")
    default_mode = str(config.get("app.default_mode", "simulation"))

    print("1. 模拟")
    print("2. 实时")
    print(f"当前默认模式: {default_mode}")

    if default_mode == "simulation":
        runner = MultiStockSimulationRunner(config=config)
        return runner.run(user_id=user_id, conversation_id=conversation_id)

    if default_mode == "realtime":
        runner = MultiStockRealtimeRunner(config=config)
        return runner.run_once(user_id=user_id, conversation_id=conversation_id)

    raise ValueError(f"unsupported default mode: {default_mode}")


if __name__ == "__main__":
    main()
