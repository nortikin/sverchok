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
from bpy.props import BoolProperty, StringProperty

from node_tree import SverchCustomTreeNode
from data_structure import (handle_read, handle_write, handle_delete,
                            SvSetSocketAnyType, updateNode)


class SvObjSelected(bpy.types.Operator):
    """ G E T   SELECTED OBJECTS """
    bl_idname = "node.sverchok_object_insertion"
    bl_label = "Sverchok object selector"
    bl_options = {'REGISTER', 'UNDO'}

    node_name = StringProperty(name='name node', description='it is name of node',
                               default='')
    tree_name = StringProperty(name='name tree', description='it is name of tree',
                               default='')
    grup_name = StringProperty(name='grup tree', description='it is name of grup',
                               default='')
    sort = BoolProperty(name='sort objects', description='to sort objects by name or not',
                               default=True)

    def enable(self, name_no, name_tr, handle, sorting):
        objects = []
        if self.grup_name and bpy.data.groups[self.grup_name].objects:
            objs = bpy.data.groups[self.grup_name].objects
        elif bpy.context.selected_objects:
            objs = bpy.context.selected_objects
        else:
            self.report({'WARNING'},'No object selected')
            return
        for o in objs:
            objects.append(o.name)
        if sorting:
            objects.sort()
        handle_write(name_no+name_tr, objects)
        # временное решение с группой. надо решать, как достать имя группы узлов
        if bpy.data.node_groups[name_tr]:
            handle = handle_read(name_no+name_tr)
            #print ('exec',name)
            bpy.data.node_groups[name_tr].nodes[name_no].objects_local = str(handle[1])

    def disable(self, name, handle):
        if not handle[0]:
            return
        handle_delete(name)

    def execute(self, context):
        name_no = self.node_name
        name_tr = self.tree_name
        sorting = self.sort
        handle = handle_read(name_no+name_tr)
        self.disable(name_no+name_tr, handle)
        self.enable(name_no, name_tr, handle, sorting)
        print('have got {0} items from scene.'.format(handle[1]))
        return {'FINISHED'}


class ObjectsNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Objects Input slot '''
    bl_idname = 'ObjectsNode'
    bl_label = 'Objects_in'
    bl_icon = 'OUTLINER_OB_EMPTY'

    #def object_select(self, context):
        #return [tuple(3 * [ob.name]) for ob in context.scene.objects if ob.type == 'MESH' or ob.type == 'EMPTY']
    objects_local = StringProperty(
        name='local objects in', description='objects, binded to current node',
        default='',
        update=updateNode)
    #ObjectProperty = EnumProperty(items = object_select, name = 'ObjectProperty')
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
        update=updateNode)
    sort = BoolProperty(
        name='sort by name',
        description='sorting inserted objects by names',
        default=True,
        update=updateNode)

    def init(self, context):
        self.outputs.new('VerticesSocket', "Vertices", "Vertices")
        self.outputs.new('StringsSocket', "Edges", "Edges")
        self.outputs.new('StringsSocket', "Polygons", "Polygons")
        self.outputs.new('MatrixSocket', "Matrixes", "Matrixes")

    def draw_buttons(self, context, layout):
        row = layout.row()
        row.scale_y = 4.0
        opera = row.operator('node.sverchok_object_insertion', text='G E T')
        opera.node_name = self.name
        opera.tree_name = self.id_data.name
        opera.grup_name = self.groupname
        opera.sort = self.sort
        row = layout.row(align=True)
        row.prop(self, 'groupname', text='')
        row.prop(self, 'sort', text='Sort objects')
        
        row = layout.row(align=True)
        row.prop(self, "modifiers", text="Post modifiers")
        # row = layout.row(align=True)
        row.prop(self, "vergroups", text="Vert groups")
        
        handle = handle_read(self.name+self.id_data.name)
        if self.objects_local:
            if handle[0]:
                for i, o in enumerate(handle[1]):
                    if i > 4:
                        layout.label('. . . more '+str(len(handle[1])-5)+' items')
                        break
                    layout.label(o)
            else:
                handle_write(self.name+self.id_data.name, literal_eval(self.objects_local))
        else:
            layout.label('--None--')

    def update(self):
        # check for grouping socket
        if self.vergroups and not ('Vers_grouped' in self.outputs):
            self.outputs.new('StringsSocket', "Vers_grouped", "Vers_grouped")
        elif not self.vergroups and ('Vers_grouped' in self.outputs):
            self.outputs.remove(self.outputs['Vers_grouped'])
        
        name = self.name + self.id_data.name
        handle = handle_read(name)
        #print (handle)
        if self.objects_local:
            # bpy.ops.node.sverchok_object_insertion(node_name=self.name, tree_name=self.id_data.name, grup_name=self.groupname)
            # not updating. need to understand mechanic of update
            self.use_custom_color = True
            self.color = (0, 0.5, 0.2)
        else:
            self.use_custom_color = True
            self.color = (0, 0.1, 0.05)
        #reload handle if possible
        if self.objects_local and not handle[0]:
            handle_write(name, literal_eval(self.objects_local))
            handle = handle_read(name)    
            
        if handle[0]:
            objs = handle[1]
            edgs_out = []
            vers_out = []
            vers_out_grouped = []
            pols_out = []
            mtrx_out = []
            for obj_ in objs:  # names of objects
                edgs = []
                vers = []
                vers_grouped = []
                pols = []
                mtrx = []
                obj = bpy.data.objects[obj_]  # objects itself
                if obj.type == 'EMPTY':
                    for m in obj.matrix_world:
                        mtrx.append(m[:])

                else:
                    #obj_data = obj.data
                    # post modifier geometry if ticked
                    scene = bpy.context.scene
                    settings = 'PREVIEW'
                    # create a temporary mesh
                    obj_data = obj.to_mesh(scene, self.modifiers, settings)

                    for m in obj.matrix_world:
                        mtrx.append(list(m))
                    for k, v in enumerate(obj_data.vertices):
                        if self.vergroups and v.groups.values():
                            vers_grouped.append(k)
                        vers.append(list(v.co))
                    #for edg in obj_data.edges:
                    #    edgs.append([edg.vertices[0], edg.vertices[1]])
                    edgs = obj_data.edge_keys
                    for p in obj_data.polygons:
                        pols.append(list(p.vertices))
                    # remove the temp mesh
                    bpy.data.meshes.remove(obj_data)
                    #print (vers, edgs, pols, mtrx)
                edgs_out.append(edgs)
                vers_out.append(vers)
                vers_out_grouped.append(vers_grouped)
                pols_out.append(pols)
                mtrx_out.append(mtrx)
            if vers_out[0]:

                if 'Vertices' in self.outputs and self.outputs['Vertices'].links:
                    SvSetSocketAnyType(self, 'Vertices', vers_out)

                if 'Edges' in self.outputs and self.outputs['Edges'].links:
                    SvSetSocketAnyType(self, 'Edges', edgs_out)

                if 'Polygons' in self.outputs and self.outputs['Polygons'].links:
                    SvSetSocketAnyType(self, 'Polygons', pols_out)

                if 'Vers_grouped' in self.outputs and self.outputs['Vers_grouped'].links:
                    SvSetSocketAnyType(self, 'Vers_grouped', vers_out_grouped)

            if 'Matrixes' in self.outputs and self.outputs['Matrixes'].links:
                SvSetSocketAnyType(self, 'Matrixes', mtrx_out)

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(SvObjSelected)
    bpy.utils.register_class(ObjectsNode)


def unregister():
    bpy.utils.unregister_class(ObjectsNode)
    bpy.utils.unregister_class(SvObjSelected)

if __name__ == '__main__':
    register()

