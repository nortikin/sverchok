# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
from bpy.props import BoolProperty, StringProperty, EnumProperty

import sverchok
from sverchok.utils.mesh_repr_utils import flatten, unflatten, generate_object
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata
from sverchok.utils.sv_operator_mixins import SvGenericNodeLocator
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode


import json

class SvObjLiteCallback(bpy.types.Operator, SvGenericNodeLocator):
    """ GET / Reject object callback"""
    bl_idname = "node.sverchok_objectinlite_cb"
    bl_label = "Sverchok object in lite callback"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    cmd: StringProperty()

    def sv_execute(self, context, node):
        getattr(node, self.cmd)()
        node.process_node(context)


class SvObjInLite(bpy.types.Node, SverchCustomTreeNode):
    ''' Objects Input Lite'''
    bl_idname = 'SvObjInLite'
    bl_label = 'Objects in Lite'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_OBJECT_IN_LITE'

    modifiers: BoolProperty(
        description='Apply modifier geometry to import (original untouched)',
        name='Modifiers', default=False, update=updateNode)

    do_not_add_obj_to_scene: BoolProperty(
        default=False,
        description="Do not add the object to the scene if this node is imported from elsewhere") 
    
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
        callback = 'node.sverchok_objectinlite_cb'
        scale_y = 4.0 if self.prefs_over_sized_buttons else 1

        col = layout.column(align=True)
        row = col.row(align=True)
        row.scale_y = scale_y

        cb_text, cmd, display_text = [
            ("G E T", "dget", "--None--"),
            ("D R O P", "drop", self.obj_name)
        ][self.currently_storing]

        self.wrapper_tracked_ui_draw_op(row, callback, text=cb_text).cmd = cmd

        row.prop(self, 'modifiers', text='', icon='MODIFIER')
        layout.label(text=display_text)
        layout.row().prop(self, "do_not_add_obj_to_scene", text="do not add to scene")


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
        if 'geom' not in node_data:
            return  # looks like a node was empty when it was imported
        geom = node_data['geom']
        if import_version < 1.0:
            name = node_data['params']["obj_name"]
        else:
            name = self.obj_name
        geom_dict = json.loads(geom)

        if not geom_dict:
            self.debug(f'{self.name}, contains no flatten geom')
            return

        unrolled_geom = unflatten(geom_dict)
        verts = unrolled_geom['Vertices']
        edges = unrolled_geom['Edges']
        polygons = unrolled_geom['Polygons']
        materials = unrolled_geom.get('MaterialIdx', [])
        matrix = unrolled_geom['Matrix']

        if self.do_not_add_obj_to_scene:
            self.node_dict[hash(self)] = unrolled_geom
            self.obj_name = name
            return

        bm = bmesh_from_pydata(verts, edges, polygons)
        if materials:
            for face, material in zip(bm.faces, materials):
                face.material_index = material
        obj = generate_object(name, bm)
        obj.matrix_world = matrix

        # rename if obj existed
        if not obj.name == name:
            self.obj_name = obj.name
            if import_version < 1.0:
                node_data['params']["obj_name"] = obj.name  # I guess the name was used for further importing

    def save_to_json(self, node_data: dict):
        # generate flat data, and inject into incoming storage variable
        obj = self.node_dict.get(hash(self))
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
