import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ai_design.agents.orchestrator_agent import OrchestratorAgent


def test_orchestrator_init():
    orch = OrchestratorAgent("http://localhost")
    assert orch.name == "OrchestratorAgent"
    assert len(orch.sub_agents) == 4
