"""Tools for design actions via MCP"""
from fastmcp import Context

def register_design_tools(mcp, revit_post):
    """Register design tools with the MCP server"""

    @mcp.tool()
    async def add_wall(start_point: dict, end_point: dict, height: float = 3.0, ctx: Context = None) -> str:
        """Create a wall between two points"""
        payload = {"start_point": start_point, "end_point": end_point, "height": height}
        return await revit_post("/add_wall/", payload, ctx)

    @mcp.tool()
    async def add_room(room_name: str, boundary_pts: list, ctx: Context = None) -> str:
        """Create a room with a boundary"""
        payload = {"room_name": room_name, "boundary_pts": boundary_pts}
        return await revit_post("/add_room/", payload, ctx)
