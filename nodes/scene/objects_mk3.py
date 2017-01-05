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
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from sverchok.utils.context_managers import hard_freeze


# class SvObjSelectObjectInItemsInSceneMK3(bpy.types.Operator):
#     """ Select node's Objects from object_in node at scene 3d """
#     bl_idname = "node.sverchok_object_in_selector_mk3"
#     bl_label = "Sv objectin selector mk3"
#     bl_options = {'REGISTER', 'UNDO'}

#     node_name = StringProperty(
#         name='name node',
#         description='it is name of node',
#         default='')

#     tree_name = StringProperty(
#         name='name tree',
#         description='it is name of tree',
#         default='')

#     def execute(self, context):
#         name_no = self.node_name
#         name_tr = self.tree_name
#         handle = handle_read(name_no + name_tr)
#         if handle[0]:
#             for o in handle[1]:
#                 bpy.data.objects[o].select = True
#             #bpy.context.active_object = bpy.data.objects[o]
#         return {'FINISHED'}


# class SvObjSelectedMK3(bpy.types.Operator):
#     """ G E T  selected or grouped objects """
#     bl_idname = "node.sverchok_object_insertion_mk3"
#     bl_label = "Sverchok object selector mk3"
#     bl_options = {'REGISTER', 'UNDO'}

#     node_name = StringProperty()
#     tree_name = StringProperty()

#     def enable(self, node, handle):
#         groups = bpy.data.groups
        
#         name_no = node.name
#         name_tr = node.id_data.name
#         group_name = node.groupname

#         objects = []
#         if group_name and groups[group_name].objects:
#             objs = groups[group_name].objects
#         elif bpy.context.selected_objects:
#             objs = bpy.context.selected_objects
#         else:
#             self.report({'WARNING'}, 'No object selected')
#             self.disable(node, handle)
#             return

#         for o in objs:
#             objects.append(o.name)

#         if node.sort:
#             objects.sort()
#         handle_write(name_no + name_tr, objects)

#         if bpy.data.node_groups[name_tr]:
#             handle = handle_read(name_no + name_tr)
#             node.objects_local = str(handle[1])


#     def disable(self, node, handle):
#         node.objects_local = ''
#         bpy.ops.node.sverchok_update_current(node_group=node.id_data.name)
#         if not handle[0]:
#             return
#         handle_delete(node.name + node.id_data.name)


#     def execute(self, context):

#         if self.node_name and self.tree_name:
#             ng = bpy.data.node_groups[self.tree_name]
#             node = ng.nodes[self.node_name]
#         else:
#             node = context.node

#         name_no = node.name
#         name_tr = node.id_data.name

#         handle = handle_read(name_no + name_tr)
#         self.disable(node, handle)
#         self.enable(node, handle)
#         handle = handle_read(name_no + name_tr)
#         print('end of execute', handle)
#         print('have got {0} items from scene.'.format(handle[1]))
#         return {'FINISHED'}


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

    objects_local = StringProperty(
        name='local objects in', description='objects, bound to current node',
        default='', update=updateNode)

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

    object_names = bpy.props.CollectionProperty(type=bpy.types.PropertyGroup)


    def sv_init(self, context):
        new = self.outputs.new
        new('VerticesSocket', "Vertices")
        new('StringsSocket', "Edges")
        new('StringsSocket', "Polygons")
        new('MatrixSocket', "Matrixes")
        new('SvObjectSocket', "Object")


    def get_objects_from_scene(self):
        """
        Collect selected objects
        """
        self.object_names.clear()
        names = [obj.name for obj in bpy.data.objects if obj.select]

        if self.sort:
            names.sort()

        for name in names:
            self.object_names.add().name = name


    def select_objs(self):
        """select all objects referenced by node"""
        for item in self.object_names:
            bpy.data.objects[item.name].select = True
         

    def draw_obj_names(self, layout):
        # display names currently being tracked, stop at the first 5..
        if self.objects_names:
            remain = len(self.objects_names) - 5

            for i, obj_name in enumerate(self.objects_names):
                layout.label(obj_name)
                if i > 4 and remain > 0:
                    postfix = ('' if remain == 1 else 's')
                    more_items = '... {0} more item' + postfix
                    layout.label(more_items.format(remain))
                    break
        else:
            layout.label('--None--')

    def draw_buttons(self, context, layout):
        #row.prop(self, 'groupname', text='')
        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop_search(self, 'groupname', bpy.data, 'groups', text='', icon='HAND')

        row = col.row()
        addon = context.user_preferences.addons.get(sverchok.__name__)
        if addon.preferences.over_sized_buttons:
            row.scale_y = 4.0
            op_text = "G E T"
        else:
            row.scale_y = 1
            op_text = "Get selection"

        row.operator('node.sverchok_object_insertion_mk3', text=op_text)

        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(self, 'sort', text='Sort', toggle=True)
        row.prop(self, "modifiers", text="Post", toggle=True)
        row.prop(self, "vergroups", text="VeGr", toggle=True)

        row = col.row(align=True)
        opera = row.operator('node.sverchok_object_in_selector_mk3', text='Select')
        opera.node_name = self.name
        opera.tree_name = self.id_data.name
        
        self.draw_obj_names(layout)


    def update(self):
        pass

    # def copy(self, node):
    #     if self.objects_local:
    #         name = self.name + self.id_data.name
    #         handle_write(name, literal_eval(self.objects_local))

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

        objs = [o for o in bpy.data.objects if o.name in self.object_names]

        edgs_out = []
        vers_out = []
        vers_out_grouped = []
        pols_out = []
        mtrx_out = []

        # iterate through references
        for obj in objs:

            edgs = []
            vers = []
            vers_grouped = []
            pols = []
            mtrx = []

            with hard_freeze(self) as _: 

                mtrx = [list(m) for m in obj.matrix_world]
                if obj.type == 'EMPTY':
                    continue

                try:
                    obj_data = obj.to_mesh(scene, self.modifiers, 'PREVIEW')
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

            Vertices = self.outputs['Vertices']
            Edges = self.outputs['Edges']
            Polygons = self.outputs['Polygons']
            Matrixes = self.outputs['Matrixes']
            Objects = self.outputs['Object']

            if Vertices.is_linked:
                Vertices.sv_set(vers_out)

            if Edges.is_linked:
                Edges.sv_set(edgs_out)

            if Polygons.is_linked:
                Polygons.sv_set(pols_out)

            if 'Vers_grouped' in self.outputs:
                Vers_grouped = self.outputs['Vers_grouped']
                if self.vergroups and Vers_grouped.is_linked:
                    Vers_grouped.sv_set(vers_out_grouped)

        if Matrixes.is_linked:
            Matrixes.sv_set(mtrx_out)
        if Objects.is_linked:
            Objects.sv_set(objs)


classes = [SvObjSelectObjectInItemsInSceneMK3, SvObjSelectedMK3, SvObjectsNodeMK3]


def register():
    _ = [bpy.utils.register_class(c) for c in classes]


def unregister():
    _ = [bpy.utils.unregister_class(c) for c in classes]

