# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from itertools import cycle
import math
import numpy as np
import bpy
from bpy.props import StringProperty, BoolProperty, EnumProperty, FloatProperty
from mathutils import Vector, Matrix

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, replace_socket, enum_item as e
from sverchok.utils.nodes_mixins.generating_objects import SvMeshData, SvViewerNode
from sverchok.ui.sv_icons import custom_icon
from sverchok.utils.handle_blender_data import correct_collection_length

def auto_release(parent, childs_name):
    for obj in bpy.data.objects[parent].children:
        if not obj.name in childs_name:
            obj.parent = None

class SvDupliInstancesLite(bpy.types.Node, SverchCustomTreeNode, SvViewerNode):
    """
    Triggers: Fast duplication
    Tooltip: Create Instances from parent object + child
    """
    bl_idname = 'SvDupliInstancesLite'
    bl_label = 'Dupli Instancer Lite'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_DUPLI_INSTANCER'

    def update_sockets(self, context):
        if self.mode == 'FACES' and self.scale:
            self.inputs['Scale'].hide_safe = False
        else:
            self.inputs['Scale'].hide_safe = True
        updateNode(self, context)
    scale: BoolProperty(default=False,
        description="scale children", update=update_sockets)
    scale_factor: FloatProperty(default=1, name='Scale',
        description="Children scale factor", update=updateNode)
    align: BoolProperty(default=False,
        description="align with vertex normal", update=updateNode)

    show_instancer_for_viewport: BoolProperty(default=False,
        description="Show instancer in viewport", update=updateNode)
    show_instancer_for_render: BoolProperty(default=False,
        description="Show instancer in render", update=updateNode)

    show_base_child: BoolProperty(
        name='Show base child',
        default=True,
        description="Hide base object in viewport", update=updateNode)

    auto_release: BoolProperty(
        name='Auto Release',
        description='Remove childs not called by this node',
        update=updateNode)

    modes = [
        ("VERTS", "Verts", "On vertices. Only Translation is used", "", 1),
        ("FACES", "Polys", "On polygons. Translation, Rotation and Scale supported", "", 2)]
    T = [
        ("POS_X", "X", "", "", 1),
        ("POS_Y", "Y", "", "", 2),
        ("POS_Z", "Z", "", "", 3),
        ("NEG_X", "-X", "", "", 4),
        ("NEG_Y", "-Y", "", "", 5),
        ("NEG_Z", "-Z", "", "", 6),]

    mode: EnumProperty(name='Mode', items=modes, default='VERTS', update=update_sockets)

    U = ['X', 'Y', 'Z']

    track: EnumProperty(name="track", default=T[0][0], items=T, update=updateNode)
    up: EnumProperty(name="up", default=U[2], items=e(U), update=updateNode)


    def sv_init(self, context):
        self.width = 160
        self.inputs.new("SvObjectSocket", "Parent")
        self.inputs.new("SvObjectSocket", "Child")
        self.sv_new_input("SvStringsSocket", "Scale", hide_safe=True, prop_name='scale_factor')
        self.outputs.new("SvObjectSocket", "Parent")
        self.outputs.new("SvObjectSocket", "Child")

    def draw_buttons(self, context, layout):
        layout.row(align=True).prop(self, "mode", expand=True)
        col = layout.column(align=True)
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
        else:
            row.prop(self, 'align', text='', icon='MOD_NORMALEDIT', toggle=True)

        row.prop(self, 'auto_release', text='', toggle=True, icon='UNLINKED')
        if self.mode == 'VERTS' and self.align:
            layout.prop(self, 'track')
            layout.prop(self, 'up')

    def set_parent_props(self, parent, scale):
        parent.instance_type = self.mode
        parent.use_instance_vertices_rotation = self.align
        parent.use_instance_faces_scale = self.scale
        parent.show_instancer_for_viewport = self.show_instancer_for_viewport
        parent.show_instancer_for_render = self.show_instancer_for_render
        parent.instance_faces_scale = scale
    def set_child_props(self, parent, child):
        child.parent = parent
        child.track_axis = self.track
        child.up_axis = self.up
        child.hide_set(not self.show_base_child)
    def process(self):
        print(True)
        parent_objects = self.inputs['Parent'].sv_get(deepcopy=False)
        child_objects = self.inputs['Child'].sv_get(deepcopy=False)
        scale = self.inputs['Scale'].sv_get(deepcopy=False)
        if not child_objects or not parent_objects:
            return

        if len(parent_objects) == 1 or len(child_objects) == 1:
            parent = parent_objects[0]
            self.set_parent_props(parent, scale[0][0])
            childs_name = []
            for child in child_objects:
                self.set_child_props(parent, child)
                childs_name.append(child.name)
            if self.auto_release:
                auto_release(parent.name, childs_name)
        else:
            childs_name = {p.name: [] for p in parent_objects}
            if len(scale) == 1:
                scale_f = scale[0]
            else:
                scale_f = [sc[0] for sc in scale]
            for child, parent, sc in zip(child_objects, cycle(parent_objects), cycle(scale_f)):
                self.set_parent_props(parent, sc)
                self.set_child_props(parent, child)
                childs_name[parent.name].append(child.name)
            if self.auto_release:
                for p in parent_objects:
                    auto_release(p.name, childs_name[p.name])

        self.outputs['Parent'].sv_set(parent_objects)
        self.outputs['Child'].sv_set(child_objects)

def register():
    bpy.utils.register_class(SvDupliInstancesLite)


def unregister():
    bpy.utils.unregister_class(SvDupliInstancesLite)
