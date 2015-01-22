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

import itertools
import random
import re

import bpy
from bpy.props import BoolProperty, StringProperty
from mathutils import Matrix, Vector

from sverchok.node_tree import (
    SverchCustomTreeNode, VerticesSocket, MatrixSocket, StringsSocket)
from sverchok.data_structure import dataCorrect, fullList, updateNode, SvGetSocketAnyType
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata


def matrix_sanitizer(matrix):
    #  reduces all values below threshold (+ or -) to 0.0, to avoid meaningless
    #  wandering floats.
    coord_strip = lambda c: 0.0 if (-1.6e-5 <= c <= 1.6e-5) else c
    san = lambda v: Vector((coord_strip(c) for c in v[:]))
    return Matrix([san(v) for v in matrix])


def default_mesh(name):
    verts = [(1, 1, -1), (1, -1, -1), (-1, -1, -1)]
    faces = [(0, 1, 2)]

    mesh_data = bpy.data.meshes.new(name)
    mesh_data.from_pydata(verts, [], faces)
    mesh_data.update()
    return mesh_data


def make_bmesh_geometry(node, context, name, geometry):
    scene = context.scene
    meshes = bpy.data.meshes
    objects = bpy.data.objects
    verts, edges, matrix = geometry

    if name in objects:
        sv_object = objects[name]
    else:
        temp_mesh = default_mesh(name)
        sv_object = objects.new(name, temp_mesh)
        scene.objects.link(sv_object)

    mesh = sv_object.data
    current_count = len(mesh.vertices)
    propose_count = len(verts)
    difference = (propose_count - current_count)

    if node.fixed_verts and difference == 0:
        f_v = list(itertools.chain.from_iterable(verts))
        mesh.vertices.foreach_set('co', f_v)
        mesh.update()
    else:
        ''' get bmesh, write bmesh to obj, free bmesh'''
        bm = bmesh_from_pydata(verts, edges, [])
        bm.to_mesh(sv_object.data)
        bm.free()
        sv_object.hide_select = False

    if matrix:
        matrix = matrix_sanitizer(matrix)
        sv_object.matrix_local = matrix
    else:
        sv_object.matrix_local = Matrix.Identity(4)


class SkinViewerNode(bpy.types.Node, SverchCustomTreeNode):

    bl_idname = 'SkinViewerNode'
    bl_label = 'Skin Viewer Draw'
    bl_icon = 'OUTLINER_OB_EMPTY'

    activate = BoolProperty(
        name='Show',
        description='When enabled this will process incoming data',
        default=True,
        update=updateNode)

    basemesh_name = StringProperty(
        default='Alpha',
        update=updateNode,
        description='sets which base name the object will use, \
        use N-panel to pick alternative random names')

    material = StringProperty(default='', update=updateNode)

    fixed_verts = BoolProperty(
        default=False,
        name="Fixed vertices",
        description="Use only with unchanging topology")

    autosmooth = BoolProperty(
        default=False,
        update=updateNode,
        description="This auto sets all faces to smooth shade")

    def sv_init(self, context):
        self.use_custom_color = True
        self.inputs.new('VerticesSocket', 'vertices', 'vertices')
        self.inputs.new('StringsSocket', 'edges', 'edges')
        self.inputs.new('MatrixSocket', 'matrix', 'matrix')

    def draw_buttons(self, context, layout):
        view_icon = 'RESTRICT_VIEW_' + ('OFF' if self.activate else 'ON')
        col = layout.column(align=True)
        col.prop(self, "activate", text="UPD", toggle=True, icon=view_icon)
        col.prop(self, "basemesh_name", text="", icon='OUTLINER_OB_MESH')

    def draw_buttons_ext(self, context, layout):
        col = layout.column(align=True)
        box = col.box()
        if box:
            box.label(text="Beta options")
            box.prop(self, "fixed_verts", text="Fixed vert count")
            box.prop(self, 'autosmooth', text='smooth shade')

    def get_geometry_from_sockets(self):
        i = self.inputs
        mverts = i['vertices'].sv_get(default=[])[0]
        medges = i['edges'].sv_get(default=[])[0]
        mmtrix = i['matrix'].sv_get(default=[[]])[0]
        return mverts, medges, mmtrix

    def process(self):

        # only interested in the first
        geometry = self.get_geometry_from_sockets()
        print(geometry)
        make_bmesh_geometry(self, bpy.context, self.basemesh_name, geometry)

        obj = bpy.data.objects[self.basemesh_name]

        if bpy.data.materials.get(self.material):
            self.set_corresponding_materials(obj)

        if self.autosmooth:
            self.set_autosmooth(obj)

    def set_corresponding_materials(self, obj):
        obj.active_material = bpy.data.materials[self.material]

    def set_autosmooth(self, obj):
        mesh = obj.data
        smooth_states = [True] * len(mesh.polygons)
        mesh.polygons.foreach_set('use_smooth', smooth_states)
        mesh.update()


def register():
    bpy.utils.register_class(SkinViewerNode)


def unregister():
    bpy.utils.unregister_class(SkinViewerNode)
