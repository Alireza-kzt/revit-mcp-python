from google.adk.agents import LlmAgent

from config import MODEl


class RegulationsAgent(LlmAgent):
    """Checks a design against simplified building regulations."""

    def __init__(self) -> None:
        super().__init__(
            name="RegulationsAgent",
            model=MODEl,
            instruction=(
                "Review the proposed design. If all rooms are at least 9 sqm, "
                "respond with `{\"approved\": true}`. Otherwise suggest "
                "modifications in JSON."
            ),
        )
