
import numpy as np

import bpy
from bpy.props import EnumProperty, IntProperty

import sverchok
from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level
from sverchok.utils.logging import info, exception
from sverchok.utils.surface import SvExSurface

U_SOCKET = 1
V_SOCKET = 2

class SvExEvalSurfaceNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Evaluate Surface
    Tooltip: Evaluate Surface
    """
    bl_idname = 'SvExEvalSurfaceNode'
    bl_label = 'Evaluate Surface'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_EVAL_SURFACE'

    @throttled
    def update_sockets(self, context):
        self.inputs[U_SOCKET].hide_safe = self.eval_mode == 'GRID' or self.input_mode == 'VERTICES'
        self.inputs[V_SOCKET].hide_safe = self.eval_mode == 'GRID' or self.input_mode == 'VERTICES'
        self.inputs['Vertices'].hide_safe = self.eval_mode == 'GRID' or self.input_mode == 'PAIRS'

        self.inputs['SamplesU'].hide_safe = self.eval_mode != 'GRID'
        self.inputs['SamplesV'].hide_safe = self.eval_mode != 'GRID'

        self.outputs['Edges'].hide_safe = self.eval_mode == 'EXPLICIT'
        self.outputs['Faces'].hide_safe = self.eval_mode == 'EXPLICIT'

    eval_modes = [
        ('GRID', "Grid", "Generate a default grid", 0),
        ('EXPLICIT', "Explicit", "Evaluate the surface in the specified points", 1)
    ]

    eval_mode : EnumProperty(
        name = "Evaluation mode",
        items = eval_modes,
        default = 'GRID',
        update = update_sockets)

    input_modes = [
        ('PAIRS', "Separate", "Separate U V (or X Y) sockets", 0),
        ('VERTICES', "Vertices", "Single socket for vertices", 1)
    ]

    input_mode : EnumProperty(
        name = "Input mode",
        items = input_modes,
        default = 'PAIRS',
        update = update_sockets)

    axes = [
        ('XY', "X Y", "XOY plane", 0),
        ('YZ', "Y Z", "YOZ plane", 1),
        ('XZ', "X Z", "XOZ plane", 2)
    ]

    orientation : EnumProperty(
            name = "Orientation",
            items = axes,
            default = 'XY',
            update = updateNode)

    samples_u : IntProperty(
            name = "Samples U",
            default = 25, min = 3,
            update = updateNode)

    samples_v : IntProperty(
            name = "Samples V",
            default = 25, min = 3,
            update = updateNode)

    clamp_modes = [
        ('NO', "As is", "Do not clamp input values - try to process them as is (you will get either error or extrapolation on out-of-bounds values, depending on specific surface type", 0),
        ('CLAMP', "Clamp", "Clamp input values into bounds - for example, turn -0.1 into 0", 1),
        ('WRAP', "Wrap", "Wrap input values into bounds - for example, turn -0.1 into 0.9", 2)
    ]

    clamp_mode : EnumProperty(
            name = "Clamp",
            items = clamp_modes,
            default = 'NO',
            update = updateNode)

    def draw_buttons(self, context, layout):
        layout.label(text="Evaluate:")
        layout.prop(self, "eval_mode", expand=True)
        if self.eval_mode == 'EXPLICIT':
            layout.label(text="Input mode:")
            layout.prop(self, "input_mode", expand=True)
            if self.input_mode == 'VERTICES':
                layout.label(text="Input orientation:")
                layout.prop(self, "orientation", expand=True)
            layout.prop(self, 'clamp_mode', expand=True)

    def sv_init(self, context):
        self.inputs.new('SvExSurfaceSocket', "Surface").display_shape = 'DIAMOND' #0
        self.inputs.new('SvStringsSocket', "U") # 1 — U_SOCKET
        self.inputs.new('SvStringsSocket', "V") # 2 — V_SOCKET
        self.inputs.new('SvVerticesSocket', "Vertices") # 3
        self.inputs.new('SvStringsSocket', "SamplesU").prop_name = 'samples_u' # 4
        self.inputs.new('SvStringsSocket', "SamplesV").prop_name = 'samples_v' # 5
        self.outputs.new('SvVerticesSocket', "Vertices") # 0
        self.outputs.new('SvStringsSocket', "Edges")
        self.outputs.new('SvStringsSocket', "Faces")
        self.update_sockets(context)

    def parse_input(self, verts):
        verts = np.array(verts)
        if self.orientation == 'XY':
            us, vs = verts[:,0], verts[:,1]
        elif self.orientation == 'YZ':
            us, vs = verts[:,1], verts[:,2]
        else: # XZ
            us, vs = verts[:,0], verts[:,2]
        return us, vs

    def _clamp(self, surface, us, vs):
        u_min = surface.get_u_min()
        u_max = surface.get_u_max()
        v_min = surface.get_v_min()
        v_max = surface.get_v_max()
        us = np.clip(us, u_min, u_max)
        vs = np.clip(vs, v_min, v_max)
        return us, vs

    def _wrap(self, surface, us, vs):
        u_min = surface.get_u_min()
        u_max = surface.get_u_max()
        v_min = surface.get_v_min()
        v_max = surface.get_v_max()
        u_len = u_max - u_min
        v_len = v_max - u_min
        us = (us - u_min) % u_len + u_min
        vs = (vs - v_min) % v_len + v_min
        return us, vs

    def build_output(self, surface, verts):
        if surface.has_input_matrix:
            orientation = surface.get_input_orientation()
            if orientation == 'X':
                reorder = np.array([2, 0, 1])
                verts = verts[:, reorder]
            elif orientation == 'Y':
                reorder = np.array([1, 2, 0])
                verts = verts[:, reorder]
            else: # Z
                pass
            matrix = surface.get_input_matrix()
            verts = verts - matrix.translation
            np_matrix = np.array(matrix.to_3x3())
            verts = np.apply_along_axis(lambda v : np_matrix @ v, 1, verts)
        return verts

    def make_grid_input(self, surface, samples_u, samples_v):
        u_min = surface.get_u_min()
        u_max = surface.get_u_max()
        v_min = surface.get_v_min()
        v_max = surface.get_v_max()
        us = np.linspace(u_min, u_max, num=samples_u)
        vs = np.linspace(v_min, v_max, num=samples_v)
        us, vs = np.meshgrid(us, vs)
        us = us.flatten()
        vs = vs.flatten()
        return us, vs

    def make_edges_xy(self, samples_u, samples_v):
        edges = []
        for row in range(samples_v):
            e_row = [(i + samples_u * row, (i+1) + samples_u * row) for i in range(samples_u-1)]
            edges.extend(e_row)
            if row < samples_v - 1:
                e_col = [(i + samples_u * row, i + samples_u * (row+1)) for i in range(samples_u)]
                edges.extend(e_col)
        return edges

    def make_faces_xy(self, samples_u, samples_v):
        faces = []
        for row in range(samples_v - 1):
            for col in range(samples_u - 1):
                i = row * samples_u + col
                face = (i, i+samples_u, i+samples_u+1, i+1)
                faces.append(face)
        return faces

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        surfaces_s = self.inputs['Surface'].sv_get()
        target_us_s = self.inputs[U_SOCKET].sv_get(default=[[]])
        target_vs_s = self.inputs[V_SOCKET].sv_get(default=[[]])
        target_verts_s = self.inputs['Vertices'].sv_get(default = [[]])
        samples_u_s = self.inputs['SamplesU'].sv_get()
        samples_v_s = self.inputs['SamplesV'].sv_get()

        if isinstance(surfaces_s[0], SvExSurface):
            surfaces_s = [surfaces_s]

        samples_u_s = ensure_nesting_level(samples_u_s, 2)
        samples_v_s = ensure_nesting_level(samples_v_s, 2)
        target_us_s = ensure_nesting_level(target_us_s, 3)
        target_vs_s = ensure_nesting_level(target_vs_s, 3)
        target_verts_s = ensure_nesting_level(target_verts_s, 4)

        verts_out = []
        edges_out = []
        faces_out = []

        inputs = zip_long_repeat(surfaces_s, target_us_s, target_vs_s, target_verts_s, samples_u_s, samples_v_s)
        for surfaces, target_us_i, target_vs_i, target_verts_i, samples_u_i, samples_v_i in inputs:
            objects = zip_long_repeat(surfaces, target_us_i, target_vs_i, target_verts_i, samples_u_i, samples_v_i)
            for surface, target_us, target_vs, target_verts, samples_u, samples_v in objects:

                if self.eval_mode == 'GRID':
                    target_us, target_vs = self.make_grid_input(surface, samples_u, samples_v)
                    new_edges = self.make_edges_xy(samples_u, samples_v)
                    new_faces = self.make_faces_xy(samples_u, samples_v)
                else:
                    if self.input_mode == 'VERTICES':
                        print(target_verts)
                        target_us, target_vs = self.parse_input(target_verts)
                    else:
                        target_us, target_vs = np.array(target_us), np.array(target_vs)
                    if self.clamp_mode == 'CLAMP':
                        target_us, target_vs = self._clamp(surface, target_us, target_vs)
                    elif self.clamp_mode == 'WRAP':
                        target_us, target_vs = self._wrap(surface, target_us, target_vs)
                    new_edges = []
                    new_faces = []
                new_verts = surface.evaluate_array(target_us, target_vs)

                new_verts = self.build_output(surface, new_verts)
                new_verts = new_verts.tolist()
                verts_out.append(new_verts)
                edges_out.append(new_edges)
                faces_out.append(new_faces)

        self.outputs['Vertices'].sv_set(verts_out)
        self.outputs['Edges'].sv_set(edges_out)
        self.outputs['Faces'].sv_set(faces_out)

def register():
    bpy.utils.register_class(SvExEvalSurfaceNode)

def unregister():
    bpy.utils.unregister_class(SvExEvalSurfaceNode)

