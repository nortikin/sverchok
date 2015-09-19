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
import bmesh
from bpy.props import StringProperty, EnumProperty, BoolProperty, FloatVectorProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (updateNode, second_as_first_cycle)


class SvVertexColorNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Vertex Colors '''
    bl_idname = 'SvVertexColorNode'
    bl_label = 'Vertex colors'
    bl_icon = 'OUTLINER_OB_EMPTY'

    vertex_color = StringProperty(default='', update=updateNode)
    clear = BoolProperty(name='clear c', default=True, update=updateNode)
    clear_c = FloatVectorProperty(name='cl_color', subtype='COLOR', min=0, max=1, size=3, default=(0, 0, 0), update=updateNode)
    modes = [("vertices", " v ", "Vcol", 1), ("polygons", " p ", "Pcol", 2)]
    mode = EnumProperty(items=modes, default='vertices', update=updateNode)
    object_ref = StringProperty(default='', update=updateNode)

    def draw_buttons(self, context,   layout):
        layout.prop_search(self, 'object_ref', bpy.data, 'objects')
        ob = bpy.data.objects[self.object_ref]
        if ob.type == 'MESH':
            layout.prop_search(self, 'vertex_color', ob.data, "vertex_colors", text="")
            layout.prop(self, "mode", expand=True)

    def draw_buttons_ext(self, context, layout):
        row = layout.row(align=True)
        row.prop(self,    "clear",   text="clear unindexed")
        row.prop(self, "clear_c", text="")

    def sv_init(self, context):
        self.inputs.new('StringsSocket', "Index")
        self.inputs.new('VerticesSocket', "Color")

    def process(self):
        objm = bpy.data.objects[self.object_ref].data
        objm.update()
        if not objm.vertex_colors:
            objm.vertex_colors.new(name='Sv_VColor')
        if self.vertex_color not in objm.vertex_colors:
            return
        ovgs = objm.vertex_colors.get(self.vertex_color)
        Ind, Col = self.inputs
        if Col.is_linked:
            sm, colors = self.mode, Col.sv_get()[0]
            idxs = Ind.sv_get()[0] if Ind.is_linked else [i.index for i in getattr(objm,sm)]
            idxs, colors = second_as_first_cycle(idxs, colors)
            bm = bmesh.new()
            bm.from_mesh(objm)
            if self.clear:
                for i in ovgs.data:
                    i.color = self.clear_c
            if sm == 'vertices':
                bv = bm.verts[:]
                for i, i2 in zip(idxs, colors):
                    for i in bv[i].link_loops:
                        ovgs.data[i.index].color = i2
            elif sm == 'polygons':
                bf = bm.faces[:]
                for i, i2 in zip(idxs, colors):
                    for i in bf[i].loops:
                        ovgs.data[i.index].color = i2
            bm.free()


def register():
    bpy.utils.register_class(SvVertexColorNode)


def unregister():
    bpy.utils.unregister_class(SvVertexColorNode)
