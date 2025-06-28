from google.adk.agents import LlmAgent
from google.adk.planners import PlanReActPlanner
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
                "Coordinate the design workflow in the following order:\n"
                "1. Use `InputAgent` to collect user requirements.\n"
                "2. Pass the requirements to `DesignAgent` and store the JSON result in state key `design`.\n"
                "3. Call `RegulationsAgent` with the design JSON. If it returns `approved: false`, loop back to `DesignAgent` with the suggested modifications until approval.\n"
                "4. Once approved, invoke `RevitAgent` with the final design to apply changes in Revit."
            ),
            sub_agents=[
                InputAgent(),
                DesignAgent(),
                RegulationsAgent(),
                RevitAgent(),
            ],
            planner=PlanReActPlanner(),
        )
