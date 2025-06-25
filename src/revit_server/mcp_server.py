import asyncio
import logging
from fastmcp import FastMCP, ToolContext, tool
from typing import List, Dict, Any # For type hints

# Configure basic logging for the server
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("RevitMCP")

# --- Globals for Revit context (populated by PyRevit script) ---
_REVIT_APP = None
_REVIT_UIDOC = None
_REVIT_DOC = None # Current Document

# Attempt to import Revit API - this will only work inside Revit Python
try:
    import clr
    clr.AddReference("RevitAPI")
    clr.AddReference("RevitAPIUI") # For UIDocument if needed for selections, views
    from Autodesk.Revit.DB import (
        Document, Wall, Line, XYZ, Level, FilteredElementCollector, BuiltInParameter,
        Transaction, ElementId, WallType
    )
    # For rooms
    from Autodesk.Revit.DB.Architecture import Room, RoomTag, NewRoomData
    from Autodesk.Revit.DB import UV, Phase # For room placement

    REVIT_API_AVAILABLE = True
    logger.info("Revit API modules loaded successfully.")
except ImportError:
    REVIT_API_AVAILABLE = False
    logger.warning("Revit API modules not found. Server will run with stubbed Revit interactions.")
    # Define mock classes for standalone execution if needed for type hinting or basic logic
    class XYZ: def __init__(self, x,y,z): self.X, self.Y, self.Z = x,y,z
    class Line: @staticmethod def CreateBound(p1,p2): return None
    class Wall: @staticmethod def Create(doc, line, level_id, structural): return ElementId(12345) if REVIT_API_AVAILABLE else None # Mock ElementId too
    class Level: pass
    class FilteredElementCollector:
        def __init__(self, doc): pass
        def OfClass(self, t): return self
        def WhereElementIsNotElementType(self): return self
        def ToElements(self): return []
        def FirstElement(self): return None # For WallType
    class Transaction:
        def __init__(self, doc, name): self.doc, self.name, self._started = doc, name, False
        def Start(self): self._started = True; logger.info(f"Mock Transaction '{self.name}' Started.")
        def Commit(self): logger.info(f"Mock Transaction '{self.name}' Committed.")
        def RollBack(self): logger.info(f"Mock Transaction '{self.name}' Rolled Back.")
        def HasStarted(self): return self._started
        def HasEnded(self): return False # Simplified
    class ElementId:
        def __init__(self, val): self.IntegerValue = val
        def ToString(self): return str(self.IntegerValue)
    class Room: @staticmethod def Create(doc, phase, level_id, uv_point): return ElementId(56789) if REVIT_API_AVAILABLE else None
    class UV: def __init__(self, u, v): self.U, self.V = u,v
    class Phase: pass
    class WallType: pass # Mock WallType

def set_revit_context(app: Any, uidoc: Any, doc: Any):
    """Called by the PyRevit plugin to pass Revit context to the server."""
    global _REVIT_APP, _REVIT_UIDOC, _REVIT_DOC
    _REVIT_APP = app
    _REVIT_UIDOC = uidoc
    _REVIT_DOC = doc
    if REVIT_API_AVAILABLE and doc:
        logger.info(f"Revit context set for MCP server. Document: {doc.Title}")
    elif doc: # doc might be a mock object if API not available
         logger.info(f"Revit context (potentially mocked) set. Document: {getattr(doc, 'Title', 'Unknown')}")
    else:
        logger.warning("Revit context set, but document is None.")

# --- Helper function to find Level ---
def _find_level_by_name(doc: Any, level_name: str) -> Any: # Returns Level or None
    if not REVIT_API_AVAILABLE or not doc: return None
    try:
        collector = FilteredElementCollector(doc).OfClass(Level)
        for level in collector:
            if level.Name == level_name:
                return level
        logger.warning(f"Level '{level_name}' not found in document '{doc.Title}'.")
    except Exception as e:
        logger.error(f"Error finding level '{level_name}': {e}", exc_info=True)
    return None

# --- MCP Tool Definitions ---
@tool
async def add_wall(
    ctx: ToolContext,
    start_point: List[float],
    end_point: List[float],
    height: float,
    level_name: str = "Level 1"
) -> Dict[str, Any]:
    """
    Adds a basic wall to the Revit model. Assumes coordinates are in feet.
    """
    logger.info(f"MCP: add_wall called: start={start_point}, end={end_point}, height={height}, level={level_name}")

    if not REVIT_API_AVAILABLE or not _REVIT_DOC:
        msg = "Revit context not available. Cannot create wall."
        logger.error(msg)
        return {"status": "error", "message": msg, "element_id": None}

    doc = _REVIT_DOC
    t = Transaction(doc, "MCP: Create Wall")
    try:
        target_level = _find_level_by_name(doc, level_name)
        if not target_level:
            return {"status": "error", "message": f"Level '{level_name}' not found.", "element_id": None}

        p1 = XYZ(start_point[0], start_point[1], start_point[2])
        p2 = XYZ(end_point[0], end_point[1], end_point[2])
        baseline = Line.CreateBound(p1, p2)

        # Find a default wall type (e.g., Generic - 8")
        wall_type_collector = FilteredElementCollector(doc).OfClass(WallType)
        # This is a very basic way to get a wall type, might need refinement
        wall_type = wall_type_collector.FirstElement()
        if not wall_type:
            return {"status": "error", "message": "No WallTypes found in the document.", "element_id": None}
        logger.info(f"Using WallType: {wall_type.Name if hasattr(wall_type, 'Name') else 'Unknown'}")

        t.Start()
        # Create wall with specified height (unconnected) on the target level
        # Wall.Create(doc, baseline, wall_type.Id, target_level.Id, height, 0, False, False) -> This is for structural wall
        # For architectural wall, it's simpler:
        new_wall = Wall.Create(doc, baseline, target_level.Id, False) # False for non-structural

        # Set unconnected height parameter
        height_param = new_wall.get_Parameter(BuiltInParameter.WALL_USER_HEIGHT_PARAM)
        if height_param and not height_param.IsReadOnly:
            height_param.Set(height)
        else:
            logger.warning(f"Could not set height for wall {new_wall.Id.ToString()}. Parameter unavailable or read-only.")

        t.Commit()
        wall_id_str = new_wall.Id.ToString()
        logger.info(f"Wall created successfully with ID: {wall_id_str} on level '{level_name}'")
        return {"status": "success", "message": "Wall created.", "element_id": wall_id_str}

    except Exception as e:
        if t.HasStarted() and not t.HasEnded(): t.RollBack()
        logger.error(f"Error in 'add_wall' Revit interaction: {e}", exc_info=True)
        return {"status": "error", "message": f"Failed to create wall: {str(e)}", "element_id": None}

@tool
async def add_room(
    ctx: ToolContext,
    room_name: str,
    boundary_points: List[List[float]], # List of [x,y] points
    level_name: str = "Level 1"
) -> Dict[str, Any]:
    """
    Adds a room to the Revit model. Assumes boundary_points are [x,y] lists in feet on the specified level.
    This simplified version places a room at the centroid of the given points.
    Actual room creation requires walls or room separation lines to bound the room.
    """
    logger.info(f"MCP: add_room called: name={room_name}, level={level_name}, num_boundary_pts={len(boundary_points)}")

    if not REVIT_API_AVAILABLE or not _REVIT_DOC:
        msg = "Revit context not available. Cannot create room."
        logger.error(msg)
        return {"status": "error", "message": msg, "element_id": None}

    doc = _REVIT_DOC
    t = Transaction(doc, "MCP: Create Room")
    try:
        target_level = _find_level_by_name(doc, level_name)
        if not target_level:
            return {"status": "error", "message": f"Level '{level_name}' not found.", "element_id": None}

        # Calculate centroid for room placement point (UV on the level's plane)
        if not boundary_points:
             return {"status": "error", "message": "No boundary points provided for room.", "element_id": None}

        avg_x = sum(p[0] for p in boundary_points) / len(boundary_points)
        avg_y = sum(p[1] for p in boundary_points) / len(boundary_points)
        location_point = UV(avg_x, avg_y)

        # Get the current phase (or a specific one, e.g., "New Construction")
        # This assumes the last phase is the one to use.
        current_phase = doc.Phases.get_Item(doc.Phases.Size - 1) if doc.Phases.Size > 0 else None
        if not current_phase:
            return {"status": "error", "message": "No phases found in the document.", "element_id": None}
        logger.info(f"Using Phase: {current_phase.Name if hasattr(current_phase, 'Name') else 'Unknown'}")

        t.Start()
        # Create an unbound room at the location point. Revit will attempt to find boundaries.
        # new_room_data = NewRoomData(target_level, location_point) # This is not how you create a room
        # new_room = doc.Create.NewRoom(new_room_data) # This is also not standard

        # Correct way for creating a room (it will be unbound initially if no boundaries exist at point)
        new_room = doc.Create.NewRoom(target_level, location_point)

        if not new_room:
            if t.HasStarted(): t.RollBack()
            return {"status": "error", "message": "Failed to create room object (returned None). Ensure area is bounded.", "element_id": None}

        # Set room name
        name_param = new_room.get_Parameter(BuiltInParameter.ROOM_NAME)
        if name_param and not name_param.IsReadOnly:
            name_param.Set(room_name)

        # Optionally, create a room tag (requires a RoomTag family to be loaded)
        # tag_location = location_point # or slightly offset
        # try:
        #     room_tag = doc.Create.NewRoomTag(new_room.Id, tag_location, None) # None for default view
        #     if room_tag: logger.info(f"Room tag created for room {new_room.Id.ToString()}")
        # except Exception as tag_ex:
        #     logger.warning(f"Could not create room tag for {new_room.Id.ToString()}: {tag_ex}")

        t.Commit()
        room_id_str = new_room.Id.ToString()
        logger.info(f"Room '{room_name}' created with ID: {room_id_str} on level '{level_name}'. May be unbound if no walls present.")
        return {"status": "success", "message": f"Room '{room_name}' created. May be unbound.", "element_id": room_id_str}

    except Exception as e:
        if t.HasStarted() and not t.HasEnded(): t.RollBack()
        logger.error(f"Error in 'add_room' Revit interaction: {e}", exc_info=True)
        return {"status": "error", "message": f"Failed to create room: {str(e)}", "element_id": None}

# --- FastMCP Server Setup ---
mcp_server = FastMCP(
    title="Revit Design AI MCP Server",
    description="Exposes Revit API functionalities for AI agents. Assumes units are in feet unless specified.",
    version="0.2.0" # Incremented version
)

mcp_server.include_tool(add_wall)
mcp_server.include_tool(add_room)

async def run_server(host: str = "127.0.0.1", port: int = 8765):
    """Runs the FastMCP server."""
    logger.info(f"Attempting to start FastMCP server for Revit on http://{host}:{port}")
    try:
        # uvicorn.run(mcp_server.app, host=host, port=port, log_config=None) # Alternative way
        await mcp_server.run_async(host=host, port=port) # Preferred for FastMCP
        logger.info(f"FastMCP server for Revit stopped on http://{host}:{port}")
    except Exception as e:
        logger.error(f"Server run failed: {e}", exc_info=True)
        raise # Re-raise to inform the caller (PyRevit script)

if __name__ == "__main__":
    print("Running MCP server in standalone mode (Revit API will be stubbed).")
    print(f"OpenAPI spec (if server runs): http://127.0.0.1:8765{mcp_server.openapi_url}")
    print(f"Interactive API docs (if server runs): http://127.0.0.1:8765{mcp_server.docs_url}")

    # For standalone testing, Revit context will be None or mocked.
    # Tools will log errors about Revit context but server should run.
    set_revit_context(None, None, Document() if not REVIT_API_AVAILABLE else None) # Mock Document for standalone

    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        logger.info("Standalone server stopped by user.")
    except Exception as e:
        # Errors from run_server (like port in use) will be caught here
        logger.error(f"Standalone server failed to run: {e}", exc_info=True)
