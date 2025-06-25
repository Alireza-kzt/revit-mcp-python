# MCP Server (FastMCP)

The Model Context Protocol (MCP) Server is the component that runs inside Revit and exposes Revit API functionalities as "tools" that can be called remotely by AI agents, specifically the `OrchestratorAgent`. This project uses **FastMCP** to implement this server.

## Purpose

The core idea is to allow the AI agents, which run in a separate Python environment, to query information from and send commands to the live Revit model. MCP provides a standardized way to define and interact with these Revit-specific tools.

## Implementation Details

*   **Location:** `src/revit_server/mcp_server.py`
*   **Framework:** `fastmcp` (a Python library for creating MCP servers, built on FastAPI/Starlette)

### Key Features:

1.  **Server Initialization:**
    *   A `FastMCP` application instance is created, configured with a title, description, and version.
    *   `mcp_server = FastMCP(...)`
2.  **Tool Definition:**
    *   Revit API functionalities are wrapped into Python `async def` functions.
    *   Each such function is decorated with `@mcp.tool` (or `@tool` from `fastmcp`). This decorator registers the function with the FastMCP application and makes it discoverable via the MCP specification (usually available at `/openapi.json` or a similar endpoint).
    *   **Tool Signature:** Tools are defined with typed arguments (e.g., `start_point: list[float]`, `room_name: str`). These types are used by FastMCP to generate the MCP tool specification and perform input validation. Each tool also receives a `ctx: ToolContext` argument providing access to request metadata.
    *   **Example Tools:**
        *   `add_wall(ctx, start_point, end_point, height, level_name)`: Conceptually creates a wall in Revit.
        *   `add_room(ctx, room_name, boundary_points, level_name)`: Conceptually creates a room.
3.  **Revit Context Handling:**
    *   The `mcp_server.py` module defines global variables (`REVIT_APP`, `REVIT_UIDOC`, `REVIT_DOC`) that are initially `None`.
    *   A function `set_revit_context(app, uidoc, doc)` is provided. This function is called by the PyRevit plugin (`script.py`) before starting the server, to inject the active Revit application, UI document, and document objects into the server module.
    *   The MCP tool functions then access these global objects to interact with the Revit API.
    *   **Important:** All Revit API calls that modify the document (e.g., creating elements) **must** be wrapped in a `Transaction`. The example tool stubs include comments indicating where `Transaction.Start()` and `Transaction.Commit()` (or `RollBack()`) would occur.
4.  **Running the Server:**
    *   An `async def run_server(host, port)` function is defined to start the FastMCP application (which typically uses `uvicorn` underneath).
    *   The PyRevit plugin calls this `run_server` function in a separate thread.
5.  **Asynchronous Operations:**
    *   FastMCP and the underlying Starlette/Uvicorn are asynchronous. Tool functions are defined as `async def`. While most Revit API calls are synchronous, defining tools as `async` is good practice with FastMCP and allows for `await`ing other async operations if needed (e.g., complex calculations or calls to other async services before interacting with Revit). Synchronous Revit API calls will block within the `async` tool function, which is generally handled by `asyncio` running the synchronous code in a thread pool executor if not careful, or simply runs if the call is quick. For long-running Revit tasks, special care might be needed to avoid blocking the server's event loop for too long.

## Interaction with OrchestratorAgent

1.  The `OrchestratorAgent` uses ADK's `MCPToolset`.
2.  It initializes the `MCPToolset` with the URL where the FastMCP server is listening (e.g., `http://localhost:8765`).
3.  The `MCPToolset` connects to the server and fetches its tool specification.
4.  The `OrchestratorAgent` can then invoke tools by their names (e.g., `mcp_toolset.invoke_tool(Call(tool_name="add_wall", args={...}))`).
5.  The FastMCP server receives the call, routes it to the appropriate `@tool` decorated function, executes the Revit API logic, and returns a response (e.g., a success message with the ID of the created element, or an error message).

This server acts as the hands and eyes of the AI agents within the Revit environment, translating their instructions into actual model changes. The quality and granularity of the tools defined here significantly impact the capabilities of the overall system.
