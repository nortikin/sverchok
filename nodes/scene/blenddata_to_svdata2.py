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
from bpy.props import BoolProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (updateNode)


class SvObjectToMeshNodeMK2(bpy.types.Node, SverchCustomTreeNode):
    '''Get Object Data'''
    bl_idname = 'SvObjectToMeshNodeMK2'
    bl_label = 'Object ID Out MK2'
    bl_icon = 'OUTLINER_OB_EMPTY'

    modifiers = BoolProperty(name='Modifiers', default=False, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvObjectSocket', "Objects")
        self.outputs.new('VerticesSocket', "Vertices")
        self.outputs.new('VerticesSocket', "VertexNormals")
        self.outputs.new('StringsSocket', "Edges")
        self.outputs.new('StringsSocket', "Polygons")
        self.outputs.new('StringsSocket', "PolygonAreas")
        self.outputs.new('VerticesSocket', "PolygonCenters")
        self.outputs.new('VerticesSocket', "PolygonNormals")
        self.outputs.new('MatrixSocket', "Matrices")

    def draw_buttons(self, context, layout):
        row = layout.row()
        row.prop(self, "modifiers", text="Post modifiers")

    def process(self):
        objs = self.inputs[0].sv_get()
        if isinstance(objs[0], list):
            objs = objs[0]
        o1,o2,o3,o4,o5,o6,o7,o8 = self.outputs
        vs,vn,es,ps,pa,pc,pn,ms = [],[],[],[],[],[],[],[]
        scene, mod = bpy.context.scene, self.modifiers
        ot = objs[0].type in ['MESH', 'CURVE', 'FONT', 'SURFACE', 'META']
        for obj in objs:
            if o8.is_linked:
                ms.append(obj.matrix_world)
            if ot:
                obj_data = obj.to_mesh(scene, mod, 'PREVIEW')
                if o1.is_linked:
                    vs.append([v.co[:] for v in obj_data.vertices])
                if o2.is_linked:
                    vn.append([v.normal[:] for v in obj_data.vertices])
                if o3.is_linked:
                    es.append(obj_data.edge_keys)
                if o4.is_linked:
                    ps.append([p.vertices[:] for p in obj_data.polygons])
                if o5.is_linked:
                    pa.append([p.area for p in obj_data.polygons])
                if o6.is_linked:
                    pc.append([p.center[:] for p in obj_data.polygons])
                if o7.is_linked:
                    pn.append([p.normal[:] for p in obj_data.polygons])
                bpy.data.meshes.remove(obj_data)
        for i,i2 in zip(self.outputs, [vs,vn,es,ps,pa,pc,pn,ms]):
            if i.is_linked:
                i.sv_set(i2)


def register():
    bpy.utils.register_class(SvObjectToMeshNodeMK2)


def unregister():
    bpy.utils.unregister_class(SvObjectToMeshNodeMK2)
