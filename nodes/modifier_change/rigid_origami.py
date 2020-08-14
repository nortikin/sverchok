# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
from bpy.props import IntProperty, FloatProperty
from sverchok.data_structure import updateNode, match_long_repeat
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.utils.rigid_origami_utils import ObjectParams, \
		CreaseLines, InsideVertex, FoldAngleCalculator, FaceRotation

class SvRigidOrigamiNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Rigid Origami
    Tooltip: Fold a paper like a rigid origami
    """

    bl_idname = 'SvRigidOrigamiNode'
    bl_label = 'Rigid Origami'
    bl_icon = 'OUTLINER_OB_EMPTY'
    # sv_icon = ''

    folding_ratio : FloatProperty(
        name = "Folding ratio",
        description = "folding ratio from 0.0 to 1.0",
        default = 0.0,
        min = 0.0, max = 1.0,
        update = updateNode)

    division_count : IntProperty(
        name = "Division count",
        description = "Count of dividing angles to calculate precisely",
        default = 20,
        min = 1, max = 100,
        update = updateNode)

    fixed_face_index : IntProperty(
        name = "Fixed face index",
        description = "index of fixed face when folding",
        default = 0,
        update = updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Vertices')
        self.inputs.new('SvStringsSocket', 'Edges')
        self.inputs.new('SvStringsSocket', 'Faces')

        self.inputs.new('SvStringsSocket', 'Fold edge indices')
        self.inputs.new('SvStringsSocket', 'Fold edge angles')

        self.inputs.new('SvStringsSocket', 'Folding ratio').prop_name = 'folding_ratio'
        self.inputs.new('SvStringsSocket', 'Division count').prop_name = 'division_count'
        self.inputs.new('SvStringsSocket', 'Fixed face index').prop_name = 'fixed_face_index'

        self.outputs.new('SvVerticesSocket', 'Vertices')

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return
        
        if not self.inputs['Fold edge indices'].is_linked \
                or not self.inputs['Fold edge angles'].is_linked:
                    return
        
        verts_in = self.inputs['Vertices'].sv_get()
        edges_in = self.inputs['Edges'].sv_get()
        faces_in = self.inputs['Faces'].sv_get()

        fold_edge_indices = self.inputs['Fold edge indices'].sv_get()
        fold_edge_angles = self.inputs['Fold edge angles'].sv_get()

        folding_ratio = self.inputs['Folding ratio'].sv_get()
        division_count = self.inputs['Division count'].sv_get()
        fixed_face_index = self.inputs['Fixed face index'].sv_get()

        meshes = match_long_repeat([verts_in, edges_in, faces_in, \
                fold_edge_indices, fold_edge_angles, folding_ratio, \
                division_count, fixed_face_index])

        verts_out = []
        for verts, edges, faces, edge_indices, edge_angles, \
                folding, step, fixed_face in zip(*meshes):

            if isinstance(folding, (list, tuple)):
                folding = folding[0]
            if isinstance(step, (list, tuple)):
                step = step[0]
            if isinstance(fixed_face, (list, tuple)):
                fixed_face = fixed_face[0]

            verts_o = verts
            try:
                # Wrap object
                obj = ObjectParams(verts, edges, faces)

                # Extract crease lines
                crease_lines = CreaseLines(obj, edge_indices, edge_angles, folding)

                if edge_indices:
                    # Extract inside vertices
                    inside_vertices = InsideVertex.generate_inside_vertices( \
                                        obj, crease_lines)
                    # Calculation loop to determine the final angles
                    FoldAngleCalculator.calc_fold_angle(step, crease_lines, inside_vertices)

                    crease_lines.delta_angles = [cur_rho - angle for cur_rho, angle \
                                in zip(FoldAngleCalculator.current_rhos, crease_lines.angles)]

                    # Rotate each faces using final angles
                    FaceRotation.obj = obj
                    FaceRotation.inside_vertices = inside_vertices
                    FaceRotation.crease_lines = crease_lines
                    FaceRotation.fixed_face_index = int(fixed_face)
                    verts_o = FaceRotation.rotate_faces()

                verts_out.append(verts_o)
            finally:
                if obj is not None:
                    obj.free()

        self.outputs['Vertices'].sv_set(verts_out)

def register():
    bpy.utils.register_class(SvRigidOrigamiNode)

def unregister():
    bpy.utils.unregister_class(SvRigidOrigamiNode)
