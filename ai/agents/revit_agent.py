from google.adk.agents import BaseAgent


class RevitAgent(BaseAgent):
    """Executes design instructions in Revit via MCP."""

    def __init__(self) -> None:
        super().__init__(name="RevitAgent")
        # ToDo
