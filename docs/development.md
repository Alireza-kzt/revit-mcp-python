# Development Notes

This page contains notes relevant for developers working on or extending the AI-Assisted Architectural Design System.

## Project Structure

```
.
├── AIDesign.extension/        # PyRevit Extension
│   └── AIDesign.tab/
│       └── AI Server.panel/
│           └── Start Server.pushbutton/
│               └── script.py
├── docs/                      # MkDocs documentation files
│   ├── agents/
│   ├── revit_integration/
│   └── ... (index.md, etc.)
├── src/                       # Source code
│   ├── agents/                # ADK Agent implementations
│   │   ├── __init__.py
│   │   ├── input_agent.py
│   │   ├── design_agent.py
│   │   ├── regulations_agent.py
│   │   └── orchestrator_agent.py
│   ├── revit_server/          # FastMCP server code
│   │   ├── __init__.py
│   │   └── mcp_server.py
│   └── __init__.py
├── tests/                     # Pytest unit tests
│   └── ... (test_agents.py, etc.)
├── .env.example               # Example environment file
├── .gitignore
├── LICENSE                    # (To be added)
├── mkdocs.yml                 # MkDocs configuration
├── README.md                  # Project README
└── requirements.txt           # Python dependencies
```

## Key Technologies & Libraries

*   **Google ADK (Agent Development Kit):** `google-adk` for agent framework.
    *   `LlmAgent` for LLM-based agents.
    *   `Session` for managing conversation history and state.
    *   `MCPToolset` for client-side MCP interactions.
*   **FastMCP:** `fastmcp` for creating the MCP server.
    *   `@tool` decorator for defining MCP tools.
    *   Relies on `uvicorn` and `starlette`.
*   **PyRevit:** For embedding the MCP server in Revit and UI.
*   **Python.NET:** `pythonnet` (often bundled or managed by PyRevit) for Revit API interop from CPython (if PyRevit is using a CPython engine).
*   **Pydantic:** Used for defining shared data models (`src/shared_models.py`) like `DesignPlanModel`, ensuring structured data flow between agents.
*   **Autodesk Revit API:** Interacted with from within the MCP tool implementations.
*   **MkDocs:** `mkdocs` with `mkdocs-material` theme for documentation.
*   **Pytest:** `pytest` for running tests.
*   **Dotenv:** `python-dotenv` for managing environment variables like API keys from a `.env` file.

## Development Environment Setup

Refer to the [Usage Guide](./usage.md#prerequisites) for initial setup. For development, ensure your virtual environment has development tools:
```bash
pip install -r requirements.txt
# pytest, pytest-asyncio, and pydantic are included in requirements.txt or as sub-dependencies
```

### Shared Data Models (Pydantic)
The system now uses Pydantic models (defined in `src/shared_models.py`) for robust data exchange:
*   `DesignPlanModel`: The primary model output by `DesignAgent`, containing lists of `WallModel`, `RoomModel`, etc.
*   `DesignAgent` is prompted to produce JSON conforming to `DesignPlanModel.schema_json()`.
*   `OrchestratorAgent` consumes the `DesignPlanModel` to make structured calls to MCP tools.
This approach is preferred over parsing free-form text for Revit commands.

### Revit API Stubs
For improved type hinting and intellisense when writing MCP tools that interact with the Revit API, you can use Revit API stubs.
*   `autodesk-revit-api-stubs` is listed in `requirements.txt`. Your IDE (like VS Code) should pick these up if configured correctly.
*   These are stubs only; they don't provide a working Revit environment. Code still needs to be tested inside Revit.

## Running Agents Individually for Testing

Each agent module (`input_agent.py`, `design_agent.py`, `regulations_agent.py`) has an `if __name__ == "__main__":` block. This allows you to run them standalone for quick testing of their core logic, provided you have an LLM API key configured.
```bash
# Example: Test InputAgent
python src/agents/input_agent.py

# Example: Test OrchestratorAgent (which calls other agents)
python -m src.agents.orchestrator_agent # Use -m from project root
```

## Testing

Unit tests are located in the `tests/` directory and use `pytest`.
*   `tests/test_agents.py` contains tests for individual agents and the orchestrator workflow.
*   **Mocking:**
    *   LLM interactions are mocked using `unittest.mock.AsyncMock` on the `LlmServiceAdapter.invoke_llm` method.
    *   `DesignAgent` tests check for successful parsing into `DesignPlanModel` or correct error handling for invalid JSON.
    *   `OrchestratorAgent` tests mock the `MCPToolset` (using `@patch('src.agents.orchestrator_agent.MCPToolset')`) to simulate interactions with the Revit MCP server without needing a live Revit instance. Assertions are made on whether `connect`, `invoke_tool` (with correct arguments derived from `DesignPlanModel`), and `close` are called.
*   Run tests from the project root: `pytest`

### Testing the MCP Server

1.  **Standalone (Limited):**
    You can run `python src/revit_server/mcp_server.py`. The server will start, and you can access its OpenAPI docs (e.g., `http://localhost:8765/docs`). Tool calls will use mocked Revit API objects if Revit is not present, allowing basic server functionality checks.
2.  **Inside Revit (Full Test):**
    Use the PyRevit plugin to start the server. Then, you can use a separate MCP client (like a Python script using `httpx` or `requests`, or even ADK's `MCPToolset` in a test script from your development environment) to send requests to the tools and verify their behavior with the live Revit model.

## Debugging the PyRevit Plugin

*   PyRevit has its own logging and debugging tools. Check the PyRevit documentation.
*   Add `print()` statements or use Python's `logging` module within `script.py`. Output might go to PyRevit's log console or a file if configured.
*   The `AI_DESIGN_ASSISTANT_PATH` environment variable is critical. If the plugin can't find `src.revit_server.mcp_server`, this is the first thing to check.
*   Ensure the Python environment PyRevit is using has all necessary dependencies for `fastmcp`.

## Writing Revit API Code in MCP Tools

*   **Transactions:** ALL changes to the Revit model MUST happen inside a `Transaction`.
    ```python
    # Inside an MCP tool in mcp_server.py
    # from Autodesk.Revit.DB import Transaction
    # t = Transaction(REVIT_DOC, "My MCP Tool Action")
    # try:
    #     t.Start()
    #     # ... Your Revit API calls to modify the model ...
    #     t.Commit()
    #     return {"status": "success", "message": "Action completed."}
    # except Exception as e:
    #     if t.HasStarted() and not t.HasEnded():
    #         t.RollBack()
    #     return {"status": "error", "message": str(e)}
    # ```
*   **Units:** Be mindful of Revit's internal units (usually imperial feet for lengths). MCP tools should clearly document the expected units for their arguments.
*   **Element Selection/Finding:** Use `FilteredElementCollector` for finding elements. Ensure correct filtering to get desired elements.
*   **Error Handling:** Wrap Revit API calls in `try-except` blocks to catch potential errors and return informative MCP responses. Log errors clearly.
*   **Units:** Be mindful of Revit's internal units (usually imperial feet for lengths). MCP tools should clearly document the expected units for their arguments, and conversions should happen consistently if agent outputs are in other units (e.g. meters). The current Pydantic models and MCP tools assume feet for simplicity.

## Future Enhancements / Considerations

*   **RegulationsAgent with Structured Data:** Enhance `RegulationsAgent` to directly consume the `DesignPlanModel` instead of just a textual summary for more precise checks.
*   **Iterative Design Loop:** Implement a loop where feedback from `RegulationsAgent` (potentially structured feedback) is passed back to `DesignAgent` for refinement of the `DesignPlanModel`.
*   **Advanced MCP Tools:** Add more tools to the MCP server for finer-grained control over Revit modeling (e.g., creating specific families, modifying parameters, creating floors, roofs, windows, doors, dimensions, views/sheets).
*   **User Interface for Orchestrator:** Instead of a command-line script, a simple web UI (e.g., using Streamlit or Flask) could be built to interact with the `OrchestratorAgent`.
*   **Configuration Management:** Centralize configuration (LLM settings, server URLs) instead of relying solely on environment variables or hardcoded values.
*   **Graceful Server Shutdown in PyRevit:** Investigate more robust methods for stopping the `asyncio` server thread from the PyRevit script.

This project provides a foundational framework. There are many avenues for expansion and refinement.
