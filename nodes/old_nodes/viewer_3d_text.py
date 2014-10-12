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
from bpy.props import BoolProperty, StringProperty

from node_tree import (SverchCustomTreeNode, VerticesSocket,
                       MatrixSocket, StringsSocket)
from data_structure import dataCorrect, fullList, updateNode, SvGetSocketAnyType
from utils.sv_bmesh_utils import bmesh_from_pydata

import random

        
def get_random_init():
    greek_alphabet = [
        'Alpha', 'Beta', 'Gamma', 'Delta',
        'Epsilon', 'Zeta', 'Eta', 'Theta',
        'Iota', 'Kappa', 'Lamda', 'Mu',
        'Nu', 'Xi', 'Omicron', 'Pi',
        'Rho', 'Sigma', 'Tau', 'Upsilon',
        'Phi', 'Chi', 'Psi', 'Omega']
    return random.choice(greek_alphabet)


def default_mesh(name):
    verts = [(1, 1, -1), (1, -1, -1), (-1, -1, -1)]
    faces = [(0, 1, 2)]

    mesh_data = bpy.data.meshes.new(name)
    mesh_data.from_pydata(verts, [], faces)
    mesh_data.update()
    return mesh_data


def make_bmesh_geometry(context, name, verts, edges, faces, matrix):
    # no verts. no processing.
    if not verts:
        return

    scene = context.scene
    meshes = bpy.data.meshes
    objects = bpy.data.objects

    if name in objects:
        sv_object = objects[name]
    else:
        temp_mesh = default_mesh(name)
        sv_object = objects.new(name, temp_mesh)
        scene.objects.link(sv_object)
        scene.update()

    # definitely verts, definitely do something.
    bm = bmesh_from_pydata(verts, edges, faces)

    # Finish up, write the bmesh back to the mesh
    bm.to_mesh(sv_object.data)
    bm.free()  # free and prevent further access

    sv_object.hide_select = False

    # apply matrices if necessary
    if matrix:
        sv_object.matrix_local = list(zip(*matrix))


class SvBmeshViewOp(bpy.types.Operator):
    ''' Pick random greek leter or select meshes in scene '''
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
            n.randname_choosed = True

    def execute(self, context):
        self.hide_unhide(context, self.fn_name)
        return {'FINISHED'}


class BmeshViewerNode(bpy.types.Node, SverchCustomTreeNode):

    bl_idname = 'BmeshViewerNode'
    bl_label = 'Bmesh Viewer Draw'
    bl_icon = 'OUTLINER_OB_EMPTY'

    activate = BoolProperty(
        name='Show', description='Activate node?',
        default=True,
        update=updateNode)

    basemesh_name = StringProperty(default='Alpha', update=updateNode)
    material = StringProperty(default='', update=updateNode)
    randname_choosed = BoolProperty(default=False)
    grouping = BoolProperty(default=False)
    state_view = BoolProperty(default=True)
    state_render = BoolProperty(default=True)
    state_select = BoolProperty(default=True)
    select_state_mesh = BoolProperty(default=False)

    def init(self, context):
        self.inputs.new('VerticesSocket', 'vertices', 'vertices')
        self.inputs.new('StringsSocket', 'edges', 'edges')
        self.inputs.new('StringsSocket', 'faces', 'faces')
        self.inputs.new('MatrixSocket', 'matrix', 'matrix')

    def draw_buttons(self, context, layout):
        row = layout.row(align=True)
        split = row.split()
        col1 = split.column()
        col1.prop(self, "activate", text="Update")

        def icons(button_type):
            icon = 'WARNING'
            if button_type == 'v':
                state = self.state_view
                icon = 'RESTRICT_VIEW_OFF' if state else 'RESTRICT_VIEW_ON'
            elif button_type == 'r':
                state = self.state_render
                icon = 'RESTRICT_RENDER_OFF' if state else 'RESTRICT_RENDER_ON'
            elif button_type == 's':
                state = self.state_select
                icon = 'RESTRICT_SELECT_OFF' if state else 'RESTRICT_SELECT_ON'

            return icon

        split = split.split()
        col2 = split.column()
        sh = 'node.showhide_bmesh'
        col2.operator(sh, text='', icon=icons('v')).fn_name = 'hide_view'
        col3 = split.column()
        col3.operator(sh, text='', icon=icons('s')).fn_name = 'hide_select'
        col4 = split.column()
        col4.operator(sh, text='', icon=icons('r')).fn_name = 'hide_render'

        row = layout.row()
        row.prop(self, "grouping", text="to Group")

        layout.label("Base mesh name(s)", icon='OUTLINER_OB_MESH')
        #row = layout.row()
        #row.prop(self, "basemesh_name", text="")
        # this is button to randomise
        col = layout.column(align=True)
        row = col.row(align=True)
        row.scale_y = 1.1
        row.prop(self, "basemesh_name", text="")
        if not self.randname_choosed:
            row.operator(sh, text='Random Name').fn_name = 'random_mesh_name'
        row = col.row(align=True)
        row.scale_y = 0.9
        row.operator(sh, text='Select/Deselect').fn_name = 'mesh_select'
        row = col.row(align=True)
        row.scale_y = 0.9
        # row.template_ID
        row.prop(self, "material", text="mat.")

    # execution of text
    def execute(self, context):
        obj = bpy.context.selected_objects
        
        for ob in obj:
            mw = ob.matrix_world
            name_all = re.match(r'(\w+)', ob.name)
            name = name_all.group(1)
            len = 1#abs(max(ob.dimensions) * (sum(mw.to_scale()) / 3))
            #print ()
            self.run(mw,name,len)
        return {'FINISHED'}

    #text baking
    def run(self, origin,text,length):
       # Create and name TextCurve object
        bpy.ops.object.text_add(view_align=False,
        enter_editmode=False,location=origin.translation[:], 
        rotation=origin.to_euler()[:])
        ob = bpy.context.object
        ob.name = 'lable_'+str(text)
        tcu = ob.data
        tcu.name = 'lable_'+str(text)
        # TextCurve attributes
        tcu.body = str(text)
        tcu.font = bpy.data.fonts[0]
        tcu.offset_x = 0
        tcu.offset_y = -0.25
        tcu.resolution_u = 2
        tcu.shear = 0
        Tsize = self.size #* length
        tcu.size = Tsize
        tcu.space_character = 1
        tcu.space_word = 1
        tcu.align = 'CENTER'
        # Inherited Curve attributes
        tcu.extrude = 0.0
        tcu.fill_mode = 'NONE'
        
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
        mverts, medges, mfaces, mmatrix = [], [], [], []

        mverts = self.get_corrected_data('vertices', VerticesSocket)

        # could be looped, yielded..
        if 'matrix' in inputs and inputs['matrix'].links:
            mmatrix = self.get_corrected_data('matrix', MatrixSocket)

        if 'edges' in inputs and inputs['edges'].links:
            medges = self.get_corrected_data('edges', StringsSocket)

        if 'faces' in inputs and inputs['faces'].links:
            mfaces = self.get_corrected_data('faces', StringsSocket)

        return mverts, medges, mfaces, mmatrix

    def get_structure(self, stype, sindex):
        if not stype:
            return []

        try:
            j = stype[sindex]
        except IndexError:
            j = []
        finally:
            return j

    def update(self):

        # startup safety net
        try:
            l = bpy.data.node_groups[self.id_data.name]
        except Exception as e:
            print(self.name, "cannot run during startup, press update.")
            return

        # regular code from this point
        inputs = self.inputs
        if self.activate and 'vertices' in inputs and inputs['vertices'].links:
            self.use_custom_color = True
            self.color = (1, 0.3, 0)
            C = bpy.context
            mverts, *mrest = self.get_geometry_from_sockets()

            def get_edges_faces_matrices(obj_index):
                for geom in mrest:
                    yield self.get_structure(geom, obj_index)

            # matrices need to define count of objects. paradigma
            maxlen = max(len(mverts), len(mrest[0]), len(mrest[1]), len(mrest[2]))
            fullList(mverts, maxlen)
            if mrest[0]:
                fullList(mrest[0], maxlen)
            if mrest[1]:
                fullList(mrest[1], maxlen)
            if mrest[2]:
                fullList(mrest[2], maxlen)

            for obj_index, Verts in enumerate(mverts):
                if not Verts:
                    continue

                data = get_edges_faces_matrices(obj_index)
                mesh_name = self.basemesh_name + "_" + str(obj_index)
                make_bmesh_geometry(C, mesh_name, Verts, *data)

            self.remove_non_updated_objects(obj_index, self.basemesh_name)
            self.set_corresponding_materials()
            if self.inputs['vertices'].links:
                if self.grouping:
                    self.to_group()
                if self.material:
                    self.set_corresponding_materials()
        else:
            self.use_custom_color = True
            self.color = (0.1, 0.05, 0)

    def to_group(self):
        # this def for grouping objects in scene
        objs = bpy.data.objects
        if self.basemesh_name not in bpy.data.groups:
            newgroup = bpy.data.groups.new(self.basemesh_name)
        else:
            newgroup = bpy.data.groups[self.basemesh_name]
        for obj in objs:
            if self.basemesh_name in obj.name:
                if obj.name not in newgroup.objects:
                    newgroup.objects.link(obj)

    def remove_non_updated_objects(self, obj_index, _name):

        meshes = bpy.data.meshes
        objects = bpy.data.objects

        objs = [obj for obj in objects if obj.type == 'MESH']
        objs = [obj for obj in objs if obj.name.startswith(_name)]
        objs = [obj.name for obj in objs if int(obj.name.split("_")[-1]) > obj_index]
        if not objs:
            return

        # select and finally remove all excess objects
        scene = bpy.context.scene  # fix for render mode is needed?

        for object_name in objs:
            obj = objects[object_name]
            obj.hide_select = False  # needed?
            scene.objects.unlink(obj)
            objects.remove(obj)

        # delete associated meshes
        for object_name in objs:
            meshes.remove(meshes[object_name])

        # fingers crossed 2x.

    def set_corresponding_materials(self):
        objs = bpy.data.objects
        for obj in objs:
            # if this object is made by bmesh - assign material of 'object_0'
            if obj.name.startswith(self.basemesh_name + "_"):
                if self.material in bpy.data.materials:
                    obj.active_material = bpy.data.materials[self.material]

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

