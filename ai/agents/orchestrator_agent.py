from google.adk.agents import LlmAgent
from ai.config import llm_model
from .input_agent import InputAgent
from .design_agent import DesignAgent
from .regulations_agent import RegulationsAgent
from .revit_agent import RevitAgent


class OrchestratorAgent(LlmAgent):
    """Pipeline orchestrating the design process."""

    def __init__(self) -> None:
        super().__init__(
            name="OrchestratorAgent",
            model=llm_model,
            instruction=(
                "Coordinate the design pipeline by delegating tasks "
                "to specialized sub-agents."
            ),
            sub_agents=[
                InputAgent(),
                DesignAgent(),
                RegulationsAgent(),
                RevitAgent(),
            ],
        )
