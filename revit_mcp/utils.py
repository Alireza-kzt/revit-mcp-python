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


def find_family_symbol_safely(doc, target_family_name, target_type_name=None):
    """
    Safely find a family symbol by name
    """
    try:
        collector = DB.FilteredElementCollector(doc).OfClass(DB.FamilySymbol)

        for symbol in collector:
            if symbol.Family.Name == target_family_name:
                if not target_type_name or symbol.Name == target_type_name:
                    return symbol
        return None
    except Exception as e:
        logger.error("Error finding family symbol: %s", str(e))
        return None


def create_line_based_element(
    doc,
    family_symbol,
    start_xyz,
    end_xyz,
    level=None,
    structural_type=DB.Structure.StructuralType.NonStructural,
    transaction_name="Create line-based element",
):
    """Place a curve-based family instance using the Revit API."""
    if family_symbol is None:
        raise ValueError("family_symbol is None")

    f_placement = family_symbol.Family.FamilyPlacementType
    if f_placement not in (
        DB.FamilyPlacementType.CurveBased,
        DB.FamilyPlacementType.CurveBasedDetail,
        DB.FamilyPlacementType.CurveDrivenStructural,
    ):
        raise ValueError(
            "Family is not curve-based.  Placement type: {}".format(f_placement)
        )

    if not family_symbol.IsActive:
        family_symbol.Activate()
        doc.Regenerate()

    curve = DB.Line.CreateBound(start_xyz, end_xyz)

    if level is None and f_placement != DB.FamilyPlacementType.CurveBasedDetail:
        try:
            level = doc.ActiveView.GenLevel
        except AttributeError:
            level = doc.GetElement(doc.ActiveView.LevelId)

    with revit.Transaction(doc, transaction_name):
        if f_placement == DB.FamilyPlacementType.CurveBasedDetail:
            view = doc.ActiveView
            instance = doc.Create.NewFamilyInstance(curve, family_symbol, view)
        else:
            instance = doc.Create.NewFamilyInstance(
                curve, family_symbol, level, structural_type
            )

    return instance
