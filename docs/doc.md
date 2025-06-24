**Project Goal:** Implement an AI-assisted architectural design system in Revit, using Google’s **Agent Development Kit (ADK-Python v1.0)** and the **Model Context Protocol (MCP)**. The system will consist of multiple specialized agents (InputAgent, RegulationsAgent, DesignAgent, RevitAgent, OrchestratorAgent) and a backend server that exposes Revit functionalities via MCP (using **FastMCP 2.x**). Also, set up a PyRevit extension to integrate with Revit, documentation (MkDocs), tests, and CI.

## Agents Overview:
We have five agents with distinct roles:
- **InputAgent:** Gathers and preprocesses user requirements for the design. For example, it might take user prompts (desired room count, size, style, etc.) and output a structured brief.
- **DesignAgent:** Proposes an architectural design solution (at a conceptual level) based on the requirements. Likely an LLM-driven agent that turns the brief into a design plan (could be text or a structured representation like JSON of building elements).
- **RegulationsAgent:** Checks the proposed design against building regulations/codes (simplify this as needed). It should analyze the DesignAgent’s output for compliance issues (e.g., room size minimums, evacuation routes) and either approve it or output required modifications.
- **RevitAgent:** Acts as an interface to the Revit API. It doesn’t use an LLM; instead it receives structured instructions (e.g., a list of walls, windows with dimensions) and carries them out in Autodesk Revit via the MCP server (detailed below). Essentially, RevitAgent’s “tools” are the actual Revit operations exposed by the MCP server.
- **OrchestratorAgent:** The coordinator that oversees the whole process. It receives the initial user request, invokes the InputAgent, then passes its output to DesignAgent, then passes the design to RegulationsAgent. If regulations feedback is OK (or after adjustments), OrchestratorAgent then instructs RevitAgent to implement the design in Revit. OrchestratorAgent is essentially the high-level workflow manager (could be implemented as an ADK `SequentialAgent` pipeline).

**Important:** Use ADK’s multi-agent capabilities to structure the above. For instance, OrchestratorAgent can be a `SequentialAgent` with sub_agents = [InputAgent, DesignAgent, RegulationsAgent], so it runs them in order:contentReference[oaicite:34]{index=34}. After that sequence, we might handle the Revit step (since RevitAgent is not an LLM, we might call it via a tool invocation). We will integrate the RevitAgent through MCP as described below.

## Using ADK and MCP Integration:
- We will use **google-adk (Python)** for agent definitions and **FastMCP 2.x** for the MCP server.
- **ADK Agents Implementation:** Use ADK’s `LlmAgent` class for InputAgent, DesignAgent, RegulationsAgent (since these involve reasoning with LLM). Give each a `name` and appropriate prompt/instructions. For example, DesignAgent might have a prompt template like, “Design a building layout based on the following requirements: ... (requirements from InputAgent’s output)”. RegulationsAgent might have a prompt like, “Check the following design for code compliance: ...”.
  - If needed, implement custom logic as a subclass of `BaseAgent` (for example, a custom agent to parse the DesignAgent output, etc.), but try to leverage LLMAgent and WorkflowAgent where possible.
- **Workflow:** Implement OrchestratorAgent as a `SequentialAgent` (or a custom Orchestrator class) that runs the three LLM agents in order:contentReference[oaicite:35]{index=35}. Ensure that data passes via the `session.state` or outputs/inputs keys between steps (e.g., InputAgent’s result is passed to DesignAgent, etc.).
- **MCP Toolset for Revit:** After obtaining a final approved design (e.g., as structured data or final text) from RegulationsAgent, the OrchestratorAgent should invoke RevitAgent’s capabilities to execute the design in Revit. We will achieve this via MCP:
  - **FastMCP Server:** Create a FastMCP server in Python that runs inside Revit (via PyRevit) and exposes various **Tools** corresponding to Revit API actions. Use the `@mcp.tool` decorator to define tools:contentReference[oaicite:36]{index=36}. Each tool function should take simple data (dimensions, parameters) and use the Revit API (via Python.NET or Revit API wrapper) to perform an action, then return a result or confirmation.
  - **Example Tools:** For instance, `add_wall(start_point, end_point, height)` to add a wall, `add_room(room_name, boundary_pts)` to define a room, etc. Include at least a couple of basic tools to demonstrate functionality. Each tool must be asynchronous (`async def`) if any await is needed (since FastMCP is async-friendly):contentReference[oaicite:37]{index=37}. Use clear naming and docstrings for each tool (these become part of MCP spec).
  - **Running Server:** Use `FastMCP(...)` to initialize the server and `mcp.run()` to start it. The server will listen on a localhost port.
  - **ADK MCP Client:** In OrchestratorAgent’s implementation, use ADK’s `MCPToolset` to connect to the FastMCP server:contentReference[oaicite:38]{index=38}. For example, configure an MCPToolset pointing to the server’s address (perhaps read from an environment variable like `FASTMCP_SERVER_URL`). Then you can call MCP tools as if they are ADK tools in the Orchestrator’s context. *Important:* With ADK v1.0+, tools can be referenced by name directly (no index hacking needed):contentReference[oaicite:39]{index=39}. Ensure the tool names in the MCP server match what you call from the agent.
  - **Data flow:** OrchestratorAgent will take the design plan (maybe as JSON or a Python dict) and call the appropriate MCP tools. You might implement a simple method to translate the design output into a sequence of MCP tool calls (e.g., iterate through walls in the plan and call `add_wall` for each).
- **Session and Cleanup:** Ensure the MCP connection is closed when done (ADK’s MCPToolset should handle this via context manager).

## PyRevit Plugin:
- Develop a PyRevit extension to host the FastMCP server inside Revit. The extension should add a Ribbon Tab (e.g., “AI Design”) with a button “Start AI Design Server”.
- **Extension Structure:** Create a folder `AIDesign.extension` with `AIDesign.tab` > `AI Server.panel` > `Start Server.pushbutton` containing a `script.py`. This script.py will initialize the FastMCP server.
- In `script.py`:
  - Use the Revit API (accessible via the `__revit__` global or `UIApplication` in PyRevit) to get the current `UIDocument` and `Document`.
  - Possibly prompt the user for confirmation, then start the FastMCP server (from the FastMCP code/module defined in our project). This might involve ensuring the Python environment can import fastmcp – if Revit 2024+, PyRevit might use CPython, otherwise consider .NET interop.
  - The server should run ideally in a background thread so that Revit UI remains responsive. Alternatively, since FastMCP is async, consider using `asyncio` event loop integration. (If simplifying, you can run it and inform the user via a TaskDialog that the server is running.)
  - Provide a way to stop the server (maybe the same button toggles stop, or a separate “Stop Server” button).
  - Make sure to handle Revit API calls within a `Transaction` when modifying the document. For example, inside any MCP tool function that creates Revit elements, start a `Transaction(doc, "AddElement")` and commit it:contentReference[oaicite:40]{index=40}.
- **RevitAgent vs MCP:** Note that we do not explicitly need a separate “RevitAgent” class in ADK; the combination of FastMCP server + PyRevit plugin essentially **is** the RevitAgent (it’s an agent in the sense of our architecture, but implemented as an MCP server).
- **Example:** If the DesignAgent output says “Create a 5m x 5m room,” the Orchestrator might call a tool `add_room(name="Room1", x=5, y=5)` which our server implements by making Revit add walls of 5m, etc. (We can hardcode some logic for simplicity.)

## Documentation:
- Set up MkDocs for project documentation:
  - Create `mkdocs.yml` with site name, theme (e.g. material) and nav structure.
  - Create docs pages: e.g. `index.md` (overview of the project), `agents.md` (describing each agent’s role and how they work together), `revit_plugin.md` (how the Revit MCP server works), and `usage.md` (instructions to run the system).
  - In the docs, explain how to install the plugin (copying the .extension folder), how to run the Orchestrator (maybe a CLI script that launches the ADK OrchestratorAgent), and how the system will respond.
  - Include any references to standards (MCP, ADK) as needed.
- Ensure the documentation is comprehensive yet concise (each page 3-5 paragraphs with lists if needed).

## Testing:
- Write unit tests for critical components:
  - Example: a test for InputAgent to ensure it correctly parses a sample prompt into a structured output.
  - Test for DesignAgent to ensure it returns something (since actual design might be text, maybe just test the format).
  - Possibly a test simulating the integration: run OrchestratorAgent with a dummy MCPToolset (you could mock the MCP calls) to see that it attempts the right sequence.
  - If feasible, test the FastMCP tools functions (e.g., if `add_wall` returns a success message).
- Use `pytest` and include a GitHub Actions workflow (CI) to run tests on push.

## CI/CD:
- Configure GitHub Actions (`.github/workflows/ci.yml`) to:
  - Install dependencies (ADK, fastmcp, etc.)
  - Run pytest for the tests.
  - (Optional) Build docs (e.g., `mkdocs build` to ensure no warnings).
- Ensure the CI is triggered on pull requests and pushes to main.

**Development notes & constraints:**
- Keep code modular (each Agent in its own module/file, the MCP server in its own module, etc.) for clarity:contentReference[oaicite:41]{index=41}.
- Adhere to ADK and MCP coding best practices (meaningful class and function names, docstrings).
- Use Python typing hints for clarity.
- Make sure to handle exceptions, especially around external calls (e.g., if Revit API call fails, perhaps catch and log).
- The unified diff output should include all new files and modifications, ready to git apply.

**Finally, provide the result as a unified diff patch** of the repository, so that the changes can be directly applied as a commit. Include all created files (agents modules, server code, PyRevit scripts, docs, tests, CI config, etc.) in the diff. Do not include any explanatory text outside the diff.