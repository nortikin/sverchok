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

import numpy as np

import bpy
import bmesh
# import mathutils
# from mathutils import Vector
from bpy.props import FloatProperty, IntProperty, BoolProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata, pydata_from_bmesh

def faces_from_grid(grid, n1, n2):

    grid_faces = np.zeros((n1-1, n2-1, 4), 'i' )
    grid_faces[:, :, 0] = grid[:-1, 1:]
    grid_faces[:, :, 1] = grid[1:, 1:]
    grid_faces[:, :, 2] = grid[1:, :-1]
    grid_faces[:, :, 3] = grid[:-1, :-1]

    return grid_faces.reshape(-1, 4)

def edges_from_grid(grid, n1, n2):
    edg_1_dir = np.empty((n1-1, n2, 2), 'i')
    edg_1_dir[:, :, 0] = grid[:-1, :]
    edg_1_dir[:, :, 1] = grid[1:, :]

    edg_2_dir = np.empty((n1, n2-1, 2), 'i')
    edg_2_dir[:, :, 0] = grid[:, :-1]
    edg_2_dir[:, :, 1] = grid[:, 1:]

    edge_num = (n1-1)* (n2) + (n1)*(n2-1)
    edges = np.empty((edge_num, 2), 'i')
    edges[:(n1 - 1) * (n2), :] = edg_1_dir.reshape(-1, 2)
    edges[(n1 - 1) * (n2):, :] = edg_2_dir.reshape(-1, 2)
    return edges

def field_faces_and_edges(xdim, ydim, zdim, get_edges, get_faces):
    xoz_grid = np.arange(xdim * zdim, dtype='i').reshape(xdim, zdim)
    xoy_grid = np.arange(0, xdim * ydim * zdim, zdim, dtype='i').reshape(ydim, xdim)
    z_range = np.arange(zdim, dtype='i')
    yoz_grid = np.concatenate([z_range + (xdim * zdim) * i for i in range(ydim)]).reshape(ydim, zdim)
    edges, faces = [], []
    if get_faces:
        xoz_faces = faces_from_grid(xoz_grid, xdim, zdim)
        all_xoz_faces = np.concatenate([xoz_faces + (xdim * zdim) * i for i in range(ydim)])
        xoy_faces = faces_from_grid(xoy_grid, ydim, xdim)
        all_xoy_faces = np.concatenate([xoy_faces + i for i in range(zdim)])
        yoz_faces = faces_from_grid(yoz_grid, ydim, zdim)
        all_yoz_faces = np.concatenate([yoz_faces + zdim * i for i in range(xdim)])
        faces = np.concatenate([all_xoz_faces, all_xoy_faces, all_yoz_faces]).tolist()

    if get_edges:
        xoz_edges = edges_from_grid(xoz_grid, xdim, zdim)
        all_xoz_edges = np.concatenate([xoz_edges + (xdim * zdim) * i for i in range(ydim)])
        xoy_edges = edges_from_grid(xoy_grid, ydim, xdim)
        all_xoy_edges = np.concatenate([xoy_edges + i for i in range(zdim)])
        yoz_edges = edges_from_grid(yoz_grid, ydim, zdim)
        all_yoz_edges = np.concatenate([yoz_edges + zdim * i for i in range(xdim)])
        edges = np.concatenate([all_xoz_edges, all_xoy_edges, all_yoz_edges]).tolist()

    return edges, faces


class SvHomogenousVectorField(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: hv 3d vector grid
    Tooltip: Evenly spaced vector field.
    """
    bl_idname = 'SvHomogenousVectorField'
    bl_label = 'Vector P Field'
    sv_icon = 'SV_VECTOR_P_FIELD'

    xdim__: IntProperty(name='N Verts X', default=2, min=1, update=updateNode)
    ydim__: IntProperty(name='N Verts Y', default=3, min=1, update=updateNode)
    zdim__: IntProperty(name='N Verts Z', default=4, min=1, update=updateNode)
    sizex__: FloatProperty(name='Size X', default=1.0, min=.01, update=updateNode)
    sizey__: FloatProperty(name='Size Y', default=1.0, min=.01, update=updateNode)
    sizez__: FloatProperty(name='Size Z', default=1.0, min=.01, update=updateNode)
    seed: IntProperty(name='Seed', default=0, min=0, update=updateNode)

    randomize_factor: FloatProperty(
        name='Randomize',
        default=0.0, min=0.0,
        description='Distance to displace vectors randomly',
        update=updateNode)

    rm_doubles_distance: FloatProperty(
        name='Merge distance',
        default=0.0,
        description='Vectors closer than this will be merged',
        update=updateNode)

    output_numpy: BoolProperty(
        name='Output NumPy',
        description='Output NumPy arrays',
        default=False, update=updateNode)

    def sv_init(self, context):
        snew = self.inputs.new
        snew("SvStringsSocket", "xdim").prop_name = 'xdim__'
        snew("SvStringsSocket", "ydim").prop_name = 'ydim__'
        snew("SvStringsSocket", "zdim").prop_name = 'zdim__'
        snew("SvStringsSocket", "size x").prop_name = 'sizex__'
        snew("SvStringsSocket", "size y").prop_name = 'sizey__'
        snew("SvStringsSocket", "size z").prop_name = 'sizez__'

        self.outputs.new("SvVerticesSocket", "verts")
        self.outputs.new("SvStringsSocket", "edges")
        self.outputs.new("SvStringsSocket", "faces")

    def draw_buttons(self, context, layout):
        col = layout.column(align=True)
        col.prop(self, 'randomize_factor')
        col.prop(self, 'rm_doubles_distance')
        col.prop(self, 'seed')

    def draw_buttons_ext(self, ctx, layout):
        self.draw_buttons(ctx, layout)
        layout.prop(self, "output_numpy", toggle=False)

    def rclick_menu(self, context, layout):
        layout.prop(self, "output_numpy", toggle=True)

    def process(self):
        if not self.outputs[0].is_linked:
            return
        params = match_long_repeat([s.sv_get(deepcopy=False)[0] for s in self.inputs])
        get_faces = 'faces' in self.outputs and self.outputs['faces'].is_linked
        get_edges = 'edges' in self.outputs and self.outputs['edges'].is_linked
        verts_out, edges_out, faces_out = [], [], []

        for xdim, ydim, zdim, *size in zip(*params):
            hs0 = size[0] / 2
            hs1 = size[1] / 2
            hs2 = size[2] / 2

            x_ = np.linspace(-hs0, hs0, xdim)
            y_ = np.linspace(-hs1, hs1, ydim)
            z_ = np.linspace(-hs2, hs2, zdim)

            v_field = np.vstack(np.meshgrid(x_, y_, z_)).reshape(3, -1).T
            num_items = v_field.shape[0]* v_field.shape[1]

            if self.randomize_factor > 0.0:
                np.random.seed(self.seed)
                v_field += (np.random.normal(0, 0.5, num_items) * self.randomize_factor).reshape(3, -1).T

            if get_faces or get_edges:
                edges, faces = field_faces_and_edges(xdim, ydim, zdim, get_edges, get_faces)
            else:
                faces, edges = [], []
            if self.rm_doubles_distance > 0.0:
                bm = bmesh_from_pydata(v_field.tolist(), edges, faces)
                bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=self.rm_doubles_distance)
                if self.output_numpy:
                    verts_out.append(np.array([v.co for v in bm.verts]))
                    faces_out.append([[e.verts[0].index, e.verts[1].index] for e in bm.edges])
                    edges_out.append([[i.index for i in p.verts] for p in bm.faces])
                else:
                    v_field, _, faces = pydata_from_bmesh(bm)
                    faces_out.append(faces)
                    edges_out.append(edges)
                    verts_out.append(v_field)
            else:
                verts_out.append(v_field if self.output_numpy else v_field.tolist())
                edges_out.append(edges)
                faces_out.append(faces)

        if verts_out:
            self.outputs['verts'].sv_set(verts_out)
        if get_edges:
            self.outputs['edges'].sv_set(edges_out)
        if get_faces:
            self.outputs['faces'].sv_set(faces_out)

def register():
    bpy.utils.register_class(SvHomogenousVectorField)


def unregister():
    bpy.utils.unregister_class(SvHomogenousVectorField)
