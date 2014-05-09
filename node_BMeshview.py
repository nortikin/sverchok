import bpy
import bmesh
import mathutils
from mathutils import Vector, Matrix
from bpy.props import BoolProperty, FloatVectorProperty

from node_s import *
from util import *
import random


def default_mesh(name):
    verts = [(1, 1, -1), (1, -1, -1), (-1, -1, -1)]
    faces = [(0, 1, 2)]

    mesh_data = bpy.data.meshes.new(name)
    mesh_data.from_pydata(verts, [], faces)
    mesh_data.update()
    return mesh_data


def bmesh_from_pydata(verts=[], edges=[], faces=[]):
    ''' verts is necessary, edges/faces are optional '''

    bm = bmesh.new()
    [bm.verts.new(co) for co in verts]
    bm.verts.index_update()

    if faces:
        for face in faces:
            bm.faces.new(tuple(bm.verts[i] for i in face))
        bm.faces.index_update()

    if edges:
        for edge in edges:
            edge_seq = tuple(bm.verts[i] for i in edge)
            try:
                bm.edges.new(edge_seq)
            except ValueError:
                # edge exists!
                pass

        bm.edges.index_update()

    return bm


def make_bmesh_geometry(context, name, obj_location, verts, edges, faces, matrix):
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

    sv_object.hide_select = True
    sv_object.location = obj_location

    # apply matrices if necessary
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

        if type_op == 'hide_render':
            for obj in objs:
                obj.hide_render = n.state_render
            n.state_render = not n.state_render

    def execute(self, context):
        self.hide_unhide(context, self.fn_name)
        return {'FINISHED'}


class BmeshViewerNode(Node, SverchCustomTreeNode):

    bl_idname = 'BmeshViewerNode'
    bl_label = 'Bmesh Viewer Draw'
    bl_icon = 'OUTLINER_OB_EMPTY'

    def get_random_init():
        greek_alphabet = [
            'Alpha', 'Beta', 'Gamma', 'Delta',
            'Epsilon', 'Zeta', 'Eta', 'Theta',
            'Iota', 'Kappa', 'Lamda', 'Mu',
            'Nu', 'Xi', 'Omicron', 'Pi',
            'Rho', 'Sigma', 'Tau', 'Upsilon',
            'Phi', 'Chi', 'Psi', 'Omega']
        return random.choice(greek_alphabet)

    activate = BoolProperty(
        name='Show', description='Activate node?',
        default=True,
        update=updateNode)

    basemesh_name = StringProperty(default=get_random_init())
    state_view = BoolProperty(default=True)
    state_render = BoolProperty(default=True)

    def init(self, context):
        self.inputs.new('VerticesSocket', 'vertices', 'vertices')
        self.inputs.new('StringsSocket', 'edges', 'edges')
        self.inputs.new('StringsSocket', 'faces', 'faces')
        self.inputs.new('MatrixSocket', 'matrix', 'matrix')
        self.inputs.new('VerticesSocket', 'obj.location', 'obj.location')

    def draw_buttons(self, context, layout):
        row = layout.row(align=True)
        row.prop(self, "activate", text="Update")

        row = layout.row()
        row.alignment = 'RIGHT'

        def icons(button_type):
            icon = 'WARNING'
            if button_type == 'v':
                state = self.state_view
                icon = 'RESTRICT_VIEW_OFF' if state else 'RESTRICT_VIEW_ON'
            elif button_type == 'r':
                state = self.state_render
                icon = 'RESTRICT_RENDER_OFF' if state else 'RESTRICT_RENDER_ON'
            return icon

        sh = 'node.showhide_bmesh'
        row.operator(sh, text='', icon=icons('v')).fn_name = 'hide_view'
        row.operator(sh, text='', icon=icons('r')).fn_name = 'hide_render'

        layout.label("Base mesh name(s)", icon='OUTLINER_OB_MESH')
        row = layout.row()
        row.prop(self, "basemesh_name", text="")

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
        mverts, medges, mfaces, mmatrix, mobj_loc = [], [], [], [], [[]]

        mverts = self.get_corrected_data('vertices', VerticesSocket)

        # could be looped, yielded..
        if 'matrix' in inputs and inputs['matrix'].links:
            mmatrix = self.get_corrected_data('matrix', MatrixSocket)

        if 'edges' in inputs and inputs['edges'].links:
            medges = self.get_corrected_data('edges', StringsSocket)

        if 'faces' in inputs and inputs['faces'].links:
            mfaces = self.get_corrected_data('faces', StringsSocket)

        if 'obj.location' in inputs and inputs['obj.location'].links:
            mobj_loc = self.get_corrected_data('obj.location', VerticesSocket)

        return mverts, medges, mfaces, mmatrix, mobj_loc[0]

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
        if not self.activate or not ('vertices' in self.inputs):
            return

        if not self.inputs['vertices'].links:
            return

        C = bpy.context
        mverts, *mrest = self.get_geometry_from_sockets()

        def get_all_structures(obj_index):
            for geom in mrest:
                yield self.get_structure(geom, obj_index)

        location = (0, 0, 0)
        for obj_index, Verts in enumerate(mverts):
            if not Verts:
                continue

            *edges_faces_matrix, obj_location = get_all_structures(obj_index)
            if obj_location:
                location = obj_location

            mesh_name = self.basemesh_name + "_" + str(obj_index)
            make_bmesh_geometry(C, mesh_name, location, Verts, *edges_faces_matrix)

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(BmeshViewerNode)
    bpy.utils.register_class(SvBmeshViewOp)


def unregister():
    bpy.utils.unregister_class(BmeshViewerNode)
    bpy.utils.unregister_class(SvBmeshViewOp)
