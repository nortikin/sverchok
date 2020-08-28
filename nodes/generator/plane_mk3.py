# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

import bpy
from bpy.props import IntProperty, FloatProperty, EnumProperty, BoolVectorProperty, BoolProperty
from mathutils import Matrix
import numpy as np

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, list_match_func, list_match_modes
from sverchok.utils.modules.matrix_utils import matrix_apply_np
from sverchok.utils.nodes_mixins.draft_mode import DraftMode

directionItems = [("XY", "XY", ""), ("YZ", "YZ", ""), ("ZX", "ZX", "")]
dimensionsItems = [
    ("SIZE", 'Size', 'Define size by total size'),
    ("NUMBER", 'Num', 'Define size by numer of steps and step size'),
    ("STEPS", 'Steps', 'Define size by total size'),
    ("SIZE_STEPS", 'Si+St', 'Define size by total size'),
]
def extend_lists(data, result):
    for d, r in zip(data, result):
        r.extend(d)

def append_lists(data, result):
    for d, r in zip(data, result):
        r.append(d)

def mesh_join_np(verts, edges, pols):
    lens = [0]
    for v in verts:
        lens.append(lens[-1]+v.shape[0])

    v = np.concatenate(verts)
    e, p = np.array([]), np.array([])

    if len(edges[0]) > 0:
        e = np.concatenate([edg + l for edg, l in zip(edges, lens)])
    if len(pols[0]) > 0:
        p = np.concatenate([pol + l for pol, l in zip(pols, lens)])
    return v, e, p

def numpy_check(data, bool_list):
    return [lg if b else [l.tolist() for l in lg] for lg, b in zip(data, bool_list)]


def planes_size_number(params, ops, flags):
    list_match = ops[1]
    v_obj, e_obj, p_obj = [], [], []
    m_par = list_match_func[list_match](params)
    for local_p in zip(*m_par):
        verts, edgs, pols = plane_size_number(local_p, ops, flags)
        append_lists([verts, edgs, pols], [v_obj, e_obj, p_obj])
    return v_obj, e_obj, p_obj

def planes_number_steps(params, ops, flags):
    list_match = ops[1]
    v_obj, e_obj, p_obj = [], [], []
    m_par = list_match_func[list_match](params)
    for local_p in zip(*m_par):
        verts, edgs, pols = plane_number_steps(local_p, ops, flags)
        append_lists([verts, edgs, pols], [v_obj, e_obj, p_obj])
    return v_obj, e_obj, p_obj

def plane_size_number(params, ops, flags):

    size_x, size_y, divx, divy, matrix = params
    get_verts, get_edges, get_faces = flags
    verts, edges, faces = [np.array([[]]) for i in range(3)]
    if get_verts:
        verts = make_verts(size_x, size_y, divx, divy, matrix, ops)
    if get_edges or get_faces:
        edges, faces = make_edg_pol(divx, divy, flags)
    return verts, edges, faces

def plane_number_steps(params, ops, flags):
    step_x, step_y, num_x, num_y, matrix = params
    get_verts, get_edges, get_faces = flags
    verts, edges, faces = [np.array([[]]) for i in range(3)]
    if get_verts:
        size_x = (num_x-1) * step_x
        size_y = (num_y-1) * step_y
        verts = make_verts(size_x, size_y, num_x, num_y, matrix, ops)
    if get_edges or get_faces:
        edges, faces = make_edg_pol(num_x, num_y, flags)
    return verts, edges, faces

def accum_steps(steps_x, steps_y):
    accum_steps_x = np.zeros(len(steps_x) + 1)
    accum_steps_x[1:] = np.add.accumulate(steps_x)
    accum_steps_y = np.zeros(len(steps_y) + 1)
    accum_steps_y[1:] = np.add.accumulate(steps_y)
    return accum_steps_x, accum_steps_y

def plane_size_steps(params, ops, flags):
    v_obj, e_obj, p_obj = [], [], []
    center, list_match, direction = ops
    steps_x = params[0]
    steps_y = params[1]
    accum_steps_x, accum_steps_y = accum_steps(steps_x, steps_y)

    edgs, pols = make_edg_pol(len(steps_x) + 1, len(steps_y) + 1, flags)

    sizes_mats = list_match_func[list_match]([params[2], params[3], params[-1]])
    accum_steps_x /= accum_steps_x[-1]
    accum_steps_y /= accum_steps_y[-1]
    for s_x, s_y, mat in zip(*sizes_mats):
        offset_x = -s_x/2 if center else 0
        offset_y = -s_y/2 if center else 0
        verts = make_verts_grid(
            (accum_steps_x * s_x) + offset_x,
            (accum_steps_y * s_y) + offset_y,
            mat,
            direction)
        append_lists([verts, edgs, pols], [v_obj, e_obj, p_obj])

    return v_obj, e_obj, p_obj


def plane_steps(params, ops, flags):

    center, _, direction = ops
    steps_x = params[0]
    steps_y = params[1]
    accum_steps_x, accum_steps_y = accum_steps(steps_x, steps_y)
    edgs, pols = make_edg_pol(len(steps_x) + 1, len(steps_y) + 1, flags)
    offset_x = -accum_steps_x[-1]/2 if center else 0
    offset_y = -accum_steps_y[-1]/2 if center else 0
    verts = make_verts_grid(
        accum_steps_x + offset_x,
        accum_steps_y + offset_y,
        params[-1][0],
        direction)

    return [verts], [edgs], [pols]

def make_verts_grid(sidex, sidey, matrix, direction):
    y_coords, x_coords = np.meshgrid(sidey, sidex, sparse=False, indexing='xy')
    z_coords = np.full(x_coords.shape, 0.0)
    if direction == 'XY':
        plane = np.array([x_coords, y_coords, z_coords]).T.reshape(-1, 3)
    elif direction == 'YZ':
        plane = np.array([z_coords, x_coords, y_coords]).T.reshape(-1, 3)
    else:
        plane = np.array([y_coords, z_coords, x_coords]).T.reshape(-1, 3)

    if not matrix == Matrix():
        return matrix_apply_np(plane, matrix)
    return plane

def make_verts(size_x, size_y, x_verts, y_verts, matrix, ops):

    sizex_h = size_x/2
    sizey_h = size_y/2
    center, _, direction = ops
    if center:
        offset = [0, 0, 0]
    else:
        offset = [sizex_h, sizey_h]

    sidex = np.linspace(-sizex_h + offset[0], sizex_h + offset[0], x_verts)
    sidey = np.linspace(-sizey_h + offset[1], sizey_h + offset[1], y_verts)

    return make_verts_grid(sidex, sidey, matrix, direction)

def make_edg_pol(x_verts, y_verts, flags):
    _, get_edges, get_faces = flags

    edges = np.array([])

    grid = np.arange(x_verts*y_verts, dtype=np.int32).reshape(y_verts, x_verts)

    if get_faces:
        grid_faces = np.zeros((y_verts-1, x_verts-1, 4), 'i' )
        grid_faces[:, :, 0] = grid[:-1, 1:]
        grid_faces[:, :, 1] = grid[1:, 1:]
        grid_faces[:, :, 2] = grid[1:, :-1]
        grid_faces[:, :, 3] = grid[:-1, :-1]

        all_faces = grid_faces.reshape(-1, 4)
    else:
        all_faces = np.empty((1, 4), 'i')


    if get_edges:
        edg_x_dir = np.empty((y_verts-1, x_verts, 2), 'i')
        edg_x_dir[:, :, 0] = grid[:-1, :]
        edg_x_dir[:, :, 1] = grid[1:, :]

        edg_y_dir = np.empty((y_verts, x_verts-1, 2), 'i')
        edg_y_dir[:, :, 0] = grid[:, :-1]
        edg_y_dir[:, :, 1] = grid[:, 1:]

        edge_num = (x_verts-1)* (y_verts) + (x_verts)*(y_verts-1)
        edges = np.empty((edge_num, 2), 'i')
        edges[:(y_verts - 1) * (x_verts), :] = edg_x_dir.reshape(-1, 2)
        edges[(y_verts - 1) * (x_verts):, :] = edg_y_dir.reshape(-1, 2)


    return edges, all_faces

socket_names = ['Vertices', 'Edges', 'Polygons']
plane_func_dict = {
    'STEPS': plane_steps,
    'SIZE_STEPS': plane_size_steps,
    'SIZE': planes_size_number,
    'NUMBER': planes_number_steps

}
class SvPlaneNodeMk3(DraftMode, bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Grid,
    Tooltip: Generate a Plane primitive.
    """

    bl_idname = 'SvPlaneNodeMk3'
    bl_label = 'Plane'
    bl_icon = 'MESH_PLANE'

    correct_output_modes = [
        ('NONE', 'None', 'Leave at multi-object level (Advanced)', 0),
        ('JOIN', 'Join', 'Join (mesh join) last level of boxes', 1),
        ('FLAT', 'Flat Output', 'Flat to object level', 2),
    ]


    def hide_socket(self, name, hide):
        if hide:
            self.inputs[name].hide_safe = True
        else:
            if self.inputs[name].hide_safe:
                self.inputs[name].hide_safe = False

    def update_sockets(self, context):

        hide = self.hide_socket
        if self.dimension_mode in ('STEPS', 'SIZE_STEPS'):
            self.inputs['Step X'].prop_name = ''
            self.inputs['Step Y'].prop_name = ''

            hide('Step X', False)
            hide('Step Y', False)
            hide('Num X', True)
            hide('Num Y', True)
            step_mode = self.dimension_mode == 'STEPS'
            hide('Size X', step_mode)
            hide('Size Y', step_mode)

        else:
            size_mode = self.dimension_mode == 'SIZE'
            number_mode = self.dimension_mode == 'NUMBER'

            hide('Size X', number_mode)
            hide('Size Y', number_mode)
            hide('Step X', size_mode)
            hide('Step Y', size_mode)

            self.inputs['Step X'].prop_name = 'stepx'
            self.inputs['Step Y'].prop_name = 'stepy'
            hide('Num X', False)
            hide('Num Y', False)

        updateNode(self, context)

    direction: EnumProperty(
        name="Direction", items=directionItems,
        default="XY", update=updateNode)
    dimension_mode: EnumProperty(
        name="Mode", items=dimensionsItems,
        default="SIZE", update=update_sockets)

    numx: IntProperty(
        name='N Verts X', description='Number of vertices along X',
        default=2, min=2, update=updateNode)

    numy: IntProperty(
        name='N Verts Y', description='Number of vertices along Y',
        default=2, min=2, update=updateNode)

    numx_draft: IntProperty(
        name='[D] N Verts X', description='Number of vertices along X (draft mode)',
        default=2, min=2, update=updateNode)

    numy_draft: IntProperty(
        name='[D] N Verts Y', description='Number of vertices along Y (draft mode)',
        default=2, min=2, update=updateNode)

    stepx: FloatProperty(
        name='Step X', description='Step length X',
        default=1.0, update=updateNode)

    stepy: FloatProperty(
        name='Step Y', description='Step length Y',
        default=1.0, update=updateNode)

    stepx_draft: FloatProperty(
        name='[D] Step X', description='Step length X (draft mode)',
        default=1.0, update=updateNode)

    stepy_draft: FloatProperty(
        name='[D] Step Y', description='Step length Y (draft mode)',
        default=1.0, update=updateNode)

    center: BoolProperty(
        name='Center', description='Center the plane around origin',
        default=False, update=updateNode)

    sizex: FloatProperty(
        name='Size X', description='Plane size along X',
        default=10.0, min=0.01, update=updateNode)

    sizey: FloatProperty(
        name='Size Y', description='Plane size along Y',
        default=10.0, min=0.01, update=updateNode)

    sizex_draft: FloatProperty(
        name='[D] Size X', description='Plane size along X (draft mode)',
        default=1.0, update=updateNode)

    sizey_draft: FloatProperty(
        name='[D] Size Y', description='Plane size along y (draft mode)',
        default=1.0, update=updateNode)

    draft_properties_mapping = dict(
            numx = 'numx_draft',
            numy = 'numy_draft',
            stepx = 'stepx_draft',
            stepy = 'stepy_draft',
            sizex = 'sizex_draft',
            sizey = 'sizey_draft'
        )

    list_match_global: EnumProperty(
        name="Match Global",
        description="Behavior on different list lengths, multiple objects level",
        items=list_match_modes, default="REPEAT",
        update=updateNode)
    list_match_local: EnumProperty(
        name="Match Local",
        description="Behavior on different list lengths, object level",
        items=list_match_modes, default="REPEAT",
        update=updateNode)

    correct_output: EnumProperty(
        name="Simplify Output",
        description="Behavior on different list lengths, object level",
        items=correct_output_modes, default="FLAT",
        update=updateNode)

    out_np: BoolVectorProperty(
        name="Ouput Numpy",
        description="Output NumPy arrays",
        default=(False, False, False),
        size=3, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "Size X").prop_name = 'sizex'
        self.inputs.new('SvStringsSocket', "Size Y").prop_name = 'sizey'
        self.inputs.new('SvStringsSocket', "Num X").prop_name = 'numx'
        self.inputs.new('SvStringsSocket', "Num Y").prop_name = 'numy'
        self.inputs.new('SvStringsSocket', "Step X").prop_name = 'stepx'
        self.inputs.new('SvStringsSocket', "Step Y").prop_name = 'stepy'
        self.inputs['Step X'].hide_safe = True
        self.inputs['Step Y'].hide_safe = True
        self.inputs.new('SvMatrixSocket', "Matrix")

        self.outputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvStringsSocket', "Edges")
        self.outputs.new('SvStringsSocket', "Polygons")

    def migrate_props_pre_relink(self, old_node):
        if old_node.normalize:
            if old_node.inputs["Step X"].is_linked or old_node.inputs["Step Y"].is_linked:
                self.dimension_mode = "SIZE_STEPS"
            else:
                self.dimension_mode = "SIZE"
        else:
            if old_node.inputs["Step X"].is_linked or old_node.inputs["Step Y"].is_linked:
                self.dimension_mode = 'STEPS'
            else:
                self.dimension_mode = 'NUMBER'

    def draw_buttons(self, context, layout):
        col = layout.column()
        row = col.row(align=True)
        row.prop(self, "direction", expand=True)
        row = col.row(align=True)
        row.prop(self, "dimension_mode", expand=True)
        col.prop(self, "center", toggle=False)

    def draw_buttons_ext(self, context, layout):
        '''draw buttons on the N-panel'''
        layout.prop(self, "center")
        layout.label(text="Simplify Output:")
        layout.prop(self, "correct_output", expand=True)

        layout.separator()
        layout.label(text="List Match:")
        layout.prop(self, "list_match_global", text="Global Match", expand=False)
        layout.prop(self, "list_match_local", text="Local Match", expand=False)

        layout.label(text="Ouput Numpy:")
        r = layout.row()
        for i in range(3):
            r.prop(self, "out_np", index=i, text=socket_names[i], toggle=True)

    def rclick_menu(self, context, layout):
        '''right click sv_menu items'''
        layout.prop_menu_enum(self, "center", text="Origin")
        layout.prop_menu_enum(self, "correct_output", text="Simplify Output")
        layout.prop_menu_enum(self, "list_match_global", text="List Match Global")
        layout.prop_menu_enum(self, "list_match_local", text="List Match Local")
        layout.label(text="Ouput Numpy:")

        for i in range(3):
            layout.prop(self, "out_np", index=i, text=socket_names[i], toggle=True)

    def get_data(self):
        inputs = self.inputs
        if self.dimension_mode == 'SIZE':
            params = [inputs['Size X'].sv_get(), inputs['Size Y'].sv_get()]
        elif self.dimension_mode == 'NUMBER':
            params = [inputs['Step X'].sv_get(), inputs['Step Y'].sv_get()]
        elif self.dimension_mode == 'STEPS':
            params = [inputs['Step X'].sv_get(default=[[1.0]]), inputs['Step Y'].sv_get(default=[[1.0]])]
        else:
            params=[inputs['Step X'].sv_get(default=[[1.0]])]
            params.append(inputs['Step Y'].sv_get(default=[[1.0]]))
            params.append(inputs['Size X'].sv_get())
            params.append(inputs['Size Y'].sv_get())

        if self.dimension_mode in ('SIZE', 'NUMBER'):
            for socket in inputs[2: 4]:
                params.append([[int(v) for v in l] for l in socket.sv_get()])

        mat_input = inputs['Matrix'].sv_get(default=[[Matrix()]])
        if type(mat_input[0]) == Matrix:
            params.append([[m] for m in mat_input])
        else:
            params.append(mat_input)

        return list_match_func[self.list_match_global](params)

    def does_support_draft_mode(self):
        return True

    def draw_label(self):
        label = self.label or self.name
        if self.id_data.sv_draft:
            label = "[D] " + label
        return label

    def process(self):

        outputs = self.outputs

        if not any(s.is_linked for s in outputs):
            return

        data_in = self.get_data()

        verts_out, edges_out, pols_out = [], [], []
        flags = [s.is_linked for s in outputs]
        output_numpy = [b for b in self.out_np]
        ops = [self.center, self.list_match_local, self.direction]


        plane_func = plane_func_dict[self.dimension_mode]
        for params in zip(*data_in):
            v_obj, e_obj, p_obj = plane_func(params, ops, flags)

            if self.correct_output == 'FLAT':
                extend_lists(
                    numpy_check([v_obj, e_obj, p_obj], output_numpy),
                    [verts_out, edges_out, pols_out])

            else:
                if self.correct_output == 'JOIN':
                    v_obj, e_obj, p_obj = mesh_join_np(v_obj, e_obj, p_obj)
                append_lists(
                    numpy_check([v_obj, e_obj, p_obj], output_numpy),
                    [verts_out, edges_out, pols_out])


        outputs['Vertices'].sv_set(verts_out)
        outputs['Edges'].sv_set(edges_out)
        outputs['Polygons'].sv_set(pols_out)


def register():
    bpy.utils.register_class(SvPlaneNodeMk3)


def unregister():
    bpy.utils.unregister_class(SvPlaneNodeMk3)
