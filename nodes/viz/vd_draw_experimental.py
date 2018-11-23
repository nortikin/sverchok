# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


import bpy
import gpu
from gpu_extras.batch import batch_for_shader

# import mathutils
from mathutils import Vector, Matrix
from mathutils.geometry import tessellate_polygon as tessellate

import sverchok
from bpy.props import StringProperty, BoolProperty, FloatVectorProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import node_id, updateNode
from sverchok.ui.bgl_callback_3dview import callback_disable, callback_enable
from sverchok.utils.sv_batch_primitives import MatrixDraw28
from sverchok.utils.geom import multiply_vectors_deep


def edges_from_faces(indices):
    """ we don't want repeat edges, ever.."""
    out = set()
    concat = out.add
    for face in indices:
        for edge in zip(face, list(face[1:]) + list([face[0]])):
            concat(tuple(sorted(edge)))
    return list(out)

def ensure_triangles(coords, indices):
    new_indices = []
    concat = new_indices.append
    concat2 = new_indices.extend
    for idxset in indices:
        num_verts = len(idxset)
        if num_verts == 3:
            concat(tuple(idxset))
        elif num_verts == 4:
            # a b c d  ->  [a, b, c], [a, c, d]
            concat2([(idxset[0], idxset[1], idxset[2]), (idxset[0], idxset[2], idxset[3])])
        else:
            subcoords = [Vector(coords[idx]) for idx in idxset]
            for pol in tessellate([subcoords]):
                concat([idxset[i] for i in pol])
    return new_indices    

def screen_v3dMatrix(context, args):
    mdraw = MatrixDraw28()
    for matrix in args[0]:
        mdraw.draw_matrix(matrix)

def draw_edges(context, args):
    geom, line4f = args
    coords, indices = geom.verts, geom.edges

    shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
    batch = batch_for_shader(shader, 'LINES', {"pos" : coords}, indices=indices)
    shader.bind()
    shader.uniform_float("color", line4f)
    batch.draw(shader)

def draw_faces(context, args):
    geom, config = args
    coords, indices = geom.verts, geom.faces

    new_indices = ensure_triangles(coords, indices)

    shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
    batch = batch_for_shader(shader, 'TRIS', {"pos" : coords}, indices=new_indices)
    shader.bind()
    shader.uniform_float("color", config.face4f)
    batch.draw(shader)

    if not config.display_edges:
        return
    
    edge_indices = edges_from_faces(indices)
    shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
    batch = batch_for_shader(shader, 'LINES', {"pos" : coords}, indices=edge_indices)
    shader.bind()
    shader.uniform_float("color", config.line4f)
    batch.draw(shader)


class SvVDExperimental(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: exp vd
    Tooltip: experimental drawing node
    
    not a very exciting node kids.
    """

    bl_idname = 'SvVDExperimental'
    bl_label = 'VD Experimental'
    bl_icon = 'GREASEPENCIL'

    n_id: StringProperty(default='')
    activate: BoolProperty(name='Show', description='Activate', default=True, update=updateNode)

    edge_color: FloatVectorProperty(
        subtype='COLOR', min=0, max=1,
        default=(0.3, 0.3, 0.3, 1.0), name='edge color', size=4, update=updateNode)

    face_color: FloatVectorProperty(
        subtype='COLOR', min=0, max=1,
        default=(0.3, 0.3, 0.3, 1.0), name='face color', size=4, update=updateNode)

    display_edges: BoolProperty(update=updateNode, name="display edges")

    def sv_init(self, context):
        inew = self.inputs.new
        inew('VerticesSocket', 'verts')
        inew('StringsSocket', 'edges')
        inew('StringsSocket', 'faces')
        inew('MatrixSocket', 'matrix')

    def draw_buttons(self, context, layout):
        layout.row().prop(self, "activate", text="ACTIVATE")
        r1 = layout.row(align=True)
        r1.label(icon="UV_EDGESEL")
        r1.prop(self, "edge_color", text='')
        r1.prop(self, "face_color", text='')
        r2 = layout.row(align=True)
        r2.prop(self, "display_edges", icon="SNAP_EDGE", expand=True, text="")

    def process(self):
        if not (self.id_data.sv_show and self.activate):
            callback_disable(node_id(self))
            return

        n_id = node_id(self)
        callback_disable(n_id)

        verts_socket, edges_socket, faces_socket, matrix_socket = self.inputs[:4]

        if verts_socket.is_linked: 
            geom = lambda: None
            config = lambda: None
            
            propv = verts_socket.sv_get(deepcopy=False, default=[])
            coords = propv[0]

            if edges_socket.is_linked:
                prope = edges_socket.sv_get(deepcopy=False, default=[])
                indices = prope[0]
            elif faces_socket.is_linked:
                propf = faces_socket.sv_get(deepcopy=False, default=[])
                indices = propf[0]

            if matrix_socket.is_linked:
                # for now just deal with first
                m = matrix_socket.sv_get(deepcopy=False, default=[Matrix()])[0]
                coords = multiply_vectors_deep(m, coords)
      
            geom.verts = coords
            
            if edges_socket.is_linked:
                geom.edges = indices
                line4f = self.edge_color[:]

                draw_data = {
                    'tree_name': self.id_data.name[:],
                    'custom_function': draw_edges,
                    'args': (geom, line4f)
                } 
                callback_enable(n_id, draw_data)
                return

            elif faces_socket.is_linked:
                geom.faces = indices
                config.line4f = self.edge_color[:]
                config.face4f = self.face_color[:]
                config.display_edges = self.display_edges

                draw_data = {
                    'tree_name': self.id_data.name[:],
                    'custom_function': draw_faces,
                    'args': (geom, config)
                } 
                callback_enable(n_id, draw_data)
                return


            return

        elif matrix_socket.is_linked:
            matrices = matrix_socket.sv_get(deepcopy=False, default=[Matrix()])

            draw_data = {
                'tree_name': self.id_data.name[:],
                'custom_function': screen_v3dMatrix,
                'args': (matrices,)
            }            

            callback_enable(n_id, draw_data)

    def copy(self, node):
        self.n_id = ''

    @property
    def fully_enabled(self):
        return "matrix" in self.inputs

    def update(self):
        if not self.fully_enabled:
            return

        try:
            socket_one_has_upstream_links = self.inputs[0].other
            socket_two_has_upstream_links = self.inputs[1].other
            
            if not socket_one_has_upstream_links:
                callback_disable(node_id(self))
        except:
            print('vd basic lines update holdout', self.n_id)


def register():
    bpy.utils.register_class(SvVDExperimental)


def unregister():
    bpy.utils.unregister_class(SvVDExperimental)
