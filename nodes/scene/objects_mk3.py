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
from bpy.props import BoolProperty, StringProperty
import bmesh

import sverchok
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from sverchok.utils.context_managers import hard_freeze
from sverchok.utils.sv_bmesh_utils import pydata_from_bmesh


class SvObj3DataCollection(bpy.types.PropertyGroup):
    name = bpy.props.StringProperty()
    icon = bpy.props.StringProperty(default="BLANK1")


class SvOB3NamesList(bpy.types.UIList):

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):

        layout.label(item.name, icon=item.icon)
        
        # This is needed to help disambiguate the origin of this click. The receiver needs
        # to know from which node tree and node it originated.
        action = layout.operator("node.sv_ob3_collection_operator", icon='X', text='')
        action.tree_name = data.id_data.name
        action.node_name = data.name
        action.fn_name = 'REMOVE'
        action.idx = data.active_obj_index


class SvOB3ItemOperator(bpy.types.Operator):

    bl_idname = "node.sv_ob3_collection_operator"
    bl_label = "bladibla"

    tree_name = bpy.props.StringProperty(default='')
    node_name = bpy.props.StringProperty(default='')
    fn_name = bpy.props.StringProperty(default='')
    idx = bpy.props.IntProperty()

    def execute(self, context):
        node = bpy.data.node_groups[self.tree_name].nodes[self.node_name]

        if self.fn_name == 'REMOVE':
            node.object_names.remove(self.idx)

        node.process_node(None)

        #
        # if not node.object_names:
        #     node.process()

        return {'FINISHED'}



class SvOB3Callback(bpy.types.Operator):

    bl_idname = "node.ob3_callback"
    bl_label = "Object In mk3 callback"

    fn_name = StringProperty(default='')
    node_name = StringProperty(default='')
    tree_name = StringProperty(default='')

    def execute(self, context):
        """
        returns the operator's 'self' too to allow the code being called to
        print from self.report.
        """
        if self.tree_name and self.node_name:
            ng = bpy.data.node_groups[self.tree_name]
            node = ng.nodes[self.node_name]
        else:
            node = context.node

        getattr(node, self.fn_name)(self)
        return {'FINISHED'}



class SvObjectsNodeMK3(bpy.types.Node, SverchCustomTreeNode):
    ''' Objects Input slot MK3'''
    bl_idname = 'SvObjectsNodeMK3'
    bl_label = 'Objects in mk3'
    bl_icon = 'OUTLINER_OB_EMPTY'

    def hide_show_versgroups(self, context):
        outs = self.outputs
        showing_vg = 'Vers_grouped' in outs

        if self.vergroups and not showing_vg:
            outs.new('StringsSocket', 'Vers_grouped')
        elif not self.vergroups and showing_vg:
            outs.remove(outs['Vers_grouped'])

    groupname = StringProperty(
        name='groupname', description='group of objects (green outline CTRL+G)',
        default='', update=updateNode)

    modifiers = BoolProperty(
        name='Modifiers',
        description='Apply modifier geometry to import (original untouched)',
        default=False, update=updateNode)

    vergroups = BoolProperty(
        name='Vergroups',
        description='Use vertex groups to nesty insertion',
        default=False, update=hide_show_versgroups)

    sort = BoolProperty(
        name='sort by name',
        description='sorting inserted objects by names',
        default=True, update=updateNode)

    object_names = bpy.props.CollectionProperty(type=SvObj3DataCollection)
    active_obj_index = bpy.props.IntProperty()


    def sv_init(self, context):
        new = self.outputs.new
        new('VerticesSocket', "Vertices")
        new('StringsSocket', "Edges")
        new('StringsSocket', "Polygons")
        new('MatrixSocket', "Matrixes")
        new('SvObjectSocket', "Object")


    def get_objects_from_scene(self, ops):
        """
        Collect selected objects
        """
        self.object_names.clear()

        groups = bpy.data.groups
        if self.groupname and groups[self.groupname].objects:
            names = [obj.name for obj in groups[self.groupname].objects]
        else:
            names = [obj.name for obj in bpy.data.objects if obj.select]

        if self.sort:
            names.sort()

        for name in names:
            item = self.object_names.add()
            item.name = name
            item.icon = 'OUTLINER_OB_' + bpy.data.objects[name].type

        if not self.object_names:
            ops.report({'WARNING'}, "Warning, no selected objects in the scene")
            return

        self.process_node(None)


    def select_objs(self, ops):
        """select all objects referenced by node"""
        for item in self.object_names:
            bpy.data.objects[item.name].select = True

        if not self.object_names:
            ops.report({'WARNING'}, "Warning, no object associated with the obj in Node")
         

    def draw_obj_names(self, layout):

        if self.object_names:
            layout.template_list(
                "SvOB3NamesList", "", 
                self, "object_names", self, "active_obj_index")
        else:
            layout.label('--None--')

    def draw_buttons(self, context, layout):

        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop_search(self, 'groupname', bpy.data, 'groups', text='', icon='HAND')

        row = col.row()
        op_text = "Get selection"  # fallback
    
        try:
            addon = context.user_preferences.addons.get(sverchok.__name__)
            if addon.preferences.over_sized_buttons:
                row.scale_y = 4.0
                op_text = "G E T"
        except:
            pass

        callback = 'node.ob3_callback'
        row.operator(callback, text=op_text).fn_name = 'get_objects_from_scene'

        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(self, 'sort', text='Sort', toggle=True)
        row.prop(self, "modifiers", text="Post", toggle=True)
        row.prop(self, "vergroups", text="VeGr", toggle=True)

        row = col.row(align=True)
        row.operator(callback, text="Select Objects").fn_name = 'select_objs'

        # OR !!

        # col = layout.column(align=True)
        # row = col.row(align=True)
        # row.prop(self, 'sort', text='', toggle=True, icon='SORTALPHA')  # sort alpha
        # row.prop(self, "modifiers", text='', toggle=True, icon='MODIFIER')  # post modifier
        # row.prop(self, "vergroups", text='', toggle=True, icon='GROUP_VERTEX') # vertex groups
        # row.operator(callback, text="Select").fn_name = 'select_objs'
        
        # self.draw_obj_names(layout)


        
        self.draw_obj_names(layout)


    def draw_sv3dpanel_ob3(self, col, little_width):
        callback = 'node.ob3_callback'
        row = col.row(align=True)
        row.label(text=self.label if self.label else self.name)
        colo = row.row(align=True)
        colo.scale_x = little_width * 5
        op = colo.operator(callback, text="Get")
        op.fn_name = 'get_objects_from_scene'
        op.tree_name = self.id_data.name
        op.node_name = self.name


    def get_verts_and_vertgroups(self, obj_data):
        vers = []
        vers_grouped = []
        for k, v in enumerate(obj_data.vertices):
            if self.vergroups and v.groups.values():
                vers_grouped.append(k)
            vers.append(list(v.co))
        return vers, vers_grouped


    def process(self):

        if not self.object_names:
            return
            
        scene = bpy.context.scene
        data_objects = bpy.data.objects
        outputs = self.outputs
        
        edgs_out = []
        vers_out = []
        vers_out_grouped = []
        pols_out = []
        mtrx_out = []

        # iterate through references
        for obj in (data_objects.get(o.name) for o in self.object_names):

            if not obj:
                continue

            edgs = []
            vers = []
            vers_grouped = []
            pols = []
            mtrx = []

            with hard_freeze(self) as _: 

                mtrx = [list(m) for m in obj.matrix_world]
                if obj.type in {'EMPTY', 'CAMERA', 'LAMP' }:
                    mtrx_out.append(mtrx)
                    continue
                try:
                    if obj.mode == 'EDIT' and obj.type == 'MESH':
                        # Mesh objects do not currently return what you see
                        # from 3dview while in edit mode when using obj.to_mesh.
                        me = obj.data
                        bm = bmesh.from_edit_mesh(me)
                        vers, edgs, pols = pydata_from_bmesh(bm)
                        del bm
                    else:
                        obj_data = obj.to_mesh(scene, self.modifiers, 'PREVIEW')
                        if obj_data.polygons:
                            pols = [list(p.vertices) for p in obj_data.polygons]
                        vers, vers_grouped = self.get_verts_and_vertgroups(obj_data)
                        edgs = obj_data.edge_keys
                        bpy.data.meshes.remove(obj_data, do_unlink=True)
                except:
                    print('failure in process between frozen area', self.name)

            vers_out.append(vers)
            edgs_out.append(edgs)
            pols_out.append(pols)
            mtrx_out.append(mtrx)
            vers_out_grouped.append(vers_grouped)

        if vers_out and vers_out[0]:
            outputs['Vertices'].sv_set(vers_out)
            outputs['Edges'].sv_set(edgs_out)
            outputs['Polygons'].sv_set(pols_out)

            if 'Vers_grouped' in outputs and self.vergroups:
                outputs['Vers_grouped'].sv_set(vers_out_grouped)

        outputs['Matrixes'].sv_set(mtrx_out)
        outputs['Object'].sv_set([data_objects.get(o.name) for o in self.object_names])


classes = [
    SvOB3ItemOperator, SvObj3DataCollection, 
    SvOB3NamesList, SvOB3Callback, SvObjectsNodeMK3
]


def register():
    _ = [bpy.utils.register_class(c) for c in classes]


def unregister():
    _ = [bpy.utils.unregister_class(c) for c in classes]

