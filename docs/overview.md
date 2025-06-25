# System Overview

This document provides a high-level overview of the AI-Assisted Architectural Design System, its components, and their interactions.

## Architecture

The system is composed of several key parts:

1.  **AI Agents (ADK-based):** A set of specialized agents built using the Google Agent Development Kit (ADK). Each agent has a distinct role in the design process.
    *   **InputAgent:** Gathers and preprocesses user requirements.
    *   **DesignAgent:** Proposes a conceptual architectural design.
    *   **RegulationsAgent:** Checks the design against building codes.
    *   **OrchestratorAgent:** Coordinates the workflow between the other agents and interacts with the Revit backend.
2.  **Revit MCP Server (FastMCP-based):** A backend server running inside Revit (via a PyRevit plugin). This server exposes Revit API functionalities as "tools" using the Model Context Protocol (MCP).
3.  **PyRevit Extension:** A plugin for Revit that hosts the MCP server and provides a user interface element (e.g., a button in the Revit ribbon) to start/stop the server.
4.  **User Interface (Conceptual):**
    *   **Input:** The user interacts with the system by providing an initial design prompt (e.g., through a command-line interface or a simple web UI that communicates with the OrchestratorAgent).
    *   **Revit UI:** The PyRevit extension adds a button to the Revit interface to manage the MCP server. The final design modifications appear directly in the active Revit model.

## Workflow

The typical workflow is as follows:

1.  **Server Activation:** The user starts the MCP server from within Revit using the PyRevit extension button. This makes Revit ready to receive commands.
2.  **User Request:** The user submits a design request (e.g., "Design a two-story house with three bedrooms...") to the `OrchestratorAgent`. This could be via a script that runs the Orchestrator.
3.  **Input Processing:** The `OrchestratorAgent` invokes the `InputAgent`, which takes the user's raw request and converts it into a structured design brief.
4.  **Conceptual Design:** The `OrchestratorAgent` passes the structured brief to the `DesignAgent`. The `DesignAgent` generates a conceptual architectural design proposal (e.g., a textual description of spaces, layout, style).
5.  **Regulations Check:** The `OrchestratorAgent` sends the design proposal to the `RegulationsAgent`. The `RegulationsAgent` checks the proposal against a predefined set of simplified building regulations. It either approves the design or suggests modifications.
    *   *(Future Enhancement): If modifications are required, the system might loop back to the `DesignAgent` with feedback, or present the issues to the user for clarification.*
6.  **Revit Implementation:** If the design is approved by the `RegulationsAgent`, the `OrchestratorAgent` proceeds to the implementation phase.
    *   It connects to the FastMCP server running in Revit using an `MCPToolset`.
    *   It translates the approved design proposal into a series of calls to the tools exposed by the MCP server (e.g., `add_wall`, `add_room`).
    *   The MCP server, upon receiving these calls, executes the corresponding Revit API commands, modifying the active Revit model (e.g., creating walls, rooms, windows).
7.  **Feedback/Completion:** The `OrchestratorAgent` reports the outcome of the process (e.g., design implemented, or issues encountered). The user can see the generated geometry directly in their Revit session.

## Data Flow

*   **User Prompt** -> `InputAgent` -> **Structured Brief**
*   **Structured Brief** -> `DesignAgent` -> **Conceptual Design Proposal**
*   **Conceptual Design Proposal** -> `RegulationsAgent` -> **Compliance Report (Approved/Needs Modification)**
*   **Approved Design Proposal** -> `OrchestratorAgent` (parsing logic) -> **MCP Tool Calls**
*   **MCP Tool Calls** -> `FastMCP Server (in Revit)` -> **Revit API Actions** -> **Modifications in Revit Model**

This modular architecture allows for flexibility and scalability. Each agent can be developed and improved independently, and the use of MCP provides a standardized way for AI agents to interact with external tools like Revit.
