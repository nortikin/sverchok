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

# from ast import literal_eval

import bpy
from bpy.props import BoolProperty, StringProperty, EnumProperty

import sverchok
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode


class SvObjLiteCallback(bpy.types.Operator):
    """ GET / Reject object callback"""
    bl_idname = "node.sverchok_objectinlite_cb"
    bl_label = "Sverchok object in lite callback"
    bl_options = {'REGISTER', 'UNDO'}

    cmd = StringProperty()

    def execute(self, context):
        getattr(context.node, self.cmd)()
        return {'FINISHED'}


class SvObjInLite(bpy.types.Node, SverchCustomTreeNode):
    ''' Objects Input Lite'''
    bl_idname = 'SvObjInLite'
    bl_label = 'Objects in Lite'
    bl_icon = 'OUTLINER_OB_EMPTY'

    modifiers = BoolProperty(
        description='Apply modifier geometry to import (original untouched)',
        name='Modifiers', default=False, update=updateNode)

    currently_storing = BoolProperty()
    obj_name = StringProperty(update=updateNode)
    node_dict = {}

    def drop(self):
        self.obj_name = ""
        self.currently_storing = False
        self.node_dict = {}

    def dget(self):
        obj = bpy.context.active_object
        if obj:
            self.obj_name = obj.name
            obj_data = obj.to_mesh(bpy.context.scene, self.modifiers, 'PREVIEW')
            self.node_dict[hash(self)] = {
                'verts': list([v.co[:] for v in obj_data.vertices]),
                'edges': obj_data.edge_keys,
                'faces': [list(p.vertices) for p in obj_data.polygons],
                'matrix': [list(m) for m in obj.matrix_world]
            }
            
            bpy.data.meshes.remove(obj_data)
            self.currently_storing = True

        else:
            self.report({'WARNING'}, 'No object selected')


    def sv_init(self, context):
        out = self.outputs.new
        out('VerticesSocket', "Vertices")
        out('StringsSocket', "Edges")
        out('StringsSocket', "Polygons")
        out('MatrixSocket', "Matrix")

    def draw_buttons(self, context, layout):
        addon = context.user_preferences.addons.get(sverchok.__name__)
        prefs = addon.preferences
        callback = 'node.sverchok_objectinlite_cb'

        col = layout.column(align=True)
        row = col.row()
        row.scale_y = 4.0 if prefs.over_sized_buttons else 1
        
        if not self.currently_storing:
            row.operator(callback, text='G E T').cmd = 'dget'
            layout.label('--None--')
        else:
            row.operator(callback, text='D R O P').cmd = 'drop'
            layout.label(self.obj_name)


    def process(self):

        if not hash(self) in self.node_dict:
            print('ending early, no node_dict')
            return
        else:
            print('not ending early')
            mesh_data = self.node_dict.get(hash(self))

        Vertices, Edges, Polygons, Matrix = self.outputs

        if Vertices.is_linked:
            Vertices.sv_set([mesh_data['verts']])
        if Edges.is_linked:
            Edges.sv_set([mesh_data['edges']])
        if Polygons.is_linked:
            Polygons.sv_set([mesh_data['faces']])
        if Matrix.is_linked:
            Matrix.sv_set([mesh_data['matrix']])


def register():
    bpy.utils.register_class(SvObjLiteCallback)
    bpy.utils.register_class(SvObjInLite)


def unregister():
    bpy.utils.unregister_class(SvObjInLite)
    bpy.utils.unregister_class(SvObjLiteCallback)
