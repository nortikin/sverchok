# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


import math
import numpy as np
import bpy
from bpy.props import StringProperty, BoolProperty, EnumProperty
from mathutils import Vector, Matrix

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, replace_socket
from sverchok.utils.nodes_mixins.generating_objects import SvMeshData, SvViewerNode
from sverchok.ui.sv_icons import custom_icon
from sverchok.utils.handle_blender_data import correct_collection_length

def auto_release(parent, childs_name):
    for obj in bpy.data.objects[parent].children:
        if not obj.name in childs_name:
            obj.parent = None

def generate_mesh_data(transforms, child, mode, ignore_location):

    A = Vector((-1, -1/3, 0))
    B = Vector((1, -1/3, 0))
    C = Vector((0, 2/3, 0))
    if ignore_location:
        if mode == "FACES":
            mtrx = Matrix.Translation(child.matrix_world.to_translation()).inverted()
            verts = []
            add_verts = verts.extend
            for _M in transforms:
                M = mtrx @ _M
                add_verts([(M @ A)[:], (M @ B)[:], (M @ C)[:]])
            faces = np.arange(3*len(transforms)).reshape(-1, 3).tolist()
        elif mode == "VERTS":
            loc = child.location
            if isinstance(transforms[0], np.ndarray):
                verts = transforms[0] -loc
            else:
                verts = [(Vector(V) -loc)[:] for V in transforms[0]]
            faces = []
    else:
        if mode == "FACES":
            verts = []
            add_verts = verts.extend
            for M in transforms:
                add_verts([(M @ A)[:], (M @ B)[:], (M @ C)[:]])
            faces = np.arange(3*len(transforms)).reshape(-1, 3).tolist()

        elif mode == "VERTS":
            verts = transforms[0]
            faces = []

    return verts, faces

class SvDupliInstancesMK5(bpy.types.Node, SverchCustomTreeNode, SvViewerNode):
    '''Copy by Dupli Faces'''
    bl_idname = 'SvDupliInstancesMK5'
    bl_label = 'Dupli Instancer'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_DUPLI_INSTANCER'

    def update_visibility(self, context):
        try:
            ob = bpy.data.objects.get(self.base_data_name)

            ob.show_instancer_for_viewport = self.show_instancer_for_viewport
            ob.show_instancer_for_render = self.show_instancer_for_render
        except AttributeError:
            pass

    def change_socket(self, context):

        change = self.inputs[1].label != 'Vertices' and self.mode == 'VERTS'
        change = change or (self.inputs[1].label != 'Matrices' and self.mode == 'FACES')
        if change:
            new_type = 'SvMatrixSocket' if self.mode == 'FACES' else 'SvVerticesSocket'
            new_name = 'Matrices' if self.mode == 'FACES' else 'Vertices'
            replace_socket(self.inputs[1], new_type)
            self.inputs[1].label = new_name
            updateNode(self, context)

    mesh_data: bpy.props.CollectionProperty(type=SvMeshData, options={'SKIP_SAVE'})

    fast_mesh_update: bpy.props.BoolProperty(
        default=True, update=updateNode,
        description="Usually should be enabled. If some glitches with mesh update, switch it off")

    scale: BoolProperty(default=False,
        description="scale children", update=updateNode)

    show_instancer_for_viewport: BoolProperty(default=False,
        description="Show instancer in viewport", update=update_visibility)
    show_instancer_for_render: BoolProperty(default=False,
        description="Show instancer in render", update=update_visibility)

    show_base_child: BoolProperty(
        name='Show base child',
        default=True,
        description="Hide base object in viewport", update=updateNode)

    auto_release: BoolProperty(
        name='Auto Release',
        description='Remove childs not called by this node',
        update=updateNode)
    ignore_base_offset: BoolProperty(
        name='Clear Location',
        description='Clear base child location',
        update=updateNode)

    modes = [
        ("VERTS", "Verts", "On vertices. Only Translation is used", "", 1),
        ("FACES", "Polys", "On polygons. Translation, Rotation and Scale supported", "", 2)]

    mode: EnumProperty(name='Mode', items=modes, default='VERTS', update=change_socket)

    name_child: StringProperty(description="named child")

    def sv_init(self, context):
        self.init_viewer()
        self.inputs.new("SvObjectSocket", "child")
        self.inputs.new("SvVerticesSocket", "matr/vert").label = 'Vertices'

    def migrate_from(self, old_node):
        self.base_data_name = old_node.name_node_generated_parent
        self.inputs[0].object_ref_pointer = old_node.inputs[0].object_ref_pointer

    def draw_buttons(self, context, layout):
        self.draw_viewer_properties(layout)
        layout.row(align=True).prop(self, "mode", expand=True)
        col = layout.column(align=True)

        if self.mode == 'FACES':
            row = col.row(align=True)
            row.label(text='Instancer')
            row.prop(self, 'show_instancer_for_viewport', text='', toggle=True,
            icon=f"RESTRICT_VIEW_{'OFF' if self.show_instancer_for_viewport else 'ON'}")
            row.prop(self, 'show_instancer_for_render', text='', toggle=True,
            icon=f"RESTRICT_RENDER_{'OFF' if self.show_instancer_for_render else 'ON'}")


        row = col.row(align=True)
        row.label(text='Child')
        row.prop(self, 'show_base_child',text='', toggle=True,
        icon=f"HIDE_{'OFF' if self.show_base_child else 'ON'}")
        if self.mode == 'FACES':
            row.prop(self, 'scale', text='', icon_value=custom_icon('SV_SCALE'), toggle=True)
        row.prop(self, 'auto_release', text='', toggle=True, icon='UNLINKED')
        row.prop(self, 'ignore_base_offset', text='', toggle=True, icon='TRANSFORM_ORIGINS')

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, 'fast_mesh_update')
        col = layout.column()
        if self.mode == "FACES":
            try:
                ob = bpy.data.objects.get(self.base_data_name)
                row = col.row()
                row.prop(ob, "show_instancer_for_viewport", text="Display Instancer") # bool
                row2 = col.row()
                row2.prop(ob, "show_instancer_for_render", text="Render Instancer") # bool
                row3 = col.row()
                row3.prop(self, "scale", text="Scale by Face Size") # bool
                row4 = col.row()
                row4.enabled = ob.use_instance_faces_scale
                row4.prop(ob, "instance_faces_scale", text="Factor")  #float

            finally:
                pass

    def sv_copy(self, other):
        super().sv_copy(other)
        self.mesh_data.clear()

    def process(self):
        if not self.is_active or not self.inputs[1].is_linked:
            return
        child_objects = self.inputs['child'].sv_get(deepcopy=False)
        transforms = self.inputs['matr/vert'].sv_get(deepcopy=False)
        if not child_objects:
            return
        child = child_objects[0]

        if transforms and len(transforms[0]) > 0:
            verts, faces = generate_mesh_data(transforms, child, self.mode, self.ignore_base_offset)

            correct_collection_length(self.mesh_data, 1)

            self.mesh_data[0].regenerate_mesh(
                self.base_data_name,
                verts, [],
                faces,
                None,
                self.fast_mesh_update)
            self.regenerate_objects([self.base_data_name], [d.mesh for d in self.mesh_data], [self.collection])
            ob = self.object_data[0].obj

            ob.instance_type = self.mode
            ob.use_instance_faces_scale = self.scale
            ob.show_instancer_for_viewport = self.show_instancer_for_viewport
            ob.show_instancer_for_render = self.show_instancer_for_render
            childs_name = []
            for child in child_objects:
                child.parent = ob
                child.hide_set(not self.show_base_child)

                childs_name.append(child.name)
            self.name_child = str(childs_name)
            if self.auto_release:
                auto_release(ob.name, childs_name)

            self.outputs['Objects'].sv_set([obj_data.obj for obj_data in self.object_data])

def register():
    bpy.utils.register_class(SvDupliInstancesMK5)


def unregister():
    bpy.utils.unregister_class(SvDupliInstancesMK5)
