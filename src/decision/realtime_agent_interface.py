from __future__ import annotations

from typing import Any, Dict


class RealtimeAgentInterface:
    def on_step(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "status": "placeholder",
            "message": "agent not implemented",
            "payload": payload,
        }
