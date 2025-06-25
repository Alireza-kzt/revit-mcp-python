# InputAgent

The `InputAgent` is the first agent in the design workflow. Its primary responsibility is to interact with the user's initial design request, process it, and transform it into a structured format that can be used by downstream agents.

## Purpose

Users often express their design needs in natural, free-form language. The `InputAgent` uses a Language Model (LLM) to understand this input and extract key architectural requirements. This structured output, often referred to as a "design brief," ensures that subsequent agents receive clear, organized information.

## Implementation Details

*   **Base Class:** `adk.llm_agent.LlmAgent`
*   **Location:** `src/agents/input_agent.py`

The agent is configured with a prompt template that guides the LLM to:
1.  Identify the type of building or space.
2.  Extract quantitative details like area, number of rooms, floors, etc.
3.  Note qualitative aspects such as architectural style, desired atmosphere, or specific features.
4.  Handle missing information gracefully, noting it as "Not specified."

## Input

A string containing the user's free-form design request.
Example: `"I want a cozy two-bedroom apartment, around 80sqm, with a modern feel and a small balcony."`

## Output

A string containing a structured design brief, typically itemized.
Example based on the input above:
```
Structured Brief:
- Building Type: Apartment
- Total Area: approx. 80 sqm
- Number of Bedrooms: 2
- Key Spaces:
    - Balcony: Small
- Architectural Style: Modern
- Specific Constraints/Preferences: Cozy feel
```

## Interaction in the Workflow

The `OrchestratorAgent` calls the `InputAgent`'s `process()` method, passing the raw user query. The `InputAgent` returns the structured brief, which the `OrchestratorAgent` then forwards to the `DesignAgent`.
