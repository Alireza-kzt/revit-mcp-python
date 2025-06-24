from google.adk.agents import SequentialAgent, BaseAgent
from .input_agent import InputAgent
from .design_agent import DesignAgent
from .regulations_agent import RegulationsAgent
from .revit_agent import RevitAgent

class OrchestratorAgent(SequentialAgent):
    """Pipeline orchestrating the design process."""

    revit_agent: RevitAgent | None = None

    def __init__(self, mcp_url: str) -> None:
        object.__setattr__(self, "revit_agent", RevitAgent(mcp_url))
        super().__init__(
            name="OrchestratorAgent",
            sub_agents=[InputAgent(), DesignAgent(), RegulationsAgent(), self.revit_agent],
        )
