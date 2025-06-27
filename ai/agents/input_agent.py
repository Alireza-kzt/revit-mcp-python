from google.adk.agents import LlmAgent

from config import MODEl


class InputAgent(LlmAgent):
    """Collects and structures user requirements."""

    def __init__(self) -> None:
        super().__init__(
            name="InputAgent",
            model=MODEl,
            instruction=(
                "Gather the user's architectural requirements and output a JSON "
                "object with keys `rooms` (list of room descriptions) and "
                "`style` (overall style keywords)."
            ),
        )
