# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from itertools import chain, cycle

import bpy
from mathutils import Vector

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, no_space
from sverchok.utils.geom_2d.merge_mesh import crop_mesh, crop_edges, crop_mesh_delaunay
from sverchok.utils.decorators import deprecated

@deprecated("Use sverchok.utils.geom_2d.merge_mesh.crop_mesh_delaunay")
def get_bl_crop_mesh_faces(verts, faces, verts_crop, faces_crop, mode, epsilon):
    return crop_mesh_delaunay(verts, faces, verts_crop, faces_crop, mode, epsilon)

@deprecated("Does not work properly")
def get_bl_crop_mesh_edges(verts, edges, verts_crop, faces_crop, mode, epsilon):
    # well, it does not work, delaunay function does not give enough information
    # about location mesh relatively to each other. Can be implemented with help of some another algorithm
    m_verts, m_edges, m_faces = join_meshes2(verts, edges, verts_crop, faces_crop)
    m_verts = [Vector(co[:2]) for co in m_verts]
    verts_new, edges_new, faces_new, _, _, _ = bl_crop_mesh(m_verts, m_edges, m_faces, 2, epsilon)
    return [v.to_3d() for v in verts_new], edges_new


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
        if self.alg_mode == 'Sweep_line':
            if self.inputs[1].name != self.input_mode:
                self.inputs[1].name = self.input_mode.title()
                self.outputs[1].name = self.input_mode.title()
        else:
            if self.inputs[1].name != 'Faces':
                self.inputs[1].name = 'Faces'
                self.outputs[1].name = 'Faces'

    alg_mode_items = [(no_space(k), k, "", i) for i, k in enumerate(['Sweep line', 'Blender'])]
    mode_items = [('inner', 'Inner', 'Fit mesh', 'SELECT_INTERSECT', 0),
                  ('outer', 'Outer', 'Make hole', 'SELECT_SUBTRACT', 1)]
    input_mode_items = [('faces', 'Faces', 'Input type', 'FACESEL', 0),
                        ('edges', 'Edges', 'Input type', 'EDGESEL', 1)]

    mode: bpy.props.EnumProperty(
        items=mode_items, name='Mode of cropping mesh', update=updateNode,
        description='Switch between creating holes and fitting mesh into another mesh')

    input_mode: bpy.props.EnumProperty(
        items=input_mode_items, name="Type of input data", update=update_sockets,
        description='Switch between input mesh type')

    accuracy: bpy.props.IntProperty(
        name='Accuracy', update=updateNode, default=5, min=3, max=12,
        description='Some errors of the node can be fixed by changing this value')

    alg_mode: bpy.props.EnumProperty(
        items=alg_mode_items, name="Name of algorithm", update=update_sockets, default="Sweep_line")

    def draw_buttons(self, context, layout):
        layout.prop(self, 'alg_mode', expand=True)
        col = layout.column(align=True)
        col.label(text='Type of input mesh:')
        if self.alg_mode == 'Sweep_line':
            col.row().prop(self, 'input_mode', expand=True)
        else:
            col.row().label(text='Faces', icon='FACESEL')
        col.row().prop(self, 'mode', expand=True)

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, 'accuracy')

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Verts')
        self.inputs.new('SvStringsSocket', "Faces")
        self.inputs.new('SvVerticesSocket', 'Verts Crop')
        self.inputs.new('SvStringsSocket', "Faces Crop")
        self.outputs.new('SvVerticesSocket', 'Verts')
        self.outputs.new('SvStringsSocket', "Faces")
        self.outputs.new('SvStringsSocket', 'Face index')

    def process(self):
        if not all([sock.is_linked for sock in self.inputs]):
            return
        if self.alg_mode == "Blender" and not crop_mesh_delaunay:
            return

        max_len = max([len(sock.sv_get(deepcopy=False)) for sock in self.inputs])
        in_verts = chain(self.inputs['Verts'].sv_get(), cycle([self.inputs['Verts'].sv_get(deepcopy=False)[-1]]))
        in_edges_faces = chain(self.inputs[1].sv_get(), cycle([self.inputs[1].sv_get(deepcopy=False)[-1]]))
        in_verts_crop = chain(self.inputs['Verts Crop'].sv_get(),
                              cycle([self.inputs['Verts Crop'].sv_get(deepcopy=False)[-1]]))
        in_faces_crop = chain(self.inputs['Faces Crop'].sv_get(),
                              cycle([self.inputs['Faces Crop'].sv_get(deepcopy=False)[-1]]))

        out = []
        for i, sv_verts, sv_faces_edges, sv_verts_crop, sv_faces_crop in zip(range(max_len), in_verts, in_edges_faces,
                                                                             in_verts_crop, in_faces_crop):
            if self.input_mode == 'faces':
                if self.alg_mode == 'Sweep_line':
                    out.append(crop_mesh(sv_verts, sv_faces_edges, sv_verts_crop, sv_faces_crop,
                                         self.mode, self.accuracy))
                else:
                    out.append(crop_mesh_delaunay(sv_verts, sv_faces_edges, sv_verts_crop, sv_faces_crop,
                                                      self.mode, 1 / 10 ** self.accuracy))
            else:
                out.append(crop_edges(sv_verts, sv_faces_edges, sv_verts_crop, sv_faces_crop, self.mode, self.accuracy))
        if self.input_mode == 'faces':
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
