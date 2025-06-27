# Usage

1. Install the pyRevit extension and start the AI Design Server from the ribbon.
2. Run the orchestrator with `adk web`.
3. The agents will process the request and create elements in Revit.

## Windows setup

On Windows, the default event loop does not support subprocesses. If you see a
`NotImplementedError` related to `subprocess_exec`, upgrade to Python 3.11+ and
ensure the project sets `asyncio.WindowsSelectorEventLoopPolicy`. This repository
configures the policy automatically in `ai/agent.py`.
