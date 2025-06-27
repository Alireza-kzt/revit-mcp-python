from google.adk.agents import LlmAgent

from config import MODEl


class DesignAgent(LlmAgent):
    """Creates a conceptual design from a structured brief."""

    def __init__(self) -> None:
        super().__init__(
            name="DesignAgent",
            model=MODEl,
            instruction=(
                "Using the provided requirements, propose a simple building layout "
                "as JSON with `walls` (start,end,height) and `rooms` (name,size)."
            ),
        )
