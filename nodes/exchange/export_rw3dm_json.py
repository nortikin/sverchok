
import json

import bpy
from bpy.props import EnumProperty, StringProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from sverchok.utils.curve.nurbs import SvNurbsCurve, SvGeomdlCurve
from sverchok.utils.surface.nurbs import SvNurbsSurface, SvGeomdlSurface
from sverchok.dependencies import geomdl

if geomdl is not None:
    # FIXME: Ugly temporary hack... Has to be replaced after
    # https://github.com/orbingol/NURBS-Python/issues/76 is fixed.
    from geomdl import _exchange
    from geomdl import multi


class SvExNurbsToJsonOp(bpy.types.Operator):
    "NURBS to JSON"
    bl_idname = "node.sv_ex_nurbs_to_json"
    bl_label = "NURBS to JSON"
    bl_options = {'REGISTER', 'INTERNAL'}

    nodename: StringProperty(name='nodename')
    treename: StringProperty(name='treename')

    def execute(self, context):
        node = bpy.data.node_groups[self.treename].nodes[self.nodename]

        def callback(data):
            return json.dumps(data, indent=2)

        geometry = node.get_geometry()
        if geometry:
            exported_data = _exchange.export_dict_str(obj=geometry, callback=callback)
            text_name = node.text_block
            self.write_data(text_name, exported_data)
            return {'FINISHED'}
        else:
            self.report({'INFO'}, "No geometry to export")
            return {'CANCELLED'}

    def write_data(self, text_name, data):
        texts = bpy.data.texts.items()
        exists = False
        for t in texts:
            if bpy.data.texts[t[0]].name == text_name:
                exists = True
                break

        if not exists:
            bpy.data.texts.new(text_name)
        bpy.data.texts[text_name].clear()
        bpy.data.texts[text_name].write(data)


class SvExNurbsToJsonNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: NURBS to JSON
    Tooltip: Export NURBS to JSON file
    """
    bl_idname = 'SvExNurbsToJsonNode'
    bl_label = 'NURBS to JSON'
    bl_icon = 'CURVE_NCURVE'
    sv_dependencies = {'geomdl'}

    text_block : StringProperty(
            name = "Text",
            default = "nurbs.json",
            update = updateNode)

    modes = [
        ('CURVE', "Curves", "Export set of curves", 0),
        ('SURFACE', "Surfaces", "Export set of surfaces", 1)
    ]

    def update_sockets(self, context):
        self.inputs['Curves'].hide_safe = self.mode != 'CURVE'
        self.inputs['Surfaces'].hide_safe = self.mode != 'SURFACE'
        updateNode(self, context)

    mode : EnumProperty(
            name = "Export",
            items = modes,
            default = 'CURVE',
            update = update_sockets)

    def draw_buttons(self, context, layout):
        layout.label(text='Export NURBS:')
        layout.prop(self, 'mode', expand=True)
        layout.prop_search(self, 'text_block', bpy.data, 'texts', text='', icon='TEXT')

        export = layout.operator('node.sv_ex_nurbs_to_json', text='Export!', icon='EXPORT')
        export.nodename = self.name
        export.treename = self.id_data.name

    def sv_init(self, context):
        self.inputs.new('SvCurveSocket', "Curves")
        self.inputs.new('SvSurfaceSocket', "Surfaces")
        self.update_sockets(context)

    def process(self):
        pass

    def get_geometry(self):
        if self.mode == 'CURVE':
            curves = self.inputs['Curves'].sv_get()
            if isinstance(curves[0], (list, tuple)):
                curves = sum(curves, [])
            container = multi.CurveContainer()
            for i, curve in enumerate(curves):
                if not isinstance(curve, SvNurbsCurve):
                    if hasattr(curve, 'to_nurbs'):
                        curve = curve.to_nurbs(implementation = SvNurbsCurve.GEOMDL)
                    else:
                        raise TypeError("Provided object #%s is not a NURBS curve, but %s!" % (i, type(curve)))
                container.append(SvGeomdlCurve.from_any_nurbs(curve).curve)
            return container
        else: # SURFACE
            surfaces = self.inputs['Surfaces'].sv_get()
            if isinstance(surfaces[0], (list, tuple)):
                surfaces = sum(surfaces, [])
            container = multi.SurfaceContainer()
            for i, surface in enumerate(surfaces):
                if not isinstance(surface, SvNurbsSurface):
                    if hasattr(surface, 'to_nurbs'):
                        surface = surface.to_nurbs(implementation = SvNurbsCurve.GEOMDL)
                    else:
                        raise TypeError("Provided object #%s is not a NURBS surface, but %s!" % (i, type(surface)))
                container.append(SvGeomdlSurface.from_any_nurbs(surface).surface)
            return container


def register():
    bpy.utils.register_class(SvExNurbsToJsonOp)
    bpy.utils.register_class(SvExNurbsToJsonNode)


def unregister():
    bpy.utils.unregister_class(SvExNurbsToJsonNode)
    bpy.utils.unregister_class(SvExNurbsToJsonOp)
