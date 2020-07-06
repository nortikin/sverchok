
import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level
from sverchok.utils.logging import info, exception
from sverchok.utils.surface.nurbs import SvExGeomdlSurface
from sverchok.dependencies import geomdl

if geomdl is not None:
    from geomdl import fitting
    
    class SvExApproxNurbsSurfaceNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: NURBS Surface
        Tooltip: Approximate NURBS Surface
        """
        bl_idname = 'SvExApproxNurbsSurfaceNode'
        bl_label = 'Approximate NURBS Surface'
        bl_icon = 'SURFACE_NSURFACE'

        input_modes = [
                ('1D', "Single list", "List of all control points (concatenated)", 1),
                ('2D', "Separated lists", "List of lists of control points", 2)
            ]

        @throttled
        def update_sockets(self, context):
            self.inputs['USize'].hide_safe = self.input_mode == '2D'
            self.inputs['PointsCntU'].hide_safe = not self.has_points_cnt
            self.inputs['PointsCntV'].hide_safe = not self.has_points_cnt

        input_mode : EnumProperty(
                name = "Input mode",
                default = '1D',
                items = input_modes,
                update = update_sockets)

        u_size : IntProperty(
                name = "U Size",
                default = 5,
                min = 3,
                update = updateNode)

        degree_u : IntProperty(
                name = "Degree U",
                min = 2, max = 6,
                default = 3,
                update = updateNode)

        degree_v : IntProperty(
                name = "Degree V",
                min = 2, max = 6,
                default = 3,
                update = updateNode)

        centripetal : BoolProperty(
                name = "Centripetal",
                default = False,
                update = updateNode)

        has_points_cnt : BoolProperty(
                name = "Specify points count",
                default = False,
                update = update_sockets)

        points_cnt_u : IntProperty(
                name = "Points count U",
                min = 3, default = 5,
                update = updateNode)

        points_cnt_v : IntProperty(
                name = "Points count V",
                min = 3, default = 5,
                update = updateNode)

        def sv_init(self, context):
            self.inputs.new('SvVerticesSocket', "Vertices")
            self.inputs.new('SvStringsSocket', "USize").prop_name = 'u_size'
            self.inputs.new('SvStringsSocket', "DegreeU").prop_name = 'degree_u'
            self.inputs.new('SvStringsSocket', "DegreeV").prop_name = 'degree_v'
            self.inputs.new('SvStringsSocket', "PointsCntU").prop_name = 'points_cnt_u'
            self.inputs.new('SvStringsSocket', "PointsCntV").prop_name = 'points_cnt_v'
            self.outputs.new('SvSurfaceSocket', "Surface")
            self.outputs.new('SvVerticesSocket', "ControlPoints")
            self.outputs.new('SvStringsSocket', "KnotsU")
            self.outputs.new('SvStringsSocket', "KnotsV")
            self.update_sockets(context)

        def draw_buttons(self, context, layout):
            layout.prop(self, 'centripetal', toggle=True)
            layout.prop(self, "input_mode")
            layout.prop(self, 'has_points_cnt', toggle=True)

        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            vertices_s = self.inputs['Vertices'].sv_get()
            u_size_s = self.inputs['USize'].sv_get()
            degree_u_s = self.inputs['DegreeU'].sv_get()
            degree_v_s = self.inputs['DegreeV'].sv_get()
            points_cnt_u_s = self.inputs['PointsCntU'].sv_get()
            points_cnt_v_s = self.inputs['PointsCntV'].sv_get()

            if self.input_mode == '1D':
                vertices_s = ensure_nesting_level(vertices_s, 3)
            else:
                vertices_s = ensure_nesting_level(vertices_s, 4)
            
            surfaces_out = []
            points_out = []
            knots_u_out = []
            knots_v_out = []
            for vertices, degree_u, degree_v, points_cnt_u, points_cnt_v, u_size in zip_long_repeat(vertices_s, degree_u_s, degree_v_s, points_cnt_u_s, points_cnt_v_s, u_size_s):
                if isinstance(degree_u, (tuple, list)):
                    degree_u = degree_u[0]
                if isinstance(degree_v, (tuple, list)):
                    degree_v = degree_v[0]
                if isinstance(u_size, (tuple, list)):
                    u_size = u_size[0]
                if isinstance(points_cnt_u, (tuple, list)):
                    points_cnt_u = points_cnt_u[0]
                if isinstance(points_cnt_v, (tuple, list)):
                    points_cnt_v = points_cnt_v[0]

                if self.input_mode == '1D':
                    n_u = u_size
                    n_v = len(vertices) // n_u
                else:
                    n_u = len(vertices[0])
                    for i, verts_i in enumerate(vertices):
                        if len(verts_i) != n_u:
                            raise Exception("Number of vertices in row #{} is not the same as in the first ({} != {})!".format(i, n_u, len(verts_i)))
                    vertices = sum(vertices, [])
                    n_v = len(vertices) // n_u

                kwargs = dict(centripetal = self.centripetal)
                if self.has_points_cnt:
                    kwargs['ctrlpts_size_u'] = points_cnt_u
                    kwargs['ctrlpts_size_v'] = points_cnt_v

                surf = fitting.approximate_surface(vertices, n_u, n_v, degree_u, degree_v, **kwargs)

                points_out.append(surf.ctrlpts2d)
                knots_u_out.append(surf.knotvector_u)
                knots_v_out.append(surf.knotvector_v)
                surf = SvExGeomdlSurface(surf)
                surfaces_out.append(surf)

            self.outputs['Surface'].sv_set(surfaces_out)
            self.outputs['ControlPoints'].sv_set(points_out)
            self.outputs['KnotsU'].sv_set(knots_u_out)
            self.outputs['KnotsV'].sv_set(knots_v_out)

def register():
    if geomdl is not None:
        bpy.utils.register_class(SvExApproxNurbsSurfaceNode)

def unregister():
    if geomdl is not None:
        bpy.utils.unregister_class(SvExApproxNurbsSurfaceNode)

