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

from random import random
import numpy as np

import bpy
from bpy.props import StringProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode


class SvObjDupliOperator(bpy.types.Operator):
    bl_idname = 'node.sv_fdp_center_child'
    bl_label = "Center Child"

    name_child = StringProperty()

    def execute(self, context):
        ref = bpy.data.objects.get(self.name_child)
        if ref:
            ref.location = 0, 0, 0
            return {'FINISHED'}
        return {'CANCELLED'}


class SvObjDuplivertOne(bpy.types.Node, SverchCustomTreeNode):
    ''' sv Object Duplivert'''
    bl_idname = 'SvObjDuplivertOne'
    bl_label = 'Duplivert Node'
    bl_icon = 'OUTLINER_OB_EMPTY'

    name_parent = StringProperty(
        description="obj's verts are used to duplicate child")  # , update=updateNode)
    name_child = StringProperty(
        description="name of object to duplicate")  # ,  update=updateNode)

    def sv_init(self, context):
        self.inputs.new("SvObjectSocket", "Parent")
        self.inputs.new("SvObjectSocket", "Child")
        self.inputs.new("VerticesSocket", "Rotations")

    def draw_buttons(self, context, layout):
        col = layout.column()
        # col.prop_search(self, 'name_parent', bpy.data, 'objects', text='parent')

        if self.name_child and self.name_parent:
            ob = bpy.data.objects[self.name_parent]

            layout.prop(ob, "dupli_type", expand=True)

            if ob.dupli_type == 'FRAMES':
                split = layout.split()

                col = split.column(align=True)
                col.prop(ob, "dupli_frames_start", text="Start")
                col.prop(ob, "dupli_frames_end", text="End")

                col = split.column(align=True)
                col.prop(ob, "dupli_frames_on", text="On")
                col.prop(ob, "dupli_frames_off", text="Off")

                layout.prop(ob, "use_dupli_frames_speed", text="Speed")

            elif ob.dupli_type == 'VERTS':
                layout.prop(ob, "use_dupli_vertices_rotation", text="Rotation")

            elif ob.dupli_type == 'FACES':
                row = layout.row()
                row.prop(ob, "use_dupli_faces_scale", text="Scale")
                sub = row.row()
                sub.active = ob.use_dupli_faces_scale
                sub.prop(ob, "dupli_faces_scale", text="Inherit Scale")

            elif ob.dupli_type == 'GROUP':
                layout.prop(ob, "dupli_group", text="Group")

        col.separator()
        op_one = col.operator('node.sv_fdp_center_child', text='Center Child')
        op_one.name_child = self.name_child

    def update(self):
        # if disconnected, the node needs one last update.
        p = self.inputs['Parent'].sv_get()
        c = self.inputs['Child'].sv_get()

        if not (p or c):
            self.process()

        if not (p and c):
            self.name_child = ''
            self.name_parent = ''

    def process(self):
        objects = bpy.data.objects

        p = self.inputs['Parent'].sv_get()[0]
        c = self.inputs['Child'].sv_get()[0]
        print('parent:', p)
        print('child:', c)

        if (p and c):
            self.name_parent = p.name
            self.name_child = c.name
            c.parent = p

            if p.use_dupli_vertices_rotation:
                print('Child uses dupli verts!')
                val = self.inputs['Rotations'].sv_get()[0]
                if val:
                    verts = p.data.vertices

                    if not (len(val) == len(verts)):
                        print("sizes don't match", len(val), len(verts))
                        return
                else:
                    print('no array')
                    return

                # reaches here iff each parent vertex has a matching rotation vertex
                for v, norm in zip(verts, val):
                    v.normal = tuple(norm[:3])

        if (not p) and c:
            c.parent = None
            self.name_parent = ''

        if p and (not c):
            self.name_parent = p.name
            self.name_child = ''


def register():
    bpy.utils.register_class(SvObjDuplivertOne)
    bpy.utils.register_class(SvObjDupliOperator)


def unregister():
    bpy.utils.unregister_class(SvObjDupliOperator)
    bpy.utils.unregister_class(SvObjDuplivertOne)
