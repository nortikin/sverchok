
import json

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, StringProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from sverchok.utils.curve.nurbs import SvGeomdlCurve
from sverchok.utils.surface.nurbs import SvGeomdlSurface
from sverchok.dependencies import geomdl

if geomdl is not None:
    # FIXME: Ugly temporary hack... Has to be replaced after
    # https://github.com/orbingol/NURBS-Python/issues/76 is fixed.
    from geomdl import _exchange
    from geomdl import BSpline


class SvExJsonToNurbsNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: JSON to NURBS
    Tooltip: Import NURBS from JSON file
    """
    bl_idname = 'SvExJsonToNurbsNode'
    bl_label = 'JSON to NURBS'
    bl_icon = 'CURVE_NCURVE'
    sv_dependencies = {'geomdl'}

    text_block : StringProperty(
            name = "Text",
            default = "nurbs.json",
            update = updateNode)

    def draw_buttons(self, context, layout):
        layout.prop_search(self, 'text_block', bpy.data, 'texts', text='', icon='TEXT')

    def sv_init(self, context):
        self.outputs.new('SvCurveSocket', "Curves")
        self.outputs.new('SvSurfaceSocket', "Surfaces")

    def load_json(self):
        def callback(data):
            return json.loads(data)

        internal_file = bpy.data.texts[self.text_block]
        data = internal_file.as_string()
        items = _exchange.import_dict_str(file_src=data, delta=-1.0, callback=callback, tmpl=False)
        return items

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        if not self.text_block:
            return

        curves_out = []
        surfaces_out = []
        items = self.load_json()
        for i, item in enumerate(items):
            if isinstance(item, BSpline.Curve):
                curve = SvGeomdlCurve(item)
                curves_out.append(curve)
            elif isinstance(item, BSpline.Surface):
                surface = SvGeomdlSurface(item)
                surfaces_out.append(surface)
            else:
                self.warning("JSON data item #%s contains unsupported data type: %s", i, type(item))

        self.outputs['Curves'].sv_set(curves_out)
        self.outputs['Surfaces'].sv_set(surfaces_out)


def register():
    bpy.utils.register_class(SvExJsonToNurbsNode)


def unregister():
    bpy.utils.unregister_class(SvExJsonToNurbsNode)
