from google.adk.agents import BaseAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams
from typing import AsyncGenerator

class RevitAgent(BaseAgent):
    """Executes design instructions in Revit via MCP."""

    toolset: MCPToolset | None = None

    def __init__(self, mcp_url: str) -> None:
        super().__init__(name="RevitAgent")
        object.__setattr__(self, "toolset", MCPToolset(
            connection_params=StreamableHTTPConnectionParams(url=mcp_url)
        ))

    async def _run_async_impl(self, ctx) -> AsyncGenerator:
        design = ctx.state.get("design")
        if not design:
            return
        walls = design.get("walls", [])
        for wall in walls:
            await self.toolset.call_tool(
                "add_wall",
                {
                    "start_point": wall.get("start"),
                    "end_point": wall.get("end"),
                    "height": wall.get("height", 3.0),
                },
                ctx,
            )
        rooms = design.get("rooms", [])
        for room in rooms:
            await self.toolset.call_tool(
                "add_room",
                {
                    "room_name": room.get("name"),
                    "boundary_pts": room.get("boundary"),
                },
                ctx,
            )
        yield
