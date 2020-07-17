
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from mathutils import Matrix

import sverchok
from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level
from sverchok.utils.logging import info, exception
from sverchok.utils.dummy_nodes import add_dummy
from sverchok.dependencies import scipy
from sverchok.utils.surface.rbf import SvRbfSurface

if scipy is None:
    add_dummy('SvExMinimalSurfaceNode', "Minimal Surface", 'scipy')
else:
    from scipy.interpolate import Rbf

    class SvExMinimalSurfaceNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Minimal Surface
        Tooltip: Minimal Surface
        """
        bl_idname = 'SvExMinimalSurfaceNode'
        bl_label = 'Minimal Surface'
        bl_icon = 'OUTLINER_OB_EMPTY'
        sv_icon = 'SV_EX_MINSURFACE'

        @throttled
        def update_sockets(self, context):
            self.inputs['Matrix'].hide_safe = self.coord_mode == 'UV'
            self.inputs['SrcU'].hide_safe = self.coord_mode != 'UV' or not self.explicit_src_uv
            self.inputs['SrcV'].hide_safe = self.coord_mode != 'UV' or not self.explicit_src_uv

        coord_modes = [
            ('XY', "X Y -> Z", "XY -> Z function", 0),
            ('UV', "U V -> X Y Z", "UV -> XYZ function", 1)
        ]

        coord_mode : EnumProperty(
            name = "Coordinates",
            items = coord_modes,
            default = 'XY',
            update = update_sockets)

        functions = [
            ('multiquadric', "Multi Quadric", "Multi Quadric", 0),
            ('inverse', "Inverse", "Inverse", 1),
            ('gaussian', "Gaussian", "Gaussian", 2),
            ('cubic', "Cubic", "Cubic", 3),
            ('quintic', "Quintic", "Qunitic", 4),
            ('thin_plate', "Thin Plate", "Thin Plate", 5)
        ]

        function : EnumProperty(
                name = "Function",
                items = functions,
                default = 'multiquadric',
                update = updateNode)

        axes = [
            ('X', "X", "X axis", 0),
            ('Y', "Y", "Y axis", 1),
            ('Z', "Z", "Z axis", 2)
        ]

        orientation : EnumProperty(
                name = "Orientation",
                items = axes,
                default = 'Z',
                update = updateNode)

        epsilon : FloatProperty(
                name = "Epsilon",
                default = 1.0,
                min = 0.0,
                update = updateNode)
        
        smooth : FloatProperty(
                name = "Smooth",
                default = 0.0,
                min = 0.0,
                update = updateNode)

        explicit_src_uv : BoolProperty(
                name = "Explicit source UV",
                default = True,
                update = update_sockets)

        def sv_init(self, context):
            self.inputs.new('SvVerticesSocket', "Vertices") # 0
            self.inputs.new('SvStringsSocket', "Epsilon").prop_name = 'epsilon' #2
            self.inputs.new('SvStringsSocket', "Smooth").prop_name = 'smooth' #3
            self.inputs.new('SvStringsSocket', "SrcU") #4
            self.inputs.new('SvStringsSocket', "SrcV") #5
            self.inputs.new('SvMatrixSocket', "Matrix") #8
            self.outputs.new('SvSurfaceSocket', "Surface")
            self.update_sockets(context)

        def draw_buttons(self, context, layout):
            layout.label(text="Surface type:")
            layout.prop(self, "coord_mode", expand=True)
            if self.coord_mode == 'XY':
                layout.prop(self, "orientation", expand=True)
            if self.coord_mode == 'UV':
                layout.prop(self, "explicit_src_uv")
            layout.prop(self, "function")

        def make_uv(self, vertices):

            def distance(v1, v2):
                v1 = np.array(v1)
                v2 = np.array(v2)
                return np.linalg.norm(v1-v2)

            u = 0
            v = 0
            us, vs = [], []
            prev_row = None
            rev_vs = None
            for row in vertices:
                u = 0
                row_vs = []
                prev_vertex = None
                for j, vertex in enumerate(row):
                    if prev_row is not None:
                        dv = distance(prev_row[j], vertex)
                        v = prev_vs[j] + dv
                    if prev_vertex is not None:
                        du = distance(prev_vertex, vertex)
                        u += du
                    us.append(u)
                    vs.append(v)
                    row_vs.append(v)
                    prev_vertex = vertex
                prev_row = row
                prev_vs = row_vs

            return np.array(us), np.array(vs)

        def process(self):

            if not any(socket.is_linked for socket in self.outputs):
                return

            vertices_s = self.inputs['Vertices'].sv_get()
            if self.coord_mode == 'UV':
                vertices_s = ensure_nesting_level(vertices_s, 4)
            epsilon_s = self.inputs['Epsilon'].sv_get()
            smooth_s = self.inputs['Smooth'].sv_get()
            src_us_s = self.inputs['SrcU'].sv_get(default = [[]])
            src_vs_s = self.inputs['SrcV'].sv_get(default = [[]])
            matrices_s = self.inputs['Matrix'].sv_get(default = [[Matrix()]])

            verts_out = []
            edges_out = []
            faces_out = []
            surfaces_out = []
            inputs = zip_long_repeat(vertices_s, src_us_s, src_vs_s, matrices_s, epsilon_s, smooth_s)
            for vertices, src_us, src_vs, matrix, epsilon, smooth in inputs:
                if isinstance(epsilon, (list, int)):
                    epsilon = epsilon[0]
                if isinstance(smooth, (list, int)):
                    smooth = smooth[0]
                if isinstance(matrix, list):
                    matrix = matrix[0]
                has_matrix = self.coord_mode == 'XY' and matrix is not None and matrix != Matrix()

                if self.coord_mode == 'UV' and self.explicit_src_uv:
                    if get_data_nesting_level(src_us) == 3:
                        src_us = sum(src_us, [])
                    if get_data_nesting_level(src_vs) == 3:
                        src_vs = sum(src_vs, [])

                if self.coord_mode == 'XY':
                    XYZ = np.array(vertices)
                else: # UV
                    all_vertices = sum(vertices, [])
                    XYZ = np.array(all_vertices)
                if has_matrix:
                    np_matrix = np.array(matrix.to_3x3())
                    inv_matrix = np.linalg.inv(np_matrix)
                    translation = np.array(matrix.translation)
                    XYZ = np.matmul(inv_matrix, XYZ.T).T + translation

                if self.coord_mode == 'XY':
                    if self.orientation == 'X':
                        reorder = np.array([1, 2, 0])
                        XYZ = XYZ[:, reorder]
                    elif self.orientation == 'Y':
                        reorder = np.array([2, 0, 1])
                        XYZ = XYZ[:, reorder]
                    else: # Z
                        pass

                    #print(XYZ[:,0])
                    #print(XYZ[:,1])
                    #print(XYZ[:,2])
                    rbf = Rbf(XYZ[:,0],XYZ[:,1],XYZ[:,2],
                            function=self.function,
                            smooth=smooth,
                            epsilon=epsilon, mode='1-D')

                    x_min = XYZ[:,0].min()
                    x_max = XYZ[:,0].max()
                    y_min = XYZ[:,1].min()
                    y_max = XYZ[:,1].max()
                    u_bounds = (x_min, x_max)
                    v_bounds = (y_min, y_max)

                else: # UV
                    if not self.explicit_src_uv:
                        src_us, src_vs = self.make_uv(vertices)
                    else:
                        src_us = np.array(src_us)
                        src_vs = np.array(src_vs)

                    #self.info("Us: %s, Vs: %s", len(src_us), len(src_vs))
                    rbf = Rbf(src_us, src_vs, all_vertices,
                            function = self.function,
                            smooth = smooth,
                            epsilon = epsilon, mode='N-D')

                    u_min = src_us.min()
                    v_min = src_vs.min()
                    u_max = src_us.max()
                    v_max = src_vs.max()
                    u_bounds = (u_min, u_max)
                    v_bounds = (v_min, v_max)

                surface = SvRbfSurface(rbf, self.coord_mode, self.orientation, matrix)
                surface.u_bounds = u_bounds
                surface.v_bounds = v_bounds
                surfaces_out.append(surface)

            self.outputs['Surface'].sv_set(surfaces_out)

def register():
    if scipy is not None:
        bpy.utils.register_class(SvExMinimalSurfaceNode)

def unregister():
    if scipy is not None:
        bpy.utils.unregister_class(SvExMinimalSurfaceNode)

