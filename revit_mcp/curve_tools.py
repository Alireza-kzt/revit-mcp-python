# -*- coding: UTF-8 -*-
"""Curve-based element creation routes for Revit MCP"""

from pyrevit import routes, DB
import json
import logging

from .utils import find_family_symbol_safely, create_line_based_element

logger = logging.getLogger(__name__)


def register_curve_tools(api):
    """Register curve-based element routes with the API"""

    @api.route('/create_line_based_element/', methods=['POST'])
    def create_line_element(doc, request):
        """Create a line-based family instance between two points."""
        try:
            if not doc:
                return routes.make_response(
                    data={'error': 'No active Revit document'}, status=503
                )

            data = json.loads(request.data) if isinstance(request.data, str) else request.data
            family_name = data.get('family_name')
            type_name = data.get('type_name')
            start = data.get('start')
            end = data.get('end')
            level_name = data.get('level_name')
            structural = data.get('structural', False)

            if not family_name or not start or not end:
                return routes.make_response(
                    data={'error': 'family_name, start and end are required'},
                    status=400,
                )

            symbol = find_family_symbol_safely(doc, family_name, type_name)
            if not symbol:
                return routes.make_response(
                    data={'error': 'Family type not found: {} - {}'.format(family_name, type_name or 'Any')},
                    status=404,
                )

            try:
                start_xyz = DB.XYZ(float(start['x']), float(start['y']), float(start['z']))
                end_xyz = DB.XYZ(float(end['x']), float(end['y']), float(end['z']))
            except Exception as coord_err:
                return routes.make_response(
                    data={'error': 'Invalid coordinates: {}'.format(coord_err)},
                    status=400,
                )

            level = None
            if level_name:
                levels = (
                    DB.FilteredElementCollector(doc)
                    .OfCategory(DB.BuiltInCategory.OST_Levels)
                    .WhereElementIsNotElementType()
                    .ToElements()
                )
                for lvl in levels:
                    try:
                        if lvl.Name == level_name:
                            level = lvl
                            break
                    except Exception:
                        continue
                if level is None:
                    return routes.make_response(
                        data={'error': 'Level not found: {}'.format(level_name)},
                        status=404,
                    )

            s_type = DB.Structure.StructuralType.Beam if structural else DB.Structure.StructuralType.NonStructural

            instance = create_line_based_element(
                doc,
                symbol,
                start_xyz,
                end_xyz,
                level,
                structural_type=s_type,
                transaction_name='MCP Create Line Element',
            )

            return routes.make_response(
                data={
                    'status': 'success',
                    'element_id': instance.Id.IntegerValue,
                    'family_name': family_name,
                    'type_name': type_name,
                }
            )
        except Exception as e:
            logger.error('Failed to create line-based element: %s', str(e))
            return routes.make_response(data={'error': str(e)}, status=500)

    logger.info('Curve tools routes registered successfully')
