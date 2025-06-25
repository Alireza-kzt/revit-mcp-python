import json
from adk.llm_agent import LlmAgent, LlmAgentConfig, UserMessage, AssistantMessage
from adk.llm_service_adapter import LlmServiceAdapter
from adk.session import Session
from pydantic import ValidationError

from ..shared_models import DesignPlanModel # Relative import if shared_models is in src/

class DesignAgent(LlmAgent):
    """
    DesignAgent proposes an architectural design solution based on structured requirements.
    It outputs a DesignPlanModel instance (serialized as JSON string by the LLM, then parsed).
    """

    def __init__(self, llm_service_adapter: LlmServiceAdapter | None = None):
        config = LlmAgentConfig(
            name="DesignAgent",
        )
        super().__init__(config=config, llm_service_adapter=llm_service_adapter)

    async def generate_design_plan(self, session: Session, structured_brief: str) -> DesignPlanModel | str:
        """
        Generates a conceptual design plan as a DesignPlanModel.
        The LLM is prompted to return JSON conforming to the DesignPlanModel schema.
        If parsing fails, it returns the raw string output from the LLM.
        """
        # Provide the Pydantic model schema in the prompt to guide the LLM.
        # This is a simplified way; more advanced methods might involve function calling if supported.
        design_plan_schema_json = DesignPlanModel.schema_json(indent=2)

        prompt_template = f"""
You are an AI architectural designer. Your task is to create a conceptual design proposal
based on the following structured brief.

Structured Brief:
{structured_brief}

Output Format:
You MUST output your design proposal as a single JSON object that strictly conforms to the following Pydantic schema.
Do NOT include any explanatory text before or after the JSON object.

Schema:
```json
{design_plan_schema_json}
```

Instructions for populating the JSON:
- `plan_description`: Provide a concise overall textual description of the design.
- `walls`: Define essential walls. For a simple rectangular building, you might define 4 exterior walls.
    - `start_point` and `end_point`: Define wall baseline coordinates (x, y, z). Assume z=0 for ground level if not specified.
    - `height`: Common wall height, e.g., 3.0 (meters or feet, be consistent with Revit's units, assume feet for now).
    - `level_name`: e.g., "Level 1".
    - `wall_id`: A unique descriptive ID, e.g., "exterior_north_wall".
- `rooms`: Define key rooms.
    - `name`: e.g., "Living Room", "Bedroom 1".
    - `level_name`: e.g., "Level 1".
    - `center_x`, `center_y`: Approximate center coordinates for the room. Try to place them logically within the defined walls.
    - `width`, `length`: Dimensions of the room.
    - `room_id`: A unique descriptive ID, e.g., "living_room_01".

Example of a simple wall:
{{
    "start_point": {{"x": 0, "y": 0, "z": 0}},
    "end_point": {{"x": 5, "y": 0, "z": 0}},
    "height": 3.0,
    "level_name": "Level 1",
    "wall_id": "south_wall"
}}
Example of a simple room:
{{
    "name": "Office",
    "level_name": "Level 1",
    "center_x": 2.5,
    "center_y": 2.0,
    "width": 2.5,
    "length": 2.0,
    "room_id": "office_01"
}}

Ensure all coordinates and dimensions are consistent and make sense spatially.
For example, rooms should generally be located within the span of the defined walls.

JSON Output:
        """

        messages = [
            UserMessage(content=prompt_template)
        ]

        response_message = await self.invoke(session, messages)
        raw_llm_output = ""

        if response_message and isinstance(response_message.content, str):
            raw_llm_output = response_message.content
        elif response_message: # Handle other content types if necessary
            raw_llm_output = str(response_message.content)
        else:
            return "Error: Could not generate a design proposal from LLM."

        # Attempt to parse the LLM output as JSON into the Pydantic model
        try:
            # The LLM might sometimes wrap the JSON in ```json ... ```
            cleaned_json_str = raw_llm_output.strip()
            if cleaned_json_str.startswith("```json"):
                cleaned_json_str = cleaned_json_str[7:]
            if cleaned_json_str.endswith("```"):
                cleaned_json_str = cleaned_json_str[:-3]

            design_plan_data = json.loads(cleaned_json_str)
            plan = DesignPlanModel(**design_plan_data)

            session.set_agent_state(self.config.name, {"design_plan_model": plan.model_dump()}) # Store dict representation
            session.add_message(AssistantMessage(content=plan.model_dump_json(indent=2), name=self.config.name))
            return plan
        except (json.JSONDecodeError, ValidationError) as e:
            error_message = f"Error: LLM output was not valid DesignPlanModel JSON. Details: {e}\nRaw LLM Output:\n{raw_llm_output}"
            session.set_agent_state(self.config.name, {"design_plan_error": error_message, "raw_output": raw_llm_output})
            session.add_message(AssistantMessage(content=raw_llm_output, name=self.config.name)) # Still log raw output
            return error_message # Return the error message string
        except Exception as e: # Catch any other unexpected errors during parsing
            error_message = f"Error: Unexpected error parsing DesignPlanModel. Details: {e}\nRaw LLM Output:\n{raw_llm_output}"
            session.set_agent_state(self.config.name, {"design_plan_error": error_message, "raw_output": raw_llm_output})
            session.add_message(AssistantMessage(content=raw_llm_output, name=self.config.name))
            return error_message


if __name__ == '__main__':
    import asyncio
    from dotenv import load_dotenv
    # from adk.llm_service_adapters.gemini_adapter import GeminiAdapter # Example

    load_dotenv() # Loads GOOGLE_API_KEY from .env

    async def main():
        # design_agent = DesignAgent(llm_service_adapter=GeminiAdapter()) # Example with specific adapter
        design_agent = DesignAgent() # Uses default adapter from ADK context (ensure API key is set)
        test_session = Session(session_id="test_design_agent_pydantic")

        sample_brief = """
- Building Type: Small Rectangular Cabin
- Total Area: approx. 30 sqm
- Number of Floors: 1
- Key Spaces:
    - Living Area: Combined with kitchenette
    - Bathroom: Small
- Architectural Style: Modern, Minimalist
- Specific Constraints/Preferences: One main entrance door, two windows. Max width 5m, max length 6m.
        """
        print(f"Input Brief:\n{sample_brief}\n")

        design_plan_result = await design_agent.generate_design_plan(test_session, sample_brief)

        print("--- DesignAgent Result ---")
        if isinstance(design_plan_result, DesignPlanModel):
            print("Successfully parsed DesignPlanModel:")
            print(design_plan_result.model_dump_json(indent=2))
        elif isinstance(design_plan_result, str): # Error string
            print("Failed to generate/parse DesignPlanModel:")
            print(design_plan_result)

        # print("\n--- Session History ---")
        # for msg in test_session.history:
        #     print(f"[{msg.role} ({getattr(msg, 'name', 'N/A')})] {msg.content}")

    # To run this:
    # 1. Ensure GOOGLE_API_KEY (or equivalent) is in .env or environment.
    # 2. Run `python -m src.agents.design_agent` from the project root.
    # asyncio.run(main()) # Commented out for non-blocking tool execution
    pass
