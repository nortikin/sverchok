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
from sverchok.utils.nodes_mixins.sv_animatable_nodes import SvAnimatableNode
from sverchok.data_structure import (updateNode)
from sverchok.core.handlers import get_sv_depsgraph, set_sv_depsgraph_need

class SvObjectToMeshNodeMK2(bpy.types.Node, SverchCustomTreeNode, SvAnimatableNode):
    '''Get Object Data'''
    bl_idname = 'SvObjectToMeshNodeMK2'
    bl_label = 'Object ID Out MK2'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_OBJECT_ID_OUT'

    def modifiers_handle(self, context):
        set_sv_depsgraph_need(self.modifiers)
        updateNode(self, context)

    modifiers: BoolProperty(name='Modifiers', default=False, update=modifiers_handle)

    def sv_init(self, context):
        self.inputs.new('SvObjectSocket', "Objects")
        self.outputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvVerticesSocket', "VertexNormals")
        self.outputs.new('SvStringsSocket', "Edges")
        self.outputs.new('SvStringsSocket', "Polygons")
        self.outputs.new('SvStringsSocket', "PolygonAreas")
        self.outputs.new('SvVerticesSocket', "PolygonCenters")
        self.outputs.new('SvVerticesSocket', "PolygonNormals")
        self.outputs.new('SvMatrixSocket', "Matrices")

    def draw_buttons(self, context, layout):
        self.animatable_buttons(layout, icon_only=True)
        row = layout.row()
        row.prop(self, "modifiers", text="Post modifiers")

    def sv_free(self):
        set_sv_depsgraph_need(False)

    def process(self):
        objs = self.inputs[0].sv_get()
        if isinstance(objs[0], list):
            objs = objs[0]

        o1,o2,o3,o4,o5,o6,o7,o8 = self.outputs
        vs,vn,es,ps,pa,pc,pn,ms = [],[],[],[],[],[],[],[]
        
        if self.modifiers:
            sv_depsgraph = get_sv_depsgraph()

        ot = objs[0].type in ['MESH', 'CURVE', 'FONT', 'SURFACE', 'META']
        for obj in objs:

            with self.sv_throttle_tree_update():

                if o8.is_linked:
                    ms.append(obj.matrix_world)

                if ot:
                    if self.modifiers:
                        obj = sv_depsgraph.objects[obj.name]
                        obj_data = obj.to_mesh(preserve_all_data_layers=True, depsgraph=sv_depsgraph)
                    else:
                        obj_data = obj.to_mesh()
                    
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
                    
                    obj.to_mesh_clear()

        for i,i2 in zip(self.outputs, [vs,vn,es,ps,pa,pc,pn,ms]):
            if i.is_linked:
                i.sv_set(i2)


def register():
    bpy.utils.register_class(SvObjectToMeshNodeMK2)


def unregister():
    bpy.utils.unregister_class(SvObjectToMeshNodeMK2)
