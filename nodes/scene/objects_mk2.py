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

import bpy
from bpy.props import BoolProperty, StringProperty, EnumProperty

import sverchok
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (
    handle_read, handle_write, handle_delete,
    SvSetSocketAnyType, updateNode
)


class SvObjSelectObjectInItemsInScene(bpy.types.Operator):
    """ Select node's Objects from object_in node at scene 3d """
    bl_idname = "node.sverchok_object_in_selector"
    bl_label = "Sv objectin selector"
    bl_options = {'REGISTER', 'UNDO'}

    node_name = StringProperty(
        name='name node',
        description='it is name of node',
        default='')

    tree_name = StringProperty(
        name='name tree',
        description='it is name of tree',
        default='')

    def execute(self, context):
        name_no = self.node_name
        name_tr = self.tree_name
        handle = handle_read(name_no + name_tr)
        if handle[0]:
            for o in handle[1]:
                bpy.data.objects[o].select = True
            #bpy.context.active_object = bpy.data.objects[o]
        return {'FINISHED'}


class SvObjSelected(bpy.types.Operator):
    """ G E T  selected or grouped objects """
    bl_idname = "node.sverchok_object_insertion"
    bl_label = "Sverchok object selector"
    bl_options = {'REGISTER', 'UNDO'}


    def enable(self, context, handle):
        groups = bpy.data.groups
        
        node = context.node
        name_no = node.name
        name_tr = node.id_data.name
        group_name = node.groupname


        objects = []
        if group_name and groups[group_name].objects:
            objs = groups[group_name].objects
        elif bpy.context.selected_objects:
            objs = bpy.context.selected_objects
        else:
            self.report({'WARNING'}, 'No object selected')
            return

        for o in objs:
            objects.append(o.name)

        if node.sort:
            objects.sort()
        handle_write(name_no + name_tr, objects)

        if bpy.data.node_groups[name_tr]:
            handle = handle_read(name_no + name_tr)
            node.objects_local = str(handle[1])


    def disable(self, context, handle):
        if not handle[0]:
            return
        node = context.active_node
        handle_delete(node.name + node.id_data.name)


    def execute(self, context):

        node = context.node
        name_no = node.name
        name_tr = node.id_data.name

        handle = handle_read(name_no + name_tr)
        self.disable(context, handle)
        self.enable(context, handle)
        handle = handle_read(name_no + name_tr)
        print('have got {0} items from scene.'.format(handle[1]))
        return {'FINISHED'}


class ObjectsNodeMK2(bpy.types.Node, SverchCustomTreeNode):
    ''' Objects Input slot MK2'''
    bl_idname = 'ObjectsNodeMK2'
    bl_label = 'Objects in mk2'
    bl_icon = 'OUTLINER_OB_EMPTY'

    def hide_show_versgroups(self, context):
        if self.vergroups and not ('Vers_grouped' in self.outputs):
            self.outputs.new('StringsSocket', "Vers_grouped", "Vers_grouped")
        elif not self.vergroups and ('Vers_grouped' in self.outputs):
            self.outputs.remove(self.outputs['Vers_grouped'])

    objects_local = StringProperty(
        name='local objects in', description='objects, binded to current node',
        default='', update=updateNode)

    groupname = StringProperty(
        name='groupname', description='group of objects (green outline CTRL+G)',
        default='',
        update=updateNode)

    modifiers = BoolProperty(
        name='Modifiers',
        description='Apply modifier geometry to import (original untouched)',
        default=False,
        update=updateNode)

    vergroups = BoolProperty(
        name='Vergroups',
        description='Use vertex groups to nesty insertion',
        default=False,
        update=hide_show_versgroups)

    sort = BoolProperty(
        name='sort by name',
        description='sorting inserted objects by names',
        default=True,
        update=updateNode)

    def sv_init(self, context):
        self.outputs.new('VerticesSocket', "Vertices")
        self.outputs.new('StringsSocket', "Edges")
        self.outputs.new('StringsSocket', "Polygons")
        self.outputs.new('MatrixSocket', "Matrixes")
        self.outputs.new('SvObjectSocket', "Object")

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

        row.operator('node.sverchok_object_insertion', text=op_text)

        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(self, 'sort', text='Sort', toggle=True)
        row.prop(self, "modifiers", text="Post", toggle=True)
        # row = layout.row(align=True)
        row.prop(self, "vergroups", text="VeGr", toggle=True)

        row = col.row(align=True)
        opera = row.operator('node.sverchok_object_in_selector', text='Select')
        opera.node_name = self.name
        opera.tree_name = self.id_data.name

        # Construct Node UI display of names currently being tracked, stop at the first 5..
        handle = handle_read(self.name + self.id_data.name)
        if self.objects_local and handle[0]:
            for i, o in enumerate(handle[1]):
                layout.label(o)                
                if i >= 4:
                    layout.label(' . . . ' + str(len(handle[1]) - 5) + ' more items')
                    break
        else:
            layout.label('--None--')

    def update(self):
        pass

    def copy(self, node):
        if self.objects_local:
            name = self.name + self.id_data.name
            handle_write(name, literal_eval(self.objects_local))

    def process(self):
        if not self.objects_local:
            return

        scene = bpy.context.scene
        
        name = self.name + self.id_data.name
        handle = handle_read(name)

        # reload handle if possible
        if self.objects_local and not handle[0]:
            handle_write(name, literal_eval(self.objects_local))
            handle = handle_read(name)

        if handle[0]:

            objs = [o for o in bpy.data.objects if o.name in handle[1]]

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

                self.id_data.freeze(hard=True)

                try:
                    if obj.type == 'EMPTY':
                        for m in obj.matrix_world:
                            mtrx.append(m[:])

                    else:
                        # create a temporary mesh
                        obj_data = obj.to_mesh(scene, self.modifiers, 'PREVIEW')
                        edgs = obj_data.edge_keys

                        for m in obj.matrix_world:
                            mtrx.append(list(m))
            
                        for k, v in enumerate(obj_data.vertices):
                            if self.vergroups and v.groups.values():
                                vers_grouped.append(k)
                            vers.append(list(v.co))
            
                        for p in obj_data.polygons:
                            pols.append(list(p.vertices))

                        bpy.data.meshes.remove(obj_data, do_unlink=True)
                except:
                    print('failure in process between freezed area')

                self.id_data.unfreeze(hard=True)

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


def register():
    bpy.utils.register_class(SvObjSelectObjectInItemsInScene)
    bpy.utils.register_class(SvObjSelected)
    bpy.utils.register_class(ObjectsNodeMK2)


def unregister():
    bpy.utils.unregister_class(ObjectsNodeMK2)
    bpy.utils.unregister_class(SvObjSelected)
    bpy.utils.unregister_class(SvObjSelectObjectInItemsInScene)

if __name__ == '__main__':
    register()
