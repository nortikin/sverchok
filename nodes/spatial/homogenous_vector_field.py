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

        verts = []
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

            if self.rm_doubles_distance > 0.0:
                bm = bmesh_from_pydata(v_field.tolist(), [], [])
                bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=self.rm_doubles_distance)
                if self.output_numpy:
                    verts.append(np.array([v.co for v in bm.verts]))
                else:
                    v_field, _, _ = pydata_from_bmesh(bm)
                    verts.append(v_field)
            else:
                verts.append(v_field if self.output_numpy else v_field.tolist())

        if verts:
            self.outputs['verts'].sv_set(verts)

def register():
    bpy.utils.register_class(SvHomogenousVectorField)


def unregister():
    bpy.utils.unregister_class(SvHomogenousVectorField)
