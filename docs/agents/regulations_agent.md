# RegulationsAgent

The `RegulationsAgent` plays a crucial role in ensuring that the conceptual design proposed by the `DesignAgent` adheres to a predefined set of building regulations or codes.

## Purpose

Before a design is implemented in Revit, it needs to be checked for basic compliance. The `RegulationsAgent` automates a simplified version of this checking process. It analyzes the textual design proposal and identifies potential conflicts with the programmed regulations.

## Implementation Details

*   **Base Class:** `adk.llm_agent.LlmAgent`
*   **Location:** `src/agents/regulations_agent.py`

This agent is configured with a prompt that includes:
1.  The conceptual design proposal from the `DesignAgent`.
2.  A summary of simplified building regulations (e.g., minimum room sizes, requirements for natural light, basic safety considerations).

The LLM is tasked to compare the design against these rules and determine:
*   If the design is "Approved" (i.e., no obvious violations found).
*   If the design "Requires Modification," in which case it should list the specific issues and, if possible, suggest how they might be rectified.

For this project, the regulations are intentionally simplified. A real-world `RegulationsAgent` would need access to comprehensive and up-to-date building codes, which is a significantly more complex task.

## Input

A string containing the conceptual design proposal from the `DesignAgent`.
Example:
```
Conceptual Design Proposal:
The house is a two-story modern building.
Ground Floor: Features a spacious living room (approx. 25 sqm) connected to an open-plan kitchen (approx. 10 sqm).
First Floor: Contains three bedrooms. The master bedroom (approx. 15 sqm) has an en-suite bathroom. Two smaller bedrooms are 6 sqm and 7 sqm respectively.
```

## Output

A string indicating the compliance status and any identified issues.
Example based on the input (and assuming a simplified rule like "Bedrooms must be at least 7.5 sqm"):
```
Compliance Check Result:
Design Requires Modification
- Issue: Bedroom 2 (6 sqm) is smaller than the minimum required size of 7.5 sqm.
- Issue: Bedroom 3 (7 sqm) is smaller than the minimum required size of 7.5 sqm.
Suggestion: Consider reallocating space or slightly increasing the overall footprint to meet minimum bedroom size requirements.
```
Or, if compliant:
```
Compliance Check Result:
Design Approved
```

## Interaction in the Workflow

The `OrchestratorAgent` calls the `RegulationsAgent`'s `check_compliance()` method with the design proposal.
*   If the result is "Design Approved," the `OrchestratorAgent` proceeds to the Revit implementation phase.
*   If "Design Requires Modification," the current workflow stops and reports the issues. (Future enhancements could involve looping back to the `DesignAgent` with this feedback for iterative refinement.)
