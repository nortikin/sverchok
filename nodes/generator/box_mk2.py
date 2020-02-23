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
from bpy.props import IntProperty, FloatProperty, EnumProperty, BoolVectorProperty
from mathutils import Matrix
import numpy as np

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, list_match_func, list_match_modes

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

def matrix_apply_np(verts, matrix):
    '''taken from https://blender.stackexchange.com/a/139517'''

    verts_co_4d = np.ones(shape=(verts.shape[0], 4), dtype=np.float)
    verts_co_4d[:, :-1] = verts  # cos v (x,y,z,1) - point,   v(x,y,z,0)- vector
    return np.einsum('ij,aj->ai', matrix, verts_co_4d)[:, :-1]

def numpy_cube(params, origin, flags):
    '''
    based on zeffii inplementation at
    https://github.com/nortikin/sverchok/pull/2876#issuecomment-584556422
    '''
    size, divx, divy, divz, matrix = params
    get_verts, get_edges, get_faces = flags
    verts, edges, faces = [np.array([[]]) for i in range(3)]
    if get_verts:
        verts = make_verts(size, divx+1, divy+1, divz+1, matrix, origin)
    if get_edges or get_faces:
        edges, faces = make_edg_pol(divx+1, divy+1, divz+1, flags)
    return verts, edges, faces

def make_verts(size, x_verts, y_verts, z_verts, matrix, origin):
    '''creates cube verts, first vertical faces as a roll and after the bottom and top caps'''
    size_h = size/2
    if origin == 'CENTER':
        offset = [0, 0, 0]
    elif origin == 'BOTTOM':
        offset = [0, 0, size_h]
    else:
        offset = [size_h, size_h, size_h]

    sidex = np.linspace(-size_h + offset[0], size_h + offset[0], x_verts)
    sidey = np.linspace(-size_h + offset[1], size_h + offset[1], y_verts)
    sidez = np.linspace(-size_h + offset[2], size_h + offset[2], z_verts)

    z_spread = 2 * x_verts+ 2 * y_verts - 4

    roll = np.zeros((z_spread * z_verts, 3))
    row_id = np.arange(z_spread * z_verts) % z_spread

    plane_y1 = row_id < y_verts
    plane_x1 = np.all((y_verts-2 < row_id, row_id < y_verts + x_verts-1), axis=0)
    plane_y2 = np.all((y_verts + x_verts - 3 < row_id, row_id < z_spread - x_verts + 2), axis=0)
    plane_x2 = row_id > z_spread - x_verts + 1

    roll[:, 2] = np.repeat(sidez, z_spread)
    roll[plane_y1, 0] = sidex[0]
    roll[plane_y1, 1] = np.repeat(sidey, z_verts).reshape(-1, z_verts).T.flat

    roll[plane_x1, 0] = np.repeat(sidex, z_verts).reshape(-1, z_verts).T.flat
    roll[plane_x1, 1] = sidey[-1]

    roll[plane_y2, 0] = sidex[-1]
    roll[plane_y2, 1] = np.repeat(np.flip(sidey), z_verts).reshape(-1, z_verts).T.flat

    roll[plane_x2, 1] = sidey[0]
    roll[plane_x2, 0] = np.repeat(np.flip(sidex[1:-1]), z_verts).reshape(-1, z_verts).T.flat


    x_coords, y_coords = np.meshgrid(sidex[1:-1], sidey[1:-1], sparse=False, indexing='xy')
    z_coords = np.full(x_coords.shape, -size_h + offset[2])
    bottom = np.array([x_coords, y_coords, z_coords]).T.reshape(-1, 3)
    top = np.array([x_coords, y_coords, z_coords + size]).T.reshape(-1, 3)


    if not matrix == Matrix():
        return matrix_apply_np(np.concatenate([roll, bottom, top]), matrix)

    return np.concatenate([roll, bottom, top])

def create_cap_grid(outside, inside, x_verts, y_verts, num_iplanar):
    '''creates the bottom or top indices grid'''
    opposite = y_verts + (x_verts-2)
    if y_verts < 3:
        plane_grid = np.empty((x_verts, y_verts), 'i')
        plane_grid[0, :] = outside[0:y_verts]
        plane_grid[1:-1, 0] = np.flip(outside[x_verts+2:])
        plane_grid[1:-1, -1] = outside[2:x_verts]
        plane_grid[-1, :] = outside[opposite:opposite+y_verts][::-1]

    else:
        stride = y_verts-2
        np_id = np.arange(0, num_iplanar, stride)
        np_idx = np.arange(np_id.shape[0])
        sides1 = outside[-(np_idx + 1)]
        mid = inside.reshape(-1, stride)
        sides2 = outside[y_verts + np_idx]
        plane_grid = np.empty((x_verts, y_verts), 'i')
        plane_grid[0, :] = outside[0:y_verts]
        plane_grid[1:-1, 0] = sides1
        plane_grid[1:-1, 1:-1] = mid
        plane_grid[1:-1, -1] = sides2
        plane_grid[-1, :] = outside[opposite : opposite+y_verts][::-1]
    return plane_grid

def roll_around(direction, outside, inside, x_verts, y_verts, num_iplanar, flags):
    '''creates the bottom or top edges and faces'''
    _, get_edges, get_faces = flags
    cap_edges, cap_faces = [], np.empty((1, 4), 'i')
    plane_grid = create_cap_grid(outside, inside, x_verts, y_verts, num_iplanar)

    if get_faces:
        cap_faces = np.empty((x_verts-1, y_verts-1, 4), 'i')
        cap_faces[:, :, 0] = plane_grid[:-1, :-1]
        cap_faces[:, :, 1] = plane_grid[:-1, 1:]
        cap_faces[:, :, 2] = plane_grid[1:, 1:]
        cap_faces[:, :, 3] = plane_grid[1:, :-1]
        if direction == 'ccw':
            cap_faces = np.flip(cap_faces, axis=2)

    if get_edges:
        edg_x_dir = np.empty((x_verts-1, y_verts-2, 2), 'i')
        edg_x_dir[:, :, 0] = plane_grid[0:-1, 1:-1]
        edg_x_dir[:, :, 1] = plane_grid[1:, 1:-1]

        edg_y_dir = np.empty((x_verts-2, y_verts-1, 2), 'i')
        edg_y_dir[:, :, 0] = plane_grid[1:-1, :-1]
        edg_y_dir[:, :, 1] = plane_grid[1:-1, 1:]

        edge_num = (x_verts-1)* (y_verts-2) + (x_verts-2)*(y_verts-1)
        cap_edges = np.empty((edge_num, 2), 'i')
        cap_edges[:(x_verts - 1) * (y_verts - 2), :] = edg_x_dir.reshape(-1, 2)
        cap_edges[(x_verts - 1) * (y_verts - 2):, :] = edg_y_dir.reshape(-1, 2)


    return cap_edges, cap_faces.reshape(-1, 4)

def make_edges(x_verts, y_verts, z_verts, z_spread, grid, edg_top, edg_bottom):
    edges_roll = (z_verts*2 - 1) * z_spread
    edges_cap = (x_verts-1)* (y_verts-2) + (x_verts-2)*(y_verts-1)
    edges_num = edges_roll + 2 * edges_cap

    egd_roll = np.empty((z_verts*2-1, z_spread, 2), 'i')
    egd_roll[:z_verts, :, 0] = grid[:, : -1]
    egd_roll[:z_verts, :, 1] = grid[:, 1: ]

    egd_roll[z_verts:, :, 0] = grid[:-1, : -1]
    egd_roll[z_verts:, :, 1] = grid[1:, :-1]

    edges = np.empty((edges_num, 2), 'i')
    edges[:edges_roll] = egd_roll.reshape(-1, 2)
    edges[edges_roll: edges_roll + edges_cap] = edg_top
    edges[edges_roll+edges_cap:] = edg_bottom

    return edges

def make_edg_pol(x_verts, y_verts, z_verts, flags):
    _, get_edges, get_faces = flags

    edges = np.array([])

    z_spread = 2 * x_verts+ 2 * y_verts - 4

    roll_faces_n = (z_verts - 1) * z_spread
    cap_faces = (x_verts-1) * (y_verts-1)
    num_faces = roll_faces_n + 2 * (cap_faces)

    grid = np.empty((z_verts, z_spread + 1), 'i')
    grid[:, : -1] = np.arange(z_spread * z_verts).reshape(z_verts, z_spread)
    grid[:, -1] = grid[:, 0]

    if get_faces:
        all_faces = np.empty((num_faces, 4), 'i')
        roll_faces = np.zeros((z_verts-1, z_spread, 4))
        roll_faces[:, :, 0] = grid[1:, :-1]
        roll_faces[:, :, 1] = grid[1:, 1:]
        roll_faces[:, :, 2] = grid[:-1, 1:]
        roll_faces[:, :, 3] = grid[:-1, :-1]
        all_faces[:roll_faces_n, :] = roll_faces.reshape(-1, 4)
    else:
        all_faces = np.empty((1, 4), 'i')
        roll_faces_n = 0
        cap_faces = 0

    top_max = z_verts * z_spread
    bottom_outer_ring = np.arange(z_spread)
    top_outer_ring = np.arange(top_max-(z_spread), top_max)

    # num internal planar
    num_iplanar = (x_verts-2) * (y_verts-2)

    # book keeping
    num_verts_bass = x_verts * y_verts
    num_verts_ring_total = (z_verts - 2) * z_spread
    last_vertex_idx = (num_verts_bass * 2) + num_verts_ring_total

    top_internal = np.arange(last_vertex_idx - num_iplanar, last_vertex_idx)
    bottom_internal = top_internal - num_iplanar
    cap_init = roll_faces_n + cap_faces

    edg_top, all_faces[roll_faces_n : cap_init, :] = roll_around('ccw', top_outer_ring, top_internal, x_verts, y_verts, num_iplanar, flags)
    edg_bottom, all_faces[cap_init :, :] = roll_around('cw', bottom_outer_ring, bottom_internal, x_verts, y_verts, num_iplanar, flags)

    if get_edges:
        edges = make_edges(x_verts, y_verts, z_verts, z_spread, grid, edg_top, edg_bottom)

    return edges, all_faces

socket_names = ['Vertices', 'Edges', 'Polygons']

class SvBoxNodeMk2(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Box
    Tooltip: Generate a Box primitive.
    """

    bl_idname = 'SvBoxNodeMk2'
    bl_label = 'Box'
    bl_icon = 'MESH_CUBE'

    correct_output_modes = [
        ('NONE', 'None', 'Leave at multi-object level (Advanced)', 0),
        ('JOIN', 'Join', 'Join (mesh join) last level of boxes', 1),
        ('FLAT', 'Flat Output', 'Flat to object level', 2),
    ]
    origin_modes = [
        ('CENTER', 'Center', 'Origin at center of the box', 0),
        ('BOTTOM', 'Bottom', 'Origin at the bottom center of the box', 1),
        ('CORNER', 'Corner', 'Origin at the bottom left front corner of the box', 2),
    ]
    Divx: IntProperty(
        name='Divx', description='divisions x',
        default=1, min=1, options={'ANIMATABLE'},
        update=updateNode)

    Divy: IntProperty(
        name='Divy', description='divisions y',
        default=1, min=1, options={'ANIMATABLE'},
        update=updateNode)

    Divz: IntProperty(
        name='Divz', description='divisions z',
        default=1, min=1, options={'ANIMATABLE'},
        update=updateNode)

    Size: FloatProperty(
        name='Size', description='Size',
        default=1.0, options={'ANIMATABLE'},
        update=updateNode)

    origin: EnumProperty(
        name="Origin",
        description="Behavior on different list lengths, multiple objects level",
        items=origin_modes, default="CENTER",
        update=updateNode)

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
        self.inputs.new('SvStringsSocket', "Size").prop_name = 'Size'
        self.inputs.new('SvStringsSocket', "Divx").prop_name = 'Divx'
        self.inputs.new('SvStringsSocket', "Divy").prop_name = 'Divy'
        self.inputs.new('SvStringsSocket', "Divz").prop_name = 'Divz'
        self.inputs.new('SvMatrixSocket', "Matrix")
        self.outputs.new('SvVerticesSocket', "Vers")
        self.outputs.new('SvStringsSocket', "Edgs")
        self.outputs.new('SvStringsSocket', "Pols")

    def draw_buttons(self, context, layout):
        layout.prop(self, "origin", expand=False)

    def draw_buttons_ext(self, context, layout):
        '''draw buttons on the N-panel'''
        layout.prop(self, "origin", expand=True)
        layout.label(text="Simplify Output:")
        layout.prop(self, "correct_output", expand=True)

        layout.separator()
        layout.label(text="List Match:")
        layout.prop(self, "list_match_global", text="Global Match", expand=False)

        layout.label(text="Ouput Numpy:")
        r = layout.row()
        for i in range(3):
            r.prop(self, "out_np", index=i, text=socket_names[i], toggle=True)

    def rclick_menu(self, context, layout):
        '''right click sv_menu items'''
        layout.prop_menu_enum(self, "origin", text="Origin")
        layout.prop_menu_enum(self, "correct_output", text="Simplify Output")
        layout.prop_menu_enum(self, "list_match_global", text="List Match Global")
        layout.prop_menu_enum(self, "list_match_local", text="List Match Local")
        layout.label(text="Ouput Numpy:")

        for i in range(3):
            layout.prop(self, "out_np", index=i, text=socket_names[i], toggle=True)
    def get_data(self):
        inputs = self.inputs

        params = [inputs['Size'].sv_get()]

        for socket in inputs[1: 4]:
            params.append([[int(v) for v in l] for l in socket.sv_get()])

        mat_input = inputs['Matrix'].sv_get(default=[[Matrix()]])
        if type(mat_input[0]) == Matrix:
            params.append([[m] for m in mat_input])
        else:
            params.append(mat_input)

        return list_match_func[self.list_match_global](params)

    def process(self):

        outputs = self.outputs

        if not any(s.is_linked for s in outputs):
            return

        data_in = self.get_data()

        verts_out, edges_out, pols_out = [], [], []
        flags = [s.is_linked for s in outputs]
        output_numpy = [b for b in self.out_np]

        for params in zip(*data_in):
            m_par = list_match_func[self.list_match_local](params)
            v_obj, e_obj, p_obj = [], [], []

            for local_p in zip(*m_par):
                verts, edgs, pols = numpy_cube(local_p, self.origin, flags)
                append_lists([verts, edgs, pols], [v_obj, e_obj, p_obj])


            if self.correct_output == 'FLAT':
                extend_lists(
                    numpy_check([v_obj, e_obj, p_obj], output_numpy),
                    [verts_out, edges_out, pols_out])

            else:
                if self.correct_output == 'JOIN':
                    mesh = mesh_join_np(v_obj, e_obj, p_obj)
                append_lists(
                    numpy_check(mesh, output_numpy),
                    [verts_out, edges_out, pols_out])


        outputs['Vers'].sv_set(verts_out)
        outputs['Edgs'].sv_set(edges_out)
        outputs['Pols'].sv_set(pols_out)


def register():
    bpy.utils.register_class(SvBoxNodeMk2)


def unregister():
    bpy.utils.unregister_class(SvBoxNodeMk2)
