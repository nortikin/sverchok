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

from ast import literal_eval

import numpy as np

import bpy
from bpy.props import BoolProperty, StringProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (updateNode)





class SvObjectToMeshNode(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvObjectToMeshNode'
    bl_label = 'Objects to Mesh'
    bl_icon = 'OUTLINER_OB_EMPTY'

    modifiers = BoolProperty(
        name='Modifiers',
        description='Apply modifier geometry to import (original untouched)',
        default=False,
        update=updateNode)
    sort = BoolProperty(
        name='sort by name',
        description='sorting inserted objects by names',
        default=True,
        update=updateNode)

    def sv_init(self, context):
        self.inputs.new("SvObjectSocket", "Objects")
        self.outputs.new('VerticesSocket', "Vertices", "Vertices")
        self.outputs.new('StringsSocket', "Edges", "Edges")
        self.outputs.new('StringsSocket', "Polygons", "Polygons")
        self.outputs.new('MatrixSocket', "Matrixes", "Matrixes")

    def draw_buttons(self, context, layout):
        row = layout.row()
        row = layout.row(align=True)
        row.prop(self, 'groupname', text='')
        row.prop(self, 'sort', text='Sort objects')
        
        row = layout.row(align=True)
        row.prop(self, "modifiers", text="Post modifiers")
        row.prop(self, "vergroups", text="Vert groups")
        
            
    def process(self):
        objs = self.inputs[0].sv_get()

        edgs_out = []
        vers_out = []
        vers_out_grouped = []
        pols_out = []
        mtrx_out = []
        for obj in objs:  # objects
            print(obj)
            edgs = []
            vers = []
            vers_grouped = []
            pols = []
            mtrx = []
            if obj.type == 'EMPTY':
                for m in obj.matrix_world:
                    mtrx.append(m[:])
            else:
                scene = bpy.context.scene
                settings = 'PREVIEW'
                # create a temporary mesh
                obj_data = obj.to_mesh(scene, self.modifiers, settings)

                for m in obj.matrix_world:
                    mtrx.append(list(m))
                for v in obj_data.vertices:
                    vers.append(v.co[:])
                edgs = obj_data.edge_keys
                for p in obj_data.polygons:
                    pols.append(p.vertices[:])
                # remove the temp mesh
                bpy.data.meshes.remove(obj_data)

            edgs_out.append(edgs)
            vers_out.append(vers)
            vers_out_grouped.append(vers_grouped)
            pols_out.append(pols)
            mtrx_out.append(mtrx)

        data_out = [vers_out, edgs_out, pols_out, mtrx_out]
        for s,d in zip(self.outputs, data_out):
            if s.is_linked:
                s.sv_set(d)


def register():
    bpy.utils.register_class(SvObjectToMeshNode)


def unregister():
    bpy.utils.unregister_class(SvObjectToMeshNode)


