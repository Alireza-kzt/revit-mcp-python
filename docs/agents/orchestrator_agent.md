# OrchestratorAgent

The `OrchestratorAgent` is the central coordinator of the AI-assisted design process. It manages the sequence of operations, invokes other specialized agents, and handles the interaction with the Revit backend via the Model Context Protocol (MCP).

## Purpose

The primary purpose of the `OrchestratorAgent` is to manage the overall workflow. It ensures that data flows correctly between agents (e.g., structured brief to `DesignAgent`, `DesignPlanModel` to MCP interaction) and that each step of the design process is executed in the correct order. It acts as the "brain" of the multi-agent system.

## Implementation Details

*   **Base Class:** `adk.agent.Agent`
*   **Location:** `src/agents/orchestrator_agent.py`
*   **Key Dependency:** `adk.mcp_toolset.MCPToolset` for Revit communication.
*   **Data Model Used:** Consumes `src.shared_models.DesignPlanModel` from `DesignAgent`.

Key responsibilities and logic:
1.  **Initialization:** Instantiates `InputAgent`, `DesignAgent`, and `RegulationsAgent`.
2.  **Workflow Management (`process_design_request` method):**
    *   Receives the initial user design prompt.
    *   Calls `InputAgent.process()` to get a structured brief.
    *   Passes the brief to `DesignAgent.generate_design_plan()` to obtain a `DesignPlanModel` object (or an error string if generation/parsing failed).
    *   If a valid `DesignPlanModel` is received, it passes a textual summary (e.g., `plan.plan_description` and element counts) to `RegulationsAgent.check_compliance()`.
3.  **MCP Integration (`trigger_revit_implementation` method):**
    *   This method is called if the `RegulationsAgent` approves the design.
    *   It takes the `DesignPlanModel` as input.
    *   Initializes an `MCPToolset` instance, providing the `FASTMCP_SERVER_URL` (typically from an environment variable loaded via `python-dotenv`).
    *   Connects to the FastMCP server running in Revit.
    *   Iterates through the elements in the `design_plan` (e.g., `design_plan.walls`, `design_plan.rooms`).
    *   For each element:
        *   It translates the Pydantic model data (e.g., `WallModel`, `RoomModel`) into the specific arguments required by the corresponding MCP tool (e.g., `add_wall`, `add_room`). For instance, for a `RoomModel`, it calls `room.calculate_boundary_points_xy()` to generate the boundary point list for the `add_room` tool.
        *   It creates an `adk.tool.Call` object with the tool name and arguments.
        *   It invokes the tool using `self.mcp_toolset.invoke_tool(call, context)`.
    *   Collects responses and logs actions taken or errors encountered.
    *   Ensures the `MCPToolset` connection is closed using a `finally` block.
4.  **State Management:** Uses the ADK `Session` object to maintain context and history. Outputs from agents (like the structured brief or the JSON representation of `DesignPlanModel`) are added to the session.
5.  **Error Handling:** Manages potential errors from sub-agents (e.g., if `DesignAgent` fails to produce a valid plan) and from MCP tool calls or connection issues.

## Input

*   An initial user design prompt (string).
*   Environment variables:
    *   `GOOGLE_API_KEY` (or equivalent for the LLM service used by sub-agents).
    *   `FASTMCP_SERVER_URL` for connecting to the Revit MCP server (defaults to `http://localhost:8765`).

## Output

*   A dictionary summarizing the design process, including:
    *   `status`: ("completed", "requires_modification", "error", "error_revit").
    *   `structured_brief`: Output from `InputAgent`.
    *   `design_plan`: The `DesignPlanModel` (as a dictionary) from `DesignAgent`.
    *   `compliance_result`: Output from `RegulationsAgent`.
    *   `revit_actions_summary`: A log of actions taken by the MCP tools or error messages.
*   **Side effects:** Modifications to the active Revit model if the workflow completes successfully and MCP calls succeed.

## Interaction in the Workflow

1.  The `OrchestratorAgent` is invoked with a user's design request.
2.  It sequentially calls `InputAgent`, then `DesignAgent`.
3.  If `DesignAgent` successfully returns a `DesignPlanModel`, the `OrchestratorAgent` calls `RegulationsAgent` with a summary from this plan.
4.  Based on `RegulationsAgent`'s output:
    *   **"Design Approved"**: It calls `trigger_revit_implementation()` with the `DesignPlanModel` to interact with Revit via MCP.
    *   **"Design Requires Modification"**: It reports this outcome. The workflow stops before Revit interaction.
    *   **Error from any agent**: It reports the error and stops.

The use of `DesignPlanModel` makes the translation from conceptual design to concrete Revit commands (via MCP tools) significantly more reliable and manageable than parsing free-form text.
