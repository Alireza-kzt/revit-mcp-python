# DesignAgent

The `DesignAgent` is responsible for taking the structured design brief (produced by the `InputAgent`) and generating a detailed, structured architectural design plan.

## Purpose

This agent acts as the creative AI designer in the workflow. It translates the itemized requirements from the brief into a structured representation of the architectural design, using Pydantic models. This structured output, specifically a `DesignPlanModel`, is then used by the `OrchestratorAgent` to make precise calls to the Revit MCP server.

## Implementation Details

*   **Base Class:** `adk.llm_agent.LlmAgent`
*   **Location:** `src/agents/design_agent.py`
*   **Output Model:** `src.shared_models.DesignPlanModel`

The `DesignAgent` is equipped with a sophisticated prompt template that instructs the LLM to:
1.  Understand the input `structured_brief`.
2.  Generate a design proposal consisting of walls, rooms, and other potential elements.
3.  Format its entire output as a single JSON object that strictly conforms to the Pydantic schema of `DesignPlanModel` (which includes `WallModel`, `RoomModel`, etc.). The schema itself is provided as part of the prompt to guide the LLM.
4.  Populate fields like `plan_description`, and lists of `walls` and `rooms` with appropriate coordinates, dimensions, and identifiers.

The agent's `generate_design_plan()` method then:
*   Receives the raw JSON string from the LLM.
*   Attempts to parse this string into a `DesignPlanModel` instance.
*   If parsing is successful, it returns the `DesignPlanModel` object.
*   If parsing fails (due to malformed JSON or schema validation errors), it returns an error message string containing details and the raw LLM output.

## Input

A string containing the structured design brief from the `InputAgent`.
Example:
```
- Building Type: Small Rectangular Cabin
- Total Area: approx. 30 sqm
- Number of Floors: 1
- Key Spaces:
    - Living Area: Combined with kitchenette
    - Bathroom: Small
- Architectural Style: Modern, Minimalist
- Specific Constraints/Preferences: Max width 5m, max length 6m.
```

## Output

*   On success: A `DesignPlanModel` Pydantic object.
*   On failure: An error string.

Example of a successful `DesignPlanModel` (represented as JSON for clarity):
```json
{
  "plan_description": "A modern, minimalist rectangular cabin with a combined living/kitchenette area and a small bathroom.",
  "walls": [
    {
      "start_point": {"x": 0.0, "y": 0.0, "z": 0.0},
      "end_point": {"x": 5.0, "y": 0.0, "z": 0.0},
      "height": 3.0,
      "level_name": "Level 1",
      "wall_id": "south_wall"
    },
    // ... other walls ...
  ],
  "rooms": [
    {
      "name": "Living/Kitchenette",
      "level_name": "Level 1",
      "center_x": 2.5,
      "center_y": 3.0,
      "width": 4.8,
      "length": 3.8,
      "room_id": "living_kitchen_01"
    },
    // ... other rooms ...
  ]
}
```

## Interaction in the Workflow

The `OrchestratorAgent` invokes the `DesignAgent`'s `generate_design_plan()` method, providing the structured brief.
*   If a `DesignPlanModel` object is returned, the `OrchestratorAgent` uses this structured plan to inform the `RegulationsAgent` (e.g., by passing the `plan_description` or a summary) and subsequently to generate precise MCP tool calls for Revit.
*   If an error string is returned, the `OrchestratorAgent` handles the error, potentially halting the process or logging the issue.
