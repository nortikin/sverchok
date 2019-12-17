# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from time import time
from itertools import chain

import bpy
from mathutils import Vector

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode
from sverchok.utils.geom_2d.merge_mesh import crop_mesh, crop_edges
from sverchok.utils.geom_2d.lin_alg import is_ccw_polygon

try:
    from mathutils.geometry import delaunay_2d_cdt as bl_crop_mesh
except ImportError:
    bl_crop_mesh = None


def get_bl_crop_mesh_faces(verts, faces, verts_crop, faces_crop, mode, epsilon):
    faces = [f if is_ccw_polygon([verts[i] for i in f], accuracy=epsilon) else f[::-1] for f in faces]
    faces_crop = [f if is_ccw_polygon([verts_crop[i] for i in f], accuracy=epsilon) else f[::-1] for f in faces_crop]
    merged_verts, merged_faces, faces_indexes, faces_crop_indexes = join_meshes(verts, faces, verts_crop, faces_crop)
    merged_verts = [Vector(co[:2]) for co in merged_verts]
    verts_new, _, faces_new, _, _, face_indexes = bl_crop_mesh(merged_verts, [], merged_faces, 3, epsilon)
    print(face_indexes)
    if mode == 'inner':
        faces_out = []
        for f, fi in zip(faces_new, face_indexes):
            if not fi:
                # it means new faces was generated
                continue
            in_1 = False
            in_2 = False
            for i in fi:
                if i in faces_indexes:
                    in_1 = True
                else:
                    in_2 = True
                if in_1 and in_2:
                    faces_out.append(f)
                    break
        return [v.to_3d()[:] for v in verts_new], faces_out
    else:
        faces_out = []
        for f, fi in zip(faces_new, face_indexes):
            if not fi:
                # it means new faces was generated
                continue
            in_2 = False
            for i in fi:
                if i in faces_crop_indexes:
                    in_2 = True
                    break
            if not in_2:
                faces_out.append(f)
        return [v.to_3d()[:] for v in verts_new], faces_out


def join_meshes(verts1, faces1, verts2, faces2):
    faces_out = faces1 + [[i + len(verts1) for i in f] for f in faces2]
    faces1_indexes = {i for i in range(len(faces1))}
    faces2_indexes = {i + len(faces1) for i in range(len(faces2))}
    return verts1 + verts2, faces_out, faces1_indexes, faces2_indexes


def del_loose(verts, poly_edge):
    indx = set(chain.from_iterable(poly_edge))
    verts_out = [v for i, v in enumerate(verts) if i in indx]
    v_index = dict([(j, i) for i, j in enumerate(sorted(indx))])
    poly_edge_out = [list(map(lambda n: v_index[n], p)) for p in poly_edge]
    return verts_out, poly_edge_out


class SvCropMesh2D(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Crop mesh by another mesh
    Tooltip: Can create holes or crop mesh by boundary contours

    Has hidden output socket, look N panel
    """
    bl_idname = 'SvCropMesh2D'
    bl_label = 'Crop mesh 2D'
    bl_icon = 'MOD_BOOLEAN'

    @throttled
    def update_sockets(self, context):
        [self.outputs.remove(sock) for sock in self.outputs[2:]]
        if self.face_index and self.input_mode == 'faces':
            self.outputs.new('SvStringsSocket', 'Face index')
        if self.inputs[1].name != self.input_mode:
            self.inputs[1].name = self.input_mode.title()
            self.outputs[1].name = self.input_mode.title()

    alg_mode_items = [(k, k, "", i) for i, k in enumerate(['Sweep line', 'Blender'])]
    mode_items = [('inner', 'Inner', 'Fit mesh', 'SELECT_INTERSECT', 0),
                  ('outer', 'Outer', 'Make hole', 'SELECT_SUBTRACT', 1)]
    input_mode_items = [('faces', 'Faces', 'Input type', 'FACESEL', 0),
                        ('edges', 'Edges', 'Input type', 'EDGESEL', 1)]

    mode: bpy.props.EnumProperty(items=mode_items, name='Mode of cropping mesh', update=updateNode,
                                 description='Switch between creating holes and fitting mesh into another mesh')
    input_mode: bpy.props.EnumProperty(items=input_mode_items, name="Type of input data", update=update_sockets,
                                       description='Switch between input mesh type')
    face_index: bpy.props.BoolProperty(name="Show face mask", update=update_sockets,
                                       description="Show output socket of index face mask")
    accuracy: bpy.props.IntProperty(name='Accuracy', update=updateNode, default=5, min=3, max=12,
                                    description='Some errors of the node can be fixed by changing this value')
    alg_mode: bpy.props.EnumProperty(items=alg_mode_items, name="Name of algorithm", update=updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'alg_mode', expand=True)
        layout.label(text='Type of input mesh:')
        col = layout.column(align=True)
        col.row().prop(self, 'input_mode', expand=True)
        col.row().prop(self, 'mode', expand=True)

    def draw_buttons_ext(self, context, layout):
        face_col = layout.column()
        if self.input_mode == 'edges':
            face_col.active = False
        face_col.prop(self, 'face_index', toggle=True)
        layout.prop(self, 'accuracy')

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Verts')
        self.inputs.new('SvStringsSocket', "Faces")
        self.inputs.new('SvVerticesSocket', 'Verts Crop')
        self.inputs.new('SvStringsSocket', "Faces Crop")
        self.outputs.new('SvVerticesSocket', 'Verts')
        self.outputs.new('SvStringsSocket', "Faces")

    def process(self):
        if not all([sock.is_linked for sock in self.inputs]):
            return
        if self.alg_mode == "Blender" and not bl_crop_mesh:
            return
        t = time()
        out = []
        for sv_verts, sv_faces_edges, sv_verts_crop, sv_faces_crop in zip(self.inputs['Verts'].sv_get(),
                                                                    self.inputs[1].sv_get(),
                                                                    self.inputs['Verts Crop'].sv_get(),
                                                                    self.inputs['Faces Crop'].sv_get()):
            if self.input_mode == 'faces':
                if self.alg_mode == 'Sweep line':
                    out.append(crop_mesh(sv_verts, sv_faces_edges, sv_verts_crop, sv_faces_crop, self.face_index,
                                         self.mode, self.accuracy))
                else:
                    out.append(get_bl_crop_mesh_faces(sv_verts, sv_faces_edges, sv_verts_crop, sv_faces_crop,
                                                      self.mode, 1 / 10 ** self.accuracy))
            else:
                out.append(crop_edges(sv_verts, sv_faces_edges, sv_verts_crop, sv_faces_crop, self.mode, self.accuracy))
        print(self.alg_mode, ": ", time() - t)
        if self.face_index and self.input_mode == 'faces':
            out_verts, out_faces_edges, face_index = zip(*out)
            self.outputs['Face index'].sv_set(face_index)
        else:
            out_verts, out_faces_edges = zip(*out)
        self.outputs['Verts'].sv_set(out_verts)
        self.outputs[1].sv_set(out_faces_edges)


def register():
    bpy.utils.register_class(SvCropMesh2D)


def unregister():
    bpy.utils.unregister_class(SvCropMesh2D)
