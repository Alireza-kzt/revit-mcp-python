# Usage Guide

This guide explains how to set up and run the AI-Assisted Architectural Design System.

## Prerequisites

1.  **Python:** Ensure you have Python 3.9+ installed.
2.  **Autodesk Revit:** Revit 2021+ (ideally 2024+ for better Python 3 support with PyRevit).
3.  **PyRevit:** Install PyRevit for your Revit version.
4.  **Project Files:** Clone or download this project repository.
5.  **Environment Variable:**
    *   Set an environment variable `AI_DESIGN_ASSISTANT_PATH` to point to the **root directory** of this project. This is crucial for the PyRevit plugin to find the server source code.
    *   Example (Windows - PowerShell): `$env:AI_DESIGN_ASSISTANT_PATH = "C:\path\to\your\AI-Design-Assistant-Project"`
    *   Example (Linux/macOS - bash): `export AI_DESIGN_ASSISTANT_PATH="/path/to/your/AI-Design-Assistant-Project"`
    *   You might want to add this to your system's environment variables permanently.
6.  **LLM API Key (for ADK Agents):**
    *   The ADK-based `LlmAgent`s (Input, Design, Regulations) require access to a Large Language Model. By default, ADK might try to use Google's Gemini.
    *   Ensure you have the necessary API key set up as an environment variable (e.g., `GOOGLE_API_KEY`).
    *   Create a `.env` file in the project root directory and add your API key:
        ```
        GOOGLE_API_KEY="your_api_key_here"
        FASTMCP_SERVER_URL="http://localhost:8765" # Optional: if you want to centrally define
        ```
    *   The `python-dotenv` package (listed in `requirements.txt`) will load this.

## Setup Steps

1.  **Install Python Dependencies (for Agents):**
    *   Navigate to the project root directory in your terminal.
    *   Create a virtual environment (recommended):
        ```bash
        python -m venv venv
        source venv/bin/activate  # On Windows: venv\Scripts\activate
        ```
    *   Install required packages:
        ```bash
        pip install -r requirements.txt
        ```

2.  **Configure PyRevit Python Environment (for MCP Server):**
    *   The PyRevit plugin runs the MCP Server. The Python environment used by PyRevit needs `fastmcp` and its dependencies (like `uvicorn`).
    *   **If PyRevit uses a CPython engine (common in newer Revit versions):** Ensure that the CPython environment PyRevit is configured to use has these packages. You might need to `pip install fastmcp uvicorn` into that specific environment. Consult PyRevit documentation on managing Python environments.
    *   **If PyRevit uses IronPython (older Revit versions):** This project is designed with CPython in mind due to `fastmcp` and `asyncio` usage. Compatibility with IronPython is unlikely without significant changes.

3.  **Install the PyRevit Extension:**
    *   Locate the `AIDesign.extension` folder in the project directory.
    *   Copy this entire folder to one of your PyRevit extension directories. You can find these paths in PyRevit's settings (Extensions -> Manage Extension Locations).
    *   Restart Revit or click "Reload" in PyRevit settings.

## Running the System

The system involves two main parts that need to be active: the Revit MCP Server and the Orchestrator Agent.

**Part 1: Start the Revit MCP Server**

1.  Open Autodesk Revit.
2.  Open any Revit project (or start a new one). This will be the model the AI interacts with.
3.  You should see an "AI Design" tab in the Revit ribbon. If not, check PyRevit installation and extension paths.
4.  Under the "AI Design" tab, find the "AI Server" panel, and click the "Start Server" button.
5.  A TaskDialog should appear confirming that the "AI Design MCP Server started" (usually on `http://127.0.0.1:8765`). If there's an error, it will be displayed. Common errors include `AI_DESIGN_ASSISTANT_PATH` not being set or Python dependencies missing in PyRevit's environment. Check the logs mentioned in `script.py` if issues persist.
    *   The default server URL is `http://localhost:8765`. This can be configured in `src/revit_server/mcp_server.py` and referenced by `OrchestratorAgent` (e.g., via `FASTMCP_SERVER_URL` env var loaded from `.env`).

**Part 2: Run the Orchestrator Agent**

1.  Open a new terminal or command prompt.
2.  Navigate to the root directory of the AI Design Assistant project.
3.  Activate your Python virtual environment (if you created one):
    ```bash
    source venv/bin/activate  # Or venv\Scripts\activate
    ```
4.  Ensure your LLM API key and `FASTMCP_SERVER_URL` (if used) are set (e.g., in the `.env` file).
5.  Run the Orchestrator Agent. A simple way to test is by running its main script (if it has a `if __name__ == "__main__":` block for testing, like the one provided):
    ```bash
    python -m src.agents.orchestrator_agent
    ```
    (Using `python -m` helps with relative imports from the project root).
6.  The Orchestrator will then:
    *   Prompt you for a design request (if its `main()` function is set up that way), or use a hardcoded test prompt.
    *   Invoke the `InputAgent`, then `DesignAgent`, then `RegulationsAgent`.
    *   If the design is approved, it will attempt to connect to the MCP server running in Revit.
    *   You will see log messages in the terminal from the Orchestrator and the sub-agents.
    *   If successful, you should see elements appearing or being modified in your Revit model.

## Example Interaction

1.  **Revit:** Start MCP Server.
2.  **Terminal (Orchestrator):**
    ```
    (venv) $ python -m src.agents.orchestrator_agent
    Orchestrator: Starting design process for prompt: 'I need a small, modern one-story cabin...'
    ... (logs from InputAgent, DesignAgent, RegulationsAgent) ...
    Orchestrator: Design approved by RegulationsAgent.
    Orchestrator: Attempting to trigger Revit implementation (MCP server URL from env: http://localhost:8765)...
    Orchestrator: Connected to MCP Server at http://localhost:8765. Tools: ['add_wall', 'add_room']
    ... (logs of MCP tool calls) ...
    Orchestrator: Revit implementation result: Conceptual Revit Actions: Called add_wall...; Called add_room...
    Orchestrator: Design process finished.

    --- Orchestrator Final Output ---
    status: completed
    ...
    ```
3.  **Revit:** Observe changes in the model.

## Stopping the System

1.  **Orchestrator Agent:** The script will typically finish execution. You can stop it earlier with `Ctrl+C` in the terminal.
2.  **Revit MCP Server:**
    *   Click the "Start Server" button again in the Revit ribbon. Since the server was running, this click should trigger the "stop" logic.
    *   A dialog should confirm the stop request. (Note: As mentioned in the PyRevit plugin docs, graceful shutdown is conceptual. The server thread might run until Revit exits).
    *   Alternatively, closing Revit will also terminate the server thread.

This covers the basic usage. For development or troubleshooting, refer to the logs generated by the agents and the PyRevit plugin script.
