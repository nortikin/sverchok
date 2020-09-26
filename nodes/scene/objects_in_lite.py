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
from bpy.props import BoolProperty, StringProperty, EnumProperty

import sverchok
from sverchok.utils.mesh_repr_utils import flatten, unflatten, generate_object
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode


import json

class SvObjLiteCallback(bpy.types.Operator):
    """ GET / Reject object callback"""
    bl_idname = "node.sverchok_objectinlite_cb"
    bl_label = "Sverchok object in lite callback"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    cmd: StringProperty()
    idname: StringProperty()
    idtree: StringProperty()

    def get_node(self):
        return bpy.data.node_groups[self.idtree].nodes[self.idname]    

    def execute(self, context):
        node = self.get_node()
        getattr(node, self.cmd)()
        node.process_node(context)
        return {'FINISHED'}


class SvObjInLite(bpy.types.Node, SverchCustomTreeNode):
    ''' Objects Input Lite'''
    bl_idname = 'SvObjInLite'
    bl_label = 'Objects in Lite'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_OBJECT_IN_LITE'

    modifiers: BoolProperty(
        description='Apply modifier geometry to import (original untouched)',
        name='Modifiers', default=False, update=updateNode)

    currently_storing: BoolProperty()
    obj_name: StringProperty(update=updateNode)
    node_dict = {}

    def drop(self):
        self.obj_name = ""
        self.currently_storing = False
        self.node_dict[hash(self)] = {}

    def dget(self, obj_name=None):
        if not obj_name:
            obj = bpy.context.active_object
            if not obj:
                self.error("No object selected")
                return
            self.obj_name = obj.name
        else:
            obj = bpy.data.objects.get(obj_name)

        if obj:
            with self.sv_throttle_tree_update():

                depsgraph = bpy.context.evaluated_depsgraph_get()
                deps_obj = depsgraph.objects[obj.name]

                if self.modifiers:
                    obj_data = deps_obj.to_mesh(depsgraph=depsgraph)
                else:
                    obj_data = deps_obj.original.to_mesh()

                self.node_dict[hash(self)] = {
                    'Vertices': list([v.co[:] for v in obj_data.vertices]),
                    'Edges': obj_data.edge_keys,
                    'Polygons': [list(p.vertices) for p in obj_data.polygons],
                    'MaterialIdx': [p.material_index for p in obj_data.polygons],
                    'Matrix': deps_obj.matrix_world
                }
                deps_obj.to_mesh_clear()
                self.currently_storing = True

        else:
            self.error("No object selected")


    def sv_init(self, context):
        out = self.outputs.new
        out('SvVerticesSocket', 'Vertices')
        out('SvStringsSocket', 'Edges')
        out('SvStringsSocket', 'Polygons')
        out('SvStringsSocket', 'MaterialIdx')
        out('SvMatrixSocket', 'Matrix')

    def draw_buttons(self, context, layout):
        addon = context.preferences.addons.get(sverchok.__name__)
        prefs = addon.preferences
        callback = 'node.sverchok_objectinlite_cb'

        col = layout.column(align=True)
        row = col.row(align=True)
        row.scale_y = 4.0 if prefs.over_sized_buttons else 1

        cb_text, cmd, display_text = [
            ("G E T", "dget", "--None--"),
            ("D R O P", "drop", self.obj_name)
        ][self.currently_storing]

        self.wrapper_tracked_ui_draw_op(row, callback, text=cb_text).cmd = cmd

        row.prop(self, 'modifiers', text='', icon='MODIFIER')
        layout.label(text=display_text)


    def pass_data_to_sockets(self):
        mesh_data = self.node_dict.get(hash(self))
        if mesh_data:
            for socket in self.outputs:
                if socket.is_linked:
                    socket.sv_set([mesh_data[socket.name]])

    def process(self):

        if not hash(self) in self.node_dict:
            if self.obj_name and bpy.data.objects.get(self.obj_name):
                self.dget(self.obj_name)
            else:
                self.debug('ending early, no node_dict')
                return

        self.pass_data_to_sockets()

    def load_from_json(self, node_data: dict, import_version: float):
        geom = node_data['geom']
        name = node_data['params']["obj_name"]
        geom_dict = json.loads(geom)

        if not geom_dict:
            print(self.name, 'contains no flatten geom')
            return

        unrolled_geom = unflatten(geom_dict)
        verts = unrolled_geom['Vertices']
        edges = unrolled_geom['Edges']
        polygons = unrolled_geom['Polygons']
        materials = unrolled_geom.get('MaterialIdx', [])
        matrix = unrolled_geom['Matrix']

        with self.sv_throttle_tree_update():
            bm = bmesh_from_pydata(verts, edges, polygons)
            if materials:
                for face, material in zip(bm.faces, materials):
                    face.material_index = material
            obj = generate_object(name, bm)
            obj.matrix_world = matrix

            # rename if obj existed
            if not obj.name == name:
                node_data['params']["obj_name"] = obj.name
                self.obj_name = obj.name

    def save_to_json(self, node_data: dict):
        # generate flat data, and inject into incoming storage variable
        obj = self.node_dict.get(hash(self))
        print(obj)
        if not obj:
            self.error('failed to obtain local geometry, can not add to json')
            return

        node_data['geom'] = json.dumps(flatten(obj))


def register():
    bpy.utils.register_class(SvObjLiteCallback)
    bpy.utils.register_class(SvObjInLite)


def unregister():
    bpy.utils.unregister_class(SvObjInLite)
    bpy.utils.unregister_class(SvObjLiteCallback)
