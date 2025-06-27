from google.adk.agents import LlmAgent

from ai.config import llm_model


class DesignAgent(LlmAgent):
    """Creates a conceptual design from a structured brief."""

    def __init__(self) -> None:
        super().__init__(
            name="DesignAgent",
            model=llm_model(),
            instruction=(
                "Using the provided requirements, propose a simple building layout "
                "as JSON with `walls` (start,end,height) and `rooms` (name,size)."
            ),
        )
