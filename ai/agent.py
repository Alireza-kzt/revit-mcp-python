"""Entry point for ADK loading."""

from ai.agents.orchestrator_agent import OrchestratorAgent

# ---------------------------------------------------------------------------
# Windows compatibility
# ---------------------------------------------------------------------------
# The ADK spawns subprocesses when launching the MCP server. On Windows,
# the default ``ProactorEventLoop`` does not implement subprocess support,
# which results in ``NotImplementedError`` when the agents run. Switching to
# ``WindowsSelectorEventLoopPolicy`` ensures subprocesses work correctly.

import asyncio
import sys

if sys.platform.startswith("win"):  # pragma: win32
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

root_agent = OrchestratorAgent()
