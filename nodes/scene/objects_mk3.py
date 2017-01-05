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


class SvOB3Callback(bpy.types.Operator):

    bl_idname = "node.ob3_callback"
    bl_label = "Object In mk3 callback"

    fn_name = bpy.props.StringProperty(default='')

    def execute(self, context):
        """
        returns the operator's 'self' too to allow the code being called to
        print from self.report.
        """
        getattr(context.node, self.fn_name)(self)
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


    def get_objects_from_scene(self, ops):
        """
        Collect selected objects
        """
        self.object_names.clear()
        names = [obj.name for obj in bpy.data.objects if obj.select]

        if self.sort:
            names.sort()

        for name in names:
            self.object_names.add().name = name

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
        # display names currently being tracked, stop at the first 5..
        if self.object_names:
            remain = len(self.object_names) - 5

            for i, obj_ref in enumerate(self.object_names):
                layout.label(obj_ref.name)
                if i > 4 and remain > 0:
                    postfix = ('' if remain == 1 else 's')
                    more_items = '... {0} more item' + postfix
                    layout.label(more_items.format(remain))
                    break
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
        
        self.draw_obj_names(layout)


    def draw_sv3dpanel_ob3(self, col, little_width):
        callback = 'node.ob3_callback'
        row = col.row(align=True)
        row.label(text=self.label if self.label else self.name)
        colo = row.row(align=True)
        colo.scale_x = little_width * 5
        colo.operator(callback, text="Get").fn_name = 'get_objects_from_scene'

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


classes = [SvOB3Callback, SvObjectsNodeMK3]


def register():
    _ = [bpy.utils.register_class(c) for c in classes]


def unregister():
    _ = [bpy.utils.unregister_class(c) for c in classes]

