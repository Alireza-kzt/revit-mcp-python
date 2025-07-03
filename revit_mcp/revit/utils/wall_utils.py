from pyrevit import DB, revit
import logging

logger = logging.getLogger(__name__)

def get_default_wall_type(doc):
    """Return a default WallType for the given document."""
    try:
        default_id = doc.GetDefaultFamilyTypeId(DB.BuiltInCategory.OST_Walls)
        if default_id and default_id != DB.ElementId.InvalidElementId:
            wall_type = doc.GetElement(default_id)
            if isinstance(wall_type, DB.WallType):
                return wall_type
    except Exception as e:
        logger.debug("Failed to get default wall type id: %s", e)

    try:
        wall_types = DB.FilteredElementCollector(doc).OfClass(DB.WallType).ToElements()
        for wt in wall_types:
            return wt
    except Exception as e:
        logger.error("Unable to collect wall types: %s", e)
    return None
