# PyRevit Plugin

The PyRevit plugin is a crucial component for bridging the gap between the AI agent system and Autodesk Revit. It serves two main purposes:
1.  Hosting the FastMCP server within the Revit environment.
2.  Providing a user interface element (a ribbon button) for the user to control the server.

## Purpose

To enable external AI agents (specifically the `OrchestratorAgent`) to interact with a Revit model, an MCP server must be running in the context of an active Revit session. The PyRevit plugin facilitates this by:
*   Allowing the user to start and (conceptually) stop the MCP server.
*   Ensuring the MCP server has access to the necessary Revit application and document objects (`Application`, `UIDocument`, `Document`).

## Implementation Details

*   **Location:** `AIDesign.extension/AIDesign.tab/AI Server.panel/Start Server.pushbutton/script.py`
*   **Framework:** PyRevit (a Python scripting environment for Revit)

### Key Features of the `script.py`:

1.  **Server Control UI:**
    *   The script is associated with a pushbutton in the Revit ribbon (e.g., under a tab named "AI Design" and panel "AI Server").
    *   Clicking the button toggles the server's state: if off, it starts; if on, it attempts to stop it.
2.  **Environment Setup:**
    *   It includes logic (`ensure_project_path`) to add the main project's `src` directory to `sys.path`. This is necessary so that it can import the `mcp_server` module from `src.revit_server`. This typically relies on an environment variable (`AI_DESIGN_ASSISTANT_PATH`) pointing to the project's root.
3.  **MCP Server Management:**
    *   **Importing:** It imports the `mcp_server` module (which contains the FastMCP app and tool definitions).
    *   **Context Injection:** Before starting the server, it calls `mcp_server.set_revit_context(__revit__.Application, __revit__.ActiveUIDocument, __revit__.ActiveUIDocument.Document)`. This passes the live Revit objects to the server module, making them available to the MCP tools.
    *   **Threading:** The MCP server (which is an `asyncio` application) is run in a separate `threading.Thread`. This is essential to prevent the Revit UI from freezing while the server is active.
    *   **Starting:** Calls the `run_server` function from the `mcp_server` module within the new thread.
    *   **Stopping (Conceptual):** Stopping an `asyncio` server running in a separate thread from an external synchronous call is non-trivial. The current script includes conceptual logic for stopping, but notes the complexities. True graceful shutdown would require inter-thread communication (e.g., an event) that the `asyncio` server loop checks. For now, the server thread is a daemon, so it should terminate when Revit exits.
4.  **User Feedback:** Uses `TaskDialog.Show()` to display messages to the user (e.g., "Server started," "Error starting server").
5.  **Error Handling:** Basic `try-except` blocks are used to catch common issues, like `ImportError` if the server module cannot be found.

## Installation and Usage

1.  **Prerequisites:**
    *   PyRevit must be installed in Autodesk Revit.
    *   The Python environment used by PyRevit should have access to the `fastmcp` and `uvicorn` (as a dependency of FastMCP) packages. This might involve configuring PyRevit to use a specific CPython environment if it's not using one that already has these packages.
    *   The `AI_DESIGN_ASSISTANT_PATH` environment variable must be set on the system, pointing to the root directory of this AI Design Assistant project.
2.  **Plugin Installation:**
    *   Copy the entire `AIDesign.extension` folder into one of PyRevit's known extension paths (check PyRevit settings for these paths).
3.  **Running:**
    *   After restarting Revit (or reloading PyRevit), a new tab "AI Design" should appear in the ribbon.
    *   Under this tab, a panel "AI Server" will contain a "Start Server" button.
    *   Click this button to start the MCP server. A dialog should confirm if it started successfully. The server will then listen for incoming requests from the `OrchestratorAgent`.

This plugin is the gateway for AI-driven modifications within the Revit environment. Its correct functioning is vital for the entire system.
