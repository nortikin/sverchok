# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


import math
from random import random

import bpy
from bpy.props import StringProperty, BoolProperty, EnumProperty
import bmesh
from mathutils import Vector

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from sverchok.utils.sv_viewer_utils import matrix_sanitizer


def wipe_object(ob):
    ''' this removes all geometry '''
    # this can be done with the new  `ob.data.clear_geometry()` i think..
    bm = bmesh.new()
    bm.to_mesh(ob.data)
    bm.free()


class SvDupliInstancesMK4(bpy.types.Node, SverchCustomTreeNode):
    '''Copy by Dupli Faces'''
    bl_idname = 'SvDupliInstancesMK4'
    bl_label = 'Dupli instancer mk4'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_DUPLI_INSTANCER'

    def set_child_quota(self, context):
        # was used for string child property
        updateNode(self, context)

        # post update check
        if self.auto_release:
            parent = self.name_node_generated_parent
            if parent:
                for obj in bpy.data.objects[parent].children:
                    if not obj.name == self.name_child:
                        obj.parent = None

    name_node_generated_parent: StringProperty(
        description="name of the parent that this node generates",
        update=updateNode)

    scale: BoolProperty(default=False,
        description="scale children", update=updateNode)

    auto_release: BoolProperty(update=set_child_quota)

    modes = [
        ("VERTS", "Verts", "On vertices", "", 1),
        ("FACES", "Polys", "On polygons", "", 2)]

    mode: EnumProperty(items=modes, default='VERTS', update=updateNode)

    name_child: StringProperty(description="named child")

    def sv_init(self, context):
        #self.inputs.new("SvObjectSocket", "parent")
        self.inputs.new("SvObjectSocket", "child")
        self.inputs.new("SvMatrixSocket", "matr/vert")
        self.name_node_generated_parent = 'parent'

    def draw_buttons(self, context, layout):
        layout.prop(self, "mode", expand=True)
        col = layout.column(align=True)
        col.prop(self, 'name_node_generated_parent', text='', icon='EDITMODE_HLT')
        #col.prop_search(self, 'name_child', bpy.data, 'objects', text='')
        col.prop(self, 'scale', text='Scale children', toggle=True)
        col.prop(self, 'auto_release', text='One Object only', toggle=True)

    def draw_buttons_ext(self, context, layout):
        col = layout.column()

        try:
            ob = bpy.data.objects.get(self.name_node_generated_parent)
            if ob.instance_type == "FACES":
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

    def process(self):
        #objectsP = self.inputs['parent'].sv_get(default=None)
        objectsC = self.inputs['child'].sv_get()
        transforms = self.inputs['matr/vert'].sv_get()
        objects = bpy.data.objects
        #if any([x.name == self.name_node_generated_parent for x in objects]):
        ob = objects.get(self.name_node_generated_parent)
        #self.name_node_generated_parent = ob.name

        if ob:
            wipe_object(ob)

        # minimum requirements.
        if (not transforms) and (not objectsC):
            if ob:
                ob.instance_type = 'NONE'
            return

        if not ob:
            name = self.name_node_generated_parent
            mesh = bpy.data.meshes.new(name + '_mesh')
            ob = bpy.data.objects.new(name, mesh)
            bpy.context.scene.collection.objects.link(ob)

        # at this point there's a reference to an ob, and the mesh is empty.
        child = self.inputs['child'].sv_get()[0]
        #print('checking',child)

        if transforms and transforms[0]:
            sin, cos = math.sin, math.cos

            theta = 2 * math.pi / 3
            thetb = theta * 2
            ofs = 0.5 * math.pi + theta

            A = Vector((cos(0 + ofs), sin(0 + ofs), 0))
            B = Vector((cos(theta + ofs), sin(theta + ofs), 0))
            C = Vector((cos(thetb + ofs), sin(thetb + ofs), 0))

            if self.mode == "FACES":
                verts = []
                add_verts = verts.extend
                for M in transforms:
                    add_verts([(M @ A), (M @ B), (M @ C)])
                faces = [[i, i + 1, i + 2] for i in range(0, len(transforms) * 3, 3)]
            elif self.mode == "VERTS":
                verts = [M.to_translation() for M in transforms]
                faces = []

            ob.data.from_pydata(verts, [], faces)
            ob.instance_type = self.mode
            ob.use_instance_faces_scale = self.scale
            child.parent = ob


def register():
    bpy.utils.register_class(SvDupliInstancesMK4)


def unregister():
    bpy.utils.unregister_class(SvDupliInstancesMK4)
