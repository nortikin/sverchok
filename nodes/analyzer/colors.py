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
from bpy.props import StringProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (updateNode, match_long_cycle)


class SvVertexColorNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Vertex Colors '''
    bl_idname = 'SvVertexColorNode'
    bl_label = 'Vertex colors'
    bl_icon = 'OUTLINER_OB_EMPTY'

    vertex_color = StringProperty(default='', description='vert group',
                                  update=updateNode)

    def draw_buttons(self, context,   layout):
        ob = self.inputs['Objects'].sv_get()[0]
        col = layout.column()
        if self.inputs['Objects'].sv_get()[0].type == 'MESH':
            col.prop_search(self, 'vertex_color', ob.data, "vertex_colors", text="")

    modes = [
        ("VERT", " v ", "Vcol", 1),
        ("POLY", " p ", "Pcol", 2)
    ]

    mode = EnumProperty(items=modes,
                        default='VERT',
                        update=updateNode)

    def draw_buttons_ext(self, context, layout):
        layout.label("Search mode:")
        layout.prop(self, "mode", expand=True)

    def sv_init(self, context):
        self.inputs.new('SvObjectSocket', 'Objects')
        self.inputs.new('StringsSocket', "Index")
        self.inputs.new('VerticesSocket', "Color")

    def process(self):

        objm = self.inputs['Objects'].sv_get()[0].data
        objm.update()
        if not objm.vertex_colors:
            objm.vertex_colors.new(name='Sv_VColor')
        if self.vertex_color not in objm.vertex_colors:
            return

        ovgs = objm.vertex_colors.get(self.vertex_color)
        obpol = objm.polygons

        if self.inputs['Color'].is_linked:
            colors = self.inputs['Color'].sv_get()[0]

            if self.mode == 'VERT':

                if self.inputs['Index'].is_linked:
                    idxs = self.inputs['Index'].sv_get()[0]
                else:
                    idxs = [i.index for i in objm.vertices]
                lidx = len(idxs)

                if lidx > len(colors):
                    idxs, colors = match_long_cycle([idxs, colors])

                g = 0
                while g < lidx:
                    i = 0
                    for poly in objm.polygons:
                        for idx in poly.loop_indices:
                            loop = objm.loops[idx]
                            v = loop.vertex_index
                            if idxs[g] == v:
                                ovgs.data[i].color = colors[g]
                            i += 1
                    g = g+1

            if self.mode == 'POLY':

                if self.inputs['Index'].is_linked:
                    idxs = self.inputs['Index'].sv_get()[0]
                else:
                    idxs = [i.index for i in obpol]
                lidx = len(idxs)

                if lidx > len(colors):
                    idxs, colors = match_long_cycle([idxs, colors])

                g = 0
                while g < lidx:
                    for loop_index in range(obpol[idxs[g]].loop_start, obpol[idxs[g]].loop_start + obpol[idxs[g]].loop_total):
                        ovgs.data[loop_index].color = colors[g]
                    g = g+1


def register():
    bpy.utils.register_class(SvVertexColorNode)


def unregister():
    bpy.utils.unregister_class(SvVertexColorNode)
