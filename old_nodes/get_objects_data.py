# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
from bpy.props import BoolProperty, StringProperty, IntProperty
import bmesh

#from sverchok.nodes.scene.get_objects_data_mk2 import SvOB3BDataCollectionMK2, SVOB3B_UL_NamesListMK2, SvOB3BItemOperatorMK2, SvOB3CallbackMK2

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.utils.sv_operator_mixins import SvGenericNodeLocator
from sverchok.data_structure import updateNode
from sverchok.utils.sv_bmesh_utils import pydata_from_bmesh
from sverchok.utils.nodes_mixins.show_3d_properties import Show3DProperties
from sverchok.utils.blender_mesh import (
    read_verts, read_edges, read_verts_normal,
    read_face_normal, read_face_center, read_face_area, read_materials_idx)


class SvOB3BDataCollectionMK2(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty()
    icon: bpy.props.StringProperty(default="BLANK1")


class ReadingObjectDataError(Exception):
    pass


class SVOB3B_UL_NamesListMK2(bpy.types.UIList):

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):

        item_icon = item.icon
        if not item.icon or item.icon == "BLANK1":
            try:
                item_icon = 'OUTLINER_OB_' + bpy.data.objects[item.name].type
            except:
                item_icon = ""

        layout.label(text=item.name, icon=item_icon)
        action = data.wrapper_tracked_ui_draw_op(layout, "node.sv_ob3b_collection_operator_mk2", icon='X', text='')
        action.fn_name = 'REMOVE'
        action.idx = index


class SvOB3BItemOperatorMK2(bpy.types.Operator, SvGenericNodeLocator):

    bl_idname = "node.sv_ob3b_collection_operator_mk2"
    bl_label = "generic bladibla"

    fn_name: StringProperty(default='')
    idx: IntProperty()

    def sv_execute(self, context, node):
        if self.fn_name == 'REMOVE':
            node.object_names.remove(self.idx)
        node.process_node(None)


class SvOB3CallbackMK2(bpy.types.Operator, SvGenericNodeLocator):

    bl_idname = "node.ob3_callback_mk2"
    bl_label = "Object In mk3 callback"
    bl_options = {'INTERNAL'}

    fn_name: StringProperty(default='')

    def sv_execute(self, context, node):
        """
        returns the operator's 'self' too to allow the code being called to
        print from self.report.
        """
        getattr(node, self.fn_name)(self)


def get_vertgroups(mesh):
    return [k for k,v in enumerate(mesh.vertices) if v.groups.values()]

numpy_socket_names = ['Vertices', 'Edges', 'Vertex Normals', 'Material Idx', 'Polygon Areas', 'Polygon Centers', 'Polygon Normals']


class SvGetObjectsData(Show3DProperties, SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Object Info
    Tooltip: Get Scene Objects into Sverchok Tree
    """

    bl_idname = 'SvGetObjectsData'
    bl_label = 'Get Objects Data'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_OBJECTS_IN'

    @property
    def is_scene_dependent(self):
        return (not self.inputs['Objects'].is_linked) and (self.inputs['Objects'].object_ref_pointer
                                                           or hasattr(self, 'objects_names') and self.object_names)

    @property
    def is_animation_dependent(self):
        return (not self.inputs['Objects'].is_linked) and (self.inputs['Objects'].object_ref_pointer
                                                           or hasattr(self, 'objects_names') and self.object_names)

    def hide_show_versgroups(self, context):
        outs = self.outputs
        showing_vg = 'Vers_grouped' in outs

        if self.vergroups and not showing_vg:
            outs.new('SvStringsSocket', 'Vers_grouped')
        elif not self.vergroups and showing_vg:
            outs.remove(outs['Vers_grouped'])

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

    object_names: bpy.props.CollectionProperty(type=SvOB3BDataCollectionMK2)

    active_obj_index: bpy.props.IntProperty()

    out_np: bpy.props.BoolVectorProperty(
        name="Output Numpy",
        description="Output NumPy arrays (makes node faster)",
        size=7, update=updateNode)
    output_np_all: BoolProperty(
        name='Output all numpy',
        description='Output numpy arrays if possible',
        default=False, update=updateNode)

    def sv_init(self, context):
        new = self.outputs.new
        self.width = 150
        self.inputs.new('SvObjectSocket', "Objects")
        new('SvVerticesSocket', "Vertices")
        new('SvStringsSocket', "Edges")
        new('SvStringsSocket', "Polygons")
        new('SvVerticesSocket', "Vertex Normals")
        new('SvStringsSocket', "Material Idx")
        new('SvStringsSocket', "Polygon Areas")
        new('SvVerticesSocket', "Polygon Centers")
        new('SvVerticesSocket', "Polygon Normals")
        new('SvMatrixSocket', "Matrix")
        new('SvObjectSocket', "Object")


    def get_objects_from_scene(self, ops):
        """
        Collect selected objects
        """
        self.object_names.clear()

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
            layout.template_list("SVOB3B_UL_NamesListMK2", "", self, "object_names", self, "active_obj_index")
        else:
            layout.label(text='--None--')

    @property
    def by_input(self):
        return self.inputs[0].object_ref_pointer is not None or self.inputs[0].is_linked

    def sv_draw_buttons(self, context, layout):
        col = layout.column(align=True)
        by_input = self.by_input
        if not by_input:
            row = col.row()

            op_text = "Get selection"  # fallback
            callback = 'node.ob3_callback_mk2'

            if self.prefs_over_sized_buttons:
                row.scale_y = 4.0
                op_text = "G E T"

            self.wrapper_tracked_ui_draw_op(row, callback, text=op_text).fn_name = 'get_objects_from_scene'

        col = layout.column(align=True)
        row = col.row(align=True)
        if not by_input:
            row.prop(self, 'sort', text='Sort', toggle=True)
        row.prop(self, "modifiers", text="Post", toggle=True)
        row.prop(self, "vergroups", text="VeGr", toggle=True)
        if not by_input:
            self.draw_obj_names(layout)

    def sv_draw_buttons_ext(self, context, layout):
        r = layout.column(align=True)
        row = r.row(align=True)
        row.label(text="Output Numpy:")
        row.prop(self, 'output_np_all', text='If possible', toggle=True)
        if not self.output_np_all:
            for i in range(7):
                r.prop(self, "out_np", index=i, text=numpy_socket_names[i], toggle=True)

        layout.prop(self, 'draw_3dpanel', text="To Control panel")

    def rclick_menu(self, context, layout):
        '''right click sv_menu items'''
        layout.label(text="Output Numpy:")
        layout.prop(self, 'output_np_all', text='All', toggle=True)
        if not self.output_np_all:
            for i in range(7):
                layout.prop(self, "out_np", index=i, text=numpy_socket_names[i], toggle=True)

    def draw_buttons_3dpanel(self, layout):
        if not self.by_input:
            callback = 'node.ob3_callback_mk2'
            row = layout.row(align=True)
            row.label(text=self.label if self.label else self.name)
            colo = row.row(align=True)
            colo.scale_x = 1.6

            self.wrapper_tracked_ui_draw_op(colo, callback, text='Get').fn_name = 'get_objects_from_scene'
        else:
            row = layout.row(align=True)
            row.label(text=self.label if self.label else self.name)
            self.draw_animatable_buttons(row, icon_only=True)

    def get_materials_from_bmesh(self, bm):
        return [face.material_index for face in bm.faces[:]]

    def process(self):

        objs = self.inputs[0].sv_get(default=[[]])
        if not self.object_names and not objs[0]:

            return
        data_objects = bpy.data.objects
        outputs = self.outputs

        vers_out_grouped = []

        o_vs, o_es, o_ps, o_vn, o_mi, o_pa, o_pc, o_pn, o_ms, o_ob = [s.is_linked for s in self.outputs[:10]]
        vs, es, ps, vn, mi, pa, pc, pn, ms = [[] for s in self.outputs[:9]]
        if self.modifiers:
            sv_depsgraph = bpy.context.evaluated_depsgraph_get()

        out_np = self.out_np if not self.output_np_all else [True for i in range(7)]
        if isinstance(objs[0], list):
            objs = objs[0]
        if not objs:
            objs = (data_objects.get(o.name) for o in self.object_names)

        # iterate through references
        for obj in objs:

            if not obj:
                continue

            mtrx = obj.matrix_world
            if obj.type in {'EMPTY', 'CAMERA', 'LAMP' }:
                if o_ms:
                    ms.append(mtrx)
                continue
            try:
                if obj.mode == 'EDIT' and obj.type == 'MESH':
                    # Mesh objects do not currently return what you see
                    # from 3dview while in edit mode when using obj.to_mesh.
                    me = obj.data
                    bm = bmesh.from_edit_mesh(me)
                    vers, edgs, pols = pydata_from_bmesh(bm)

                    if o_vs:
                        vs.append(vers)
                    if o_es:
                        es.append(edgs)
                    if o_ps:
                        ps.append(pols)
                    if o_vn:
                        vn.append([v.normal[:] for v in bm.verts])
                    if o_mi:
                        mi.append(self.get_materials_from_bmesh(bm))
                    if o_pa:
                        pa.append([p.calc_area() for p in bm.faces])
                    if o_pc:
                        pc.append([p.calc_center_median()[:] for p in bm.faces])
                    if o_pn:
                        pn.append([p.normal[:] for p in bm.faces])

                    del bm
                else:

                    # https://developer.blender.org/T99661
                    if obj.type == 'CURVE' and obj.mode == 'EDIT' and bpy.app.version[:2] == (3, 2):
                        raise ReadingObjectDataError("Does not support curves in edit mode in Blender 3.2")
                    elif self.modifiers:
                        obj = sv_depsgraph.objects[obj.name]
                        obj_data = obj.to_mesh(preserve_all_data_layers=True, depsgraph=sv_depsgraph)
                    else:
                        obj_data = obj.to_mesh()

                    if o_vs:
                        vs.append(read_verts(obj_data, out_np[0]))
                    if o_es:
                        es.append(read_edges(obj_data, out_np[1]))
                    if o_ps:
                        ps.append([list(p.vertices) for p in obj_data.polygons])
                    if self.vergroups:
                        vers_out_grouped.append(get_vertgroups(obj_data))
                    if o_vn:
                        vn.append(read_verts_normal(obj_data, out_np[2]))
                    if o_mi:
                        mi.append(read_materials_idx(obj_data, out_np[3]))
                    if o_pa:
                        pa.append(read_face_area(obj_data, out_np[4]))
                    if o_pc:
                        if out_np[5]:
                            pc.append(read_face_center(obj_data, output_numpy=True))
                        else:
                            pc.append([p.center[:] for p in obj_data.polygons])
                    if o_pn:
                        if out_np[6]:
                            pn.append(read_face_normal(obj_data, True))
                        else:
                            pn.append([p.normal[:] for p in obj_data.polygons])

                    obj.to_mesh_clear()

            except ReadingObjectDataError:
                raise
            except Exception as err:
                # it's not clear which cases this try catch should handle
                # probably it should skip wrong object types
                self.debug('failure in process between frozen area', self.name, err)

            if o_ms:
                ms.append(mtrx)


        for i, i2 in zip(self.outputs, [vs, es, ps, vn, mi, pa, pc, pn, ms]):
            if i.is_linked:
                i.sv_set(i2)

        if vers_out_grouped and vers_out_grouped[0]:
            if 'Vers_grouped' in outputs and self.vergroups:
                outputs['Vers_grouped'].sv_set(vers_out_grouped)
        if o_ob:
            if self.by_input:
                outputs['Object'].sv_set(objs)
            else:
                outputs['Object'].sv_set([data_objects.get(o.name) for o in self.object_names])


classes = [SvOB3BItemOperatorMK2, SvOB3BDataCollectionMK2, SVOB3B_UL_NamesListMK2, SvOB3CallbackMK2, SvGetObjectsData]
#classes = [SvGetObjectsData]
register, unregister = bpy.utils.register_classes_factory(classes)
