from google.adk.agents import SequentialAgent, BaseAgent
from .input_agent import InputAgent
from .design_agent import DesignAgent
from .regulations_agent import RegulationsAgent
from .revit_agent import RevitAgent

class OrchestratorAgent(SequentialAgent):
    """Pipeline orchestrating the design process."""

    def __init__(self) -> None:
        super().__init__(
            name="OrchestratorAgent",
            sub_agents=[InputAgent(), DesignAgent(), RegulationsAgent(), RevitAgent()],
        )
