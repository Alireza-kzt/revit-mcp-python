import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ai_design.agents.input_agent import InputAgent
from ai_design.agents.design_agent import DesignAgent
from ai_design.agents.regulations_agent import RegulationsAgent


def test_agent_names():
    assert InputAgent().name == "InputAgent"
    assert DesignAgent().name == "DesignAgent"
    assert RegulationsAgent().name == "RegulationsAgent"
