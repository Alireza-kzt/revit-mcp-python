from google.adk.agents import LlmAgent
from ai.config import llm_model


class RegulationsAgent(LlmAgent):
    """Checks a design against simplified building regulations."""

    def __init__(self) -> None:
        super().__init__(
            name="RegulationsAgent",
            model=llm_model,
            instruction=(
                "Review the proposed design. If all rooms are at least 9 sqm, "
                "respond with `{\"approved\": true}`. Otherwise suggest "
                "modifications in JSON."
            ),
            output_key="review",
        )
