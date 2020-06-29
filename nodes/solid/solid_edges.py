
from sverchok.dependencies import FreeCAD

if FreeCAD is not None:
    import numpy as np
    import bpy
    from bpy.props import BoolProperty
    from sverchok.node_tree import SverchCustomTreeNode
    from sverchok.data_structure import updateNode
    from sverchok.data_structure import match_long_repeat as mlr
    from sverchok.utils.curve import SvLine, SvCircle, SvCurve
    from sverchok.utils.modules.matrix_utils import vectors_to_matrix
    import Part
    from FreeCAD import Base

    class SvEdgeCurve(SvCurve):
        __description__ = "Edge Curve"
        def __init__(self, solid_edge):
            self.edge = solid_edge
            self.curve = solid_edge.Curve
            self.u_bounds = (self.edge.FirstParameter, self.edge.LastParameter)

        def evaluate(self, t):
            return np.array(self.curve.value(t))

        def evaluate_array(self, ts):
            t_out = []
            for t in ts:
                t_out.append(self.curve.value(t))
            return np.array(t_out)

        def get_u_bounds(self):
            return self.u_bounds

    class SvSolidEdgesNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Solid Edges
        Tooltip: Get Edges from Solid
        """
        bl_idname = 'SvSolidEdgesNode'
        bl_label = 'Solid Edges'
        bl_icon = 'EDGESEL'


        flat_output: BoolProperty(
            name="Flat Output",
            default=False,
            update=updateNode)


        def sv_init(self, context):
            self.inputs.new('SvSolidSocket', "Solid")
            self.outputs.new('SvCurveSocket', "Edges")


        def draw_buttons(self, context, layout):
            layout.prop(self, 'flat_output')

        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            solids = self.inputs[0].sv_get()

            edges = []
            edges_add = edges.extend if self.flat_output else edges.append
            for solid in solids:
                edges_curves = []
                for e in solid.Edges:
                    try:
                        edge_curve = e.Curve
                        if issubclass(type(e.Curve), Part.Line):
                            curve = SvEdgeCurve(e)
                            direction = np.array(e.Curve.Direction)
                            point1 = np.array(e.Curve.value(e.FirstParameter))
                            line = SvLine(point1, direction)
                            line.u_bounds = (e.FirstParameter, e.LastParameter)
                            edges_curves.append(curve)

                        elif issubclass(type(e.Curve), Part.Circle):
                            center = vectors_to_matrix([e.Curve.Center], [e.Curve.Axis], [e.Curve.value(e.FirstParameter)])[0]
                            curve = SvCircle(center, e.Curve.Radius)
                            curve.u_bounds = (e.FirstParameter, e.LastParameter)
                            edges_curves.append(curve)
                        else:
                            curve = SvEdgeCurve(e)
                            edges_curves.append(curve)
                    except TypeError:
                        pass


                edges_add(edges_curves)

            self.outputs['Edges'].sv_set(edges)


def register():
    if FreeCAD is not None:
        bpy.utils.register_class(SvSolidEdgesNode)

def unregister():
    if FreeCAD is not None:
        bpy.utils.unregister_class(SvSolidEdgesNode)
