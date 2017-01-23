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
from bpy.props import EnumProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import dataCorrect
from sverchok.data_structure import updateNode

options = 'X Y Z -1 0 1 Scalar'.split(' ')
options2 = 'X Y Z'.split(' ')
mode_options = [(n, n, '', idx) for idx, n in enumerate(options)]
mode_options2 = [(n, n, '', idx) for idx, n in enumerate(options2)]

class SvVectorRewire(bpy.types.Node, SverchCustomTreeNode):
    ''' Rewire components of a vector'''
    bl_idname = 'SvVectorRewire'
    bl_label = 'Vector Rewire'
    bl_icon = 'OUTLINER_OB_EMPTY'

    selected_mode_from = EnumProperty(
        items=mode_options,
        description="offers....",
        default="X", update=updateNode
    )

    selected_mode_to = EnumProperty(
        items=mode_options2,
        description="offers....",
        default="Z", update=updateNode
    )

    scalar = FloatProperty(default=0.0, update=updateNode)
    
    def sv_init(self, context):
        self.inputs.new('VerticesSocket', "Vectors")
        self.inputs.new('StringsSocket', "Scalar").prop_name = "scalar"
        self.outputs.new('VerticesSocket', "Vectors")

    def draw_buttons(self, context, layout):
        row = layout.row(align=True)
        row.prop(self, 'selected_mode_from', text='')
        row.label(icon='ARROW_LEFTRIGHT')
        row.prop(self, 'selected_mode_to', text='')

    def process(self):
        vectors_in = self.inputs[0]
        scalar_in = self.inputs[1]
        vectors_out = self.outputs[0]

        if not all([vectors_out.is_linked, vectors_in.is_linked]):
            return
        
        xyz = vectors_in.sv_get()

        index_from = options.index(self.selected_mode_from)
        index_to = options.index(self.selected_mode_to)
        switching = (index_from, index_to)

        # for instance X->X  , return unprocessed
        if len(set(switching)) == 1:
            vectors_out.sv_set(xyz)
            return

        sorted_tuple = tuple(sorted(switching))
        rewire_dict = {(0, 1): (1, 0, 2), (0, 2): (2, 1, 0), (1, 2): (0, 2, 1)}
        
        series_vec = []
        for obj in xyz:

            if sorted_tuple in rewire_dict.keys():
                # handles xy xz yx yz zx zy
                x, y, z = rewire_dict.get(sorted_tuple)
                coords = ([v[x], v[y], v[z]] for v in obj)
                series_vec.append(list(coords))

            elif switching[0] in {3, 4, 5}:
                # handles -1 0 1 -> xyz
                value = {3: -1, 4: 0, 5: 1}.get(switching[0])
                if switching[1] == 0:
                    coords = ([value, v[1], v[2]] for v in obj)
                elif switching[1] == 1:
                    coords = ([v[0], value, v[2]] for v in obj)
                else:  # 2
                    coords = ([v[0], v[1], value] for v in obj)
                series_vec.append(list(coords))

            else switching[0] == 6:
                # handles socket s. -> xyz
                scalar_data = scalar_in.sv_get()
                if isinstance(scalar_data, list) and len(scalar_data) > 0:
                    


        vectors_out.sv_set(series_vec)                    


def register():
    bpy.utils.register_class(SvVectorRewire)


def unregister():
    bpy.utils.unregister_class(SvVectorRewire)
