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


def assign_empty_mesh():
    mt_name = 'empty_skin_mesh_sv'
    if mt_name in bpy.data.meshes:
        return bpy.data.meshes[mt_name]
    else:
        return bpy.data.meshes.new(mt_name)


def force_pydata(mesh, verts, edges):
    mesh.vertices.add(len(verts))
    f_v = list(itertools.chain.from_iterable(verts))
    mesh.vertices.foreach_set('co', f_v)
    mesh.update()

    mesh.edges.add(len(edges))
    f_e = list(itertools.chain.from_iterable(edges))
    mesh.edges.foreach_set('vertices', f_e)
    mesh.update(calc_edges=True)


def make_bmesh_geometry(node, context, name, geometry):
    scene = context.scene
    meshes = bpy.data.meshes
    objects = bpy.data.objects
    verts, edges, matrix = geometry

    # remove object
    if name in objects:
        obj = objects[name]
        # assign the object an empty mesh, this allows the current mesh
        # to be uncoupled and removed from bpy.data.meshes
        obj.data = assign_empty_mesh()

        # remove mesh uncoupled mesh, and add it straight back.
        if name in meshes:
            meshes.remove(meshes[name])
        mesh = meshes.new(name)
        obj.data = mesh
    else:
        # this is only executed once, upon the first run.
        mesh = meshes.new(name)
        obj = objects.new(name, mesh)
        scene.objects.link(obj)

    current_count = len(mesh.vertices)
    propose_count = len(verts)
    difference = (propose_count - current_count)

    if node.fixed_verts and difference == 0:
        f_v = list(itertools.chain.from_iterable(verts))
        mesh.vertices.foreach_set('co', f_v)
        mesh.update()
    else:
        # at this point the mesh is always fresh and empty
        force_pydata(obj.data, verts, edges)
        obj.update_tag(refresh={'OBJECT', 'DATA'})
        context.scene.update()
        if not obj.data.skin_vertices:
            # if modifier present, remove
            if 'sv_skin' in obj.modifiers:
                sk = obj.modifiers['sv_skin']
                obj.modifiers.remove(sk)

            # (re)add.
            obj.modifiers.new(type='SKIN', name='sv_skin')

    if matrix:
        matrix = matrix_sanitizer(matrix)
        obj.matrix_local = matrix
    else:
        obj.matrix_local = Matrix.Identity(4)


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
        description="sets which base name the object will use, "
        "use N-panel to pick alternative random names")

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
        view_icon = 'MOD_ARMATURE' if self.activate else 'ARMATURE_DATA'
        r = layout.row(align=True)
        r.prop(self, "activate", text="", toggle=True, icon=view_icon)
        r.prop(self, "basemesh_name", text="", icon='OUTLINER_OB_MESH')

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
        if not self.activate:
            return

        # only interested in the first
        geometry = self.get_geometry_from_sockets()
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
