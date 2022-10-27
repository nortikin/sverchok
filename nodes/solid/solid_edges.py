import bpy
from bpy.props import BoolProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, map_recursive, flatten_data
from sverchok.utils.curve.freecad import SvSolidEdgeCurve
from sverchok.dependencies import FreeCAD

if FreeCAD is not None:
    import Part


class SvSolidEdgesNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Solid Edges
    Tooltip: Get Edges from Solid
    """
    bl_idname = 'SvSolidEdgesNode'
    bl_label = 'Solid Edges (Curves)'
    bl_icon = 'EDGESEL'
    sv_category = "Solid Outputs"
    sv_dependencies = {'FreeCAD'}

    flat_output: BoolProperty(
        name="Flat Output",
        default=False,
        update=updateNode)

    nurbs_output : BoolProperty(
        name = "NURBS Output",
        description = "Output curves in NURBS representation",
        default = False,
        update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvSolidSocket', "Solid")
        self.outputs.new('SvCurveSocket', "Edges")

    def draw_buttons(self, context, layout):
        layout.prop(self, 'flat_output')

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.prop(self, 'nurbs_output', toggle=True)

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        solids = self.inputs['Solid'].sv_get()

        def get_edges(solid):
            edges_curves = []
            for e in solid.Edges:
                try:
                    curve = SvSolidEdgeCurve(e)
                    if self.nurbs_output:
                        curve = curve.to_nurbs()
                    edges_curves.append(curve)
                except TypeError:
                    pass
            return edges_curves

        edges_out = map_recursive(get_edges, solids, data_types=(Part.Shape,))
        if self.flat_output:
            edges_out = flatten_data(edges_out, data_types=(Part.Shape,))

        self.outputs['Edges'].sv_set(edges_out)


def register():
    bpy.utils.register_class(SvSolidEdgesNode)


def unregister():
    bpy.utils.unregister_class(SvSolidEdgesNode)
