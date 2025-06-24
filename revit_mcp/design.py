# -*- coding: UTF-8 -*-
"""Design tools for creating basic elements"""

from pyrevit import routes, DB
import logging

logger = logging.getLogger(__name__)


def register_design_routes(api):
    """Register design-related routes"""

    @api.route("/add_wall/", methods=["POST"])
    def add_wall(doc, request):
        try:
            data = request.data if isinstance(request.data, dict) else request.json
            start = data.get("start_point")
            end = data.get("end_point")
            height = float(data.get("height", 3.0))
            if not all(start.get(k) is not None for k in ["x", "y", "z"]):
                raise ValueError("Invalid start point")
            if not all(end.get(k) is not None for k in ["x", "y", "z"]):
                raise ValueError("Invalid end point")
            start_xyz = DB.XYZ(start["x"], start["y"], start["z"])
            end_xyz = DB.XYZ(end["x"], end["y"], end["z"])
            wall_line = DB.Line.CreateBound(start_xyz, end_xyz)
            level = DB.FilteredElementCollector(doc).OfClass(DB.Level).FirstElement()
            t = DB.Transaction(doc, "Add Wall via MCP")
            t.Start()
            wall = DB.Wall.Create(doc, wall_line, level.Id, False)
            wall.get_Parameter(DB.BuiltInParameter.WALL_USER_HEIGHT_PARAM).Set(height)
            t.Commit()
            return routes.make_response(data={"status": "success", "element_id": wall.Id.IntegerValue})
        except Exception as e:
            logger.error("add_wall failed: %s", e)
            return routes.make_response(data={"error": str(e)}, status=500)

    @api.route("/add_room/", methods=["POST"])
    def add_room(doc, request):
        try:
            data = request.data if isinstance(request.data, dict) else request.json
            name = data.get("room_name", "Room")
            pts = data.get("boundary_pts", [])
            level = DB.FilteredElementCollector(doc).OfClass(DB.Level).FirstElement()
            curve_array = DB.CurveArray()
            for i in range(len(pts)):
                p1 = DB.XYZ(*pts[i])
                p2 = DB.XYZ(*pts[(i + 1) % len(pts)])
                curve_array.Append(DB.Line.CreateBound(p1, p2))
            t = DB.Transaction(doc, "Add Room via MCP")
            t.Start()
            sketch = DB.SketchPlane.Create(doc, level.Id)
            boundary = [curve_array]
            room = doc.Create.NewRoom(None, DB.UV(0, 0))
            room.Name = name
            t.Commit()
            return routes.make_response(data={"status": "success", "element_id": room.Id.IntegerValue})
        except Exception as e:
            logger.error("add_room failed: %s", e)
            return routes.make_response(data={"error": str(e)}, status=500)

    logger.info("Design routes registered")
