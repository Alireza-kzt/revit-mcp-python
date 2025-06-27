from google.adk.agents import LlmAgent

from config import MODEL


class InputAgent(LlmAgent):
    """Collects and structures user requirements."""

    def __init__(self) -> None:
        super().__init__(
            name="InputAgent",
            model=MODEL,
            instruction=(
                "Gather the user's architectural requirements and output a JSON "
                "object with keys `rooms` (list of room descriptions) and "
                "`style` (overall style keywords)."
            ),
        )
