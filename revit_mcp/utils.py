from pyrevit import DB, revit
import traceback
import logging

logger = logging.getLogger(__name__)


def normalize_string(text):
    """Safely normalize string values"""
    if text is None:
        return "Unnamed"
    return str(text).strip()


def get_element_name(element):
    """
    Get the name of a Revit element.
    Useful for both FamilySymbol and other elements.
    """
    try:
        return element.Name
    except AttributeError:
        return DB.Element.Name.__get__(element)


def find_family_symbol_safely(doc, family_name, type_name=None):
    """Safely locate a *FamilySymbol* in the active Revit model (pyRevit)."""

    try:
        symbols = (DB.FilteredElementCollector(doc)
                   .WhereElementIsElementType()
                   .OfClass(DB.FamilySymbol))

        for symbol in symbols:
            if get_element_name(symbol.Family) != family_name:
                continue

            if type_name is None:
                return symbol

            if get_element_name(symbol) == type_name:
                return symbol

            pname = symbol.get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM)
            if pname and pname.AsString() == type_name:
                return symbol

        return None
    except Exception as exc:
        logger.warning("find_family_symbol_safely failed: %s", exc)
        return None
