from __future__ import annotations
import os
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import (
    MCPToolset,
    StdioServerParameters,
    StdioConnectionParams,
)

from ai.config import llm_model
from config import REVIT_MCP_PY_DIR

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
6. After performing the requested changes, verify the model and end your reply
   with `status: success` once everything is complete.   
"""


class RevitAgent(LlmAgent):
    """Main conversational agent with full toolset."""

    def __init__(self) -> None:
        super().__init__(
            name="RevitAgent",
            model=llm_model,
            instruction=MAIN_SYSTEM_MESSAGE,
            tools=[
                MCPToolset(
                    connection_params=StdioConnectionParams(
                        server_params=StdioServerParameters(
                            command="fastmcp",
                            args=[
                                "run",
                                os.path.join(REVIT_MCP_PY_DIR, "main.py"),
                            ],
                        ),
                    ),
                ),
            ],
            output_key="revit_summary",
        )