"""Utility functions related to Revit wall types."""

from pyrevit import DB, revit
import logging

__all__ = ["get_default_wall_type"]

logger = logging.getLogger(__name__)


def get_default_wall_type(doc=None):
    """Return a :class:`DB.WallType` that is safe to use as default.

    Steps:
    1. Use the active document if ``doc`` is ``None``.
    2. First try ``doc.GetDefaultElementTypeId(DB.ElementTypeGroup.WallType)``.
       If that Id is valid, return ``doc.GetElement(id)``.
    3. Fallback: iterate over ``FilteredElementCollector(doc)``
       ``.OfClass(DB.WallType).WhereElementIsElementType()`` and return the
       first whose ``Kind`` is ``DB.WallKind.Basic`` *and*
       (``'Generic' in wt.Name`` or ``'Basic' in wt.Name``).
    4. If nothing found, return ``None``.
    """

    try:
        if doc is None:
            doc = revit.doc
        if not doc:
            return None

        # Try the document's default wall type id
        default_id = doc.GetDefaultElementTypeId(DB.ElementTypeGroup.WallType)
        if default_id and default_id != DB.ElementId.InvalidElementId:
            wall_type = doc.GetElement(default_id)
            if isinstance(wall_type, DB.WallType):
                return wall_type

        # Fallback to iterating over wall types
        collector = (
            DB.FilteredElementCollector(doc)
            .OfClass(DB.WallType)
            .WhereElementIsElementType()
        )
        for wt in collector:
            try:
                name = wt.Name
            except Exception:
                name = None

            if (
                wt.Kind == DB.WallKind.Basic
                and name
                and ("Generic" in name or "Basic" in name)
            ):
                return wt

    except Exception as err:
        logger.debug("Error getting default wall type: %s", err)

    return None

