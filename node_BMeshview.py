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

    if not verts:
        print("verts data seems empty")
        return

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


def make_bmesh_geometry(context, verts, edges, faces, matrix, origin, name):
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
    #print('origin:', origin)
    sv_object.location = origin

    # apply matrices if necessary
    if matrix:
        sv_object.data.transform(matrix)


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
        self.inputs.new('VerticesSocket', 'origins', 'origins')

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

    def get_geometry_from_sockets(self):
        inputs = self.inputs

        iv_links = inputs['vertices'].links
        mverts, medges, mfaces, mmatrix, morigins = [], [], [], [], []

        # gather vertices from input
        if isinstance(iv_links[0].from_socket, VerticesSocket):
            propv = SvGetSocketAnyType(self, inputs['vertices'])
            mverts = dataCorrect(propv)

        # matrix might be operating on vertices, check and act on.
        if 'matrix' in inputs:
            im_links = inputs['matrix'].links

            # find the transform matrices
            if im_links and isinstance(im_links[0].from_socket, MatrixSocket):
                propm = SvGetSocketAnyType(self, inputs['matrix'])
                mmatrix = dataCorrect(propm)

        data_feind = []
        for socket in ['edges', 'faces']:
            try:
                propm = SvGetSocketAnyType(self, inputs[socket])
                input_stream = dataCorrect(propm)
            except:
                input_stream = []
            finally:
                data_feind.append(input_stream)

        if 'origins' in inputs and inputs['origins'].links:
            # gather origin vectors from input
            origins_socket = inputs['origins'].links[0].from_socket
            if isinstance(origins_socket, VerticesSocket):
                origins_in = SvGetSocketAnyType(self, inputs['origins'])
                morigins = dataCorrect(origins_in)

        return mverts, data_feind[0], data_feind[1], mmatrix, morigins[0]

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

        C = bpy.context
        r = self.get_geometry_from_sockets()
        mverts, medges, mfaces, mmatrix, morigins = r

        last_origin = (0, 0, 0)
        for obj_index, Verts in enumerate(mverts):
            Edges = self.get_structure(medges, obj_index)
            Faces = self.get_structure(mfaces, obj_index)
            matrix = self.get_structure(mmatrix, obj_index)
            origin = self.get_structure(morigins, obj_index)
            if origin:
                last_origin = origin
            else:
                origin = last_origin

            mesh_name = self.basemesh_name + "_" + str(obj_index)
            #print('origin here:', origin)
            make_bmesh_geometry(C, Verts, Edges, Faces, matrix, origin, mesh_name)

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(BmeshViewerNode)
    bpy.utils.register_class(SvBmeshViewOp)


def unregister():
    bpy.utils.unregister_class(BmeshViewerNode)
    bpy.utils.unregister_class(SvBmeshViewOp)
