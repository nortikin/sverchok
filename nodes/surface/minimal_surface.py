
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
from sverchok.utils.surface.rbf import SvExRbfSurface

if scipy is None:
    add_dummy('SvExMinimalSurfaceNode', "Minimal Surface", 'scipy')
else:
    from scipy.interpolate import Rbf

    TARGET_U_SOCKET = 6
    TARGET_V_SOCKET = 7

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
            self.inputs[TARGET_U_SOCKET].hide_safe = self.generate_mode != 'EXPLICIT'
            self.inputs[TARGET_V_SOCKET].hide_safe = self.generate_mode != 'EXPLICIT'
            self.inputs[TARGET_U_SOCKET].name = "TargetU" if self.coord_mode == 'UV' else "TargetX"
            self.inputs[TARGET_V_SOCKET].name = "TargetV" if self.coord_mode == 'UV' else "TargetY"
            self.inputs['GridPoints'].hide_safe = self.generate_mode != 'GRID'
            self.outputs['Vertices'].hide_safe = self.generate_mode == 'NONE'
            self.outputs['Edges'].hide_safe = self.generate_mode != 'GRID'
            self.outputs['Faces'].hide_safe = self.generate_mode != 'GRID'

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

        grid_points : IntProperty(
                name = "Points",
                default = 25,
                min = 3,
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
                default = False,
                update = update_sockets)

        generate_modes = [
            ('NONE', "None", "Do not generate surface vertices / faces", 0),
            ('GRID', "Grid", "Generate automatic grid", 1),
            ('EXPLICIT', "Explicit", "Generate vertices at provided U/V coordinates", 2)
        ]

        generate_mode : EnumProperty(
                name = "Evaluate",
                items = generate_modes,
                default = 'NONE',
                update = update_sockets)

        def sv_init(self, context):
            self.inputs.new('SvVerticesSocket', "Vertices") # 0
            self.inputs.new('SvStringsSocket', "GridPoints").prop_name = 'grid_points' #1
            self.inputs.new('SvStringsSocket', "Epsilon").prop_name = 'epsilon' #2
            self.inputs.new('SvStringsSocket', "Smooth").prop_name = 'smooth' #3
            self.inputs.new('SvStringsSocket', "SrcU") #4
            self.inputs.new('SvStringsSocket', "SrcV") #5
            self.inputs.new('SvStringsSocket', "TargetU") #6 - TARGET_U_SOCKET
            self.inputs.new('SvStringsSocket', "TargetV") #7 - TARGET_V_SOCKET
            self.inputs.new('SvMatrixSocket', "Matrix") #8
            self.outputs.new('SvVerticesSocket', "Vertices")
            self.outputs.new('SvStringsSocket', "Edges")
            self.outputs.new('SvStringsSocket', "Faces")
            self.outputs.new('SvSurfaceSocket', "Surface")
            self.update_sockets(context)

        def draw_buttons(self, context, layout):
            layout.label(text="Surface type:")
            layout.prop(self, "coord_mode", expand=True)
            layout.prop(self, "function")
            if self.coord_mode == 'XY':
                layout.prop(self, "orientation", expand=True)
            if self.coord_mode == 'UV':
                layout.prop(self, "explicit_src_uv")
            layout.label(text='Generate:')
            layout.prop(self, 'generate_mode', text='')

        def make_edges_xy(self, n_points):
            edges = []
            for row in range(n_points):
                e_row = [(i + n_points * row, (i+1) + n_points * row) for i in range(n_points-1)]
                edges.extend(e_row)
                if row < n_points - 1:
                    e_col = [(i + n_points * row, i + n_points * (row+1)) for i in range(n_points)]
                    edges.extend(e_col)
            return edges

        def make_faces_xy(self, n_points):
            faces = []
            for row in range(n_points - 1):
                for col in range(n_points - 1):
                    i = row + col * n_points
                    face = (i, i+n_points, i+n_points+1, i+1)
                    faces.append(face)
            return faces

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
            points_s = self.inputs['GridPoints'].sv_get()
            epsilon_s = self.inputs['Epsilon'].sv_get()
            smooth_s = self.inputs['Smooth'].sv_get()
            src_us_s = self.inputs['SrcU'].sv_get(default = [[]])
            src_vs_s = self.inputs['SrcV'].sv_get(default = [[]])
            target_us_s = self.inputs[TARGET_U_SOCKET].sv_get(default = [[]])
            target_vs_s = self.inputs[TARGET_V_SOCKET].sv_get(default = [[]])
            matrices_s = self.inputs['Matrix'].sv_get(default = [[Matrix()]])

            verts_out = []
            edges_out = []
            faces_out = []
            surfaces_out = []
            inputs = zip_long_repeat(vertices_s, src_us_s, src_vs_s, matrices_s, points_s, target_us_s, target_vs_s, epsilon_s, smooth_s)
            for vertices, src_us, src_vs, matrix, grid_points, target_us, target_vs, epsilon, smooth in inputs:
                if isinstance(epsilon, (list, int)):
                    epsilon = epsilon[0]
                if isinstance(smooth, (list, int)):
                    smooth = smooth[0]
                if isinstance(grid_points, (list, int)):
                    grid_points = grid_points[0]
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

                    if self.generate_mode == 'NONE':
                        new_verts = np.array([])
                    else:
                        if self.generate_mode == 'GRID':
                            target_x_range = np.linspace(x_min, x_max, grid_points)
                            target_y_range = np.linspace(y_min, y_max, grid_points)
                            XI, YI = np.meshgrid(target_x_range, target_y_range)
                            XI = XI.flatten()
                            YI = YI.flatten()
                        else: # EXPLICIT
                            XI, YI = np.array(target_us), np.array(target_vs)
                        ZI = rbf(XI, YI)

                        if self.orientation == 'X':
                            YI, ZI, XI = XI, YI, ZI
                        elif self.orientation == 'Y':
                            ZI, XI, YI = XI, YI, ZI
                        else: # Z
                            pass

                        new_verts = np.stack((XI,YI,ZI)).T
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

                    if self.generate_mode == 'NONE':
                        new_verts = np.array([])
                    else:
                        if self.generate_mode == 'GRID':
                            target_u_range = np.linspace(u_min, u_max, grid_points)
                            target_v_range = np.linspace(v_min, v_max, grid_points)
                            target_us, target_vs = np.meshgrid(target_u_range, target_v_range)
                            target_us = target_us.flatten()
                            target_vs = target_vs.flatten()
                        else:
                            if len(target_us) == 0:
                                raise Exception("Target U values are not specified")
                            if len(target_vs) == 0:
                                raise Exception("Target V values are not specified")

                        new_verts = rbf(target_us, target_vs)

                if has_matrix and self.generate_mode != 'NONE':
                    new_verts = new_verts - translation
                    print(new_verts.shape)
                    new_verts = np.apply_along_axis(lambda v : np_matrix @ v, 1, new_verts)
                new_verts = new_verts.tolist()
                #if not (self.coord_mode == 'UV' and self.generate_mode == 'EXPLICIT'):
                #    new_verts = sum(new_verts, [])
                new_edges = self.make_edges_xy(grid_points)
                new_faces = self.make_faces_xy(grid_points)

                verts_out.append(new_verts)
                edges_out.append(new_edges)
                faces_out.append(new_faces)
                surface = SvExRbfSurface(rbf, self.coord_mode, self.orientation, matrix)
                surface.u_bounds = u_bounds
                surface.v_bounds = v_bounds
                surfaces_out.append(surface)

            self.outputs['Vertices'].sv_set(verts_out)
            self.outputs['Edges'].sv_set(edges_out)
            self.outputs['Faces'].sv_set(faces_out)
            self.outputs['Surface'].sv_set(surfaces_out)

def register():
    if scipy is not None:
        bpy.utils.register_class(SvExMinimalSurfaceNode)

def unregister():
    if scipy is not None:
        bpy.utils.unregister_class(SvExMinimalSurfaceNode)

