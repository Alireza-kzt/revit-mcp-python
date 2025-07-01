"""Curve element creation tools"""

from fastmcp import Context


def register_curve_tools(mcp, revit_get, revit_post):
    """Register curve-related tools"""

    @mcp.tool()
    async def create_line_based_element(
        family_name: str,
        type_name: str = None,
        start_x: float = 0.0,
        start_y: float = 0.0,
        start_z: float = 0.0,
        end_x: float = 1.0,
        end_y: float = 0.0,
        end_z: float = 0.0,
        level_name: str = None,
        structural: bool = False,
        ctx: Context = None,
    ) -> str:
        """Create line-based elements like walls or beams"""
        data = {
            "family_name": family_name,
            "type_name": type_name,
            "start": {"x": start_x, "y": start_y, "z": start_z},
            "end": {"x": end_x, "y": end_y, "z": end_z},
            "level_name": level_name,
            "structural": structural,
        }
        return await revit_post("/create_line_based_element/", data, ctx)
