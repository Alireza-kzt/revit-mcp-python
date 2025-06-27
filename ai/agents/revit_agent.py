from __future__ import annotations

import os
from typing import AsyncGenerator

from google.adk.agents import BaseAgent, LlmAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.adk.tools.mcp_tool.mcp_toolset import (
    MCPToolset,
    StdioServerParameters,
)

# ---------------------------------------------------------------------------
# Helper: build the MCP toolset that proxies to revit‑mcp‑python
# ---------------------------------------------------------------------------

REVIT_MCP_PY_DIR: str = os.getenv("REVIT_MCP_PY_DIR", "./revit-mcp-python")

revit_mcp_toolset = MCPToolset(
    connection_params=StdioServerParameters(
        command="uv",
        args=["--directory", REVIT_MCP_PY_DIR, "run", "main.py"],
    ),
    # Expose **all** tools – adjust tool_filter=[...] if you need a subset.
)

# ---------------------------------------------------------------------------
# Sub‑agent 1: connectivity / context bootstrap
# ---------------------------------------------------------------------------


class StatusCheckAgent(LlmAgent):
    """Helper agent that verifies the MCP connection."""

    def __init__(self) -> None:
        super().__init__(
            name="RevitStatusChecker",
            model=os.getenv("MODEL_NAME", "gemini-1.5-pro"),
            instruction=(
                "You are a helper whose sole job is to verify the current connection to "
                "Autodesk Revit via the MCP server.\n"
                "Call the function `get_revit_status` without arguments.\n"
                "If the status response is not OK, apologise and terminate."
            ),
            tools=[revit_mcp_toolset],
        )


# ---------------------------------------------------------------------------
# Sub‑agent 2: main conversational agent with full toolset
# ---------------------------------------------------------------------------

MAIN_SYSTEM_MESSAGE = """
You are **RevitAgent**, an expert architectural assistant. You can analyse and
modify Autodesk Revit projects through the tools provided by the MCP server.

Guidelines:
1. Always start by making sure Revit is connected (the status checker will run
   before you, but feel free to double‑check if something looks wrong).
2. Retrieve model context (`get_revit_model_info`, `list_levels`, etc.) before
   making invasive changes – this keeps you grounded in the current project.
3. When exporting view images, use `get_revit_view` and return the image URL to
   the user wrapped in Markdown so it renders inline.
4. For *write* operations (creating walls, placing families, etc.) respond with
   clear, short descriptions of what you did and reference element IDs if the
   tool returns them.
5. Think step‑by‑step. When faced with a multi‑stage task, break it into atomic
   tool calls. Never hallucinate parameters – inspect existing elements first.
"""


class ConversationAgent(LlmAgent):
    """Main conversational agent with full toolset."""

    def __init__(self) -> None:
        super().__init__(
            name="RevitConversationAgent",
            model=os.getenv("MODEL_NAME", "gemini-1.5-pro"),
            instruction=MAIN_SYSTEM_MESSAGE,
            tools=[revit_mcp_toolset],
        )


# ---------------------------------------------------------------------------
# Orchestrator: run status checker then conversation agent
# ---------------------------------------------------------------------------


class RevitAgent(BaseAgent):
    """Custom orchestrator that guarantees connectivity before conversation."""

    status_checker: LlmAgent
    agent: LlmAgent

    def __init__(self) -> None:
        super().__init__(name="RevitAgent")
        self.status_checker = StatusCheckAgent()
        self.agent = ConversationAgent()

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        # 1) Ensure Revit is reachable
        async for event in self.status_checker.run_async(ctx):
            yield event
        # 2) Delegate the actual user query to the conversation agent
        async for event in self.agent.run_async(ctx):
            yield event
