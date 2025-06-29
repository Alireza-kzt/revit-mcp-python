# -*- coding: UTF-8 -*-
"""Wall creation utilities for Revit MCP."""

from pyrevit import routes, DB
from .utils import get_element_name
import json
import logging

logger = logging.getLogger(__name__)


def register_wall_routes(api):
    """Register wall-related routes with the API."""

    @api.route('/create_wall/', methods=["POST"])
    def create_wall(doc, request):
        """Create a straight wall between two points."""
        try:
            if not doc:
                return routes.make_response(
                    data={"error": "No active Revit document"}, status=503
                )

            if not request or not request.data:
                return routes.make_response(
                    data={"error": "No data provided or invalid request format"},
                    status=400,
                )

            payload = request.data
            if isinstance(payload, str):
                try:
                    payload = json.loads(payload)
                except Exception as json_err:
                    return routes.make_response(
                        data={"error": "Invalid JSON format: {}".format(str(json_err))},
                        status=400,
                    )

            if not isinstance(payload, dict):
                return routes.make_response(
                    data={"error": "Invalid data format - expected JSON object"},
                    status=400,
                )

            start = payload.get("start")
            end = payload.get("end")
            height = payload.get("height", 10.0)
            level_name = payload.get("level_name")
            wall_type_name = payload.get("wall_type")

            if not start or not end:
                return routes.make_response(
                    data={"error": "start and end coordinates are required"}, status=400
                )

            def to_xyz(pt):
                if not all(k in pt for k in ["x", "y", "z"]):
                    raise ValueError("Coordinates must include x, y, z")
                return DB.XYZ(float(pt["x"]), float(pt["y"]), float(pt["z"]))

            try:
                start_pt = to_xyz(start)
                end_pt = to_xyz(end)
            except Exception as e:
                return routes.make_response(
                    data={"error": "Invalid coordinates: {}".format(str(e))}, status=400
                )

            base_level = None
            if level_name:
                levels = (
                    DB.FilteredElementCollector(doc)
                    .OfClass(DB.Level)
                    .ToElements()
                )
                for lvl in levels:
                    try:
                        if get_element_name(lvl) == level_name:
                            base_level = lvl
                            break
                    except Exception:
                        continue
                if not base_level:
                    return routes.make_response(
                        data={"error": "Level not found: {}".format(level_name)},
                        status=404,
                    )
            else:
                try:
                    base_level = doc.ActiveView.GenLevel
                except Exception:
                    pass
                if not base_level:
                    base_level = (
                        DB.FilteredElementCollector(doc)
                        .OfClass(DB.Level)
                        .FirstElement()
                    )

            wall_type = None
            if wall_type_name:
                wall_types = (
                    DB.FilteredElementCollector(doc)
                    .OfClass(DB.WallType)
                    .ToElements()
                )
                for wt in wall_types:
                    try:
                        if get_element_name(wt) == wall_type_name:
                            wall_type = wt
                            break
                    except Exception:
                        continue
            if not wall_type:
                try:
                    default_id = doc.GetDefaultElementTypeId(DB.ElementTypeGroup.WallType)
                    wall_type = doc.GetElement(default_id)
                except Exception:
                    wall_type = (
                        DB.FilteredElementCollector(doc)
                        .OfClass(DB.WallType)
                        .FirstElement()
                    )

            line = DB.Line.CreateBound(start_pt, end_pt)

            t = DB.Transaction(doc, "Create Wall via MCP")
            t.Start()
            try:
                new_wall = DB.Wall.Create(
                    doc,
                    line,
                    wall_type.Id,
                    base_level.Id,
                    float(height),
                    0.0,
                    False,
                    False,
                )
                t.Commit()
                return routes.make_response(
                    data={
                        "status": "success",
                        "element_id": new_wall.Id.IntegerValue,
                        "level": get_element_name(base_level),
                        "wall_type": get_element_name(wall_type),
                    }
                )
            except Exception as tx_error:
                if t.HasStarted() and not t.HasEnded():
                    t.RollBack()
                raise tx_error
        except Exception as e:
            logger.error("Failed to create wall: %s", str(e))
            return routes.make_response(data={"error": str(e)}, status=500)

    logger.info("Wall routes registered successfully")

