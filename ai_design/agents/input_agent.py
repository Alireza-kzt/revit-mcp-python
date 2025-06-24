from google.adk.agents import LlmAgent

class InputAgent(LlmAgent):
    """Collects and structures user requirements."""

    def __init__(self) -> None:
        super().__init__(
            name="InputAgent",
            instruction=(
                "Gather the user's architectural requirements and output a JSON "
                "object with keys `rooms` (list of room descriptions) and "
                "`style` (overall style keywords)."
            ),
            model="gemini-1.5-flash",
        )
