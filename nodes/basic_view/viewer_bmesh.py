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

from node_tree import (
    SverchCustomTreeNode, VerticesSocket, MatrixSocket, StringsSocket)
from data_structure import dataCorrect, fullList, updateNode, SvGetSocketAnyType
from utils.sv_bmesh_utils import bmesh_from_pydata


def natural_plus_one(object_names):

    ''' sorts ['Alpha', 'Alpha1', 'Alpha11', 'Alpha2', 'Alpha23']
        into ['Alpha', 'Alpha1', 'Alpha2', 'Alpha11', 'Alpha23']
        and returns (23+1)
    '''

    def extended_sort(a):
        ''' finds the digit trailing, or 0 if no digits '''
        k = re.split('(\d*)', a)
        return 0 if len(k) == 1 else int(k[1])

    natural_sort = sorted(object_names, key=extended_sort)
    last = natural_sort[-1]
    num = extended_sort(last)
    return num+1


def get_random_init():
    objects = bpy.data.objects

    greek_alphabet = [
        'Alpha', 'Beta', 'Gamma', 'Delta',
        'Epsilon', 'Zeta', 'Eta', 'Theta',
        'Iota', 'Kappa', 'Lamda', 'Mu',
        'Nu', 'Xi', 'Omicron', 'Pi',
        'Rho', 'Sigma', 'Tau', 'Upsilon',
        'Phi', 'Chi', 'Psi', 'Omega']

    with_underscore = lambda obj: '_' in obj.name and obj.type == 'MESH'
    names_with_underscores = list(filter(with_underscore, objects))
    print(names_with_underscores)
    set_of_names_pre_underscores = set([n.name.split('_')[0] for n in names_with_underscores])
    if '' in set_of_names_pre_underscores:
        set_of_names_pre_underscores.remove('')

    n = random.choice(greek_alphabet)

    # not picked yet.
    if not n in set_of_names_pre_underscores:
        return n

    # at this point the name was already picked, we don't want to overwrite
    # existing obj/meshes and instead append digits onto the greek letter
    # if Alpha is present already a new one will be Alpha2, Alpha3 etc..
    # (not Alpha002, or Alpha.002)
    similar_names = [name for name in set_of_names_pre_underscores if n in name]
    plus_one = natural_plus_one(similar_names)
    return n + str(plus_one)


def default_mesh(name):
    verts = [(1, 1, -1), (1, -1, -1), (-1, -1, -1)]
    faces = [(0, 1, 2)]

    mesh_data = bpy.data.meshes.new(name)
    mesh_data.from_pydata(verts, [], faces)
    mesh_data.update()
    return mesh_data


def make_bmesh_geometry(node, context, name, verts, *topology):
    scene = context.scene
    meshes = bpy.data.meshes
    objects = bpy.data.objects
    edges, faces, matrix = topology

    if name in objects:
        sv_object = objects[name]
    else:
        temp_mesh = default_mesh(name)
        sv_object = objects.new(name, temp_mesh)
        scene.objects.link(sv_object)

    ''' There is overalapping code here for testing! '''

    mesh = sv_object.data
    current_count = len(mesh.vertices)
    propose_count = len(verts)
    difference = (propose_count - current_count)

    ''' With this mode you make a massive assumption about the
        constant state of geometry. Assumes the count of verts
        edges/faces stays the same, and only updates the locations

        node.fixed_verts is not suitable for initial object creation
        but if over time you find that the only change is going to be
        vertices, this mode can be switched to to increase efficiency
    '''
    if node.fixed_verts and difference == 0:
        f_v = list(itertools.chain.from_iterable(verts))
        mesh.vertices.foreach_set('co', f_v)
    else:

        ''' get bmesh, write bmesh to obj, free bmesh'''
        bm = bmesh_from_pydata(verts, edges, faces)
        bm.to_mesh(sv_object.data)
        bm.free()
        sv_object.hide_select = False

    if matrix:
        sv_object.matrix_local = list(zip(*matrix))


class SvBmeshViewOp(bpy.types.Operator):

    bl_idname = "node.showhide_bmesh"
    bl_label = "Sverchok bmesh showhide"
    bl_options = {'REGISTER', 'UNDO'}

    fn_name = StringProperty(default='')

    def hide_unhide(self, context, type_op):
        n = context.node
        k = n.basemesh_name + "_"

        # maybe do hash+(obj_name + treename)
        child = lambda obj: obj.type == "MESH" and obj.name.startswith(k)
        objs = list(filter(child, bpy.data.objects))

        if type_op == 'hide_view':
            for obj in objs:
                obj.hide = n.state_view
            n.state_view = not n.state_view

        elif type_op == 'hide_render':
            for obj in objs:
                obj.hide_render = n.state_render
            n.state_render = not n.state_render

        elif type_op == 'hide_select':
            for obj in objs:
                obj.hide_select = n.state_select
            n.state_select = not n.state_select

        elif type_op == 'mesh_select':
            for obj in objs:
                obj.select = n.select_state_mesh
            n.select_state_mesh = not n.select_state_mesh

        elif type_op == 'random_mesh_name':
            n.basemesh_name = get_random_init()

    def execute(self, context):
        self.hide_unhide(context, self.fn_name)
        return {'FINISHED'}


class BmeshViewerNode(bpy.types.Node, SverchCustomTreeNode):

    bl_idname = 'BmeshViewerNode'
    bl_label = 'Bmesh Viewer Draw'
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
    grouping = BoolProperty(default=False)
    state_view = BoolProperty(default=True)
    state_render = BoolProperty(default=True)
    state_select = BoolProperty(default=True)
    select_state_mesh = BoolProperty(default=False)

    fixed_verts = BoolProperty(
        default=False,
        name="Fixed vertices",
        description="Use only with unchanging topology")
    autosmooth = BoolProperty(
        default=False,
        update=updateNode,
        description="This auto sets all faces to smooth shade")

    def init(self, context):
        self.use_custom_color = True
        self.inputs.new('VerticesSocket', 'vertices', 'vertices')
        self.inputs.new('StringsSocket', 'edges', 'edges')
        self.inputs.new('StringsSocket', 'faces', 'faces')
        self.inputs.new('MatrixSocket', 'matrix', 'matrix')

    def draw_buttons(self, context, layout):
        view_icon = 'RESTRICT_VIEW_' + ('OFF' if self.activate else 'ON')
        sh = 'node.showhide_bmesh'

        def icons(button_type):
            icon = 'WARNING'
            if button_type == 'v':
                icon = 'RESTRICT_VIEW_' + ['ON', 'OFF'][self.state_view]
            elif button_type == 'r':
                icon = 'RESTRICT_RENDER_' + ['ON', 'OFF'][self.state_render]
            elif button_type == 's':
                icon = 'RESTRICT_SELECT_' + ['ON', 'OFF'][self.state_select]
            return icon
        
        #split = row.split()
        col = layout.column(align=True)
        row = col.row(align=True)
        #split = row.split()
        #r = split.column()
        row.column().prop(self, "activate", text="UPD", toggle=True, icon=view_icon)
        
        #row = layout.row(align=True)
        #split = row.split()
        #col1 = split.column()
        #col1.prop(self, "activate", text="Update")


        #split = split.split()
        #if split:
        #row = col.row(align=True)
        row.operator(sh, text='', icon=icons('v')).fn_name = 'hide_view'
        row.operator(sh, text='', icon=icons('s')).fn_name = 'hide_select'
        row.operator(sh, text='', icon=icons('r')).fn_name = 'hide_render'


        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(self, "grouping", text="Group", toggle=True)
        #row.split()
        row = col.row(align=True)
        row.scale_y = 1
        row.prop(self, "basemesh_name", text="", icon='OUTLINER_OB_MESH')

        row = col.row(align=True)
        row.scale_y = 2
        row.operator(sh, text='Select / Deselect').fn_name = 'mesh_select'
        row = col.row(align=True)
        row.scale_y = 1

        # row.prop(self, "material", text="", icon='MATERIAL_DATA')
        row.prop_search(self, 'material', bpy.data, 'materials', text='', icon='MATERIAL_DATA')

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.separator()

        row = layout.row(align=True)
        sh = 'node.showhide_bmesh'
        row.operator(sh, text='Random Name').fn_name = 'random_mesh_name'

        col = layout.column(align=True)
        box = col.box()
        if box:
            box.label(text="Beta options")
            box.prop(self, "fixed_verts", text="Fixed vert count")
            box.prop(self, 'autosmooth', text='smooth shade')

    def get_corrected_data(self, socket_name, socket_type):
        inputs = self.inputs
        socket = inputs[socket_name].links[0].from_socket
        if isinstance(socket, socket_type):
            socket_in = SvGetSocketAnyType(self, inputs[socket_name])
            return dataCorrect(socket_in)
        else:
            return []

    def get_geometry_from_sockets(self):
        inputs = self.inputs
        get_data = lambda s, t: self.get_corrected_data(s, t) if inputs[s].links else []

        mverts = get_data('vertices', VerticesSocket)
        mmtrix = get_data('matrix', MatrixSocket)
        medges = get_data('edges', StringsSocket)
        mfaces = get_data('faces', StringsSocket)
        return mverts, medges, mfaces, mmtrix

    def get_structure(self, stype, sindex):
        if not stype:
            return []

        try:
            j = stype[sindex]
        except IndexError:
            j = []
        finally:
            return j

    def set_dormant_color(self):
        self.color = (0.5, 0.5, 0.5)

    def update(self):

        # startup safety net
        try:
            l = bpy.data.node_groups[self.id_data.name]
        except Exception as e:
            print(self.name, "cannot run during startup, press update.")
            self.set_dormant_color()
            return

        # explicit statement about which states are useful to process.
        if not self.activate:
            self.set_dormant_color()
            return

        inputs = self.inputs
        if not ('matrix' in inputs) or not self.inputs['vertices'].links:
            self.set_dormant_color()
            return

        self.color = (1, 0.3, 0)
        self.process()

    def process(self):
        mverts, *mrest = self.get_geometry_from_sockets()

        def get_edges_faces_matrices(obj_index):
            for geom in mrest:
                yield self.get_structure(geom, obj_index)

        # extend all non empty lists to longest of mverts or *mrest
        maxlen = max(len(mverts), *(map(len, mrest)))
        fullList(mverts, maxlen)
        for idx in range(3):
            if mrest[idx]:
                fullList(mrest[idx], maxlen)

        for obj_index, Verts in enumerate(mverts):
            if not Verts:
                continue

            data = get_edges_faces_matrices(obj_index)
            mesh_name = self.basemesh_name + "_" + str(obj_index)
            make_bmesh_geometry(self, bpy.context, mesh_name, Verts, *data)

        self.remove_non_updated_objects(obj_index)
        objs = self.get_children()

        if self.grouping:
            self.to_group(objs)

        # truthy if self.material is in .materials
        if bpy.data.materials.get(self.material):
            self.set_corresponding_materials(objs)

        if self.autosmooth:
            self.set_autosmooth(objs)

    def get_children(self):
        objects = bpy.data.objects
        objs = [obj for obj in objects if obj.type == 'MESH']
        return [o for o in objs if o.name.startswith(self.basemesh_name + "_")]

    def remove_non_updated_objects(self, obj_index):
        objs = self.get_children()
        objs = [obj.name for obj in objs if int(obj.name.split("_")[-1]) > obj_index]
        if not objs:
            return

        meshes = bpy.data.meshes
        objects = bpy.data.objects
        scene = bpy.context.scene

        # remove excess objects
        for object_name in objs:
            obj = objects[object_name]
            obj.hide_select = False
            scene.objects.unlink(obj)
            objects.remove(obj)

        # delete associated meshes
        for object_name in objs:
            meshes.remove(meshes[object_name])

    def to_group(self, objs):
        groups = bpy.data.groups
        named = self.basemesh_name

        # alias group, or generate new group and alias that
        group = groups.get(named, groups.new(named))

        for obj in objs:
            if obj.name not in group.objects:
                group.objects.link(obj)

    def set_corresponding_materials(self, objs):
        for obj in objs:
            obj.active_material = bpy.data.materials[self.material]

    def set_autosmooth(self, objs):
        for obj in objs:
            mesh = obj.data
            smooth_states = [True] * len(mesh.polygons)
            mesh.polygons.foreach_set('use_smooth', smooth_states)
            mesh.update()

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(BmeshViewerNode)
    bpy.utils.register_class(SvBmeshViewOp)


def unregister():
    bpy.utils.unregister_class(BmeshViewerNode)
    bpy.utils.unregister_class(SvBmeshViewOp)

if __name__ == '__main__':
    register()
