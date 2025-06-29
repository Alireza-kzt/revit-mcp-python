"""Wall creation tools"""

from fastmcp import Context
from typing import Dict, Any


def register_wall_tools(mcp, revit_get, revit_post):
    """Register wall-related tools"""

    @mcp.tool()
    async def create_wall(
        start: Dict[str, float],
        end: Dict[str, float],
        height: float = 10.0,
        level_name: str = None,
        wall_type: str = None,
        ctx: Context = None,
    ) -> str:
        """Create a straight wall between two points."""
        data = {
            "start": start,
            "end": end,
            "height": height,
            "level_name": level_name,
            "wall_type": wall_type,
        }
        return await revit_post("/create_wall/", data, ctx)

