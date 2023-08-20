# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
from bpy.props import BoolProperty, StringProperty, IntProperty
import bmesh

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.utils.sv_operator_mixins import SvGenericNodeLocator
from sverchok.data_structure import updateNode
from sverchok.utils.sv_bmesh_utils import pydata_from_bmesh
from sverchok.utils.nodes_mixins.show_3d_properties import Show3DProperties

class SvOB3BDataCollection(bpy.types.PropertyGroup):
    bl_idname = "SvOB3BDataCollection"
    name: bpy.props.StringProperty()
    icon: bpy.props.StringProperty(default="BLANK1")


class SVOB3B_UL_NamesList(bpy.types.UIList):

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):

        item_icon = item.icon
        if not item.icon or item.icon == "BLANK1":
            try:
                item_icon = 'OUTLINER_OB_' + bpy.data.objects[item.name].type
            except:
                item_icon = ""

        layout.label(text=item.name, icon=item_icon)
        action = data.wrapper_tracked_ui_draw_op(layout, "node.sv_ob3b_collection_operator", icon='X', text='')
        action.fn_name = 'REMOVE'
        action.idx = index


class SvOB3BItemOperator(bpy.types.Operator, SvGenericNodeLocator):

    bl_idname = "node.sv_ob3b_collection_operator"
    bl_label = "generic bladibla"

    fn_name: StringProperty(default='')
    idx: IntProperty()

    def sv_execute(self, context, node):
        if self.fn_name == 'REMOVE':
            node.object_names.remove(self.idx)

        node.process_node(None)


class SvOB3Callback(bpy.types.Operator, SvGenericNodeLocator):

    bl_idname = "node.ob3_callback"
    bl_label = "Object In mk3 callback"
    bl_options = {'INTERNAL'}

    fn_name: StringProperty(default='')

    def sv_execute(self, context, node):
        """
        returns the operator's 'self' too to allow the code being called to
        print from self.report.
        """
        getattr(node, self.fn_name)(self)


class SvObjectsNodeMK3(Show3DProperties, SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: obj Input Scene Objects pydata
    Tooltip: Get Scene Objects into Sverchok Tree
    """

    bl_idname = 'SvObjectsNodeMK3'
    bl_label = 'Objects in'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_OBJECTS_IN'
    is_animation_dependent = True

    replacement_nodes = [('SvGetObjectsData',
                          None,
                          dict(Matrixes='Matrix',
                               MaterialIdx='Material Idx'))]
    def hide_show_versgroups(self, context):
        outs = self.outputs
        showing_vg = 'Vers_grouped' in outs

        if self.vergroups and not showing_vg:
            outs.new('SvStringsSocket', 'Vers_grouped')
        elif not self.vergroups and showing_vg:
            outs.remove(outs['Vers_grouped'])

    groupname: StringProperty(
        name='groupname', description='group of objects (green outline CTRL+G)',
        default='', update=updateNode)

    modifiers: BoolProperty(
        name='Modifiers',
        description='Apply modifier geometry to import (original untouched)',
        default=False, update=updateNode)

    vergroups: BoolProperty(
        name='Vergroups',
        description='Use vertex groups to nesty insertion',
        default=False, update=hide_show_versgroups)

    sort: BoolProperty(
        name='sort by name',
        description='sorting inserted objects by names',
        default=True, update=updateNode)

    object_names: bpy.props.CollectionProperty(type=SvOB3BDataCollection)

    active_obj_index: bpy.props.IntProperty()

    def sv_init(self, context):
        new = self.outputs.new
        new('SvVerticesSocket', "Vertices")
        new('SvStringsSocket', "Edges")
        new('SvStringsSocket', "Polygons")
        new('SvStringsSocket', "MaterialIdx")
        new('SvMatrixSocket', "Matrixes")
        new('SvObjectSocket', "Object")


    def get_objects_from_scene(self, ops):
        """
        Collect selected objects
        """
        self.object_names.clear()

        if self.groupname and groups[self.groupname].objects:
            groups = bpy.data.groups
            names = [obj.name for obj in groups[self.groupname].objects]
        else:
            names = [obj.name for obj in bpy.data.objects if (obj.select_get() and len(obj.users_scene) > 0 and len(obj.users_collection) > 0)]

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
            layout.template_list("SVOB3B_UL_NamesList", "", self, "object_names", self, "active_obj_index")
        else:
            layout.label(text='--None--')

    def sv_draw_buttons(self, context, layout):
        col = layout.column(align=True)
        row = col.row()

        op_text = "Get selection"  # fallback
        callback = 'node.ob3_callback'

        if self.prefs_over_sized_buttons:
            row.scale_y = 4.0
            op_text = "G E T"

        self.wrapper_tracked_ui_draw_op(row, callback, text=op_text).fn_name = 'get_objects_from_scene'

        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(self, 'sort', text='Sort', toggle=True)
        row.prop(self, "modifiers", text="Post", toggle=True)
        row.prop(self, "vergroups", text="VeGr", toggle=True)
        self.draw_obj_names(layout)

    def sv_draw_buttons_ext(self, context, layout):
        layout.prop(self, 'draw_3dpanel', text="To Control panel")

    def draw_buttons_3dpanel(self, layout):
        callback = 'node.ob3_callback'
        row = layout.row(align=True)
        row.label(text=self.label if self.label else self.name)
        colo = row.row(align=True)
        colo.scale_x = 1.6

        self.wrapper_tracked_ui_draw_op(colo, callback, text='Get').fn_name = 'get_objects_from_scene'


    def get_verts_and_vertgroups(self, obj_data):
        vers = []
        vers_grouped = []
        for k, v in enumerate(obj_data.vertices):
            if self.vergroups and v.groups.values():
                vers_grouped.append(k)
            vers.append(list(v.co))
        return vers, vers_grouped

    def get_materials_from_bmesh(self, bm):
        return [face.material_index for face in bm.faces[:]]

    def get_materials_from_mesh(self, mesh):
        return [face.material_index for face in mesh.polygons[:]]

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
        materials_out = []

        if self.modifiers:
            sv_depsgraph = bpy.context.evaluated_depsgraph_get()

        # iterate through references
        for obj in (data_objects.get(o.name) for o in self.object_names):

            if not obj:
                continue

            edgs = []
            vers = []
            vers_grouped = []
            pols = []
            mtrx = []
            materials = []

            mtrx = obj.matrix_world
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
                    materials = self.get_materials_from_bmesh(bm)
                    del bm
                else:

                    if self.modifiers:
                        obj = sv_depsgraph.objects[obj.name]
                        obj_data = obj.to_mesh(preserve_all_data_layers=True, depsgraph=sv_depsgraph)
                    else:
                        obj_data = obj.to_mesh()

                    if obj_data.polygons:
                        pols = [list(p.vertices) for p in obj_data.polygons]
                    vers, vers_grouped = self.get_verts_and_vertgroups(obj_data)
                    materials = self.get_materials_from_mesh(obj_data)
                    edgs = obj_data.edge_keys

                    obj.to_mesh_clear()


            except Exception as err:
                print('failure in process between frozen area', self.name, err)

            vers_out.append(vers)
            edgs_out.append(edgs)
            pols_out.append(pols)
            mtrx_out.append(mtrx)
            materials_out.append(materials)
            vers_out_grouped.append(vers_grouped)

        if vers_out and vers_out[0]:
            outputs['Vertices'].sv_set(vers_out)
            outputs['Edges'].sv_set(edgs_out)
            outputs['Polygons'].sv_set(pols_out)
            if 'MaterialIdx' in outputs:
                outputs['MaterialIdx'].sv_set(materials_out)

            if 'Vers_grouped' in outputs and self.vergroups:
                outputs['Vers_grouped'].sv_set(vers_out_grouped)

        outputs['Matrixes'].sv_set(mtrx_out)
        outputs['Object'].sv_set([data_objects.get(o.name) for o in self.object_names])

    def load_from_json(self, node_data: dict, import_version: float):
        if import_version < 1.0:
            for named_object in node_data.get('object_names', []):
                self.object_names.add().name = named_object


classes = [SvOB3BItemOperator, SvOB3BDataCollection, SVOB3B_UL_NamesList, SvOB3Callback, SvObjectsNodeMK3]
register, unregister = bpy.utils.register_classes_factory(classes)
