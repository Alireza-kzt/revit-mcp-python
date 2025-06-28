from google.adk.agents import LlmAgent

from ai.config import llm_model


class InputAgent(LlmAgent):
    """Collects and structures user requirements."""

    def __init__(self) -> None:
        super().__init__(
            name="InputAgent",
            model=llm_model,
            instruction=(
                "Gather the user's architectural requirements and output a JSON "
                "object with keys `rooms` (list of room descriptions) and "
                "`style` (overall style keywords)."
            ),
            output_key="requirements",
        )
